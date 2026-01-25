"""Authentication routes for Descope Flow-based authentication."""

import logging
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .config import get_config

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Initialize Jinja2 templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """Render login page with Descope Flow web component.

    This endpoint serves an HTML page that embeds the Descope web component.
    The component loads the authentication flow configured in Descope Console.

    Args:
        request: The incoming HTTP request.

    Returns:
        HTMLResponse: Login page with embedded Descope web component.
    """
    config = get_config()

    logger.info(f"Rendering login page with flow: {config.DESCOPE_FLOW_ID}")

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "project_id": config.DESCOPE_PROJECT_ID,
            "flow_id": config.DESCOPE_FLOW_ID,
            "base_url": config.DESCOPE_BASE_URL,
            "redirect_url": config.DESCOPE_REDIRECT_URL,
            "web_component_url": config.web_component_url,
            "session_cookie_name": config.SESSION_COOKIE_NAME,
            "refresh_cookie_name": config.REFRESH_COOKIE_NAME,
        },
    )


@router.get("/logout")
async def logout(request: Request):
    """Logout endpoint - clears authentication cookies.

    This endpoint clears the session and refresh token cookies, effectively
    logging the user out. It then redirects to the login page.

    Args:
        request: The incoming HTTP request.

    Returns:
        RedirectResponse: Redirects to login page after clearing cookies.
    """
    config = get_config()

    logger.info("User logging out")

    # Create redirect response
    response = RedirectResponse(url="/auth/login", status_code=302)

    # Clear authentication cookies
    response.delete_cookie(config.SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(config.REFRESH_COOKIE_NAME, path="/")

    return response


@router.get("/user")
async def get_current_user(request: Request):
    """Get current authenticated user information.

    This endpoint returns information about the currently authenticated user
    based on the request state set by the authentication middleware.

    Args:
        request: The incoming HTTP request.

    Returns:
        dict: User information including username, roles, and permissions.
    """
    # Check if user is authenticated (set by middleware)
    if not hasattr(request.state, "username"):
        return {"error": "Not authenticated"}, 401

    return {
        "username": request.state.username,
        "email": getattr(request.state, "email", None),
        "name": getattr(request.state, "name", None),
        "roles": getattr(request.state, "roles", []),
        "permissions": getattr(request.state, "permissions", []),
        "is_admin": getattr(request.state, "is_admin", False),
    }


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring.

    Returns:
        dict: Health status of the authentication service.
    """
    config = get_config()

    return {
        "status": "healthy",
        "service": "mlflow-descope-auth",
        "project_id": config.DESCOPE_PROJECT_ID,
        "flow_id": config.DESCOPE_FLOW_ID,
    }


@router.get("/config")
async def get_auth_config():
    """Get public authentication configuration.

    Returns non-sensitive configuration information that can be used
    by frontend clients.

    Returns:
        dict: Public configuration including project ID and flow ID.
    """
    config = get_config()

    return {
        "project_id": config.DESCOPE_PROJECT_ID,
        "flow_id": config.DESCOPE_FLOW_ID,
        "web_component_version": config.DESCOPE_WEB_COMPONENT_VERSION,
        "redirect_url": config.DESCOPE_REDIRECT_URL,
    }
