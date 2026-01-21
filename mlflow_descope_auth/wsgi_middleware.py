"""WSGI middleware to pass FastAPI auth info to MLflow Flask app."""

import asyncio
import logging

from asgiref.wsgi import WsgiToAsgi
from starlette.types import Receive, Scope, Send

logger = logging.getLogger(__name__)


class AuthInjectingWSGIApp:
    """WSGI app wrapper that injects FastAPI auth info into Flask environ.

    This bridges FastAPI authentication with MLflow's Flask app by injecting
    user information into the WSGI environ dict.
    """

    def __init__(self, flask_app, scope: Scope):
        self.flask_app = flask_app
        self.scope = scope

    def __call__(self, environ, start_response):
        """Inject auth info from ASGI scope into WSGI environ."""
        # Extract auth info from request state (set by AuthenticationMiddleware)
        state = self.scope.get("state", {})

        username = state.get("username")
        is_admin = state.get("is_admin", False)
        email = state.get("email")
        roles = state.get("roles", [])
        permissions = state.get("permissions", [])

        if username:
            logger.debug(f"Injecting auth into WSGI environ: user={username}, admin={is_admin}")
            # Inject auth info for MLflow to access
            environ["mlflow_descope_auth.username"] = username
            environ["mlflow_descope_auth.is_admin"] = is_admin
            environ["mlflow_descope_auth.email"] = email or username
            environ["mlflow_descope_auth.roles"] = ",".join(roles)
            environ["mlflow_descope_auth.permissions"] = ",".join(permissions)

            # Also set standard REMOTE_USER for compatibility
            environ["REMOTE_USER"] = username

        return self.flask_app(environ, start_response)


class AuthAwareWSGIMiddleware:
    """ASGI middleware that passes FastAPI auth to MLflow Flask app.

    This middleware:
    1. Extracts authentication info from ASGI scope
    2. Wraps the Flask app to inject auth into WSGI environ
    3. Converts ASGI to WSGI using asgiref
    """

    def __init__(self, flask_app):
        self.flask_app = flask_app
        logger.info("Initialized AuthAwareWSGIMiddleware")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            # Create auth-injecting wrapper for this request
            auth_injecting_app = AuthInjectingWSGIApp(self.flask_app, scope)

            # Use asgiref to convert WSGI to ASGI
            wsgi_adapter = WsgiToAsgi(auth_injecting_app)
            await wsgi_adapter(scope, receive, send)
        else:
            # For non-HTTP requests (websocket/lifespan)
            if callable(self.flask_app):
                result = self.flask_app(scope, receive, send)
                if asyncio.iscoroutine(result) or asyncio.isfuture(result):
                    await result
                    return

            # Fallback to WSGI adapter
            adapter = WsgiToAsgi(self.flask_app)
            await adapter(scope, receive, send)
