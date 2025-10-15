import logging
import os

from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter as HTTPTraceExporter,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from ...utils import create_basic_auth_token, merge
from ...wrappers import ScopeFilterExporter
from ..base import Exporter
from .constants import (
    LANGFUSE_ENDPOINT,
    LANGFUSE_HOST,
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_REGION,
    LANGFUSE_REGION_US,
    LANGFUSE_SECRET_KEY,
    LANGFUSE_URL_EU,
    LANGFUSE_URL_US,
)
from .types import LangfuseConfig


class LangfuseExporter(Exporter):
    config: LangfuseConfig

    def __init__(self, config: LangfuseConfig = None):
        """Initialize the langfuse exporter with merged configurations from environment variables and args."""
        self.config: LangfuseConfig = merge(LangfuseExporter.env(), config)
        self.validate()

    @property
    def endpoint(self) -> str:
        """Get the langfuse HTTP endpoint."""
        host = self.config.get("host")

        if host:
            return host if host.endswith("traces") else f"{host}{LANGFUSE_ENDPOINT}"
        elif self.config.get("region") == LANGFUSE_REGION_US:
            return LANGFUSE_URL_US
        else:
            return LANGFUSE_URL_EU

    def create_span_processor(self, resource: Resource) -> SpanProcessor:
        """Create a span processor for the langfuse exporter w/ scope filtering."""
        http_exporter = HTTPTraceExporter(
            endpoint=self.endpoint,
            headers={
                "authorization": create_basic_auth_token(
                    self.config.get("public_key"),
                    self.config.get("secret_key"),
                )
            },
            timeout=10.0,
        )

        exporter = ScopeFilterExporter(
            http_exporter,
            self.config,
        )

        return BatchSpanProcessor(
            exporter,
        )

    def validate(self) -> None:
        """Validate the langfuse config contains required keys."""
        errors = []

        if self.config.get("public_key") is None:
            errors.append("Langfuse `public_key` must be set")
        if self.config.get("secret_key") is None:
            errors.append("Langfuse `secret_key` must be set")

        if len(errors) > 0:
            logging.error(f"Langfuse validation errors: {', '.join(errors)}")
            raise ValueError("\n".join(errors))

    @staticmethod
    def env() -> LangfuseConfig:
        """Get the langfuse config from environment variables."""
        return LangfuseConfig(
            host=os.environ.get(LANGFUSE_HOST),
            public_key=os.environ.get(LANGFUSE_PUBLIC_KEY),
            region=os.environ.get(LANGFUSE_REGION),
            secret_key=os.environ.get(LANGFUSE_SECRET_KEY),
        )
