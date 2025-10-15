from __future__ import annotations

from unittest.mock import patch

from verse_sdk.exporters import ExportersRegistry


class TestExportersRegistry:
    def setup_method(self):
        self.registry = ExportersRegistry()

    def test_console_exporter_with_no_config(self):
        exporter = self.registry.console()

        assert exporter is not None
        assert hasattr(exporter, "config")
        assert exporter.config == {}

    def test_console_exporter_with_config(self):
        config = {"scopes": ["test_scope"]}
        exporter = self.registry.console(config)

        assert exporter is not None
        assert hasattr(exporter, "config")
        assert exporter.config == config

    def test_console_exporter_with_none_config(self):
        exporter = self.registry.console(None)

        assert exporter is not None
        assert hasattr(exporter, "config")
        assert exporter.config == {}

    def test_langfuse_exporter_with_config(self):
        config = {
            "public_key": "custom_public_key",
            "secret_key": "custom_secret_key",
            "host": "custom_host",
            "region": "us",
            "scopes": ["test_scope"],
        }

        exporter = self.registry.langfuse(config)

        assert exporter is not None
        assert hasattr(exporter, "config")
        assert exporter.config["public_key"] == "custom_public_key"
        assert exporter.config["secret_key"] == "custom_secret_key"

    def test_langfuse_exporter_validation_error(self):
        config = {
            "public_key": "test_public_key",
            "secret_key": None,
        }

        exporter = self.registry.langfuse(config)

        assert exporter is None

    def test_safe_named_exporter_decorator_success(self):
        @ExportersRegistry.safe_named_exporter
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"

    def test_safe_named_exporter_decorator_exception(self):
        @ExportersRegistry.safe_named_exporter
        def test_function():
            raise ValueError("Test error")

        with patch("verse_sdk.exporters.logging") as mock_logging:
            result = test_function()

            assert result is None
            mock_logging.warning.assert_called_once()

    def test_safe_named_exporter_decorator_preserves_function_metadata(self):
        @ExportersRegistry.safe_named_exporter
        def test_function():
            return "success"

        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ is None

    def test_registry_instance_methods(self):
        console_exporter = self.registry.console()
        assert console_exporter is not None

        langfuse_exporter = self.registry.langfuse(
            {"public_key": "test", "secret_key": "test"}
        )
        assert langfuse_exporter is not None

    def test_registry_class_methods(self):
        registry = ExportersRegistry()
        console_exporter = registry.console()
        assert console_exporter is not None

        langfuse_exporter = registry.langfuse(
            {"public_key": "test", "secret_key": "test"}
        )
        assert langfuse_exporter is not None
