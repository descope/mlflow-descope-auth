"""Descope authentication provider for MLflow."""

import logging
import os

from descope import AuthException
from mlflow.tracking.request_auth.abstract_request_auth_provider import (
    RequestAuthProvider,
)

from .client import get_descope_client
from .config import get_config

logger = logging.getLogger(__name__)


class DescopeAuth:
    """Authentication handler for Descope session tokens."""

    def __init__(self):
        self.client = get_descope_client()
        self.config = get_config()

    def __call__(self, request):
        session_token = os.environ.get("DESCOPE_SESSION_TOKEN")
        refresh_token = os.environ.get("DESCOPE_REFRESH_TOKEN")

        if not session_token:
            logger.warning("No DESCOPE_SESSION_TOKEN found in environment")
            return request

        try:
            jwt_response = self.client.validate_session(session_token, refresh_token)

            if jwt_response.get("sessionToken"):
                new_token = jwt_response["sessionToken"]["jwt"]
                request.headers["Authorization"] = f"Bearer {new_token}"

                claims = self.client.extract_user_claims(jwt_response)
                request.headers["X-MLflow-User"] = claims["username"]
                request.headers["X-MLflow-User-Email"] = claims["email"]

                if self.config.is_admin_role(claims["roles"]):
                    request.headers["X-MLflow-Admin"] = "true"

            return request

        except AuthException as e:
            logger.error(f"Descope authentication failed: {e}")
            return request


class DescopeAuthProvider(RequestAuthProvider):
    """MLflow auth provider for Descope authentication."""

    def get_name(self):
        return "descope"

    def get_auth(self):
        return DescopeAuth()
