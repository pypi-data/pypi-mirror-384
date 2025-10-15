from __future__ import annotations

import contextlib
import gc
import logging
from typing import Any

import httpcore
import httpx
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import ProxyTracerProvider

from .decorators import with_decorators
from .exporters import (
    Exporter,
    ExportersRegistry,
)
from .integrations import apply_integrations
from .processors import AttributeProcessor
from .sdk import VerseSDK


class VerseSDKBuilder:
    exporters = ExportersRegistry()

    _initialized: bool = False
    _sdk: VerseSDK | None
    _tracer: trace.Tracer | None
    _vendor: str | None = None

    def __getattr__(self, name: str) -> Any:
        """Dynamically access methods from the SDK."""
        if not self._sdk:
            raise ValueError("SDK not initialized")

        return getattr(self._sdk, name)

    def init(
        self,
        app_name: str = "verse_sdk_observability",
        environment: str | None = "development",
        exporters: list[Exporter] | None = None,
        vendor: str | None = None,
        version: str | None = "1.0.0",
    ) -> VerseSDK:
        """
        Lazily initialize the observability client.

        Args:
            app_name: Service name for tracing
            exporters: Exporter name(s) or None for auto-detection
            environment: Deployment environment (e.g., "production", "staging")
            version: Service version

        Returns:
            VerseSDK w/ decorations
        """
        try:
            if self._initialized:
                return self._sdk

            resource = Resource.create(
                {
                    "deployment.environment": environment,
                    "service.name": app_name,
                    "service.version": version,
                }
            )

            provider = TracerProvider(resource=resource)

            provider.add_span_processor(AttributeProcessor())

            for exporter in exporters:
                try:
                    provider.add_span_processor(
                        exporter.create_span_processor(resource)
                    )
                    logging.info(
                        "Added span processor `%s`",
                        exporter.__class__.__name__,
                    )
                except Exception as e:
                    logging.warning(
                        "Error adding span processor `%s`",
                        exporter.__class__.__name__,
                        exc_info=e,
                    )

            trace.set_tracer_provider(provider)

            self._tracer = trace.get_tracer(app_name)
            self._sdk = VerseSDK(self._tracer)
            self._sdk = with_decorators(self._sdk)
            self._vendor = vendor
            self._initialized = True

            apply_integrations(self._sdk, vendor)
            logging.info("🚀 VerseSDK initialized")

            return self._sdk
        except Exception as e:
            logging.error("Error initializing SDK", exc_info=e)
            raise e

    def flush(self, timeout_ms: int = 30000) -> None:
        """
        Flush all pending traces to exporters.

        Args:
            timeout_ms: Maximum time to wait for flush in milliseconds
        """
        try:
            if not self._initialized:
                return

            provider = trace.get_tracer_provider()
            if isinstance(provider, ProxyTracerProvider):
                provider.force_flush(timeout_millis=timeout_ms)
        except Exception as e:
            logging.warning("Error flushing traces", exc_info=e)

    def shutdown(self, timeout_ms: int = 30000) -> None:
        """
        Shutdown the SDK and stop all background threads.
        This should be called during application teardown to ensure clean shutdown.

        Args:
            timeout_ms: Maximum time to wait for shutdown in milliseconds
        """
        if not self._initialized:
            return

        try:
            self._cleanup_vendor_resources()
            self.flush(timeout_ms)
            self._cleanup_http_resources()
            self._shutdown_tracer_provider(timeout_ms)
            self._reset_sdk_state()
            logging.info("VerseSDK shutdown complete")
        except Exception as e:
            logging.warning("Error shutting down SDK", exc_info=e)

    def _cleanup_vendor_resources(self) -> None:
        """Clean up vendor-specific resources."""
        if self._vendor == "litellm":
            try:
                from .integrations.litellm import cleanup_litellm

                cleanup_litellm()
                logging.info("Cleaned up litellm HTTP clients")
            except Exception as e:
                logging.warning("Error cleaning up litellm", exc_info=e)

    def _cleanup_http_resources(self) -> None:
        """Clean up HTTP resources to prevent memory leaks."""
        provider = trace.get_tracer_provider()
        if not isinstance(provider, TracerProvider):
            return

        try:
            self._close_exporter_clients(provider)
            self._force_close_http_objects()
        except Exception as e:
            logging.debug("Error during HTTP cleanup", exc_info=e)

    def _close_exporter_clients(self, provider: TracerProvider) -> None:
        """Close HTTP clients in span processors."""
        for processor in provider._active_span_processor._span_processors:
            try:
                if not hasattr(processor, "span_exporter"):
                    continue

                exporter = processor.span_exporter
                if hasattr(exporter, "_exporter"):
                    exporter = exporter._exporter

                if hasattr(exporter, "_session") and exporter._session:
                    exporter._session.close()

                if hasattr(exporter, "httpx_client") and exporter.httpx_client:
                    with contextlib.suppress(Exception):
                        if not exporter.httpx_client.is_closed:
                            exporter.httpx_client.close()
            except Exception as e:
                logging.debug("Error closing exporter clients", exc_info=e)

    def _force_close_http_objects(self) -> None:
        """Force close HTTP objects to prevent memory leaks during shutdown."""
        try:
            self._close_httpx_responses()
            gc.collect()
            self._close_httpcore_objects()
            self._close_httpx_clients()
        except Exception:
            pass

    def _close_httpx_responses(self) -> None:
        """Close all active httpx.Response objects."""
        responses_to_close = [
            object for object in gc.get_objects() if isinstance(object, httpx.Response)
        ]

        for response in responses_to_close:
            try:
                if not response.is_closed:
                    response.close()
            except Exception:
                pass

    def _close_httpcore_objects(self) -> None:
        """Close httpcore HTTP11 connections and connection pools."""
        for object in gc.get_objects():
            try:
                if (
                    hasattr(httpcore, "HTTP11Connection")
                    and isinstance(object, httpcore.HTTP11Connection)
                    and hasattr(object, "close")
                ) or isinstance(object, httpcore.ConnectionPool):
                    object.close()
            except Exception:
                pass

    def _close_httpx_clients(self) -> None:
        """Close all remaining httpx.Client instances."""
        for object in gc.get_objects():
            try:
                if isinstance(object, httpx.Client) and not object.is_closed:
                    if hasattr(object, "_transport") and object._transport:
                        with contextlib.suppress(Exception):
                            object._transport.close()

                    object.close()
                    logging.debug("Closed httpx.Client during shutdown")
            except Exception:
                pass

    def _shutdown_tracer_provider(self, timeout_ms: int) -> None:
        """Shutdown the tracer provider."""
        provider = trace.get_tracer_provider()
        if hasattr(provider, "shutdown") and callable(provider.shutdown):
            provider.shutdown()

    def _reset_sdk_state(self) -> None:
        """Reset SDK internal state."""
        self._initialized = False
        self._sdk = None
        self._tracer = None
        self._vendor = None
