import json
import logging
from typing import Any, Tuple

from pydantic_ai import RunContext, RunUsage

from ...contexts import GenerationMessage, GenerationUsage
from ...utils import get
from .constants import VENDOR_ANTHROPIC, VENDOR_OPENAI, VENDOR_UNKNOWN


def calculate_total_tokens(usage: RunUsage) -> int | None:
    """Calculate the total tokens."""
    return (
        usage.input_tokens + usage.output_tokens
        if usage.input_tokens and usage.output_tokens
        else None
    )


def get_finish_reason(ctx: RunContext) -> str:
    """Get the finish reason from RunContext."""
    if hasattr(ctx, "messages") and ctx.messages:
        return get(ctx.messages[-1], "finish_reason", "")

    return ""


def get_generation_messages(ctx: RunContext) -> list[GenerationMessage]:
    """Convert Pydantic AI RunContext messages to GenerationMessage format."""
    messages = []

    if not hasattr(ctx, "messages") or not ctx.messages:
        return messages

    for message in ctx.messages:
        if hasattr(message, "parts"):
            content_parts = []
            tool_calls = []

            for part in message.parts:
                part_type = part.__class__.__name__

                if part_type == "SystemPromptPart":
                    messages.append(
                        GenerationMessage(
                            content=part.content,
                            function_call=None,
                            name=None,
                            role="system",
                            tool_calls=None,
                        )
                    )
                elif part_type == "UserPromptPart":
                    messages.append(
                        GenerationMessage(
                            content=part.content,
                            function_call=None,
                            name=None,
                            role="user",
                            tool_calls=None,
                        )
                    )
                elif part_type == "ToolCallPart":
                    tool_calls.append(
                        {
                            "function": {
                                "arguments": part.args,
                                "name": part.tool_name,
                            },
                            "id": part.tool_call_id,
                            "type": "function",
                        }
                    )
                elif part_type == "TextPart":
                    content_parts.append(part.content)
                elif part_type == "ToolReturnPart":
                    messages.append(
                        GenerationMessage(
                            content=json.dumps(part.content),
                            id=part.tool_call_id,
                            role="tool",
                        )
                    )

            if tool_calls or content_parts:
                messages.append(
                    GenerationMessage(
                        content=" ".join(content_parts) if content_parts else "",
                        function_call=None,
                        name=None,
                        role="assistant",
                        tool_calls=tool_calls if tool_calls else None,
                    )
                )

    return messages


def get_llm_info_from_model(model: Any) -> Tuple[str, str]:
    """Get the vendor and model name."""
    try:
        if isinstance(model, get_model_instance(VENDOR_OPENAI)):
            return VENDOR_OPENAI, model.model_name
        if isinstance(model, get_model_instance(VENDOR_ANTHROPIC)):
            return VENDOR_ANTHROPIC, model.model_name

        return VENDOR_UNKNOWN, getattr(model, "model_name", VENDOR_UNKNOWN)
    except Exception:
        return VENDOR_UNKNOWN, VENDOR_UNKNOWN


def get_model_instance(model_name: str) -> Any:
    """Lazy load the vendor model by name."""
    try:
        if model_name.startswith(VENDOR_OPENAI):
            from pydantic_ai.models.openai import OpenAIChatModel

            return OpenAIChatModel
        if model_name.startswith(VENDOR_ANTHROPIC):
            from pydantic_ai.models.anthropic import AnthropicChatModel

            return AnthropicChatModel

        return None
    except Exception:
        logging.warning(f"Error loading model {model_name}", exc_info=True)
        return None


def get_operation_type(ctx: RunContext) -> str:
    """Get the operation type based on the messages."""
    if hasattr(ctx, "messages") and ctx.messages:
        return "chat"
    return "completion"


def get_usage(usage: RunUsage) -> GenerationUsage:
    """Get the usage from RunContext."""
    return GenerationUsage(
        completion_tokens=usage.output_tokens,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        prompt_tokens=usage.input_tokens,
        tool_calls=usage.tool_calls,
        total_tokens=calculate_total_tokens(usage),
    )
