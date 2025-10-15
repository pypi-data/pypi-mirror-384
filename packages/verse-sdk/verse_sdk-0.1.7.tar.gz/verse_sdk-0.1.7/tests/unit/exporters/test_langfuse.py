from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from verse_sdk.exporters.langfuse.exporter import LangfuseExporter


class TestLangfuseExporter:
    def setup_method(self):
        self.valid_config = {
            "public_key": "test_public_key",
            "secret_key": "test_secret_key",
        }

    def test_init_with_valid_config(self):
        exporter = LangfuseExporter(self.valid_config)

        assert exporter.config["public_key"] == "test_public_key"
        assert exporter.config["secret_key"] == "test_secret_key"

    def test_init_with_none_config(self):
        with patch.dict(
            "os.environ",
            {
                "LANGFUSE_PUBLIC_KEY": "env_public_key",
                "LANGFUSE_SECRET_KEY": "env_secret_key",
            },
        ):
            exporter = LangfuseExporter(None)

            assert exporter.config["public_key"] == "env_public_key"
            assert exporter.config["secret_key"] == "env_secret_key"

    def test_init_with_empty_config(self):
        with patch.dict(
            "os.environ",
            {
                "LANGFUSE_PUBLIC_KEY": "env_public_key",
                "LANGFUSE_SECRET_KEY": "env_secret_key",
            },
        ):
            exporter = LangfuseExporter({})

            assert exporter.config["public_key"] == "env_public_key"
            assert exporter.config["secret_key"] == "env_secret_key"

    def test_init_merges_env_and_config(self):
        with patch.dict(
            "os.environ",
            {
                "LANGFUSE_PUBLIC_KEY": "env_public_key",
                "LANGFUSE_SECRET_KEY": "env_secret_key",
                "LANGFUSE_HOST": "https://env.langfuse.com",
                "LANGFUSE_REGION": "us",
            },
        ):
            config = {
                "public_key": "config_public_key",
                "secret_key": "config_secret_key",
            }
            exporter = LangfuseExporter(config)

            assert exporter.config["public_key"] == "config_public_key"
            assert exporter.config["secret_key"] == "config_secret_key"
            assert exporter.config["host"] == "https://env.langfuse.com"
            assert exporter.config["region"] == "us"

    def test_validation_missing_public_key(self):
        config = {"secret_key": "test_secret_key"}

        with pytest.raises(ValueError, match="Langfuse `public_key` must be set"):
            LangfuseExporter(config)

    def test_validation_missing_secret_key(self):
        config = {"public_key": "test_public_key"}

        with pytest.raises(ValueError, match="Langfuse `secret_key` must be set"):
            LangfuseExporter(config)

    def test_validation_missing_both_keys(self):
        config = {}

        with pytest.raises(
            ValueError,
            match="Langfuse `public_key` must be set\nLangfuse `secret_key` must be set",
        ):
            LangfuseExporter(config)

    def test_validation_with_none_values(self):
        config = {"public_key": None, "secret_key": None}

        with pytest.raises(
            ValueError,
            match="Langfuse `public_key` must be set\nLangfuse `secret_key` must be set",
        ):
            LangfuseExporter(config)

    def test_endpoint_with_custom_host(self):
        config = {
            "public_key": "test_public_key",
            "secret_key": "test_secret_key",
            "host": "https://custom.langfuse.com",
        }
        exporter = LangfuseExporter(config)

        assert (
            exporter.endpoint == "https://custom.langfuse.com/api/public/otel/v1/traces"
        )

    def test_endpoint_with_us_region(self):
        config = {
            "public_key": "test_public_key",
            "secret_key": "test_secret_key",
            "region": "US",
        }
        exporter = LangfuseExporter(config)

        assert (
            exporter.endpoint
            == "https://us.cloud.langfuse.com/api/public/otel/v1/traces"
        )

    def test_endpoint_with_eu_region(self):
        config = {
            "public_key": "test_public_key",
            "secret_key": "test_secret_key",
            "region": "EU",
        }
        exporter = LangfuseExporter(config)

        assert (
            exporter.endpoint == "https://cloud.langfuse.com/api/public/otel/v1/traces"
        )

    def test_endpoint_default_eu(self):
        config = {"public_key": "test_public_key", "secret_key": "test_secret_key"}
        exporter = LangfuseExporter(config)

        assert (
            exporter.endpoint == "https://cloud.langfuse.com/api/public/otel/v1/traces"
        )

    def test_endpoint_host_overrides_region(self):
        config = {
            "public_key": "test_public_key",
            "secret_key": "test_secret_key",
            "host": "https://custom.langfuse.com",
            "region": "US",
        }
        exporter = LangfuseExporter(config)

        assert (
            exporter.endpoint == "https://custom.langfuse.com/api/public/otel/v1/traces"
        )

    @patch("verse_sdk.exporters.langfuse.exporter.HTTPTraceExporter")
    @patch("verse_sdk.exporters.langfuse.exporter.ScopeFilterExporter")
    @patch("verse_sdk.exporters.langfuse.exporter.BatchSpanProcessor")
    def test_create_span_processor(
        self, mock_batch_processor, mock_scope_filter, mock_http_exporter
    ):
        with patch.dict("os.environ", {}, clear=True):
            config = {
                "public_key": "test_public_key",
                "secret_key": "test_secret_key",
                "host": "https://test.langfuse.com",
            }
            exporter = LangfuseExporter(config)

            mock_resource = Mock()
            mock_http_exporter.return_value = Mock()
            mock_scope_filter.return_value = Mock()
            mock_batch_processor.return_value = Mock()

            result = exporter.create_span_processor(mock_resource)

            mock_http_exporter.assert_called_once_with(
                endpoint="https://test.langfuse.com/api/public/otel/v1/traces",
                headers={
                    "authorization": "Basic dGVzdF9wdWJsaWNfa2V5OnRlc3Rfc2VjcmV0X2tleQ=="
                },
                timeout=10.0,
            )
            mock_scope_filter.assert_called_once_with(
                mock_http_exporter.return_value, exporter.config
            )
            mock_batch_processor.assert_called_once_with(mock_scope_filter.return_value)
            assert result == mock_batch_processor.return_value

    def test_env_method(self):
        with patch.dict(
            "os.environ",
            {
                "LANGFUSE_HOST": "https://test.langfuse.com",
                "LANGFUSE_PUBLIC_KEY": "env_public_key",
                "LANGFUSE_REGION": "us",
                "LANGFUSE_SECRET_KEY": "env_secret_key",
            },
        ):
            env_config = LangfuseExporter.env()

            assert env_config["host"] == "https://test.langfuse.com"
            assert env_config["public_key"] == "env_public_key"
            assert env_config["region"] == "us"
            assert env_config["secret_key"] == "env_secret_key"

    def test_env_method_missing_vars(self):
        with patch.dict("os.environ", {}, clear=True):
            env_config = LangfuseExporter.env()

            assert env_config["host"] is None
            assert env_config["public_key"] is None
            assert env_config["region"] is None
            assert env_config["secret_key"] is None

    def test_config_with_scopes(self):
        config = {
            "public_key": "test_public_key",
            "secret_key": "test_secret_key",
            "scopes": ["generation", "span"],
        }
        exporter = LangfuseExporter(config)

        assert exporter.config["scopes"] == ["generation", "span"]

    def test_config_with_all_options(self):
        config = {
            "public_key": "test_public_key",
            "secret_key": "test_secret_key",
            "host": "https://custom.langfuse.com",
            "region": "us",
            "scopes": ["generation"],
        }
        exporter = LangfuseExporter(config)

        assert exporter.config["public_key"] == "test_public_key"
        assert exporter.config["secret_key"] == "test_secret_key"
        assert exporter.config["host"] == "https://custom.langfuse.com"
        assert exporter.config["region"] == "us"
        assert exporter.config["scopes"] == ["generation"]

    def test_validation_logging(self):
        config = {"public_key": "test_public_key"}

        with patch("verse_sdk.exporters.langfuse.exporter.logging") as mock_logging:
            with pytest.raises(ValueError, match="Langfuse `secret_key` must be set"):
                LangfuseExporter(config)

            mock_logging.error.assert_called_once_with(
                "Langfuse validation errors: Langfuse `secret_key` must be set"
            )

    def test_validation_multiple_errors_logging(self):
        config = {}

        with patch("verse_sdk.exporters.langfuse.exporter.logging") as mock_logging:
            with pytest.raises(ValueError, match="Langfuse `public_key` must be set"):
                LangfuseExporter(config)

            mock_logging.error.assert_called_once_with(
                "Langfuse validation errors: Langfuse `public_key` must be set, Langfuse `secret_key` must be set"
            )
