"""Integration tests for MLflow plugin entry points."""

import inspect
import sys

# Use importlib.metadata for all Python versions (available in 3.8+ via importlib_metadata backport)
if sys.version_info >= (3, 10):
    from importlib.metadata import entry_points
else:
    from importlib_metadata import entry_points


class TestPluginEntryPoints:
    def test_app_entry_point(self):
        eps = entry_points(group="mlflow.app")
        names = [ep.name for ep in eps]

        assert "descope" in names, "descope app not registered"

    def test_app_entry_point_can_be_loaded(self):
        eps = {ep.name: ep for ep in entry_points(group="mlflow.app")}

        assert "descope" in eps
        factory = eps["descope"].load()
        assert factory is not None
        assert callable(factory)

    def test_create_app_signature(self):
        from mlflow_descope_auth.server import create_app

        sig = inspect.signature(create_app)
        assert "app" in sig.parameters
