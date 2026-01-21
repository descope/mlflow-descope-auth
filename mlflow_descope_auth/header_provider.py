"""Descope request header provider for MLflow."""

import logging
import os

from mlflow.tracking.request_header.abstract_request_header_provider import (
    RequestHeaderProvider,
)

from .client import get_descope_client
from .config import get_config

logger = logging.getLogger(__name__)


class DescopeHeaderProvider(RequestHeaderProvider):
    """Add Descope user context headers to MLflow requests."""

    def __init__(self):
        self._client = None
        self._config = None

    @property
    def client(self):
        if self._client is None:
            self._client = get_descope_client()
        return self._client

    @property
    def config(self):
        if self._config is None:
            self._config = get_config()
        return self._config

    def in_context(self):
        return os.environ.get("DESCOPE_SESSION_TOKEN") is not None

    def request_headers(self):
        session_token = os.environ.get("DESCOPE_SESSION_TOKEN")
        refresh_token = os.environ.get("DESCOPE_REFRESH_TOKEN")

        if not session_token:
            return {}

        try:
            jwt_response = self.client.validate_session(session_token, refresh_token)
            claims = self.client.extract_user_claims(jwt_response)

            headers = {
                "X-Descope-User-ID": claims["user_id"],
                "X-Descope-Username": claims["username"],
                "X-Descope-Email": claims["email"],
                "X-Descope-Project-ID": self.config.DESCOPE_PROJECT_ID,
            }

            if claims["name"]:
                headers["X-Descope-Name"] = claims["name"]

            if claims["roles"]:
                headers["X-Descope-Roles"] = ",".join(claims["roles"])

            if claims["permissions"]:
                headers["X-Descope-Permissions"] = ",".join(claims["permissions"])

            if claims["tenants"]:
                headers["X-Descope-Tenants"] = ",".join(claims["tenants"])

            return headers

        except Exception as e:
            logger.error(f"Failed to add Descope headers: {e}")
            return {}
