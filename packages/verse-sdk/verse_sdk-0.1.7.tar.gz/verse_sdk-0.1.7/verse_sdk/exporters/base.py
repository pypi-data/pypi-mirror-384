from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanProcessor


class Exporter(ABC):
    @abstractmethod
    def __init__(self, config: Any):
        raise NotImplementedError("`__init__` is not implemented")

    @abstractmethod
    def create_span_processor(self, resource: Resource) -> SpanProcessor:
        raise NotImplementedError("`create_span_processor` is not implemented")
