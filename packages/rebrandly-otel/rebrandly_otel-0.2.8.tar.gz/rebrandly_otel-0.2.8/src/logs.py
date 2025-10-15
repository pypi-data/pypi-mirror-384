# logs.py
"""Logging implementation for Rebrandly OTEL SDK."""
import logging
import sys
from typing import Optional
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import (
    BatchLogRecordProcessor,
    ConsoleLogExporter,
    SimpleLogRecordProcessor
)
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry._logs import set_logger_provider

from .otel_utils import *


class RebrandlyLogger:
    """Wrapper for OpenTelemetry logging with Rebrandly-specific features."""

    # Expose logging levels for convenience (compatible with standard logging)
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    NOTSET = logging.NOTSET

    def __init__(self):
        self._logger: Optional[logging.Logger] = None
        self._provider: Optional[LoggerProvider] = None
        self._setup_logging()

    def _setup_logging(self):
        """Initialize logging with configured exporters."""

        # Create provider with resource
        self._provider = LoggerProvider(resource=create_resource())

        # Add console exporter for local debugging
        if is_otel_debug():
            console_exporter = ConsoleLogExporter()
            self._provider.add_log_record_processor(SimpleLogRecordProcessor(console_exporter))

        # Add OTLP exporter if configured
        otel_endpoint = get_otlp_endpoint()
        if otel_endpoint:
            otlp_exporter = OTLPLogExporter(
                timeout=5,
                endpoint=otel_endpoint
            )
            batch_processor = BatchLogRecordProcessor(otlp_exporter, export_timeout_millis=get_millis_batch_time())
            self._provider.add_log_record_processor(batch_processor)

        set_logger_provider(self._provider)

        # Configure standard logging
        self._configure_standard_logging()

    def _configure_standard_logging(self):
        """Configure standard Python logging with OTEL handler."""
        # Get root logger
        root_logger = logging.getLogger()

        # Only configure basic logging if no handlers exist (not in Lambda)
        if not root_logger.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                stream=sys.stdout
            )

        # Add OTEL handler without removing existing handlers
        otel_handler = LoggingHandler(logger_provider=self._provider)
        otel_handler.setLevel(logging.INFO)

        # Add filter to prevent OpenTelemetry's internal logs from being captured
        # This prevents infinite recursion when OTEL tries to log warnings
        otel_handler.addFilter(lambda record: not record.name.startswith('opentelemetry'))

        root_logger.addHandler(otel_handler)

        # Create service-specific logger
        self._logger = logging.getLogger(get_service_name())


    @property
    def logger(self) -> logging.Logger:
        """Get the standard Python logger."""
        if not self._logger:
            self._logger = logging.getLogger(get_service_name())
        return self._logger

    def getLogger(self) -> logging.Logger:
        """
        Get the internal logger instance.
        Alias for the logger property for consistency with standard logging API.
        """
        return self.logger

    def setLevel(self, level: int):
        """
        Set the logging level for both the internal logger and OTEL handler.

        Args:
            level: Logging level (e.g., logging.INFO, logging.DEBUG, logging.WARNING)
        """
        # Set level on the service-specific logger using the original unbound method
        # This avoids infinite recursion if the logger's setLevel has been monkey-patched
        if self._logger:
            logging.Logger.setLevel(self._logger, level)

        # Set level on the OTEL handler
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if isinstance(handler, LoggingHandler):
                handler.setLevel(level)

    def force_flush(self, timeout_millis: int = 5000) -> bool:
        """
        Force flush all pending logs.

        Args:
            timeout_millis: Maximum time to wait for flush in milliseconds

        Returns:
            True if flush succeeded, False otherwise
        """
        if not self._provider:
            return True

        try:
            # Force flush the logger provider
            success = self._provider.force_flush(timeout_millis)

            # Also flush Python's logging handlers
            if self._logger:
                for handler in self._logger.handlers:
                    if hasattr(handler, 'flush'):
                        handler.flush()

            return success
        except Exception as e:
            print(f"[Logger] Error during force flush: {e}")
            return False

    def shutdown(self):
        """Shutdown the logger provider."""
        if self._provider:
            try:
                self._provider.shutdown()
                print("[Logger] Shutdown completed")
            except Exception as e:
                print(f"[Logger] Error during shutdown: {e}")
