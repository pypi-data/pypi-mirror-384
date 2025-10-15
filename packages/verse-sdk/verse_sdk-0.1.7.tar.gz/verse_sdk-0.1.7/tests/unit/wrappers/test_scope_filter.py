from __future__ import annotations

from unittest.mock import Mock

from verse_sdk.exporters.types import ExporterConfig
from verse_sdk.wrappers.scope_filter import ScopeFilterExporter


class TestScopeFilterExporter:
    def setup_method(self):
        self.mock_exporter = Mock()
        self.mock_span_context = Mock()
        self.mock_span_context.trace_id = 12345

    def _create_mock_span(self, trace_id=12345, scope=None, attributes=None):
        span = Mock()
        span.get_span_context.return_value.trace_id = trace_id
        span.attributes = attributes or {}
        if scope is not None:
            span.attributes["session.scope"] = scope
        return span

    def test_initialization_with_scopes(self):
        config: ExporterConfig = {"scopes": ["user", "admin"]}
        exporter = ScopeFilterExporter(self.mock_exporter, config)

        assert exporter._exporter == self.mock_exporter
        assert exporter._allowed_scopes == ["user", "admin"]

    def test_initialization_with_empty_scopes(self):
        config: ExporterConfig = {"scopes": []}
        exporter = ScopeFilterExporter(self.mock_exporter, config)

        assert exporter._exporter == self.mock_exporter
        assert exporter._allowed_scopes == []

    def test_initialization_with_none_scopes(self):
        config: ExporterConfig = {"scopes": None}
        exporter = ScopeFilterExporter(self.mock_exporter, config)

        assert exporter._exporter == self.mock_exporter
        assert exporter._allowed_scopes is None

    def test_initialization_without_scopes_key(self):
        config: ExporterConfig = {}
        exporter = ScopeFilterExporter(self.mock_exporter, config)

        assert exporter._exporter == self.mock_exporter
        assert exporter._allowed_scopes == []

    def test_export_with_no_scopes_configured(self):
        config: ExporterConfig = {"scopes": []}
        exporter = ScopeFilterExporter(self.mock_exporter, config)

        spans = [
            self._create_mock_span(trace_id=1, scope="user"),
            self._create_mock_span(trace_id=2, scope="admin"),
            self._create_mock_span(trace_id=3, scope="guest"),
        ]

        exporter.export(spans)
        self.mock_exporter.export.assert_called_once_with(spans)

    def test_export_with_none_scopes_configured(self):
        config: ExporterConfig = {"scopes": None}
        exporter = ScopeFilterExporter(self.mock_exporter, config)

        spans = [
            self._create_mock_span(trace_id=1, scope="user"),
            self._create_mock_span(trace_id=2, scope="admin"),
        ]

        exporter.export(spans)
        self.mock_exporter.export.assert_called_once_with(spans)

    def test_export_without_scopes_key(self):
        config: ExporterConfig = {}
        exporter = ScopeFilterExporter(self.mock_exporter, config)

        spans = [
            self._create_mock_span(trace_id=1, scope="user"),
            self._create_mock_span(trace_id=2, scope="admin"),
        ]

        exporter.export(spans)
        self.mock_exporter.export.assert_called_once_with(spans)

    def test_export_filters_spans_by_allowed_scopes(self):
        config: ExporterConfig = {"scopes": ["user", "admin"]}
        exporter = ScopeFilterExporter(self.mock_exporter, config)

        user_span = self._create_mock_span(trace_id=1, scope="user")
        admin_span = self._create_mock_span(trace_id=2, scope="admin")
        guest_span = self._create_mock_span(trace_id=3, scope="guest")
        no_scope_span = self._create_mock_span(trace_id=4, scope=None)

        spans = [user_span, admin_span, guest_span, no_scope_span]
        exporter.export(spans)
        expected_filtered_spans = [user_span, admin_span]
        self.mock_exporter.export.assert_called_once_with(expected_filtered_spans)

    def test_export_filters_spans_by_single_allowed_scope(self):
        config: ExporterConfig = {"scopes": ["admin"]}
        exporter = ScopeFilterExporter(self.mock_exporter, config)

        user_span = self._create_mock_span(trace_id=1, scope="user")
        admin_span = self._create_mock_span(trace_id=2, scope="admin")
        guest_span = self._create_mock_span(trace_id=3, scope="guest")

        spans = [user_span, admin_span, guest_span]
        exporter.export(spans)

        expected_filtered_spans = [admin_span]
        self.mock_exporter.export.assert_called_once_with(expected_filtered_spans)

    def test_export_includes_all_spans_from_trace_with_allowed_scope(self):
        config: ExporterConfig = {"scopes": ["user"]}
        exporter = ScopeFilterExporter(self.mock_exporter, config)

        user_span1 = self._create_mock_span(trace_id=1, scope="user")
        user_span2 = self._create_mock_span(trace_id=1, scope=None)
        admin_span = self._create_mock_span(trace_id=2, scope="admin")

        spans = [user_span1, user_span2, admin_span]
        exporter.export(spans)

        expected_filtered_spans = [user_span1, user_span2]
        self.mock_exporter.export.assert_called_once_with(expected_filtered_spans)

    def test_export_excludes_all_spans_from_trace_without_allowed_scope(self):
        config: ExporterConfig = {"scopes": ["user"]}
        exporter = ScopeFilterExporter(self.mock_exporter, config)

        admin_span1 = self._create_mock_span(trace_id=1, scope="admin")
        admin_span2 = self._create_mock_span(trace_id=1, scope=None)
        guest_span = self._create_mock_span(trace_id=2, scope="guest")

        spans = [admin_span1, admin_span2, guest_span]

        exporter.export(spans)

        expected_filtered_spans = []
        self.mock_exporter.export.assert_called_once_with(expected_filtered_spans)

    def test_export_with_empty_spans_list(self):
        config: ExporterConfig = {"scopes": ["user"]}
        exporter = ScopeFilterExporter(self.mock_exporter, config)
        exporter.export([])

        self.mock_exporter.export.assert_called_once_with([])

    def test_shutdown_delegates_to_exporter(self):
        config: ExporterConfig = {"scopes": ["user"]}
        exporter = ScopeFilterExporter(self.mock_exporter, config)

        exporter.shutdown()

        self.mock_exporter.shutdown.assert_called_once()

    def test_force_flush_delegates_to_exporter(self):
        config: ExporterConfig = {"scopes": ["user"]}
        exporter = ScopeFilterExporter(self.mock_exporter, config)

        exporter.force_flush(5000)

        self.mock_exporter.force_flush.assert_called_once_with(5000)

    def test_force_flush_with_no_timeout(self):
        config: ExporterConfig = {"scopes": ["user"]}
        exporter = ScopeFilterExporter(self.mock_exporter, config)

        exporter.force_flush()

        self.mock_exporter.force_flush.assert_called_once_with(None)

    def test_export_with_mixed_scope_scenarios(self):
        config: ExporterConfig = {"scopes": ["user", "guest"]}
        exporter = ScopeFilterExporter(self.mock_exporter, config)

        spans = [
            self._create_mock_span(trace_id=1, scope="user"),
            self._create_mock_span(trace_id=1, scope=None),
            self._create_mock_span(trace_id=2, scope="admin"),
            self._create_mock_span(trace_id=2, scope=None),
            self._create_mock_span(trace_id=3, scope="guest"),
            self._create_mock_span(trace_id=4, scope=None),
        ]

        exporter.export(spans)
        self.mock_exporter.export.assert_called_once()
        call_args = self.mock_exporter.export.call_args[0][0]
        assert len(call_args) == 3

    def test_export_with_span_attributes_access(self):
        config: ExporterConfig = {"scopes": ["user"]}
        exporter = ScopeFilterExporter(self.mock_exporter, config)

        span = Mock()
        span.get_span_context.return_value.trace_id = 1
        span.attributes = {"session.scope": "user", "other.attr": "value"}

        spans = [span]

        exporter.export(spans)

        assert "session.scope" in span.attributes
        self.mock_exporter.export.assert_called_once()
