from typing import Any

from ..utils import get
from .types import CompletionChoice, CompletionChoiceMessage, GenerationMessage


def get_choice_message(
    choice: CompletionChoice | None,
) -> CompletionChoiceMessage | None:
    """Get message dict from choice"""
    if hasattr(choice, "message") and choice.message:
        return choice.message
    elif hasattr(choice, "delta") and choice.delta:
        return choice.delta
    elif isinstance(choice, dict):
        return choice.get("message") or choice.get("delta") or None
    return None


def get_content_from_choice_message(message: CompletionChoiceMessage | None) -> str:
    """Get the content from the choice message"""
    content = get(message, "content")

    if content is None:
        content = ""
    elif not isinstance(content, str):
        content = str(content)

    return content


def get_content_from_generation_message(message: GenerationMessage | None) -> str:
    """Get the content from the generation message."""
    content = get(message, "content")

    if isinstance(content, list):
        text_parts = []
        for part in content:
            text = get(part, "text")
            if text:
                text_parts.append(text)
        content = "\n".join(text_parts)
    elif not isinstance(content, str):
        content = str(content)

    return content


def get_function_call(
    message: Any | None,
    default_name: str = "function_call",
) -> tuple[str | None, str | None]:
    """Get function call details from message"""
    func_call = get(message, default_name)
    return (
        (get(func_call, "arguments"), get(func_call, "name"))
        if func_call
        else (None, None)
    )


def get_tool_call_from_choice_message(
    message: CompletionChoiceMessage | None,
) -> list[dict]:
    """Get tools calls from message if available"""
    tool_calls = get(message, "tool_calls", [])
    return tool_calls if isinstance(tool_calls, list) else []


def get_tool_call(
    tool_call: Any | None,
) -> tuple[str | None, str | None]:
    """Get tool call details"""
    return (
        (get(tool_call, "id"), get(tool_call, "type")) if (None, None) else (None, None)
    )
