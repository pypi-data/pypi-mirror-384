from __future__ import annotations

import logging

from opentelemetry.trace import Span, Status, StatusCode

from .types import ContextMetadata, ContextType, ObservationType, OperationType, Score


class BaseContext:
    def __init__(self, span: Span):
        """Initialize the base observation context."""
        if not span or not span.get_span_context().is_valid:
            logging.error("Context received invalid span", span=span)
            raise ValueError("Span invalid")

        self._span = span
        self._span.set_attribute("context.type", self.type)
        self._span.set_attribute("observation.type", self.observation_type)

    @property
    def span(self) -> Span:
        """Get the underlying OpenTelemetry span."""
        return self._span

    @property
    def observation_type(self) -> ObservationType:
        """Get the type of observation being created."""
        raise NotImplementedError("Observation type must be implemented")

    @property
    def type(self) -> ContextType:
        """Identify the type of context being created."""
        raise NotImplementedError("Context type must be implemented")

    def metadata(self, data: ContextMetadata) -> BaseContext:
        """Add metadata to the span."""
        self.set_attributes(prefix="metadata", **data)
        return self

    def error(self, exception: Exception) -> BaseContext:
        """Record an error on the span."""
        try:
            self._span.set_attribute("error", True)
            self._span.set_attribute("error.type", type(exception).__name__)
            self._span.set_attribute("error.message", str(exception))
            self._span.record_exception(exception)
            self._span.set_status(Status(StatusCode.ERROR, str(exception)))
            return self
        except Exception as e:
            logging.warning("Error setting exception on context", exc_info=e)
            return self

    def operation(self, operation: OperationType) -> BaseContext:
        """Set the AI operation of the context."""
        self._span.set_attribute("ai.operation", operation)
        self._span.set_attribute("langfuse.observation.type", operation)
        return self

    def score(
        self,
        score: Score,
    ) -> BaseContext:
        """Set score details and register it as an event."""
        try:
            score_type = f"{self.type}_score"
            score_type_key = (
                f"{score_type}.{score['name']}"
                if self.type != "observation"
                else score["name"]
            )

            self.set_attributes(
                prefix=score_type_key,
                comment=score["comment"],
                value=str(score["value"]),
            )

            self._span.add_event(
                score_type,
                {
                    "name": score["name"],
                    "value": str(score["value"]),
                    "comment": score["comment"] or "",
                },
            )

            return self
        except Exception as e:
            logging.warning("Error setting score on context", exc_info=e)
            return self

    def set_attributes(self, prefix: str | None = None, **attributes) -> BaseContext:
        """Helper to set attributes with optional prefix."""
        try:
            for key, value in attributes.items():
                if value is not None:
                    attr_key = f"{prefix}.{key}" if prefix else key
                    self._span.set_attribute(attr_key, str(value))

            return self
        except Exception as e:
            logging.warning("Error setting attributes on context", exc_info=e)
            return self

    def status(self, status: Status) -> BaseContext:
        """Set the status for the span."""
        self._span.set_status(status)
        return self
