"""Tests for authentication routes."""

import pytest
from flask import Flask
from unittest.mock import Mock, patch


@pytest.fixture
def mock_config():
    config = Mock()
    config.DESCOPE_PROJECT_ID = "test_project_id"
    config.DESCOPE_FLOW_ID = "sign-up-or-in"
    config.SESSION_COOKIE_NAME = "DS"
    config.REFRESH_COOKIE_NAME = "DSR"
    config.DESCOPE_REDIRECT_URL = "/"
    config.web_component_url = "https://unpkg.com/@descope/web-component@3.54.0/dist/index.js"
    return config


@pytest.fixture
def app(mock_config):
    app = Flask(__name__)
    app.config["TESTING"] = True

    with patch("mlflow_descope_auth.auth_routes.get_config", return_value=mock_config):
        from mlflow_descope_auth.auth_routes import register_auth_routes

        register_auth_routes(app)

    return app


@pytest.fixture
def client(app):
    return app.test_client()


class TestLoginRoute:
    def test_login_returns_html(self, client):
        response = client.get("/auth/login")
        assert response.status_code == 200
        assert response.content_type == "text/html"

    def test_login_contains_descope_component(self, client):
        response = client.get("/auth/login")
        html = response.data.decode("utf-8")
        assert "descope-wc" in html
        assert "project-id" in html
        assert "flow-id" in html

    def test_login_contains_project_id(self, client):
        response = client.get("/auth/login")
        html = response.data.decode("utf-8")
        assert "test_project_id" in html

    def test_login_contains_web_component_script(self, client):
        response = client.get("/auth/login")
        html = response.data.decode("utf-8")
        assert "@descope/web-component" in html


class TestLogoutRoute:
    def test_logout_redirects_to_login(self, client):
        response = client.get("/auth/logout")
        assert response.status_code == 302
        assert "/auth/login" in response.location

    def test_logout_clears_session_cookie(self, client):
        response = client.get("/auth/logout")
        cookies = response.headers.getlist("Set-Cookie")
        ds_cookies = [c for c in cookies if c.startswith("DS=")]
        assert len(ds_cookies) > 0
        assert any("Max-Age=0" in c or "expires=" in c.lower() for c in ds_cookies)

    def test_logout_clears_refresh_cookie(self, client):
        response = client.get("/auth/logout")
        cookies = response.headers.getlist("Set-Cookie")
        dsr_cookies = [c for c in cookies if c.startswith("DSR=")]
        assert len(dsr_cookies) > 0


class TestUserRoute:
    def test_user_unauthenticated_returns_401(self, client):
        response = client.get("/auth/user")
        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "Not authenticated"


class TestHealthRoute:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json(self, client):
        response = client.get("/health")
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["service"] == "mlflow-descope-auth"
        assert "project_id" in data
