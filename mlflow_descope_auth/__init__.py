"""MLflow Descope Authentication Plugin.

This plugin provides authentication for MLflow using Descope with two modes:

1. Server-Side (Recommended): Cookie-based auth with Descope Web Component
   - Start with: mlflow server --app-name descope
   - Browser login at /auth/login
   - Automatic token refresh

2. Client-Side: Environment variable tokens for CLI/API usage
   - Set MLFLOW_TRACKING_AUTH=descope
   - Set DESCOPE_SESSION_TOKEN and optionally DESCOPE_REFRESH_TOKEN
"""

__version__ = "0.1.0"

from .auth_provider import DescopeAuth, DescopeAuthProvider
from .auth_routes import register_auth_routes
from .client import DescopeClientWrapper, get_descope_client
from .config import Config, get_config
from .context_provider import DescopeContextProvider
from .header_provider import DescopeHeaderProvider
from .server import create_app
from .store import DescopeUserStore, get_user_store

__all__ = [
    "DescopeAuth",
    "DescopeAuthProvider",
    "DescopeHeaderProvider",
    "DescopeContextProvider",
    "DescopeClientWrapper",
    "get_descope_client",
    "Config",
    "get_config",
    "DescopeUserStore",
    "get_user_store",
    "create_app",
    "register_auth_routes",
    "__version__",
]
