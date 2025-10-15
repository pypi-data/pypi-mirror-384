import asyncio
import atexit
import contextlib
from typing import Any, ClassVar

import litellm
from opentelemetry.trace import Status, StatusCode

from ...contexts import GenerationContext, GenerationMessage
from ...sdk import VerseSDK
from ...utils import apply_value
from .utils import (
    get_completition_choices,
    get_finish_reason,
    get_operation_type,
    get_stream_text,
    get_usage,
    get_usage_from_response,
)


def configure_litellm(sdk: VerseSDK):
    """Configure Litellm to use the Verse SDK."""
    import litellm
    from litellm.integrations.custom_logger import CustomLogger

    class LitellmCallbackHandlers(CustomLogger):
        current_spans: ClassVar[dict[str, GenerationContext]] = {}

        async def async_log_failure_event(
            self, kwargs: dict, response_obj: Any, start_time: float, end_time: float
        ):
            """Handle failed async LLM requests"""
            self.log_failure_event(kwargs, response_obj, start_time, end_time)

        async def async_log_stream_event(
            self, kwargs: dict, response_obj: Any, start_time: float, end_time: float
        ):
            """Called for each streaming chunk."""
            self.log_stream_event(kwargs, response_obj, start_time, end_time)

        async def async_log_success_event(
            self, kwargs: dict, response_obj: Any, start_time: float, end_time: float
        ):
            """Handle successful async LLM requests"""
            self.log_success_event(kwargs, response_obj, start_time, end_time)

        def log_failure_event(
            self, kwargs, response_obj: Any, start_time: float, end_time: float
        ):
            """Handle failed LLM requests"""
            span_ctx = self._get_current_span(kwargs)

            if span_ctx:
                span_ctx.error(kwargs.get("exception", response_obj))
                self._drop_current_span(kwargs)

        def log_post_api_call(
            self, kwargs: dict, response_obj: Any, start_time: float, end_time: float
        ):
            """End the generation span and remove from the active context variable"""
            span_ctx = self._get_current_span(kwargs)

            if span_ctx:
                sdk.event(
                    "llm.response_received",
                    metadata={"length": len(str(response_obj))},
                    level="info",
                    span=span_ctx.span,
                )

        def log_pre_api_call(
            self, model: str, messages: list[GenerationMessage], kwargs: dict
        ):
            """Create a generation span around the LLM request"""
            id = kwargs.get("litellm_call_id")
            self.current_spans[id] = sdk.create_generation(
                name=f"LiteLLM: {(get_operation_type(messages, kwargs)).capitalize()}",
                messages=messages,
                metadata=kwargs.get("metadata", {}),
                model=model,
                usage=get_usage(kwargs),
            )

        def log_stream_event(
            self, kwargs: dict, response_obj: Any, start_time: float, end_time: float
        ):
            """Called for each streaming chunk."""
            span_ctx = self._get_current_span(kwargs)

            if span_ctx:
                try:
                    text = get_stream_text(response_obj)
                    if text:
                        span_ctx.event(
                            "gen_ai.stream.delta",
                            metadata={"content": text[:512]},
                        )
                except Exception:
                    pass

        def log_success_event(
            self, kwargs, response_obj: Any, start_time: float, end_time: float
        ):
            """Handle successful LLM requests"""
            span_ctx = self._get_current_span(kwargs)

            if span_ctx:
                try:
                    apply_value(span_ctx, "model_used", response_obj.model)
                    apply_value(span_ctx, "reason", get_finish_reason(response_obj))

                    span_ctx.completions(
                        get_completition_choices(
                            kwargs.get("complete_streaming_response", response_obj)
                        )
                    )

                    span_ctx.usage(get_usage_from_response(response_obj))
                    span_ctx.status(Status(StatusCode.OK))
                except Exception as e:
                    span_ctx.error(e)
                finally:
                    self._drop_current_span(kwargs)

        def _drop_current_span(self, kwargs: dict):
            span = self.current_spans.pop(kwargs.get("litellm_call_id"), None)
            if span:
                span.span.end()

        def _get_current_span(self, kwargs: dict) -> GenerationContext:
            return self.current_spans.get(kwargs.get("litellm_call_id"))

    litellm.callbacks = [LitellmCallbackHandlers()]


def cleanup_litellm():
    """Clean up litellm HTTP clients to prevent garbage collection issues."""
    try:
        _cleanup_async_clients()
        _cleanup_sync_clients()
        _unregister_atexit_handlers()
    except Exception:
        pass


def _cleanup_async_clients():
    """Clean up async litellm clients."""
    if not hasattr(litellm, "close_litellm_async_clients"):
        return

    try:
        loop = _get_or_create_event_loop()
        loop.run_until_complete(litellm.close_litellm_async_clients())
    except Exception:
        pass


def _cleanup_sync_clients():
    """Clean up synchronous litellm clients."""
    if hasattr(litellm, "module_level_client") and litellm.module_level_client:
        with contextlib.suppress(Exception):
            litellm.module_level_client.close()

    if hasattr(litellm, "client_session") and litellm.client_session:
        with contextlib.suppress(Exception):
            litellm.client_session.close()


def _unregister_atexit_handlers():
    """
    Clear all atexit handlers since we've already done cleanup.
    This prevents litellm's atexit handlers from running during Python shutdown
    when logging streams are already closed, which would cause errors.
    """
    with contextlib.suppress(Exception):
        atexit._clear()


def _get_or_create_event_loop():
    """Get existing event loop or create a new one if needed."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop
