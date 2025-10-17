import atexit
import socket
import uuid
from typing import TYPE_CHECKING, Optional

from platzky.config import TelemetryConfig

if TYPE_CHECKING:
    from opentelemetry.trace import Tracer

    from platzky.engine import Engine

# Error messages
_MISSING_EXPORTERS_MSG = (
    "Telemetry is enabled but no exporters are configured. "
    "Set endpoint or console_export=True to export traces."
)


def setup_telemetry(app: "Engine", telemetry_config: TelemetryConfig) -> Optional["Tracer"]:
    """Setup OpenTelemetry tracing for Flask application.

    Configures and initializes OpenTelemetry tracing with OTLP and/or console exporters.
    Automatically instruments Flask to capture HTTP requests and trace information.
    Optionally instruments logging to add trace context to log records.

    Args:
        app: Engine instance (Flask-based application)
        telemetry_config: Telemetry configuration specifying endpoint and export options

    Returns:
        OpenTelemetry tracer instance if enabled, None otherwise

    Raises:
        ImportError: If OpenTelemetry packages are not installed when telemetry is enabled
        ValueError: If telemetry is enabled but no exporters are configured
    """
    if not telemetry_config.enabled:
        return None

    # Reject telemetry enabled without exporters (creates overhead without benefit)
    if not telemetry_config.endpoint and not telemetry_config.console_export:
        raise ValueError(_MISSING_EXPORTERS_MSG)

    # If already instrumented, return tracer without rebuilding provider/exporters
    if app.telemetry_instrumented:
        from opentelemetry import trace

        return trace.get_tracer(__name__)

    # Import OpenTelemetry modules (will raise ImportError if not installed)
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.flask import FlaskInstrumentor
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
        SimpleSpanProcessor,
    )
    from opentelemetry.semconv.resource import ResourceAttributes

    # Build resource attributes
    service_name = app.config.get("APP_NAME", "platzky")
    resource_attrs: dict[str, str] = {
        ResourceAttributes.SERVICE_NAME: service_name,
    }

    # Auto-detect service version from package metadata
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as get_version

    try:
        resource_attrs[ResourceAttributes.SERVICE_VERSION] = get_version("platzky")
    except PackageNotFoundError:
        pass  # Version not available

    if telemetry_config.deployment_environment:
        resource_attrs[ResourceAttributes.DEPLOYMENT_ENVIRONMENT] = (
            telemetry_config.deployment_environment
        )

    # Add instance ID (user-provided or auto-generated)
    if telemetry_config.service_instance_id:
        resource_attrs[ResourceAttributes.SERVICE_INSTANCE_ID] = (
            telemetry_config.service_instance_id
        )
    else:
        # Generate unique instance ID: hostname + short UUID
        hostname = socket.gethostname()
        instance_uuid = str(uuid.uuid4())[:8]
        resource_attrs[ResourceAttributes.SERVICE_INSTANCE_ID] = f"{hostname}-{instance_uuid}"

    resource = Resource.create(resource_attrs)
    provider = TracerProvider(resource=resource)

    # Configure exporter based on endpoint
    if telemetry_config.endpoint:
        exporter = OTLPSpanExporter(
            endpoint=telemetry_config.endpoint, timeout=telemetry_config.timeout
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))

    # Optional console export
    if telemetry_config.console_export:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    FlaskInstrumentor().instrument_app(app)

    # Instrument logging to add trace context to log records
    # Note: set_logging_format=False to avoid modifying existing log formats
    # Users can access trace context in their custom formatters via log record attributes
    if telemetry_config.instrument_logging:
        LoggingInstrumentor().instrument(set_logging_format=False)

    app.telemetry_instrumented = True

    # Optionally flush spans after each request (may impact latency)
    if telemetry_config.flush_on_request:

        @app.teardown_appcontext
        def flush_telemetry(_exc: Optional[BaseException] = None) -> None:
            """Flush pending spans after request completion."""
            provider.force_flush(timeout_millis=telemetry_config.flush_timeout_ms)

    # Shutdown provider once at process exit
    atexit.register(provider.shutdown)

    return trace.get_tracer(__name__)
