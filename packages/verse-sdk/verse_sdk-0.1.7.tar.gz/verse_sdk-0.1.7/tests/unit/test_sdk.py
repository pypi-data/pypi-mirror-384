from unittest.mock import Mock, patch

import pytest

from verse_sdk.sdk import VerseSDK


class TestVerseSDK:
    def setup_method(self):
        self.mock_tracer = Mock()
        self.mock_span = Mock()

        self.mock_trace_patcher = patch("verse_sdk.sdk.trace")
        self.mock_trace = self.mock_trace_patcher.start()
        self.mock_trace.get_current_span.return_value = self.mock_span
        self.mock_provider = Mock()
        self.mock_trace.get_tracer_provider.return_value = self.mock_provider

        class MockNoOpTracerProvider:
            pass

        self.mock_trace.NoOpTracerProvider = MockNoOpTracerProvider

    def teardown_method(self):
        self.mock_trace_patcher.stop()

    def test_score_with_observation_target(self):
        sdk = VerseSDK(self.mock_tracer)
        score_data = {"accuracy": 0.95, "confidence": 0.8}

        with patch("verse_sdk.sdk.SpanContext") as mock_span_context:
            mock_span_instance = Mock()
            mock_span_context.return_value = mock_span_instance

            sdk.score(score_data, "observation")

            mock_span_context.assert_called_once_with(self.mock_span)
            mock_span_instance.score.assert_called_once_with(score_data)

    def test_score_with_trace_target(self):
        sdk = VerseSDK(self.mock_tracer)
        score_data = {"overall": 0.9, "quality": 0.85}

        with patch("verse_sdk.sdk.TraceContext") as mock_trace_context:
            mock_trace_instance = Mock()
            mock_trace_context.return_value = mock_trace_instance

            sdk.score(score_data, "trace")

            mock_trace_context.assert_called_once_with(self.mock_span)
            mock_trace_instance.score.assert_called_once_with(score_data)

    def test_score_handles_exception(self):
        sdk = VerseSDK(self.mock_tracer)
        score_data = {"test": "value"}

        with patch("verse_sdk.sdk.SpanContext") as mock_span_context:
            mock_span_context.side_effect = Exception("Test error")

            with patch("verse_sdk.sdk.logging") as mock_logging:
                sdk.score(score_data, "observation")

                mock_logging.warning.assert_called_once()

    def test_set_tracer_with_valid_tracer(self):
        sdk = VerseSDK(self.mock_tracer)
        assert sdk._tracer == self.mock_tracer

    def test_set_tracer_with_none_tracer(self):
        with pytest.raises(ValueError, match="Tracer not initialized"):
            VerseSDK(None)

    def test_set_tracer_with_false_tracer(self):
        with pytest.raises(ValueError, match="Tracer not initialized"):
            VerseSDK(False)

    def test_set_tracer_with_empty_string_tracer(self):
        with pytest.raises(ValueError, match="Tracer not initialized"):
            VerseSDK("")

    def test_set_tracer_with_zero_tracer(self):
        with pytest.raises(ValueError, match="Tracer not initialized"):
            VerseSDK(0)

    def test_validate_tracer_provider_with_valid_provider(self):
        sdk = VerseSDK(self.mock_tracer)
        sdk._validate_tracer_provider()

    def test_validate_tracer_provider_with_exception(self):
        self.mock_trace.get_tracer_provider.side_effect = Exception("Provider error")

        with pytest.raises(ValueError, match="Tracer provider unavailable"):
            VerseSDK(self.mock_tracer)

    def test_validate_tracer_provider_with_none_provider(self):
        self.mock_trace.get_tracer_provider.return_value = None

        with pytest.raises(ValueError, match="Invalid tracer provider given"):
            VerseSDK(self.mock_tracer)

    def test_validate_tracer_provider_with_noop_provider(self):
        mock_noop_provider = Mock()
        mock_noop_provider.__class__ = self.mock_trace.NoOpTracerProvider
        self.mock_trace.get_tracer_provider.return_value = mock_noop_provider

        with pytest.raises(ValueError, match="Invalid tracer provider given"):
            VerseSDK(self.mock_tracer)

    def test_score_with_different_score_types(self):
        sdk = VerseSDK(self.mock_tracer)

        with patch("verse_sdk.sdk.SpanContext") as mock_span_context:
            mock_span_instance = Mock()
            mock_span_context.return_value = mock_span_instance

            numeric_score = {"rating": 4.5}
            sdk.score(numeric_score, "observation")
            mock_span_instance.score.assert_called_with(numeric_score)

            boolean_score = {"passed": True, "failed": False}
            sdk.score(boolean_score, "observation")
            mock_span_instance.score.assert_called_with(boolean_score)

            string_score = {"status": "excellent", "grade": "A"}
            sdk.score(string_score, "observation")
            mock_span_instance.score.assert_called_with(string_score)

    def test_score_with_empty_score(self):
        sdk = VerseSDK(self.mock_tracer)

        with patch("verse_sdk.sdk.SpanContext") as mock_span_context:
            mock_span_instance = Mock()
            mock_span_context.return_value = mock_span_instance

            empty_score = {}
            sdk.score(empty_score, "observation")
            mock_span_instance.score.assert_called_once_with(empty_score)

    def test_score_with_nested_score(self):
        sdk = VerseSDK(self.mock_tracer)

        with patch("verse_sdk.sdk.SpanContext") as mock_span_context:
            mock_span_instance = Mock()
            mock_span_context.return_value = mock_span_instance

            nested_score = {
                "metrics": {"accuracy": 0.95, "precision": 0.92, "recall": 0.88},
                "overall": 0.91,
            }
            sdk.score(nested_score, "observation")
            mock_span_instance.score.assert_called_once_with(nested_score)
