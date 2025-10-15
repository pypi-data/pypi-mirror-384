from __future__ import annotations

import logging
from typing import Any

from ..utils import get
from .span import SpanContext
from .types import (
    CompletionChoice,
    ContextType,
    GenerationMessage,
    GenerationUsage,
    ObservationType,
)
from .utils import (
    get_choice_message,
    get_content_from_choice_message,
    get_content_from_generation_message,
    get_function_call,
    get_tool_call,
    get_tool_call_from_choice_message,
)


class GenerationContext(SpanContext):
    """Context for generation spans (LLM operations)."""

    observation_type: ObservationType = "observation"
    type: ContextType = "generation"

    def __init__(self, *args, **kwargs):
        """Initialize the generation context with a special attribute."""
        super().__init__(*args, **kwargs)
        self.operation(self.observation_type)

    def completions(
        self,
        completion_choices: list[CompletionChoice],
    ) -> GenerationContext:
        """Recursively trace completion choices w/ support for tool calling."""
        try:
            for choice_index, choice in enumerate(completion_choices):
                if choice is None:
                    continue

                message = get_choice_message(choice)
                text = get(choice, "text", "")

                if message:
                    func_args, func_name = get_function_call(message)

                    attrs = {
                        f"gen_ai.completion.{choice_index}.content": str(
                            get_content_from_choice_message(message)
                        ),
                        f"gen_ai.completion.{choice_index}.function_call.name": func_name,
                        f"gen_ai.completion.{choice_index}.function_call.arguments": func_args,
                        f"gen_ai.completion.{choice_index}.role": get(
                            message, "role", "assistant"
                        ),
                    }

                    for tool_index, tool_call in enumerate(
                        get_tool_call_from_choice_message(message)
                    ):
                        tool_id, tool_type = get_tool_call(tool_call)
                        tool_func_args, tool_func_name = get_function_call(
                            tool_call, "function"
                        )

                        attrs.update(
                            {
                                f"gen_ai.completion.{choice_index}.tool_call.{tool_index}.id": tool_id,
                                f"gen_ai.completion.{choice_index}.tool_call.{tool_index}.type": tool_type,
                                f"gen_ai.completion.{choice_index}.tool_call.{tool_index}.function.name": tool_func_name,
                                f"gen_ai.completion.{choice_index}.tool_call.{tool_index}.function.arguments": tool_func_args,
                            }
                        )

                    self.set_attributes(**attrs)
                else:
                    self.set_attributes(
                        **{
                            f"gen_ai.completion.{choice_index}.role": "assistant",
                            f"gen_ai.completion.{choice_index}.content": text or "",
                        }
                    )

            return self
        except Exception as e:
            logging.warning("Completions could not be traced", exc_info=e)
            return self

    def input(self, content: Any) -> GenerationContext:
        """Set the input for the generation."""
        self._span.set_attribute("gen_ai.prompt", str(content))
        return self

    def messages(self, messages: list[GenerationMessage]) -> GenerationContext:
        """Recursively trace messages w/ support for tool calling."""
        try:
            for message_index, message in enumerate(messages):
                if not message:
                    continue

                func_args, func_name = get_function_call(message)
                attrs = {
                    f"gen_ai.prompt.{message_index}.id": get(message, "id", None),
                    f"gen_ai.prompt.{message_index}.role": get(message, "role", "user"),
                    f"gen_ai.prompt.{message_index}.content": get_content_from_generation_message(
                        message
                    ),
                    f"gen_ai.prompt.{message_index}.function_call.name": func_name,
                    f"gen_ai.prompt.{message_index}.function_call.arguments": func_args,
                    f"gen_ai.prompt.{message_index}.name": get(message, "name", None),
                }

                for tool_index, tool_call in enumerate(
                    # note: same structure as completion choices
                    get_tool_call_from_choice_message(message)
                ):
                    tool_id, tool_type = get_tool_call(tool_call)
                    tool_func_args, tool_func_name = get_function_call(
                        tool_call, "function"
                    )

                    attrs.update(
                        {
                            f"gen_ai.prompt.{message_index}.tool_call.{tool_index}.id": tool_id,
                            f"gen_ai.prompt.{message_index}.tool_call.{tool_index}.type": tool_type,
                            f"gen_ai.prompt.{message_index}.tool_call.{tool_index}.function.name": tool_func_name,
                            f"gen_ai.prompt.{message_index}.tool_call.{tool_index}.function.arguments": tool_func_args,
                        }
                    )

                self.set_attributes(**attrs)

            return self
        except Exception as e:
            logging.warning("Messages could not be traced", exc_info=e)
            return self

    def model(self, model_name: str) -> GenerationContext:
        """Set the desired model for generation."""
        self._span.set_attribute("gen_ai.request.model", model_name)
        return self

    def model_used(self, model_used: str) -> GenerationContext:
        """Set the actual model used for generation."""
        self._span.set_attribute("gen_ai.response.model", model_used)
        return self

    def reason(self, reason: str) -> GenerationContext:
        """Set the reason for the generation."""
        self._span.set_attribute("gen_ai.response.finish_reasons", [reason])
        return self

    def output(self, content: Any) -> GenerationContext:
        """Set the output of the generation."""
        self._span.set_attribute("gen_ai.response.completion", str(content))
        return self

    def usage(
        self,
        usage: GenerationUsage,
    ) -> GenerationContext:
        """Set token usage metrics."""
        self.set_attributes(
            prefix="gen_ai.usage",
            **usage,
        )

        return self

    def vendor(self, vendor: str) -> GenerationContext:
        """Set the vendor for the generation."""
        self._span.set_attribute("gen_ai.request.vendor", vendor)
        return self
