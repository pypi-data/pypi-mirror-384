
import json
import time
import psutil
import functools
from contextlib import contextmanager
from datetime import datetime
from opentelemetry.trace import Status, StatusCode, SpanKind
from typing import Optional, Dict, Any, Callable, TypeVar
from opentelemetry import baggage, propagate, context

from .traces import RebrandlyTracer
from .metrics import RebrandlyMeter
from .logs import RebrandlyLogger
from .otel_utils import extract_event_from


T = TypeVar('T')

class RebrandlyOTEL:
    """Main entry point for Rebrandly's OpenTelemetry instrumentation."""

    _instance: Optional['RebrandlyOTEL'] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._tracer: Optional[RebrandlyTracer] = None
            self._meter: Optional[RebrandlyMeter] = None
            self._logger: Optional[RebrandlyLogger] = None
            self.__class__._initialized = True

    def initialize(self, **kwargs) -> 'RebrandlyOTEL':
        # Force initialization of components
        _ = self.tracer
        _ = self.meter
        _ = self.logger

        return self

    @property
    def tracer(self) -> RebrandlyTracer:
        """Get the tracer instance."""
        if self._tracer is None:
            self._tracer = RebrandlyTracer()
        return self._tracer

    @property
    def meter(self) -> RebrandlyMeter:
        """Get the meter instance."""
        if self._meter is None:
            self._meter = RebrandlyMeter()
        return self._meter

    @property
    def logger(self) -> RebrandlyLogger:
        """Get the logger instance."""
        if self._logger is None:
            self._logger = RebrandlyLogger()
        return self._logger

    # Convenience methods for common operations

    @contextmanager
    def span(self,
             name: str,
             attributes: Optional[Dict[str, Any]] = None,
             kind: SpanKind = SpanKind.INTERNAL,
             message=None):
        """Create a span using context manager."""
        with self.tracer.start_span(name=name, attributes=attributes, kind=kind) as span:
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    def trace_decorator(self,
                        name: Optional[str] = None,
                        attributes: Optional[Dict[str, Any]] = None,
                        kind: SpanKind = SpanKind.INTERNAL) -> Callable[[T], T]:
        """Decorator for tracing functions."""
        def decorator(func: T) -> T:
            span_name = name or f"{func.__module__}.{func.__name__}"

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with self.span(span_name, attributes=attributes, kind=kind):
                    return func(*args, **kwargs)

            return wrapper
        return decorator

    def lambda_handler(self,
                       name: Optional[str] = None,
                       attributes: Optional[Dict[str, Any]] = None,
                       kind: SpanKind = SpanKind.SERVER,
                       auto_flush: bool = True,
                       skip_aws_link: bool = False):
        """
        Decorator specifically for Lambda handlers with automatic flushing.
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(event=None, lambda_context=None):
                # Determine span name
                span_name = name or f"lambda.{func.__name__}"
                start_time = datetime.now()

                # Build span attributes
                span_attributes = attributes or {}
                span_attributes['faas.trigger'] = self._detect_lambda_trigger(event)

                # Add Lambda-specific attributes if context is available
                if lambda_context is not None:
                    span_attributes.update({
                        "faas.execution": getattr(lambda_context, 'aws_request_id', 'unknown'),
                        "faas.id": getattr(lambda_context, 'function_arn', 'unknown'),
                        "faas.name": getattr(lambda_context, 'function_name', 'unknown'),
                        "faas.version": getattr(lambda_context, 'function_version', 'unknown')
                    })

                # Handle context extraction from AWS events
                token = None

                if not skip_aws_link and event and isinstance(event, dict) and 'Records' in event:
                    first_record = event['Records'][0] if event['Records'] else None
                    if first_record:
                        carrier = {}

                        # Extract from SQS
                        if 'MessageAttributes' in first_record:
                            for key, value in first_record['MessageAttributes'].items():
                                if isinstance(value, dict) and 'StringValue' in value:
                                    carrier[key] = value['StringValue']
                        if ('messageAttributes' in first_record and 'traceparent' in first_record['messageAttributes']
                                and 'stringValue' in first_record['messageAttributes']['traceparent']):
                            carrier['traceparent'] = first_record['messageAttributes']['traceparent']['stringValue']

                        # Extract from SNS
                        elif 'Sns' in first_record and 'MessageAttributes' in first_record['Sns']:
                            for key, value in first_record['Sns']['MessageAttributes'].items():
                                if isinstance(value, dict):
                                    if 'Value' in value:
                                        carrier[key] = value['Value']
                                    elif 'StringValue' in value:
                                        carrier[key] = value['StringValue']

                        # Attach extracted context
                        if carrier:
                            from opentelemetry import propagate, context as otel_context
                            extracted_context = propagate.extract(carrier)
                            token = otel_context.attach(extracted_context)

                result = None
                span = None
                try:

                    # Create and execute within span
                    with self.tracer.start_span(
                            name=span_name,
                            attributes=span_attributes,
                            kind=kind
                    ) as span:
                        # Add invocation start event with standardized attributes
                        start_event_attrs = {
                            'event.type': type(event).__name__ if event else 'None'
                        }

                        # Add records count if present
                        if event and isinstance(event, dict) and 'Records' in event:
                            start_event_attrs['event.records'] = f"{len(event['Records'])}"

                        span.add_event("lambda.invocation.start", start_event_attrs)

                        # Execute handler
                        result = func(event, lambda_context)

                        # Process result with standardized attributes
                        success = True
                        complete_event_attrs = {}

                        if isinstance(result, dict) and 'statusCode' in result:
                            span.set_attribute("http.status_code", result['statusCode'])
                            complete_event_attrs['status_code'] = result['statusCode']

                            # Set span status based on HTTP status code
                            if result['statusCode'] >= 400:
                                success = False
                                span.set_status(Status(StatusCode.ERROR, f"HTTP {result['statusCode']}"))
                            else:
                                span.set_status(Status(StatusCode.OK))
                        else:
                            span.set_status(Status(StatusCode.OK))

                        # Add completion event with success indicator
                        complete_event_attrs['success'] = success
                        span.add_event("lambda.invocation.complete", complete_event_attrs)

                    return result

                except Exception as e:

                    # Add failed completion event with error attribute (only if span exists)
                    if span is not None and hasattr(span, 'is_recording') and span.is_recording():
                        span.add_event("lambda.invocation.complete", {
                            'success': False,
                            'error': type(e).__name__
                        })

                        # Record the exception in the span
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))

                    # Log error
                    print(f"Lambda execution failed: {e}")
                    raise

                finally:
                    # Always detach context if we attached it
                    if token is not None:
                        from opentelemetry import context as otel_context
                        otel_context.detach(token)

                    # Force flush if enabled
                    if auto_flush:
                        print(f"[Rebrandly OTEL] Lambda '{span_name}', flushing...")
                        flush_success = self.force_flush(timeout_millis=1000)
                        if not flush_success:
                            print("[Rebrandly OTEL] Force flush may not have completed fully")

            return wrapper
        return decorator

    def aws_message_handler(self,
                            name: Optional[str] = None,
                            attributes: Optional[Dict[str, Any]] = None,
                            kind: SpanKind = SpanKind.CONSUMER,
                            auto_flush: bool = True):
        """
        Decorator for AWS message handlers (SQS/SNS record processing).
        Requires a record object parameter to the function.
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(record=None, *args, **kwargs):
                # Determine span name
                span_name = name or f"message.{func.__name__}"
                start_func = datetime.now()

                # Build span attributes
                span_attributes = attributes or {}
                span_attributes['messaging.operation'] = 'process'

                result = None
                try:
                    # Create span and execute function
                    span_function = self.span
                    if record is not None and (('MessageAttributes' in record or 'messageAttributes' in record) or ('Sns' in record and 'MessageAttributes' in record['Sns'])):
                        span_function = self.aws_message_span
                        evt = extract_event_from(record)
                        if evt:
                            span_attributes['event.type'] = evt

                    with span_function(span_name, message=record, attributes=span_attributes, kind=kind) as span_context:
                        # Add processing start event with standardized name
                        span_context.add_event("message.processing.start", {})

                        # Execute the actual handler function
                        result = func(record, *args, **kwargs)

                        # Process result
                        success = True
                        complete_event_attrs = {}

                        if result and isinstance(result, dict):
                            if 'statusCode' in result:
                                span_context.set_attribute("http.status_code", result['statusCode'])

                                # Set span status based on status code
                                if result['statusCode'] >= 400:
                                    success = False
                                    span_context.set_status(
                                        Status(StatusCode.ERROR, f"Handler returned {result['statusCode']}")
                                    )
                                else:
                                    span_context.set_status(Status(StatusCode.OK))

                            # Add custom result attributes if present
                            if 'processed' in result:
                                complete_event_attrs['processed'] = result['processed']
                                span_context.set_attribute("message.processed", result['processed'])
                            if 'skipped' in result:
                                complete_event_attrs['skipped'] = result['skipped']
                                span_context.set_attribute("message.skipped", result['skipped'])
                        else:
                            span_context.set_status(Status(StatusCode.OK))

                        # Add completion event with standardized name
                        complete_event_attrs['success'] = success
                        span_context.add_event("message.processing.complete", complete_event_attrs)

                        return result

                except Exception as e:
                    # Record the exception in the span
                    if 'span_context' in locals():
                        span_context.record_exception(e)
                        span_context.set_status(Status(StatusCode.ERROR, str(e)))

                        # Add failed processing event
                        span_context.add_event("message.processing.complete", {
                            'success': False,
                            'error': type(e).__name__
                        })

                    # Re-raise the exception
                    raise

                finally:
                    if auto_flush:
                        self.force_flush(start_datetime=start_func)

            return wrapper
        return decorator

    def force_flush(self, start_datetime: datetime=None, timeout_millis: int = 1000) -> bool:
        """
        Force flush all telemetry data.
        This is CRITICAL for Lambda functions to ensure data is sent before function freezes.

        Args:
            start_datetime: Optional start time for system metrics capture
            timeout_millis: Maximum time to wait for flush in milliseconds

        Returns:
            True if all flushes succeeded, False otherwise
        """
        success = True

        if start_datetime is not None:
            end_func = datetime.now()
            cpu_percent = psutil.cpu_percent(interval=0.1)  # Shorter interval for Lambda
            memory = psutil.virtual_memory()

            # Record metrics using standardized names (with safety checks)
            try:
                if self.meter.GlobalMetrics.memory_usage_bytes:
                    self.meter.GlobalMetrics.memory_usage_bytes.set(memory.used)
                if self.meter.GlobalMetrics.cpu_usage_percentage:
                    self.meter.GlobalMetrics.cpu_usage_percentage.set(cpu_percent)
            except Exception as e:
                print(f"[Rebrandly OTEL] Warning: Could not record system metrics: {e}")

            print(f"Function Memory usage: {memory.percent}%, CPU usage: {cpu_percent}%")

        try:
            # Flush traces
            if self._tracer:
                if not self._tracer.force_flush(timeout_millis):
                    success = False

            # Flush metrics
            if self._meter:
                if not self._meter.force_flush(timeout_millis):
                    success = False

            # Flush logs
            if self._logger:
                if not self._logger.force_flush(timeout_millis):
                    success = False

            # Add a small delay to ensure network operations complete
            time.sleep(0.1)

        except Exception as e:
            print(f"[Rebrandly OTEL] Error during force flush: {e}")
            success = False

        return success

    def shutdown(self):
        """
        Shutdown all OTEL components gracefully.
        Call this at the end of your Lambda handler if you want to ensure clean shutdown.
        """
        try:
            if self._tracer:
                self._tracer.shutdown()
            if self._meter:
                self._meter.shutdown()
            if self._logger:
                self._logger.shutdown()
        except Exception as e:
            print(f"[Rebrandly OTEL] Error during shutdown: {e}")

    def _detect_lambda_trigger(self, event: Any) -> str:
        """Detect Lambda trigger type from event."""
        if not event or not isinstance(event, dict):
            return 'direct'

        if 'Records' in event:
            first_record = event['Records'][0] if event['Records'] else None
            if first_record:
                event_source = first_record.get('eventSource', '')
                if event_source == 'aws:sqs':
                    return 'sqs'
                elif event_source == 'aws:sns':
                    return 'sns'
                elif event_source == 'aws:s3':
                    return 's3'
                elif event_source == 'aws:kinesis':
                    return 'kinesis'
                elif event_source == 'aws:dynamodb':
                    return 'dynamodb'

        if 'httpMethod' in event:
            return 'api_gateway'
        if 'requestContext' in event and 'http' in event.get('requestContext', {}):
            return 'api_gateway_v2'
        if event.get('source') == 'aws.events':
            return 'eventbridge'
        if event.get('source') == 'aws.scheduler':
            return 'eventbridge_scheduler'
        if 'jobName' in event:
            return 'batch'

        return 'unknown'

    def set_baggage(self, key: str, value: str):
        """Set baggage item."""
        return baggage.set_baggage(key, value)

    def get_baggage(self, key: str) -> Optional[str]:
        """Get baggage item."""
        return baggage.get_baggage(key)

    def inject_context(self, carrier: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Inject trace context into headers for outbound requests."""
        if carrier is None:
            carrier = {}
        propagate.inject(carrier)
        return carrier

    def extract_context(self, carrier: Dict[str, Any]) -> context.Context:
        """Extract trace context from incoming request headers."""
        return propagate.extract(carrier)

    def attach_context(self, carrier: Dict[str, Any]) -> object:
        """Extract and attach context, returning a token for cleanup."""
        ctx = self.extract_context(carrier)
        return context.attach(ctx)

    def detach_context(self, token):
        """Detach a previously attached context."""
        context.detach(token)

    @contextmanager
    def aws_message_span(self,
                         name: str,
                         message: Dict[str, Any]=None,
                         attributes: Optional[Dict[str, Any]] = None,
                         kind: SpanKind = SpanKind.CONSUMER):
        """Create span from AWS message - properly handling trace context."""

        from opentelemetry import trace, context as otel_context

        combined_attributes = attributes or {}
        combined_attributes['messaging.operation'] = 'process'

        # Extract message attributes for linking/attributes
        if message and isinstance(message, dict):
            # Add message-specific attributes
            if 'Sns' in message:
                sns_msg = message['Sns']
                if 'MessageId' in sns_msg:
                    combined_attributes['messaging.message_id'] = sns_msg['MessageId']
                if 'Subject' in sns_msg:
                    combined_attributes['messaging.sns.subject'] = sns_msg['Subject']
                if 'TopicArn' in sns_msg:
                    combined_attributes['messaging.destination'] = sns_msg['TopicArn']
                combined_attributes['messaging.system'] = 'sns'

            elif 'messageId' in message:
                # SQS message
                combined_attributes['messaging.message_id'] = message['messageId']
                if 'eventSource' in message:
                    combined_attributes['messaging.system'] = message['eventSource']


            if 'awsRegion' in message:
                combined_attributes['cloud.region'] = message['awsRegion']

            evt = extract_event_from(message)
            if evt:
                combined_attributes['event.type'] = evt


        # Use the tracer's start_span method directly to ensure it works
        # This creates a child span of whatever is currently active
        with self.tracer.start_span(
                name=name,
                attributes=combined_attributes,
                kind=kind
        ) as span:
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise


# Create Singleton instance
otel = RebrandlyOTEL()

# Export commonly used functions
span = otel.span
aws_message_span = otel.aws_message_span
traces = otel.trace_decorator
tracer = otel.tracer
meter = otel.meter
logger = otel.logger.logger
lambda_handler = otel.lambda_handler
aws_message_handler = otel.aws_message_handler
initialize = otel.initialize
inject_context = otel.inject_context
extract_context = otel.extract_context
attach_context = otel.attach_context
detach_context = otel.detach_context
force_flush = otel.force_flush
shutdown = otel.shutdown

# Attach logging levels to logger for convenience
# This allows: from rebrandly_otel import logger; logger.setLevel(logger.INFO)
import logging as _logging
logger.DEBUG = _logging.DEBUG
logger.INFO = _logging.INFO
logger.WARNING = _logging.WARNING
logger.ERROR = _logging.ERROR
logger.CRITICAL = _logging.CRITICAL
logger.NOTSET = _logging.NOTSET
logger.setLevel = otel.logger.setLevel
logger.getLogger = otel.logger.getLogger
