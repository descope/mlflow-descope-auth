"""Tests for user store."""

from unittest.mock import Mock, patch

import pytest

from mlflow_descope_auth.store import DescopeUserStore


@pytest.fixture
def user_store(mock_descope_client, mock_config):
    """Create a user store instance for testing."""
    with patch("mlflow_descope_auth.store.get_config", return_value=mock_config):
        return DescopeUserStore(descope_client=mock_descope_client)


def test_get_user_from_jwt(user_store, mock_jwt_response):
    """Test extracting user from JWT response."""
    user = user_store.get_user_from_jwt(mock_jwt_response)

    assert user["username"] == "test@example.com"
    assert user["email"] == "test@example.com"
    assert user["display_name"] == "Test User"
    assert user["is_admin"] is False
    assert user["roles"] == ["user"]


def test_get_admin_user_from_jwt(user_store, mock_admin_jwt_response):
    """Test extracting admin user from JWT response."""
    user = user_store.get_user_from_jwt(mock_admin_jwt_response)

    assert user["username"] == "admin@example.com"
    assert user["is_admin"] is True
    assert "admin" in user["roles"]


def test_map_permission_level_admin(user_store):
    """Test permission mapping for admin users."""
    permission = user_store.map_permission_level(["admin"], [])
    assert permission == "MANAGE"


def test_map_permission_level_manage_permission(user_store):
    """Test permission mapping with manage permission."""
    permission = user_store.map_permission_level(["user"], ["mlflow:manage"])
    assert permission == "MANAGE"


def test_map_permission_level_edit_permission(user_store):
    """Test permission mapping with edit permission."""
    permission = user_store.map_permission_level(["user"], ["mlflow:edit"])
    assert permission == "EDIT"


def test_map_permission_level_read_permission(user_store):
    """Test permission mapping with read permission."""
    permission = user_store.map_permission_level(["user"], ["mlflow:read"])
    assert permission == "READ"


def test_map_permission_level_default(user_store):
    """Test default permission mapping."""
    permission = user_store.map_permission_level(["user"], [])
    assert permission == "READ"  # Default from config


def test_check_experiment_permission(user_store):
    """Test experiment permission checking."""
    # This is a placeholder test - actual implementation would check real permissions
    result = user_store.check_experiment_permission("test@example.com", "exp123", "READ")
    assert isinstance(result, bool)
