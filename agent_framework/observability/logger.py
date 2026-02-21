"""
Structured logging and OpenTelemetry tracing setup.

Usage:
    from agent_framework.observability.logger import get_logger
    logger = get_logger(__name__)
    logger.info("agent_run", agent="my-agent", tokens=120)
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Optional

try:
    import structlog

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if sys.stderr.isatty() else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if os.environ.get("AGENT_DEBUG") else logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

    def get_logger(name: str):
        return structlog.get_logger(name)

except ImportError:
    # Fallback to stdlib logging when structlog isn't installed
    def get_logger(name: str):  # type: ignore[misc]
        return logging.getLogger(name)


def setup_telemetry(service_name: str = "ms-ai-agent-framework", endpoint: Optional[str] = None) -> None:
    """
    Configure OpenTelemetry tracing.

    Call this once at application startup.
    If *endpoint* is None we look for OTEL_EXPORTER_OTLP_ENDPOINT in the environment.
    If still not set, telemetry is a no-op.
    """
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)

        otlp_endpoint = endpoint or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        if otlp_endpoint:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))

        trace.set_tracer_provider(provider)
        if otlp_endpoint:
            get_logger(__name__).info("telemetry_configured", service=service_name, endpoint=otlp_endpoint)
    except ImportError:
        pass  # opentelemetry-sdk not installed — skip silently
