import json
from unittest.mock import Mock

from verse_sdk.contexts.span import SpanContext
from verse_sdk.contexts.types import EventMetadata


class TestSpanContext:
    def setup_method(self):
        self.mock_span = Mock()
        self.mock_span.add_event = Mock()
        self.mock_span.get_span_context.return_value.is_valid = True
        self.mock_span.record_exception = Mock()
        self.mock_span.set_attribute = Mock()
        self.mock_span.set_status = Mock()

    def test_event_basic(self):
        context = SpanContext(self.mock_span)
        result = context.event("test_event")

        assert result == context
        self.mock_span.add_event.assert_called_once_with(
            "test_event", {"level": "info"}
        )

    def test_event_with_custom_level(self):
        context = SpanContext(self.mock_span)
        result = context.event("error_event", level="error")

        assert result == context
        self.mock_span.add_event.assert_called_once_with(
            "error_event", {"level": "error"}
        )

    def test_event_with_metadata(self):
        context = SpanContext(self.mock_span)
        metadata: EventMetadata = {"key1": "value1", "key2": "value2"}
        result = context.event("test_event", metadata=metadata)

        assert result == context
        self.mock_span.add_event.assert_called_once_with(
            "test_event", {"level": "info", "metadata": json.dumps(metadata)}
        )

    def test_event_with_attrs(self):
        context = SpanContext(self.mock_span)
        result = context.event("test_event", custom_attr="value", another_attr=123)

        assert result == context
        self.mock_span.add_event.assert_called_once_with(
            "test_event", {"level": "info", "custom_attr": "value", "another_attr": 123}
        )

    def test_event_with_metadata_and_attrs(self):
        context = SpanContext(self.mock_span)
        metadata: EventMetadata = {"meta_key": "meta_value"}
        result = context.event("test_event", metadata=metadata, custom_attr="value")

        assert result == context
        self.mock_span.add_event.assert_called_once_with(
            "test_event",
            {"level": "info", "metadata": json.dumps(metadata), "custom_attr": "value"},
        )

    def test_event_with_none_metadata(self):
        context = SpanContext(self.mock_span)
        result = context.event("test_event", metadata=None)

        assert result == context
        self.mock_span.add_event.assert_called_once_with(
            "test_event", {"level": "info"}
        )

    def test_event_with_invalid_span(self):
        context = SpanContext(self.mock_span)
        self.mock_span.get_span_context.return_value.is_valid = False
        result = context.event("test_event")

        assert result == context
        self.mock_span.add_event.assert_not_called()
