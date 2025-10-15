from opentelemetry.sdk.trace.export import SpanExporter

from ..exporters.types import ExporterConfig


class ScopeFilterExporter(SpanExporter):
    _allowed_scopes: list[str]
    _exporter: SpanExporter

    def __init__(self, exporter: SpanExporter, config: ExporterConfig):
        self._allowed_scopes = config.get("scopes", [])
        self._exporter = exporter

    def export(self, spans):
        """Export the spans, filtering out anything that doesn't have an allowed scope."""
        if not self.is_enabled():
            return self._exporter.export(spans)

        exported_spans = []
        trace_scopes = {}

        for span in spans:
            scope = span.attributes.get("session.scope")
            trace_id = span.get_span_context().trace_id

            if scope is not None and trace_id not in trace_scopes:
                trace_scopes[trace_id] = scope

            # assumes that trace wraps fully observation
            if self._has_scope(trace_scopes.get(trace_id)):
                exported_spans.append(span)

        return self._exporter.export(exported_spans)

    def force_flush(self, timeout_millis=None):
        """Force flush the scope filter processor."""
        return self._exporter.force_flush(timeout_millis)

    def shutdown(self):
        """Shutdown the scope filter processor."""
        return self._exporter.shutdown()

    def _has_scope(self, scope: str | None) -> bool:
        """Check if the span has a scope."""
        return scope and scope in self._allowed_scopes

    def is_enabled(self) -> bool:
        """Check if the scope filter processor is enabled."""
        return self._allowed_scopes is not None and len(self._allowed_scopes) > 0
