import os

from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter as HTTPTraceExporter,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from ..base import Exporter
from .constants import OTEL_HOST
from .types import OtelConfig


class OTLPExporter(Exporter):
    """Generic OTLP exporter for OpenTelemetry-compatible backends and collectors."""

    def __init__(self, config: OtelConfig = None):
        self.config = config or OTLPExporter.env()

    @property
    def endpoint(self) -> str:
        """Get the langfuse HTTP endpoint."""
        host = self.config.get("host")

        if host:
            return host if host.endswith("traces") else f"{host}/v1/traces"
        return ""

    def create_span_processor(self, resource: Resource) -> SpanProcessor:
        exporter = HTTPTraceExporter(self.endpoint)
        return BatchSpanProcessor(exporter)

    def get_name(self) -> str:
        return "otlp"

    @staticmethod
    def env() -> OtelConfig:
        """Get the langfuse config from environment variables."""
        return OtelConfig(
            host=os.environ.get(OTEL_HOST),
        )
