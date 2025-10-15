import functools
import logging
from collections.abc import AsyncIterable

from ...sdk import VerseSDK


def patch_pydantic_ai(sdk: VerseSDK):
    """Patch Pydantic AI to use the Verse SDK."""

    from pydantic_ai import Agent, RunContext
    from pydantic_ai.messages import (
        AgentStreamEvent,
        FunctionToolResultEvent,
        PartDeltaEvent,
    )

    from .utils import (
        get_finish_reason,
        get_generation_messages,
        get_llm_info_from_model,
        get_operation_type,
        get_usage,
    )

    async def handle_events(ctx: RunContext, events: AsyncIterable[AgentStreamEvent]):
        """
        Handle Pydantic events to create LLM generation spans.
        Pydantic dispatches more events than we need, so the delta and finish reason checks are necessary to avoid duplicates.
        """
        try:
            contains_generation = get_finish_reason(ctx) == "stop"

            async for event in events:
                if isinstance(event, (PartDeltaEvent, FunctionToolResultEvent)):
                    contains_generation = True

            if not contains_generation:
                return

            op = get_operation_type(ctx)
            vendor, model_name = get_llm_info_from_model(ctx.model)

            sdk.create_generation(
                f"Pydantic AI: {op.capitalize()}",
                messages=get_generation_messages(ctx),
                model=model_name,
                usage=get_usage(ctx.usage),
                vendor=vendor,
            ).span.end()
        except Exception as e:
            logging.warning("Pydantic streaming event dropped", exc_info=e)

    def patch():
        """Setup monkey-patches for Pydantic AI if not already patched."""
        if not getattr(Agent, "_verse_patched", False):
            patch_run()
            Agent._verse_patched = True

    def patch_run():
        """Setup a moneky patch for Agent.run() that captures the LLM call in a generation span."""
        original_run_method = Agent.run

        @functools.wraps(original_run_method)
        async def run__patched(self, *args, **kwargs):
            try:
                return await original_run_method(
                    self, *args, **kwargs, event_stream_handler=handle_events
                )
            except Exception as e:
                logging.warning("Error patching Agent.run()", exc_info=e)
                return original_run_method(self, *args, **kwargs)

        Agent.run = run__patched

    patch()
