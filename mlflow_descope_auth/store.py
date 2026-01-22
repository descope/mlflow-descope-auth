"""User store adapter for MLflow integration."""

import logging
from typing import Dict, List, Optional

from .client import get_descope_client
from .config import get_config

logger = logging.getLogger(__name__)


class DescopeUserStore:
    """Adapter between Descope and MLflow user management.

    This class provides an interface for managing users in MLflow
    based on Descope authentication and authorization.
    """

    def __init__(self, descope_client=None):
        """Initialize the user store.

        Args:
            descope_client: Optional Descope client (for testing).
        """
        self.descope_client = descope_client or get_descope_client()
        self.config = get_config()

    def get_user_from_jwt(self, jwt_response: Dict) -> Dict:
        """Extract user information from JWT response.

        Args:
            jwt_response: Validated JWT response from Descope.

        Returns:
            Dict containing user information suitable for MLflow.
        """
        claims = self.descope_client.extract_user_claims(jwt_response)

        user = {
            "username": claims["username"],
            "email": claims["email"],
            "display_name": claims["name"] or claims["username"],
            "is_admin": self.config.is_admin_role(claims["roles"]),
            "roles": claims["roles"],
            "permissions": claims["permissions"],
            "user_id": claims["user_id"],
        }

        logger.debug(f"Extracted user from JWT: {user['username']}")
        return user

    def map_permission_level(self, roles: List[str], permissions: List[str]) -> str:
        """Map Descope roles/permissions to MLflow permission level.

        MLflow permission levels: READ, EDIT, MANAGE

        Args:
            roles: List of user roles from Descope.
            permissions: List of user permissions from Descope.

        Returns:
            str: MLflow permission level (READ, EDIT, or MANAGE).
        """
        # Check if user is admin
        if self.config.is_admin_role(roles):
            return "MANAGE"

        # Check for specific MLflow permissions
        if "mlflow:manage" in permissions:
            return "MANAGE"
        elif "mlflow:edit" in permissions or "mlflow:write" in permissions:
            return "EDIT"
        elif "mlflow:read" in permissions:
            return "READ"

        # Check for role-based mapping
        role_permission_map = {
            "mlflow-manager": "MANAGE",
            "mlflow-editor": "EDIT",
            "mlflow-viewer": "READ",
        }

        for role in roles:
            if role in role_permission_map:
                return role_permission_map[role]

        # Default to configured default permission
        return self.config.DEFAULT_PERMISSION

    def check_experiment_permission(
        self, username: str, experiment_id: str, required_permission: str
    ) -> bool:
        """Check if user has required permission for an experiment.

        This is a simplified implementation. In a production system,
        you might want to:
        - Cache permissions
        - Query Descope for fine-grained authorization
        - Implement tenant-based access control

        Args:
            username: The username to check.
            experiment_id: The experiment ID.
            required_permission: Required permission level (READ, EDIT, MANAGE).

        Returns:
            bool: True if user has required permission, False otherwise.
        """
        # For now, we'll do a simple check based on user's global permission
        # In a real implementation, you'd want to check per-experiment permissions
        logger.debug(
            f"Checking permission for user {username} on experiment {experiment_id}: "
            f"{required_permission}"
        )

        # This is a placeholder - you would implement actual permission checking here
        # For example, query Descope's FGA (Fine-Grained Authorization) if enabled
        return True

    def get_user_experiments(self, username: str) -> List[str]:
        """Get list of experiments the user has access to.

        Args:
            username: The username to check.

        Returns:
            List of experiment IDs the user can access.
        """
        logger.debug(f"Getting experiments for user: {username}")

        # This is a placeholder - you would implement actual experiment listing here
        # For example:
        # - Query MLflow backend for experiments
        # - Filter by user permissions from Descope
        # - Return list of accessible experiment IDs

        return []

    def sync_user_from_descope(self, refresh_token: str) -> Dict:
        """Sync user information from Descope.

        This method can be used to periodically sync user information
        from Descope, including updated roles and permissions.

        Args:
            refresh_token: User's refresh token.

        Returns:
            Dict containing updated user information.
        """
        try:
            user_info = self.descope_client.get_user_info(refresh_token)
            logger.info(f"Synced user info from Descope: {user_info.get('email')}")
            return user_info
        except Exception as e:
            logger.error(f"Failed to sync user from Descope: {e}")
            raise


# Global store instance
_store: Optional[DescopeUserStore] = None


def get_user_store() -> DescopeUserStore:
    """Get the global user store instance.

    Returns:
        DescopeUserStore: The global store instance.
    """
    global _store
    if _store is None:
        _store = DescopeUserStore()
    return _store


def set_user_store(store: DescopeUserStore) -> None:
    """Set the global user store instance (for testing).

    Args:
        store: Store instance to set.
    """
    global _store
    _store = store
