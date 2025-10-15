import logging
from functools import wraps
from typing import Any

from .base import Exporter
from .console import ConsoleExporter
from .langfuse import LangfuseExporter
from .langfuse.types import LangfuseConfig
from .otel import OTLPExporter
from .types import ExporterConfig


class ExportersRegistry:
    @staticmethod
    def safe_named_exporter(fn):
        """Create an error boundary around each exporter factory function."""

        @wraps(fn)
        def create_exporter(*args, **kwargs) -> Exporter | None:
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                logging.warning("Error creating exporter `%s`", fn.__name__, exc_info=e)
                return None

        return create_exporter

    @safe_named_exporter
    def console(self, config: ExporterConfig = None) -> ConsoleExporter:
        """Create a console exporter."""
        return ConsoleExporter(config or {})

    @safe_named_exporter
    def langfuse(self, config: LangfuseConfig = None) -> LangfuseExporter:
        """Create a langfuse exporter."""
        return LangfuseExporter(config or {})

    @safe_named_exporter
    def otel(self, config: Any = None) -> OTLPExporter:
        """Create a otel exporter."""
        return OTLPExporter(config or {})


__all__ = [
    "Exporter",
    "ExportersRegistry",
]
