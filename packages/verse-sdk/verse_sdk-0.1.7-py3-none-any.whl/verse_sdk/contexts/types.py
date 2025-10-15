from __future__ import annotations

from typing import Any, Literal, TypedDict

ContextType = Literal["generation", "span", "trace"]
Level = Literal["debug", "error", "fatal", "info", "warning"]
ObservationType = Literal["observation", "trace"]
OperationType = Literal[
    "agent",
    "chain",
    "embedding",
    "evaluator",
    "event",
    "guardrail",
    "retriever",
    "tool",
]


class CompletionChoiceMessage(TypedDict):
    role: str
    content: Any
    function_call: dict | None
    name: str | None
    tool_calls: list[dict] | None


class CompletionChoice(TypedDict):
    message: CompletionChoiceMessage | None
    delta: str | None
    text: str | None


class ContextMetadata(TypedDict):
    pass


class EventMetadata(TypedDict):
    pass


class GenerationMessage(TypedDict):
    role: str
    content: str
    function_call: dict | None
    name: str | None
    tool_calls: list[dict] | None


class GenerationUsage(TypedDict):
    completion_tokens: int | None
    input_tokens: int | None
    max_tokens: int | None
    output_tokens: int | None
    prompt_tokens: int | None
    stream: bool | None
    temperature: float | None
    tool_calls: int | None
    total_tokens: int | None
    top_p: float | None


class Score(TypedDict):
    name: str
    value: float | str
    comment: str | None
