"""Configuration module for MLflow Descope Auth plugin."""

import os
from dataclasses import dataclass, field
from typing import List, Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class Config:
    """Configuration for Descope authentication plugin."""

    # Required
    DESCOPE_PROJECT_ID: str

    # Optional - Descope settings
    DESCOPE_MANAGEMENT_KEY: Optional[str] = None
    DESCOPE_FLOW_ID: str = "sign-up-or-in"
    DESCOPE_REDIRECT_URL: str = "/"
    DESCOPE_WEB_COMPONENT_VERSION: str = "3.54.0"
    DESCOPE_BASE_URL: str = "https://api.descope.com"

    # MLflow integration
    MLFLOW_BACKEND_STORE_URI: str = "sqlite:///mlflow.db"
    MLFLOW_ARTIFACT_ROOT: str = "./mlartifacts"

    # Permission mapping
    ADMIN_ROLES: List[str] = field(default_factory=lambda: ["admin", "mlflow-admin"])
    DEFAULT_PERMISSION: str = "READ"

    # JWT configuration
    USERNAME_CLAIM: str = "sub"  # or "email"

    # Cookie names (Descope standard)
    SESSION_COOKIE_NAME: str = "DS"
    REFRESH_COOKIE_NAME: str = "DSR"

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables.

        Returns:
            Config: Configuration instance populated from environment variables.

        Raises:
            ValueError: If required environment variables are missing.
        """
        project_id = os.getenv("DESCOPE_PROJECT_ID")
        if not project_id:
            raise ValueError(
                "DESCOPE_PROJECT_ID environment variable is required. "
                "Please set it in your .env file or environment."
            )

        # Parse admin roles from comma-separated string
        admin_roles_str = os.getenv("DESCOPE_ADMIN_ROLES", "admin,mlflow-admin")
        admin_roles = [role.strip() for role in admin_roles_str.split(",")]

        return cls(
            DESCOPE_PROJECT_ID=project_id,
            DESCOPE_MANAGEMENT_KEY=os.getenv("DESCOPE_MANAGEMENT_KEY"),
            DESCOPE_FLOW_ID=os.getenv("DESCOPE_FLOW_ID", "sign-up-or-in"),
            DESCOPE_REDIRECT_URL=os.getenv("DESCOPE_REDIRECT_URL", "/"),
            DESCOPE_WEB_COMPONENT_VERSION=os.getenv("DESCOPE_WEB_COMPONENT_VERSION", "3.54.0"),
            DESCOPE_BASE_URL=os.getenv("DESCOPE_BASE_URL", "https://api.descope.com"),
            MLFLOW_BACKEND_STORE_URI=os.getenv("MLFLOW_BACKEND_STORE_URI", "sqlite:///mlflow.db"),
            MLFLOW_ARTIFACT_ROOT=os.getenv("MLFLOW_ARTIFACT_ROOT", "./mlartifacts"),
            ADMIN_ROLES=admin_roles,
            DEFAULT_PERMISSION=os.getenv("DESCOPE_DEFAULT_PERMISSION", "READ"),
            USERNAME_CLAIM=os.getenv("DESCOPE_USERNAME_CLAIM", "sub"),
        )

    def is_admin_role(self, roles: List[str]) -> bool:
        """Check if any of the provided roles is an admin role.

        Args:
            roles: List of role names to check.

        Returns:
            bool: True if any role matches admin roles, False otherwise.
        """
        return any(role in self.ADMIN_ROLES for role in roles)

    @property
    def web_component_url(self) -> str:
        """Get the Descope web component CDN URL.

        Returns:
            str: Full CDN URL for the Descope web component.
        """
        return f"https://unpkg.com/@descope/web-component@{self.DESCOPE_WEB_COMPONENT_VERSION}/dist/index.js"


# Global config instance (initialized when module is imported)
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance.

    Returns:
        Config: The global configuration instance.

    Raises:
        RuntimeError: If configuration hasn't been initialized.
    """
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance (for testing).

    Args:
        config: Configuration instance to set.
    """
    global _config
    _config = config
