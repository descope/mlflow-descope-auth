"""MLflow Descope Authentication Plugin.

This plugin provides Flow-based authentication for MLflow using Descope.
Authentication flows are configured in the Descope Console, making it easy
to support multiple auth methods without code changes.
"""

__version__ = "0.1.0"

from .app import app, create_app, get_app
from .client import DescopeClientWrapper, get_descope_client
from .config import Config, get_config
from .middleware import AuthenticationMiddleware
from .store import DescopeUserStore, get_user_store

__all__ = [
    "app",
    "create_app",
    "get_app",
    "DescopeClientWrapper",
    "get_descope_client",
    "Config",
    "get_config",
    "AuthenticationMiddleware",
    "DescopeUserStore",
    "get_user_store",
    "__version__",
]
