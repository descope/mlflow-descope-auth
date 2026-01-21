"""Tests for configuration module."""

import os

import pytest

from mlflow_descope_auth.config import Config


def test_config_from_env():
    """Test loading configuration from environment variables."""
    os.environ["DESCOPE_PROJECT_ID"] = "P2TEST123"
    os.environ["DESCOPE_FLOW_ID"] = "custom-flow"
    os.environ["DESCOPE_ADMIN_ROLES"] = "admin,superuser"

    config = Config.from_env()

    assert config.DESCOPE_PROJECT_ID == "P2TEST123"
    assert config.DESCOPE_FLOW_ID == "custom-flow"
    assert "admin" in config.ADMIN_ROLES
    assert "superuser" in config.ADMIN_ROLES

    # Cleanup
    os.environ.pop("DESCOPE_PROJECT_ID")
    os.environ.pop("DESCOPE_FLOW_ID")
    os.environ.pop("DESCOPE_ADMIN_ROLES")


def test_config_missing_project_id():
    """Test that missing PROJECT_ID raises ValueError."""
    # Remove PROJECT_ID if set
    os.environ.pop("DESCOPE_PROJECT_ID", None)

    with pytest.raises(ValueError, match="DESCOPE_PROJECT_ID"):
        Config.from_env()

    # Restore for other tests
    os.environ["DESCOPE_PROJECT_ID"] = "test_project_id"


def test_config_defaults():
    """Test configuration default values."""
    config = Config(DESCOPE_PROJECT_ID="test123")

    assert config.DESCOPE_FLOW_ID == "sign-up-or-in"
    assert config.DESCOPE_REDIRECT_URL == "/"
    assert config.DEFAULT_PERMISSION == "READ"
    assert "admin" in config.ADMIN_ROLES
    assert "mlflow-admin" in config.ADMIN_ROLES


def test_is_admin_role():
    """Test admin role checking."""
    config = Config(DESCOPE_PROJECT_ID="test123", ADMIN_ROLES=["admin", "superuser"])

    assert config.is_admin_role(["admin"]) is True
    assert config.is_admin_role(["superuser"]) is True
    assert config.is_admin_role(["user"]) is False
    assert config.is_admin_role(["admin", "user"]) is True
    assert config.is_admin_role([]) is False


def test_web_component_url():
    """Test web component URL generation."""
    config = Config(DESCOPE_PROJECT_ID="test123", DESCOPE_WEB_COMPONENT_VERSION="3.54.0")

    expected_url = "https://unpkg.com/@descope/web-component@3.54.0/dist/index.js"
    assert config.web_component_url == expected_url
