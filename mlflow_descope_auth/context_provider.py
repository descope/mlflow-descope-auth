"""Descope run context provider for MLflow."""

import logging
import os

from mlflow.tracking.context.abstract_context import RunContextProvider

from .client import get_descope_client

logger = logging.getLogger(__name__)


class DescopeContextProvider(RunContextProvider):
    """Automatically add Descope user context as tags to MLflow runs."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = get_descope_client()
        return self._client

    def in_context(self):
        return os.environ.get("DESCOPE_SESSION_TOKEN") is not None

    def tags(self):
        session_token = os.environ.get("DESCOPE_SESSION_TOKEN")
        refresh_token = os.environ.get("DESCOPE_REFRESH_TOKEN")

        if not session_token:
            return {}

        try:
            jwt_response = self.client.validate_session(session_token, refresh_token)
            claims = self.client.extract_user_claims(jwt_response)

            tags = {
                "descope.user_id": claims["user_id"],
                "descope.username": claims["username"],
                "descope.email": claims["email"],
            }

            if claims["name"]:
                tags["descope.name"] = claims["name"]

            if claims["roles"]:
                tags["descope.roles"] = ",".join(claims["roles"])

            if claims["permissions"]:
                tags["descope.permissions"] = ",".join(claims["permissions"])

            if claims["tenants"]:
                tags["descope.tenants"] = ",".join(claims["tenants"])

            logger.debug(f"Added Descope context for user: {claims['username']}")
            return tags

        except Exception as e:
            logger.error(f"Failed to add Descope context: {e}")
            return {}
