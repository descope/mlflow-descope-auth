"""Authentication middleware for session validation."""

import logging
from typing import Callable

from descope import AuthException
from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .client import get_descope_client
from .config import get_config

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate Descope session on each request.

    This middleware:
    1. Checks if the request path requires authentication
    2. Validates session tokens using Descope SDK
    3. Automatically refreshes expired tokens
    4. Attaches user information to request state
    5. Redirects to login if authentication fails
    """

    def __init__(self, app, descope_client=None):
        """Initialize the authentication middleware.

        Args:
            app: The FastAPI application.
            descope_client: Optional Descope client (for testing).
        """
        super().__init__(app)
        self.descope_client = descope_client or get_descope_client()
        self.config = get_config()

        # Public routes that don't require authentication
        self.public_routes = {
            "/auth/login",
            "/auth/logout",
            "/auth/health",
            "/auth/config",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        }

    def _is_public_route(self, path: str) -> bool:
        """Check if a route is public (doesn't require authentication).

        Args:
            path: The request path.

        Returns:
            bool: True if the route is public, False otherwise.
        """
        # Check exact matches
        if path in self.public_routes:
            return True

        # Check if path starts with public prefixes
        public_prefixes = ["/static/", "/_static/"]
        return any(path.startswith(prefix) for prefix in public_prefixes)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process each request through authentication middleware.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            Response: The HTTP response.
        """
        path = request.url.path

        # Skip authentication for public routes
        if self._is_public_route(path):
            return await call_next(request)

        # Get tokens from cookies
        session_token = request.cookies.get(self.config.SESSION_COOKIE_NAME)
        refresh_token = request.cookies.get(self.config.REFRESH_COOKIE_NAME)

        # If no session token, redirect to login
        if not session_token:
            logger.debug(f"No session token found for path: {path}")
            return RedirectResponse(url="/auth/login", status_code=302)

        # Validate session with Descope
        try:
            jwt_response = self.descope_client.validate_session(session_token, refresh_token)

            # Extract user claims
            claims = self.descope_client.extract_user_claims(jwt_response)

            # Attach user information to request state
            request.state.username = claims["username"]
            request.state.email = claims["email"]
            request.state.name = claims["name"]
            request.state.roles = claims["roles"]
            request.state.permissions = claims["permissions"]
            request.state.user_id = claims["user_id"]
            request.state.tenants = claims["tenants"]

            # Check if user is admin
            request.state.is_admin = self.config.is_admin_role(claims["roles"])

            logger.debug(
                f"Authenticated user: {claims['username']} "
                f"(admin: {request.state.is_admin}) for path: {path}"
            )

            # Process the request
            response = await call_next(request)

            # Check if token was refreshed and update cookie
            if jwt_response.get("cookieData"):
                session_jwt = jwt_response["sessionToken"]["jwt"]
                response.set_cookie(
                    key=self.config.SESSION_COOKIE_NAME,
                    value=session_jwt,
                    max_age=3600,  # 1 hour
                    path="/",
                    secure=True,
                    httponly=True,
                    samesite="strict",
                )
                logger.debug(f"Updated session cookie for user: {claims['username']}")

            return response

        except AuthException as e:
            # Session validation failed, redirect to login
            logger.warning(f"Session validation failed: {e}")
            return RedirectResponse(url="/auth/login", status_code=302)

        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error in authentication middleware: {e}", exc_info=True)
            return RedirectResponse(url="/auth/login?error=internal_error", status_code=302)


def require_permission(permission: str):
    """Decorator to require specific permission for a route.

    Args:
        permission: The required permission name.

    Returns:
        Callable: The decorator function.
    """

    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            if not hasattr(request.state, "permissions"):
                return {"error": "Not authenticated"}, 401

            if permission not in request.state.permissions:
                return {"error": f"Missing required permission: {permission}"}, 403

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_role(role: str):
    """Decorator to require specific role for a route.

    Args:
        role: The required role name.

    Returns:
        Callable: The decorator function.
    """

    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            if not hasattr(request.state, "roles"):
                return {"error": "Not authenticated"}, 401

            if role not in request.state.roles:
                return {"error": f"Missing required role: {role}"}, 403

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_admin(func):
    """Decorator to require admin role for a route.

    Args:
        func: The route handler function.

    Returns:
        Callable: The wrapped function.
    """

    async def wrapper(request: Request, *args, **kwargs):
        if not hasattr(request.state, "is_admin") or not request.state.is_admin:
            return {"error": "Admin access required"}, 403

        return await func(request, *args, **kwargs)

    return wrapper
