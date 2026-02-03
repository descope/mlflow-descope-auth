"""MLflow Descope Authentication Plugin.

This plugin provides server-side authentication for MLflow using Descope.

Usage:
    Start MLflow with: mlflow server --app-name descope
    Browser login at /auth/login with automatic token refresh via cookies.
"""

__version__ = "0.1.0"

from .auth_routes import register_auth_routes
from .client import DescopeClientWrapper, get_descope_client
from .config import Config, get_config, set_config
from .server import create_app
from .store import DescopeUserStore, get_user_store

__all__ = [
    "DescopeClientWrapper",
    "get_descope_client",
    "Config",
    "get_config",
    "set_config",
    "DescopeUserStore",
    "get_user_store",
    "create_app",
    "register_auth_routes",
    "__version__",
]
