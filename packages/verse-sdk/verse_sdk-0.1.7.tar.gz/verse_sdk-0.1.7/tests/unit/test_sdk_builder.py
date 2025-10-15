from unittest.mock import Mock, patch

from verse_sdk.sdk_builder import VerseSDKBuilder


class TestVerseSDKBuilderShutdown:
    """Tests for shutdown method - ensures background threads are stopped."""

    @patch("verse_sdk.sdk_builder.trace")
    def test_shutdown_stops_provider_and_cleans_up(self, mock_trace):
        """Shutdown should flush pending spans, stop the provider, and mark SDK as uninitialized."""
        builder = VerseSDKBuilder()
        builder._initialized = True
        mock_provider = Mock()
        mock_trace.get_tracer_provider.return_value = mock_provider

        builder.shutdown()

        mock_provider.shutdown.assert_called_once()
        assert builder._initialized is False

    @patch("verse_sdk.sdk_builder.trace")
    def test_shutdown_is_idempotent(self, mock_trace):
        """Calling shutdown multiple times should be safe."""
        builder = VerseSDKBuilder()
        builder._initialized = True
        mock_provider = Mock()
        mock_trace.get_tracer_provider.return_value = mock_provider

        builder.shutdown()
        builder.shutdown()  # Second call should be no-op

        mock_provider.shutdown.assert_called_once()

    @patch("verse_sdk.sdk_builder.trace")
    @patch("verse_sdk.sdk_builder.logging")
    def test_shutdown_handles_errors_gracefully(self, mock_logging, mock_trace):
        """Shutdown should not raise exceptions even if provider.shutdown() fails."""
        builder = VerseSDKBuilder()
        builder._initialized = True
        mock_provider = Mock()
        mock_provider.shutdown.side_effect = Exception("Provider error")
        mock_trace.get_tracer_provider.return_value = mock_provider

        builder.shutdown()  # Should not raise

        mock_logging.warning.assert_called_once()
