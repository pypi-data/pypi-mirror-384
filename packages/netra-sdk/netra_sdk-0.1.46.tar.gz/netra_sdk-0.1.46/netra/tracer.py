"""Netra OpenTelemetry tracer configuration module.

This module handles the initialization and configuration of OpenTelemetry tracing,
including exporter setup and span processor configuration.
"""

import logging
from typing import Any, Dict

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import DEPLOYMENT_ENVIRONMENT, SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)

from netra.config import Config
from netra.exporters import FilteringSpanExporter

logger = logging.getLogger(__name__)


class Tracer:
    """
    Configures Netra's OpenTelemetry tracer with OTLP exporter (or Console exporter as fallback)
    and appropriate span processor.
    """

    def __init__(self, cfg: Config) -> None:
        """Initialize the Netra tracer with the provided configuration.

        Args:
            cfg: Configuration object with tracer settings
        """
        self.cfg = cfg
        self._setup_tracer()

    def _setup_tracer(self) -> None:
        """Set up the OpenTelemetry tracer with appropriate exporters and processors.

        Creates a resource with service name and custom attributes,
        configures the appropriate exporter (OTLP or Console fallback),
        and sets up either a batch or simple span processor based on configuration.
        """
        # Create Resource with service.name + custom attributes
        resource_attrs: Dict[str, Any] = {
            SERVICE_NAME: self.cfg.app_name,
            DEPLOYMENT_ENVIRONMENT: self.cfg.environment,
        }
        if self.cfg.resource_attributes:
            resource_attrs.update(self.cfg.resource_attributes)
        resource = Resource(attributes=resource_attrs)

        # Build TracerProvider
        provider = TracerProvider(resource=resource)

        # Configure exporter based on configuration
        if not self.cfg.otlp_endpoint:
            logger.warning("OTLP endpoint not provided, falling back to console exporter")
            exporter = ConsoleSpanExporter()
        else:
            exporter = OTLPSpanExporter(
                endpoint=self._format_endpoint(self.cfg.otlp_endpoint),
                headers=self.cfg.headers,
            )
        # Wrap exporter with filtering to support both global and local (baggage-based) rules
        try:
            patterns = getattr(self.cfg, "blocked_spans", None) or []
            exporter = FilteringSpanExporter(exporter, patterns)
            if patterns:
                logger.info("Enabled FilteringSpanExporter with %d global pattern(s)", len(patterns))
            else:
                logger.info("Enabled FilteringSpanExporter with local-only rules")
        except Exception as e:
            logger.warning("Failed to enable FilteringSpanExporter: %s", e)
        # Add span processors: first instrumentation wrapper, then session processor
        from netra.processors import (
            InstrumentationSpanProcessor,
            LocalFilteringSpanProcessor,
            ScrubbingSpanProcessor,
            SessionSpanProcessor,
        )

        # Apply local filtering propagation first so later processors and spans see attributes
        provider.add_span_processor(LocalFilteringSpanProcessor())
        provider.add_span_processor(InstrumentationSpanProcessor())
        provider.add_span_processor(SessionSpanProcessor())

        # Add scrubbing processor if enabled
        if self.cfg.enable_scrubbing:
            provider.add_span_processor(ScrubbingSpanProcessor())  # type: ignore[no-untyped-call]

        # Install appropriate span processor
        if self.cfg.disable_batch:
            provider.add_span_processor(SimpleSpanProcessor(exporter))
        else:
            provider.add_span_processor(BatchSpanProcessor(exporter))

        # Set global tracer provider
        trace.set_tracer_provider(provider)
        logger.info(
            "Netra TracerProvider initialized: endpoint=%s, disable_batch=%s",
            self.cfg.otlp_endpoint,
            self.cfg.disable_batch,
        )

    def _format_endpoint(self, endpoint: str) -> str:
        """Format the OTLP endpoint URL to ensure it ends with '/v1/traces'.

        Args:
            endpoint: Base OTLP endpoint URL

        Returns:
            Properly formatted endpoint URL
        """
        if not endpoint.endswith("/v1/traces"):
            return endpoint.rstrip("/") + "/v1/traces"
        return endpoint
