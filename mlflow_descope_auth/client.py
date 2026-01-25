"""Descope SDK wrapper for MLflow integration."""

import logging
from typing import Any, Dict, List, Optional

from descope import AuthException, DescopeClient

from .config import get_config

logger = logging.getLogger(__name__)


class DescopeClientWrapper:
    """Wrapper around Descope SDK for MLflow authentication."""

    def __init__(self, project_id: Optional[str] = None, management_key: Optional[str] = None):
        """Initialize Descope client.

        Args:
            project_id: Descope project ID. If None, loads from config.
            management_key: Descope management key. If None, loads from config.
        """
        config = get_config()
        self.project_id = project_id or config.DESCOPE_PROJECT_ID
        self.management_key = management_key or config.DESCOPE_MANAGEMENT_KEY

        self.client = DescopeClient(
            project_id=self.project_id,
            management_key=self.management_key,
        )

        logger.info(f"Initialized Descope client for project: {self.project_id}")

    def validate_session(
        self, session_token: str, refresh_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate session token and optionally refresh if expired.

        Args:
            session_token: The session JWT token.
            refresh_token: Optional refresh token for automatic refresh.

        Returns:
            Dict containing the validated JWT response with user claims.

        Raises:
            AuthException: If validation fails and refresh is not possible.
        """
        try:
            if refresh_token:
                # Validate and automatically refresh if expired
                jwt_response = self.client.validate_and_refresh_session(
                    session_token, refresh_token
                )
                logger.debug("Session validated and refreshed successfully")
            else:
                # Just validate
                jwt_response = self.client.validate_session(session_token)
                logger.debug("Session validated successfully")

            return jwt_response

        except AuthException as e:
            logger.warning(f"Session validation failed: {e}")
            raise

    def get_user_info(self, refresh_token: str) -> Dict[str, Any]:
        """Get user details from Descope using refresh token.

        Args:
            refresh_token: The refresh token.

        Returns:
            Dict containing user information (email, name, phone, etc.).

        Raises:
            AuthException: If the refresh token is invalid.
        """
        try:
            user_info = self.client.me(refresh_token)
            logger.debug(f"Retrieved user info for: {user_info.get('email', 'unknown')}")
            return user_info
        except AuthException as e:
            logger.warning(f"Failed to get user info: {e}")
            raise

    def validate_permissions(self, jwt_response: Dict[str, Any], permissions: List[str]) -> bool:
        """Validate that user has required permissions.

        Args:
            jwt_response: The validated JWT response.
            permissions: List of required permissions.

        Returns:
            bool: True if all permissions are granted, False otherwise.
        """
        try:
            result = self.client.validate_permissions(jwt_response, permissions)
            logger.debug(f"Permission validation result: {result} for {permissions}")
            return result
        except Exception as e:
            logger.warning(f"Permission validation failed: {e}")
            return False

    def validate_roles(self, jwt_response: Dict[str, Any], roles: List[str]) -> bool:
        """Validate that user has required roles.

        Args:
            jwt_response: The validated JWT response.
            roles: List of required roles.

        Returns:
            bool: True if all roles are granted, False otherwise.
        """
        try:
            result = self.client.validate_roles(jwt_response, roles)
            logger.debug(f"Role validation result: {result} for {roles}")
            return result
        except Exception as e:
            logger.warning(f"Role validation failed: {e}")
            return False

    def validate_tenant_permissions(
        self, jwt_response: Dict[str, Any], tenant: str, permissions: List[str]
    ) -> bool:
        """Validate permissions for a specific tenant.

        Args:
            jwt_response: The validated JWT response.
            tenant: Tenant ID.
            permissions: List of required permissions.

        Returns:
            bool: True if all permissions are granted for the tenant.
        """
        try:
            result = self.client.validate_tenant_permissions(jwt_response, tenant, permissions)
            logger.debug(f"Tenant permission validation: {result} for tenant {tenant}")
            return result
        except Exception as e:
            logger.warning(f"Tenant permission validation failed: {e}")
            return False

    def validate_tenant_roles(
        self, jwt_response: Dict[str, Any], tenant: str, roles: List[str]
    ) -> bool:
        """Validate roles for a specific tenant.

        Args:
            jwt_response: The validated JWT response.
            tenant: Tenant ID.
            roles: List of required roles.

        Returns:
            bool: True if all roles are granted for the tenant.
        """
        try:
            result = self.client.validate_tenant_roles(jwt_response, tenant, roles)
            logger.debug(f"Tenant role validation: {result} for tenant {tenant}")
            return result
        except Exception as e:
            logger.warning(f"Tenant role validation failed: {e}")
            return False

    def extract_user_claims(self, jwt_response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user claims from JWT response.

        Args:
            jwt_response: The validated JWT response.

        Returns:
            Dict containing user claims (username, email, roles, etc.).
        """
        config = get_config()
        session_token = jwt_response.get("sessionToken", {})

        # Extract username based on configured claim
        username = session_token.get(config.USERNAME_CLAIM)
        if not username:
            # Fallback to email if configured claim not found
            username = session_token.get("email", session_token.get("sub", "unknown"))

        claims = {
            "username": username,
            "email": session_token.get("email"),
            "name": session_token.get("name"),
            "roles": session_token.get("roles", []),
            "permissions": session_token.get("permissions", []),
            "tenants": session_token.get("tenants", {}),
            "user_id": session_token.get("sub"),
        }

        logger.debug(f"Extracted user claims for: {username}")
        return claims


# Global client instance
_client: Optional[DescopeClientWrapper] = None


def get_descope_client() -> DescopeClientWrapper:
    """Get the global Descope client instance.

    Returns:
        DescopeClientWrapper: The global client instance.
    """
    global _client
    if _client is None:
        _client = DescopeClientWrapper()
    return _client


def set_descope_client(client: DescopeClientWrapper) -> None:
    """Set the global Descope client instance (for testing).

    Args:
        client: Client instance to set.
    """
    global _client
    _client = client
