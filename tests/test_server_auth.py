"""Tests for server-side authentication."""

import pytest
from flask import Flask, g
from unittest.mock import Mock, patch, MagicMock
from descope import AuthException


class TestIsPublicRoute:
    def test_auth_login_is_public(self):
        from mlflow_descope_auth.server import _is_public_route

        assert _is_public_route("/auth/login") is True

    def test_auth_logout_is_public(self):
        from mlflow_descope_auth.server import _is_public_route

        assert _is_public_route("/auth/logout") is True

    def test_health_is_public(self):
        from mlflow_descope_auth.server import _is_public_route

        assert _is_public_route("/health") is True

    def test_static_prefix_is_public(self):
        from mlflow_descope_auth.server import _is_public_route

        assert _is_public_route("/static/css/style.css") is True
        assert _is_public_route("/_static/js/app.js") is True

    def test_api_routes_are_protected(self):
        from mlflow_descope_auth.server import _is_public_route

        assert _is_public_route("/api/2.0/mlflow/experiments/list") is False
        assert _is_public_route("/ajax-api/2.0/mlflow/runs/search") is False

    def test_root_is_protected(self):
        from mlflow_descope_auth.server import _is_public_route

        assert _is_public_route("/") is False


class TestCreateApp:
    def test_create_app_returns_flask_app(self):
        mock_app = MagicMock(spec=Flask)
        mock_app.before_request = MagicMock()
        mock_app.after_request = MagicMock()
        mock_app.route = MagicMock(return_value=lambda f: f)

        with patch("mlflow_descope_auth.server.get_config") as mock_config:
            mock_config.return_value = Mock(
                DESCOPE_PROJECT_ID="test_project",
                SESSION_COOKIE_NAME="DS",
                REFRESH_COOKIE_NAME="DSR",
                DESCOPE_FLOW_ID="sign-up-or-in",
                DESCOPE_REDIRECT_URL="/",
                web_component_url="https://example.com/wc.js",
            )
            with patch("mlflow_descope_auth.auth_routes.get_config", mock_config):
                from mlflow_descope_auth.server import create_app

                result = create_app(mock_app)

        assert result is mock_app
        mock_app.before_request.assert_called_once()
        mock_app.after_request.assert_called_once()

    def test_create_app_imports_mlflow_app_when_none(self):
        with patch("mlflow_descope_auth.server.get_config") as mock_config:
            mock_config.return_value = Mock(
                DESCOPE_PROJECT_ID="test_project",
                SESSION_COOKIE_NAME="DS",
                REFRESH_COOKIE_NAME="DSR",
            )
            with patch("mlflow_descope_auth.auth_routes.get_config", mock_config):
                with patch("mlflow.server.app") as mock_mlflow_app:
                    mock_mlflow_app.before_request = MagicMock()
                    mock_mlflow_app.after_request = MagicMock()
                    mock_mlflow_app.route = MagicMock(return_value=lambda f: f)

                    from mlflow_descope_auth.server import create_app

                    result = create_app(None)

                    assert result is mock_mlflow_app


class TestBeforeRequest:
    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        return app

    @pytest.fixture
    def mock_config(self):
        config = Mock()
        config.SESSION_COOKIE_NAME = "DS"
        config.REFRESH_COOKIE_NAME = "DSR"
        config.COOKIE_SECURE = False
        config.is_admin_role = Mock(return_value=False)
        return config

    @pytest.fixture
    def mock_client(self):
        client = Mock()
        client.validate_session = Mock(
            return_value={
                "sessionToken": {"jwt": "new_token"},
            }
        )
        client.extract_user_claims = Mock(
            return_value={
                "user_id": "user123",
                "username": "testuser",
                "email": "test@example.com",
                "name": "Test User",
                "roles": ["user"],
                "permissions": ["read"],
                "tenants": {},
            }
        )
        return client

    def test_public_route_skips_auth(self, app, mock_config):
        with app.test_request_context("/auth/login"):
            with patch("mlflow_descope_auth.server.get_config", return_value=mock_config):
                from mlflow_descope_auth.server import _before_request

                result = _before_request()
                assert result is None

    def test_no_session_redirects_to_login(self, app, mock_config):
        with app.test_request_context("/api/experiments", headers={}):
            with patch("mlflow_descope_auth.server.get_config", return_value=mock_config):
                from mlflow_descope_auth.server import _before_request

                result = _before_request()
                assert result is not None
                assert result.status_code == 302
                assert "/auth/login" in result.location

    def test_valid_session_sets_user_context(self, app, mock_config, mock_client):
        with app.test_request_context(
            "/api/experiments",
            headers={"Cookie": "DS=valid_token; DSR=refresh_token"},
        ):
            from flask import request

            request.cookies = {"DS": "valid_token", "DSR": "refresh_token"}

            with patch("mlflow_descope_auth.server.get_config", return_value=mock_config):
                with patch(
                    "mlflow_descope_auth.server.get_descope_client", return_value=mock_client
                ):
                    from mlflow_descope_auth.server import _before_request

                    result = _before_request()

                    assert result is None
                    assert g.username == "testuser"
                    assert g.email == "test@example.com"
                    assert g.user_id == "user123"

    def test_invalid_session_redirects_to_login(self, app, mock_config, mock_client):
        mock_client.validate_session.side_effect = AuthException(401, "invalid", "Invalid token")

        with app.test_request_context("/api/experiments"):
            from flask import request

            request.cookies = {"DS": "invalid_token"}

            with patch("mlflow_descope_auth.server.get_config", return_value=mock_config):
                with patch(
                    "mlflow_descope_auth.server.get_descope_client", return_value=mock_client
                ):
                    from mlflow_descope_auth.server import _before_request

                    result = _before_request()

                    assert result is not None
                    assert result.status_code == 302
                    assert "/auth/login" in result.location


class TestAfterRequest:
    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        return app

    @pytest.fixture
    def mock_config(self):
        config = Mock()
        config.SESSION_COOKIE_NAME = "DS"
        config.COOKIE_SECURE = False
        return config

    def test_no_jwt_response_returns_unchanged(self, app, mock_config):
        with app.test_request_context("/"):
            from flask import make_response

            from mlflow_descope_auth.server import _after_request

            response = make_response("OK")

            with patch("mlflow_descope_auth.server.get_config", return_value=mock_config):
                result = _after_request(response)

            assert result is response

    def test_refreshed_token_sets_cookie(self, app, mock_config):
        with app.test_request_context("/"):
            from flask import make_response

            g._descope_jwt_response = {"sessionToken": {"jwt": "new_refreshed_token"}}
            g._descope_session_token = "old_token"
            g.username = "testuser"

            from mlflow_descope_auth.server import _after_request

            response = make_response("OK")

            with patch("mlflow_descope_auth.server.get_config", return_value=mock_config):
                result = _after_request(response)

            cookies = result.headers.getlist("Set-Cookie")
            assert any("DS=new_refreshed_token" in cookie for cookie in cookies)

    def test_same_token_no_cookie_update(self, app, mock_config):
        with app.test_request_context("/"):
            from flask import make_response

            g._descope_jwt_response = {"sessionToken": {"jwt": "same_token"}}
            g._descope_session_token = "same_token"

            from mlflow_descope_auth.server import _after_request

            response = make_response("OK")

            with patch("mlflow_descope_auth.server.get_config", return_value=mock_config):
                result = _after_request(response)

            cookies = result.headers.getlist("Set-Cookie")
            assert not any("DS=" in cookie for cookie in cookies)
