import logging
from typing import Any

from ...contexts import CompletionChoice, GenerationUsage


def calculate_total_tokens(
    prompt_tokens: int | None, completion_tokens: int | None
) -> int | None:
    """Calculate the total tokens."""
    if prompt_tokens is not None or completion_tokens is not None:
        return (prompt_tokens or 0) + (completion_tokens or 0)
    return None


def get_completition_choices(data: Any) -> list[CompletionChoice]:
    """Get the completion choices from the response."""

    choices = []
    if hasattr(data, "choices"):
        choices = data.choices
    elif isinstance(data, dict) and "choices" in data:
        choices = data["choices"]

    return choices if len(choices) > 0 else []


def get_finish_reason(response_obj: Any) -> str | None:
    """Trace response metadata like model and ID."""
    if getattr(response_obj, "choices", None):
        fr = getattr(response_obj.choices[0], "finish_reason", None)
        if fr:
            return fr

    return None


def get_operation_type(messages: list, kwargs: dict) -> str:
    try:
        """Determine the operation type based on request parameters."""
        if kwargs.get("litellm_params", {}).get("api_base", "").endswith("/embeddings"):
            return "embedding"

        return "chat" if messages else "completion"
    except Exception as e:
        logging.warning("Error determining operation type from Litellm", exc_info=e)
        return "completion"


def get_stream_text(response_obj: Any) -> str:
    """Get the text from the response."""
    chunk = getattr(response_obj, "choices", None)
    if not chunk:
        return ""

    c = chunk[0]
    return (
        getattr(getattr(c, "delta", None), "content", None)
        or getattr(c, "text", None)
        or ""
    )


def get_usage(kwargs: dict) -> GenerationUsage:
    """Get the usage for the request."""
    try:
        optional = kwargs.get("optional_params", {})
        return {
            "max_tokens": kwargs.get("max_tokens", optional.get("max_tokens")),
            "temperature": kwargs.get("temperature", optional.get("temperature")),
            "top_p": kwargs.get("top_p", optional.get("top_p")),
            "stream": kwargs.get("stream", optional.get("stream")),
        }
    except Exception as e:
        logging.warning("Error getting usage from Litellm", exc_info=e)
        return {}


def get_usage_from_response(response_obj: Any) -> GenerationUsage:
    """Get the usage from the response."""
    try:
        usage = getattr(response_obj, "usage", None)

        usage_output = {
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
        }

        usage_output["total_tokens"] = getattr(
            usage,
            "total_tokens",
            calculate_total_tokens(
                usage_output["prompt_tokens"],
                usage_output["completion_tokens"],
            ),
        )

        return usage_output

    except Exception as e:
        logging.warning("Error getting usage from response", exc_info=e)
        return {}
