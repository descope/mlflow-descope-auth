"""Integration tests for MLflow plugin entry points."""

import sys


class TestPluginEntryPoints:
    def test_auth_provider_entry_point(self):
        if sys.version_info >= (3, 10):
            from importlib.metadata import entry_points

            eps = entry_points(group="mlflow.request_auth_provider")
            names = [ep.name for ep in eps]
        else:
            import pkg_resources

            eps = list(pkg_resources.iter_entry_points("mlflow.request_auth_provider"))
            names = [ep.name for ep in eps]

        assert "descope" in names, "descope auth provider not registered"

    def test_header_provider_entry_point(self):
        if sys.version_info >= (3, 10):
            from importlib.metadata import entry_points

            eps = entry_points(group="mlflow.request_header_provider")
            names = [ep.name for ep in eps]
        else:
            import pkg_resources

            eps = list(pkg_resources.iter_entry_points("mlflow.request_header_provider"))
            names = [ep.name for ep in eps]

        assert "descope" in names, "descope header provider not registered"

    def test_context_provider_entry_point(self):
        if sys.version_info >= (3, 10):
            from importlib.metadata import entry_points

            eps = entry_points(group="mlflow.run_context_provider")
            names = [ep.name for ep in eps]
        else:
            import pkg_resources

            eps = list(pkg_resources.iter_entry_points("mlflow.run_context_provider"))
            names = [ep.name for ep in eps]

        assert "descope" in names, "descope context provider not registered"

    def test_auth_provider_can_be_loaded(self):
        if sys.version_info >= (3, 10):
            from importlib.metadata import entry_points

            eps = {ep.name: ep for ep in entry_points(group="mlflow.request_auth_provider")}
        else:
            import pkg_resources

            eps = {
                ep.name: ep
                for ep in pkg_resources.iter_entry_points("mlflow.request_auth_provider")
            }

        assert "descope" in eps
        provider_class = eps["descope"].load()
        assert provider_class is not None
        assert hasattr(provider_class, "get_name")
        assert hasattr(provider_class, "get_auth")

    def test_header_provider_can_be_loaded(self):
        if sys.version_info >= (3, 10):
            from importlib.metadata import entry_points

            eps = {ep.name: ep for ep in entry_points(group="mlflow.request_header_provider")}
        else:
            import pkg_resources

            eps = {
                ep.name: ep
                for ep in pkg_resources.iter_entry_points("mlflow.request_header_provider")
            }

        assert "descope" in eps
        provider_class = eps["descope"].load()
        assert provider_class is not None
        assert hasattr(provider_class, "in_context")
        assert hasattr(provider_class, "request_headers")

    def test_context_provider_can_be_loaded(self):
        if sys.version_info >= (3, 10):
            from importlib.metadata import entry_points

            eps = {ep.name: ep for ep in entry_points(group="mlflow.run_context_provider")}
        else:
            import pkg_resources

            eps = {
                ep.name: ep for ep in pkg_resources.iter_entry_points("mlflow.run_context_provider")
            }

        assert "descope" in eps
        provider_class = eps["descope"].load()
        assert provider_class is not None
        assert hasattr(provider_class, "in_context")
        assert hasattr(provider_class, "tags")

    def test_auth_provider_instantiation(self):
        from mlflow_descope_auth.auth_provider import DescopeAuthProvider

        provider = DescopeAuthProvider()
        assert provider.get_name() == "descope"
        assert callable(provider.get_auth())

    def test_header_provider_not_in_context_without_token(self):
        import os

        os.environ.pop("DESCOPE_SESSION_TOKEN", None)

        from mlflow_descope_auth.header_provider import DescopeHeaderProvider

        provider = DescopeHeaderProvider()
        assert not provider.in_context()
        assert provider.request_headers() == {}

    def test_context_provider_not_in_context_without_token(self):
        import os

        os.environ.pop("DESCOPE_SESSION_TOKEN", None)

        from mlflow_descope_auth.context_provider import DescopeContextProvider

        provider = DescopeContextProvider()
        assert not provider.in_context()
        assert provider.tags() == {}
