"""Pytest configuration and fixtures for tests."""

import os
from unittest.mock import Mock

import pytest

from mlflow_descope_auth.client import DescopeClientWrapper
from mlflow_descope_auth.config import Config


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return Config(
        DESCOPE_PROJECT_ID="test_project_id",
        DESCOPE_MANAGEMENT_KEY="test_management_key",
        DESCOPE_FLOW_ID="test-flow",
        DESCOPE_REDIRECT_URL="/",
        ADMIN_ROLES=["admin", "test-admin"],
        DEFAULT_PERMISSION="READ",
    )


@pytest.fixture
def mock_descope_client():
    """Create a mock Descope client for testing."""
    client = Mock(spec=DescopeClientWrapper)

    # Mock successful validation
    client.validate_session.return_value = {
        "sessionToken": {
            "jwt": "mock_jwt_token",
            "sub": "test_user_id",
            "email": "test@example.com",
            "name": "Test User",
            "roles": ["user"],
            "permissions": ["mlflow:read"],
        },
        "refreshSessionToken": {"jwt": "mock_refresh_token"},
    }

    # Mock user claims extraction
    client.extract_user_claims.return_value = {
        "username": "test@example.com",
        "email": "test@example.com",
        "name": "Test User",
        "roles": ["user"],
        "permissions": ["mlflow:read"],
        "tenants": {},
        "user_id": "test_user_id",
    }

    return client


@pytest.fixture
def mock_jwt_response():
    """Create a mock JWT response for testing."""
    return {
        "sessionToken": {
            "jwt": "mock_jwt_token",
            "sub": "test_user_id",
            "email": "test@example.com",
            "name": "Test User",
            "roles": ["user"],
            "permissions": ["mlflow:read"],
        },
        "refreshSessionToken": {"jwt": "mock_refresh_token"},
    }


@pytest.fixture
def mock_admin_jwt_response():
    """Create a mock JWT response for admin user."""
    return {
        "sessionToken": {
            "jwt": "mock_admin_jwt_token",
            "sub": "admin_user_id",
            "email": "admin@example.com",
            "name": "Admin User",
            "roles": ["admin", "user"],
            "permissions": ["mlflow:manage", "mlflow:read", "mlflow:write"],
        },
        "refreshSessionToken": {"jwt": "mock_admin_refresh_token"},
    }


@pytest.fixture(autouse=True)
def set_test_env():
    """Set test environment variables."""
    os.environ["DESCOPE_PROJECT_ID"] = "test_project_id"
    os.environ["DESCOPE_FLOW_ID"] = "test-flow"
    yield
    # Cleanup
    os.environ.pop("DESCOPE_PROJECT_ID", None)
    os.environ.pop("DESCOPE_FLOW_ID", None)
