from unittest.mock import Mock

import pytest

from verse_sdk.processors import AttributeProcessor


class TestAttributeProcessor:
    @pytest.fixture
    def processor(self):
        return AttributeProcessor()

    @pytest.fixture
    def mock_span(self):
        span = Mock()
        span_context = Mock()
        span_context.span_id = 12345
        span.get_span_context.return_value = span_context
        span.parent = None
        span._attributes = {}
        return span

    @pytest.fixture
    def mock_parent_span(self):
        span = Mock()
        span_context = Mock()
        span_context.span_id = 67890
        span.get_span_context.return_value = span_context
        span.parent = None
        span._attributes = {
            "session.id": "test-session",
            "project.id": "test-project",
            "other.attr": "should-not-copy",
        }
        return span

    def test_on_start_registers_span(self, processor, mock_span):
        processor.on_start(mock_span)

        assert 12345 in processor._active_spans
        assert processor._active_spans[12345] == mock_span

    def test_on_start_without_parent(self, processor, mock_span):
        mock_span.parent = None
        processor.on_start(mock_span)

        assert 12345 in processor._active_spans

    def test_on_start_propagates_from_active_parent(
        self, processor, mock_span, mock_parent_span
    ):
        processor.on_start(mock_parent_span)

        parent_context = Mock()
        parent_context.span_id = 67890
        parent_context.is_valid = True
        mock_span.parent = parent_context

        processor.on_start(mock_span)

        assert mock_span.set_attribute.call_count == 2
        mock_span.set_attribute.assert_any_call("session.id", "test-session")
        mock_span.set_attribute.assert_any_call("project.id", "test-project")

    def test_on_start_propagates_from_cache(self, processor, mock_span):
        processor._span_cache[67890] = {
            "session.id": "cached-session",
            "project.id": "cached-project",
        }

        parent_context = Mock()
        parent_context.span_id = 67890
        parent_context.is_valid = True
        mock_span.parent = parent_context

        processor.on_start(mock_span)

        assert mock_span.set_attribute.call_count == 2
        mock_span.set_attribute.assert_any_call("session.id", "cached-session")
        mock_span.set_attribute.assert_any_call("project.id", "cached-project")

    def test_on_end_caches_attributes(self, processor):
        span = Mock()
        parent_span_context = Mock()
        parent_span_context.span_id = 12345
        span.get_span_context.return_value = parent_span_context
        span.attributes = {
            "session.id": "test-session",
            "project.id": "test-project",
            "other.attr": "should-not-cache",
        }

        processor.on_end(span)

        assert 12345 in processor._span_cache
        assert processor._span_cache[12345] == {
            "session.id": "test-session",
            "project.id": "test-project",
        }

    def test_on_end_removes_from_active_spans(self, processor, mock_span):
        processor._active_spans[12345] = mock_span

        readable_span = Mock()
        span_context = Mock()
        span_context.span_id = 12345
        readable_span.get_span_context.return_value = span_context
        readable_span.attributes = {}

        processor.on_end(readable_span)

        assert 12345 not in processor._active_spans

    def test_shutdown_clears_caches(self, processor, mock_span):
        processor._active_spans[12345] = mock_span
        processor._span_cache[67890] = {"session.id": "test"}

        processor.shutdown()

        assert len(processor._active_spans) == 0
        assert len(processor._span_cache) == 0

    def test_force_flush_returns_true(self, processor):
        assert processor.force_flush() is True
        assert processor.force_flush(timeout_millis=5000) is True

    def test_only_propagates_configured_attributes(
        self, processor, mock_span, mock_parent_span
    ):
        processor.on_start(mock_parent_span)

        parent_context = Mock()
        parent_context.span_id = 67890
        parent_context.is_valid = True
        mock_span.parent = parent_context

        processor.on_start(mock_span)

        assert mock_span.set_attribute.call_count == 2
        calls = [call[0][0] for call in mock_span.set_attribute.call_args_list]
        assert "other.attr" not in calls
