"""Server-side authentication for MLflow using Descope.

This module provides the Flask app factory for the `mlflow.app` entry point,
enabling cookie-based authentication with the Descope Web Component.

Usage:
    mlflow server --app-name descope
"""

import logging
from typing import Optional

from descope import AuthException
from flask import Flask, g, redirect, request

from .auth_routes import register_auth_routes
from .client import get_descope_client
from .config import get_config

logger = logging.getLogger(__name__)

# Public routes that don't require authentication
PUBLIC_ROUTES = {
    "/auth/login",
    "/auth/logout",
    "/auth/callback",
    "/health",
    "/version",
}

# Public route prefixes
PUBLIC_PREFIXES = [
    "/static/",
    "/_static/",
]


def _is_public_route(path: str) -> bool:
    """Check if a route is public (doesn't require authentication).

    Args:
        path: The request path.

    Returns:
        bool: True if the route is public, False otherwise.
    """
    if path in PUBLIC_ROUTES:
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)


def _before_request():
    """Validate Descope session on each request.

    This function is called before every request to the MLflow server.
    It validates the session token from cookies and sets user info in Flask g.

    Returns:
        None if authenticated, or redirect Response if not.
    """
    # Skip auth for public routes
    if _is_public_route(request.path):
        return None

    config = get_config()
    client = get_descope_client()

    # Read tokens from cookies
    session_token = request.cookies.get(config.SESSION_COOKIE_NAME)
    refresh_token = request.cookies.get(config.REFRESH_COOKIE_NAME)

    # No session token? Redirect to login
    if not session_token:
        logger.debug(f"No session token for path: {request.path}")
        return redirect("/auth/login", code=302)

    # Validate session with Descope
    try:
        jwt_response = client.validate_session(session_token, refresh_token)
        claims = client.extract_user_claims(jwt_response)

        # Store user info in Flask g for this request
        g.user_id = claims["user_id"]
        g.username = claims["username"]
        g.email = claims["email"]
        g.name = claims["name"]
        g.roles = claims["roles"]
        g.permissions = claims["permissions"]
        g.tenants = claims["tenants"]
        g.is_admin = config.is_admin_role(claims["roles"])

        # Store JWT response for potential cookie update in after_request
        g._descope_jwt_response = jwt_response
        g._descope_session_token = session_token

        logger.debug(f"Authenticated user: {claims['username']} (admin: {g.is_admin})")
        return None

    except AuthException as e:
        logger.warning(f"Session validation failed: {e}")
        return redirect("/auth/login", code=302)

    except Exception as e:
        logger.error(f"Unexpected error in auth: {e}", exc_info=True)
        return redirect("/auth/login?error=internal_error", code=302)


def _after_request(response):
    """Update session cookie if token was refreshed.

    This function is called after every request. If the session token
    was refreshed during validation, the new token is set in cookies.

    Args:
        response: The Flask Response object.

    Returns:
        The Response with updated cookies if needed.
    """
    # Check if we have a new session token from refresh
    if hasattr(g, "_descope_jwt_response"):
        jwt_response = g._descope_jwt_response
        original_token = getattr(g, "_descope_session_token", None)

        # Check if token was refreshed (new token different from original)
        new_session = jwt_response.get("sessionToken", {})
        new_jwt = new_session.get("jwt") if isinstance(new_session, dict) else None

        if new_jwt and new_jwt != original_token:
            config = get_config()

            # Update session cookie with refreshed token
            response.set_cookie(
                key=config.SESSION_COOKIE_NAME,
                value=new_jwt,
                max_age=3600,  # 1 hour
                path="/",
                secure=config.COOKIE_SECURE,
                httponly=True,
                samesite="Lax",
            )
            logger.debug(f"Updated session cookie for user: {g.username}")

    return response


def create_app(app: Optional[Flask] = None) -> Flask:
    """Create Descope-authenticated MLflow Flask app.

    This is the factory function for the `mlflow.app` entry point.
    It adds Descope authentication to the MLflow Flask server.

    Args:
        app: The MLflow Flask app. If None, imports from mlflow.server.

    Returns:
        Flask: The app with Descope authentication enabled.

    Usage:
        mlflow server --app-name descope
    """
    # Import MLflow app if not provided
    if app is None:
        from mlflow.server import app as mlflow_app

        app = mlflow_app

    config = get_config()
    logger.info(f"Initializing MLflow Descope Auth for project: {config.DESCOPE_PROJECT_ID}")

    # Register authentication routes (/auth/login, /auth/logout, etc.)
    register_auth_routes(app)

    # Add before_request hook for authentication
    app.before_request(_before_request)

    # Add after_request hook for cookie refresh
    app.after_request(_after_request)

    logger.info("MLflow Descope Auth initialized successfully")
    return app
