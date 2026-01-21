"""Tests for Descope client wrapper."""

from unittest.mock import Mock, patch

import pytest
from descope import AuthException

from mlflow_descope_auth.client import DescopeClientWrapper


@patch("mlflow_descope_auth.client.DescopeClient")
def test_client_initialization(mock_descope_class, mock_config):
    """Test Descope client initialization."""
    with patch("mlflow_descope_auth.client.get_config", return_value=mock_config):
        client = DescopeClientWrapper()

        assert client.project_id == mock_config.DESCOPE_PROJECT_ID
        mock_descope_class.assert_called_once()


@patch("mlflow_descope_auth.client.DescopeClient")
def test_validate_session_success(mock_descope_class, mock_config, mock_jwt_response):
    """Test successful session validation."""
    mock_client_instance = Mock()
    mock_client_instance.validate_and_refresh_session.return_value = mock_jwt_response
    mock_descope_class.return_value = mock_client_instance

    with patch("mlflow_descope_auth.client.get_config", return_value=mock_config):
        client = DescopeClientWrapper()
        result = client.validate_session("session_token", "refresh_token")

        assert result == mock_jwt_response
        mock_client_instance.validate_and_refresh_session.assert_called_once_with(
            "session_token", "refresh_token"
        )


@patch("mlflow_descope_auth.client.DescopeClient")
def test_validate_session_failure(mock_descope_class, mock_config):
    """Test session validation failure."""
    mock_client_instance = Mock()
    mock_client_instance.validate_and_refresh_session.side_effect = AuthException(
        401, "invalid_token", "Invalid session"
    )
    mock_descope_class.return_value = mock_client_instance

    with patch("mlflow_descope_auth.client.get_config", return_value=mock_config):
        client = DescopeClientWrapper()

        with pytest.raises(AuthException):
            client.validate_session("invalid_token", "refresh_token")


@patch("mlflow_descope_auth.client.DescopeClient")
def test_extract_user_claims(mock_descope_class, mock_config, mock_jwt_response):
    """Test extracting user claims from JWT response."""
    mock_descope_class.return_value = Mock()

    with patch("mlflow_descope_auth.client.get_config", return_value=mock_config):
        client = DescopeClientWrapper()
        claims = client.extract_user_claims(mock_jwt_response)

        assert claims["username"] == "test_user_id"
        assert claims["email"] == "test@example.com"
        assert claims["name"] == "Test User"
        assert claims["roles"] == ["user"]
        assert claims["permissions"] == ["mlflow:read"]


@patch("mlflow_descope_auth.client.DescopeClient")
def test_validate_permissions(mock_descope_class, mock_config, mock_jwt_response):
    """Test permission validation."""
    mock_client_instance = Mock()
    mock_client_instance.validate_permissions.return_value = True
    mock_descope_class.return_value = mock_client_instance

    with patch("mlflow_descope_auth.client.get_config", return_value=mock_config):
        client = DescopeClientWrapper()
        result = client.validate_permissions(mock_jwt_response, ["mlflow:read"])

        assert result is True
        mock_client_instance.validate_permissions.assert_called_once()


@patch("mlflow_descope_auth.client.DescopeClient")
def test_validate_roles(mock_descope_class, mock_config, mock_jwt_response):
    """Test role validation."""
    mock_client_instance = Mock()
    mock_client_instance.validate_roles.return_value = True
    mock_descope_class.return_value = mock_client_instance

    with patch("mlflow_descope_auth.client.get_config", return_value=mock_config):
        client = DescopeClientWrapper()
        result = client.validate_roles(mock_jwt_response, ["user"])

        assert result is True
        mock_client_instance.validate_roles.assert_called_once()
