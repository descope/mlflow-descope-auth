"""MLflow Descope Authentication Plugin.

This plugin provides simple, standards-compliant authentication for MLflow using Descope.
It integrates via MLflow's plugin system with:
- Request authentication provider
- Request header provider
- Run context provider

Authentication tokens are managed via environment variables:
- DESCOPE_SESSION_TOKEN: Current session token
- DESCOPE_REFRESH_TOKEN: Refresh token for automatic renewal
"""

__version__ = "0.1.0"

from .auth_provider import DescopeAuth, DescopeAuthProvider
from .client import DescopeClientWrapper, get_descope_client
from .config import Config, get_config
from .context_provider import DescopeContextProvider
from .header_provider import DescopeHeaderProvider
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
    "__version__",
]
