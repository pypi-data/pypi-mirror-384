from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace import Span, Tracer

from .contexts import (
    ContextMetadata,
    EventMetadata,
    GenerationContext,
    GenerationMessage,
    GenerationUsage,
    ObservationType,
    Score,
    SpanContext,
    TraceContext,
)
from .utils import apply_value


class VerseSDK:
    """Core context manager factory"""

    tracer: trace.Tracer

    def __init__(self, tracer: Tracer):
        self._set_tracer(tracer)
        self._validate_tracer_provider()

    def create_generation(
        self,
        name: str,
        *,
        input: Any | None = None,
        messages: list[GenerationMessage] | None = None,
        model: str | None = None,
        output: Any | None = None,
        span: Span | None = None,
        usage: GenerationUsage | None = None,
        vendor: str | None = None,
        **attrs,
    ) -> GenerationContext:
        """
        Create or configure a generation span (LLM operation).

        Args:
            name: Name of the generation span
            messages: Optional list of messages
            model: Model name/identifier
            metadata: Optional metadata dictionary
            usage: Optional usage dictionary
            **attrs: Additional attributes to set on the span

        Returns:
            GenerationContext: A context object for the generation span
        """
        gen_ctx = GenerationContext(span or self._tracer.start_span(name))
        apply_value(gen_ctx, "input", input)
        apply_value(gen_ctx, "messages", messages)
        apply_value(gen_ctx, "model", model)
        apply_value(gen_ctx, "output", output)
        apply_value(gen_ctx, "usage", usage)
        apply_value(gen_ctx, "vendor", vendor)
        return gen_ctx.set_attributes(**attrs)

    def create_span(
        self,
        name: str,
        *,
        input: Any | None = None,
        level: str | None = None,
        metadata: ContextMetadata | None = None,
        op: str | None = None,
        output: Any | None = None,
        span: Span | None = None,
        status_message: str | None = None,
        **attrs,
    ):
        """
        Create or configure a new span (sub-operation).

        Args:
            name: Name of the span
            input: Optional input for the span
            level: Optional level for the span
            metadata: Optional metadata dictionary
            op: Optional operation for the span
            output: Optional output for the span
            status_message: Optional status message for the span
            **attrs: Additional attributes to set on the span

        Returns:
            SpanContext: A context object for the span
        """
        span_ctx = SpanContext(span or self._tracer.start_span(name))
        apply_value(span_ctx, "input", input)
        apply_value(span_ctx, "level", level)
        apply_value(span_ctx, "metadata", metadata)
        apply_value(span_ctx, "operation", op)
        apply_value(span_ctx, "output", output)
        apply_value(span_ctx, "status_message", status_message)
        return span_ctx.set_attributes(**attrs)

    def create_trace(
        self,
        name: str,
        *,
        metadata: ContextMetadata | None = None,
        project_id: str | None = None,
        scope: str | None = None,
        session_id: str | None = None,
        span: Span | None = None,
        tags: list[str] | None = None,
        user_id: str | None = None,
        **attrs,
    ):
        """
        Create or configure a new trace span (top-level operation).

        Args:
            metadata: Optional metadata dictionary
            name: Name of the trace
            project_id: Optional project ID for the trace
            scope: Optional scope for the trace
            session_id: Optional session identifier
            tags: Optional list of tags
            user_id: Optional user identifier
            **attrs: Additional attributes to set on the span

        Returns:
            TraceContext: A context object for the trace span
        """
        trace_ctx = TraceContext(span or self._tracer.start_span(name))
        apply_value(trace_ctx, "metadata", metadata)
        apply_value(trace_ctx, "project", project_id)
        apply_value(trace_ctx, "scope", scope)
        apply_value(trace_ctx, "session", session_id)
        apply_value(trace_ctx, "tags", tags)
        apply_value(trace_ctx, "user", user_id)
        return trace_ctx.set_attributes(**attrs)

    @contextmanager
    def generation(
        self,
        name: str,
        *,
        input: Any | None = None,
        messages: list[GenerationMessage] | None = None,
        model: str | None = None,
        output: Any | None = None,
        usage: GenerationUsage | None = None,
        vendor: str | None = None,
        **attrs,
    ):
        """
        Create a generation span as a context manager (LLM operation).

        Args:
            name: Name of the generation span
            messages: Optional list of messages
            model: Model name/identifier
            metadata: Optional metadata dictionary
            usage: Optional usage dictionary
            **attrs: Additional attributes to set on the span

        Yields:
            GenerationContext: A context object for the generation span
        """
        with self._tracer.start_as_current_span(name) as span:
            yield self.create_generation(
                name,
                input=input,
                messages=messages,
                model=model,
                output=output,
                span=span,
                usage=usage,
                vendor=vendor,
                **attrs,
            )

    @contextmanager
    def span(
        self,
        name: str,
        *,
        input: Any | None = None,
        level: str | None = None,
        metadata: ContextMetadata | None = None,
        op: str | None = None,
        output: Any | None = None,
        status_message: str | None = None,
        **attrs,
    ):
        """
        Create a new span as a context manager (sub-operation).

        Args:
            name: Name of the span
            input: Optional input for the span
            level: Optional level for the span
            metadata: Optional metadata dictionary
            op: Optional operation for the span
            output: Optional output for the span
            status_message: Optional status message for the span
            **attrs: Additional attributes to set on the span

        Yields:
            SpanContext: A context object for the span
        """
        with self._tracer.start_as_current_span(name) as span:
            yield self.create_span(
                name,
                input=input,
                level=level,
                metadata=metadata,
                op=op,
                output=output,
                status_message=status_message,
                span=span,
                **attrs,
            )

    @contextmanager
    def trace(
        self,
        name: str,
        *,
        metadata: ContextMetadata | None = None,
        project_id: str | None = None,
        scope: str | None = None,
        session_id: str | None = None,
        tags: list[str] | None = None,
        user_id: str | None = None,
        **attrs,
    ):
        """
        Create a new trace span as a context manager (top-level operation).

        Args:
            metadata: Optional metadata dictionary
            name: Name of the trace
            project_id: Optional project ID for the trace
            scope: Optional scope for the trace
            session_id: Optional session identifier
            tags: Optional list of tags
            user_id: Optional user identifier
            **attrs: Additional attributes to set on the span

        Yields:
            TraceContext: A context object for the trace span
        """
        with self._tracer.start_as_current_span(name) as span:
            yield self.create_trace(
                name,
                metadata=metadata,
                project_id=project_id,
                scope=scope,
                session_id=session_id,
                span=span,
                tags=tags,
                user_id=user_id,
                **attrs,
            )

    def event(
        self,
        name: str,
        *,
        level: str = "info",
        metadata: EventMetadata | None = None,
        span: Span | None = None,
        **attrs,
    ) -> None:
        """
        Add an event to the current span.

        Args:
            name: Event name
            level: Event level (e.g., "info", "warning", "error")
            metadata: Optional metadata dictionary
            span: Optional span to add the event to
            **attrs: Additional event attributes

        Returns:
            None
        """
        try:
            SpanContext(span or trace.get_current_span()).event(
                name, level=level, metadata=metadata, **attrs
            )
        except Exception as e:
            logging.warning("Error adding event to span", exc_info=e)

    def score(
        self,
        score: Score,
        target: ObservationType,
    ) -> None:
        """
        Add a score to the current observation or trace.

        Args:
            name: Score name/metric
            score: Score dictionary
            target: Whether to score the observation or entire trace
        """
        try:
            span = trace.get_current_span()
            if target == "observation":
                SpanContext(span).score(score)
            else:
                TraceContext(span).score(score)
        except Exception as e:
            logging.warning("Error adding score to span", exc_info=e)

    def _set_tracer(self, tracer: Tracer | None) -> None:
        """Check null check when setting tracer instance"""
        if not tracer:
            raise ValueError("Tracer not initialized")
        self._tracer = tracer

    def _validate_tracer_provider(self) -> None:
        """Validate tracer provider"""
        provider = None

        try:
            provider = trace.get_tracer_provider()
        except Exception as e:
            raise ValueError("Tracer provider unavailable") from e

        if not provider or isinstance(provider, trace.NoOpTracerProvider):
            raise ValueError("Invalid tracer provider given")
