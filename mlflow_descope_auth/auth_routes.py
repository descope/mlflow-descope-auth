"""Authentication routes for MLflow Descope integration.

This module provides Flask routes for login, logout, and user info endpoints.
The login page uses the Descope Web Component for authentication.
"""

import logging
from flask import Flask, g, jsonify, make_response, redirect

from .config import get_config

logger = logging.getLogger(__name__)

# Inline HTML template for login page with Descope Web Component
LOGIN_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MLflow Login - Descope</title>
    <script src="{web_component_url}"></script>
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            padding: 2.5rem;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            text-align: center;
            max-width: 400px;
            width: 90%;
        }}
        h1 {{
            margin: 0 0 0.5rem 0;
            color: #1a1a2e;
            font-size: 1.75rem;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 1.5rem;
            font-size: 0.9rem;
        }}
        descope-wc {{
            display: block;
        }}
        .error-message {{
            background: #fee2e2;
            border: 1px solid #ef4444;
            color: #dc2626;
            padding: 0.75rem;
            border-radius: 6px;
            margin-bottom: 1rem;
            font-size: 0.875rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>MLflow</h1>
        <p class="subtitle">Sign in to continue</p>
        <div id="error-container"></div>
        <descope-wc
            project-id="{project_id}"
            flow-id="{flow_id}"
        ></descope-wc>
    </div>

    <script>
        const wcElement = document.querySelector('descope-wc');
        const errorContainer = document.getElementById('error-container');

        // Show error if redirected with error param
        const urlParams = new URLSearchParams(window.location.search);
        const error = urlParams.get('error');
        if (error) {{
            errorContainer.innerHTML = '<div class="error-message">Authentication failed. Please try again.</div>';
        }}

        wcElement.addEventListener('success', (e) => {{
            const sessionJwt = e.detail.sessionJwt;
            const refreshJwt = e.detail.refreshJwt;

            // Set cookies with appropriate options
            const secure = window.location.protocol === 'https:' ? '; secure' : '';
            const cookieBase = 'path=/; max-age=86400; samesite=lax' + secure;

            document.cookie = '{session_cookie}=' + sessionJwt + '; ' + cookieBase;
            if (refreshJwt) {{
                document.cookie = '{refresh_cookie}=' + refreshJwt + '; ' + cookieBase;
            }}

            // Redirect to MLflow UI
            window.location.href = '{redirect_url}';
        }});

        wcElement.addEventListener('error', (e) => {{
            console.error('Login error:', e.detail);
            errorContainer.innerHTML = '<div class="error-message">Login failed: ' + (e.detail.message || 'Unknown error') + '</div>';
        }});
    </script>
</body>
</html>"""


def register_auth_routes(app: Flask) -> None:
    """Register authentication routes on the Flask app.

    This adds the following routes:
    - /auth/login - Login page with Descope Web Component
    - /auth/logout - Logout endpoint (clears cookies)
    - /auth/user - Get current user info
    - /health - Health check endpoint

    Args:
        app: The Flask application.
    """
    config = get_config()

    @app.route("/auth/login")
    def auth_login():
        """Render login page with Descope Web Component."""
        html = LOGIN_TEMPLATE.format(
            web_component_url=config.web_component_url,
            project_id=config.DESCOPE_PROJECT_ID,
            flow_id=config.DESCOPE_FLOW_ID,
            session_cookie=config.SESSION_COOKIE_NAME,
            refresh_cookie=config.REFRESH_COOKIE_NAME,
            redirect_url=config.DESCOPE_REDIRECT_URL,
        )
        return html, 200, {"Content-Type": "text/html"}

    @app.route("/auth/logout")
    def auth_logout():
        """Clear authentication cookies and redirect to login."""
        response = make_response(redirect("/auth/login", code=302))

        # Delete authentication cookies
        response.delete_cookie(config.SESSION_COOKIE_NAME, path="/")
        response.delete_cookie(config.REFRESH_COOKIE_NAME, path="/")

        logger.info("User logged out")
        return response

    @app.route("/auth/user")
    def auth_user():
        """Get current authenticated user information."""
        if not hasattr(g, "username"):
            return jsonify({"error": "Not authenticated"}), 401

        return jsonify(
            {
                "user_id": getattr(g, "user_id", None),
                "username": g.username,
                "email": getattr(g, "email", None),
                "name": getattr(g, "name", None),
                "roles": getattr(g, "roles", []),
                "permissions": getattr(g, "permissions", []),
                "tenants": getattr(g, "tenants", []),
                "is_admin": getattr(g, "is_admin", False),
            }
        )

    @app.route("/health")
    def health_check():
        """Health check endpoint."""
        return jsonify(
            {
                "status": "healthy",
                "service": "mlflow-descope-auth",
                "project_id": config.DESCOPE_PROJECT_ID,
            }
        )

    logger.debug("Registered auth routes: /auth/login, /auth/logout, /auth/user, /health")
