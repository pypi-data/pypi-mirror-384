from __future__ import annotations

from typing import Any

from ..utils import to_json
from .base import BaseContext, ContextType
from .types import EventMetadata, Level, ObservationType


class SpanContext(BaseContext):
    """Context for regular spans (sub-operations)."""

    observation_type: ObservationType = "observation"
    type: ContextType = "span"

    def event(
        self,
        name: str,
        *,
        level: Level = "info",
        metadata: EventMetadata | None = None,
        **attrs,
    ) -> SpanContext:
        """Add an event to the span with severity level and metadata."""
        if self._span.get_span_context().is_valid:
            payload = {"level": level}
            if metadata:
                payload.update(metadata=to_json(metadata))
            payload.update(**attrs)
            self._span.add_event(name, payload)
        return self

    def input(self, input: Any) -> SpanContext:
        """Set the input for the span."""
        self._span.set_attribute("input", str(input))
        return self

    def level(self, level: Level) -> SpanContext:
        """Set the level for the span."""
        self._span.set_attribute("observation.level", str(level))
        return self

    def output(self, output: Any) -> SpanContext:
        """Set the output for the span."""
        self._span.set_attribute("output", str(output))
        return self

    def status_message(self, status_message: str) -> SpanContext:
        """Set the status message for the span."""
        self._span.set_attribute("observation.status_message", str(status_message))
        return self
