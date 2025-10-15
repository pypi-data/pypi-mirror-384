# Rebrandly OpenTelemetry SDK for Python

A comprehensive OpenTelemetry instrumentation SDK designed specifically for Rebrandly services, with built-in support for AWS Lambda functions and message processing.

## Overview

The Rebrandly OpenTelemetry SDK provides a unified interface for distributed tracing, metrics collection, and structured logging across Python applications. It offers automatic instrumentation for AWS Lambda functions, simplified span management, and seamless integration with OTLP-compatible backends.

## Installation

```bash
pip install rebrandly-otel
```

### Dependencies

- `opentelemetry-api`
- `opentelemetry-sdk`
- `opentelemetry-exporter-otlp-proto-grpc`
- `opentelemetry-semantic-conventions`
- `psutil` (for system metrics)

## Configuration

The SDK is configured through environment variables:

| Variable                           | Description | Default |
|------------------------------------|-------------|---------|
| `OTEL_SERVICE_NAME`                | Service identifier | `default-service-python` |
| `OTEL_SERVICE_VERSION`             | Service version | `1.0.0` |
| `OTEL_EXPORTER_OTLP_ENDPOINT`      | OTLP collector endpoint | `None` |
| `OTEL_DEBUG`                       | Enable console debugging | `false` |
| `BATCH_EXPORT_TIME_MILLIS`         | Batch export interval | `100` |
| `ENV` or `ENVIRONMENT` or `NODE_ENV`       | Deployment environment | `local` |

## Core Components

### RebrandlyOTEL Class

The main entry point for all telemetry operations. Implements a singleton pattern to ensure consistent instrumentation across your application.

#### Properties

- **`tracer`**: Returns the `RebrandlyTracer` instance for distributed tracing
- **`meter`**: Returns the `RebrandlyMeter` instance for metrics collection
- **`logger`**: Returns the configured Python logger with OpenTelemetry integration

#### Initialization

The SDK auto-initializes as soon as you embed it.

### Key Methods

#### `span(name, attributes=None, kind=SpanKind.INTERNAL, message=None)`

Context manager for creating traced spans with automatic error handling and status management.

#### `lambda_handler(name=None, attributes=None, kind=SpanKind.CONSUMER, auto_flush=True, skip_aws_link=True)`

Decorator for AWS Lambda functions with automatic instrumentation, metrics collection, and telemetry flushing.

#### `aws_message_handler(name=None, attributes=None, kind=SpanKind.CONSUMER, auto_flush=True)`

Decorator for processing individual AWS messages (SQS/SNS) with context propagation.

#### `aws_message_span(name, message=None, attributes=None, kind=SpanKind.CONSUMER)`

Context manager for creating spans from AWS messages with automatic context extraction.

#### `force_flush(start_datetime=None, timeout_millis=1000)`

Forces all pending telemetry data to be exported. Critical for serverless environments.

#### `shutdown()`

Gracefully shuts down all OpenTelemetry components.

## Built-in Metrics

The SDK automatically registers and tracks the following metrics:

### Standard Metrics

- **`cpu_usage_percentage`** (Gauge): CPU utilization percentage
- **`memory_usage_bytes`** (Gauge): Memory usage in bytes


### Custom Metrics

You can create the custom metrics you need using the default open telemetry metrics

```python
from src.rebrandly_otel import meter

sqs_counter = meter.meter.create_counter(
    name="sqs_sender_counter",
    description="Number of messages sent",
    unit="1"
)
sqs_counter.add(1)
```

## Tracing Features

### Automatic Context Propagation

The SDK automatically extracts and propagates trace context from:
- AWS SQS message attributes
- AWS SNS message attributes
- HTTP headers
- Custom carriers

### Span Attributes

Lambda spans automatically include:
- `faas.trigger`: Detected trigger type (sqs, sns, api_gateway, etc.)
- `faas.execution`: AWS request ID
- `faas.id`: Function ARN
- `cloud.provider`: Always "aws" for Lambda
- `cloud.platform`: Always "aws_lambda" for Lambda

### Exception Handling

Spans automatically capture exceptions with:
- Full exception details and stack traces
- Automatic status code setting
- Exception events in the span timeline

## Logging Integration

The SDK integrates with Python's standard logging module:

```python
from rebrandly_otel import logger

# Use as a standard Python logger
logger.info("Processing started", extra={"request_id": "123"})
logger.error("Processing failed", exc_info=True)
```

Features:
- Automatic trace context injection
- Structured logging support
- Console and OTLP export
- Log level configuration via environment

## AWS Lambda Support

### Trigger Detection

Automatically detects and labels Lambda triggers:
- API Gateway (v1 and v2)
- SQS
- SNS
- S3
- Kinesis
- DynamoDB
- EventBridge
- Batch

### Automatic Metrics

For Lambda functions, the SDK automatically captures:
- Memory usage
- CPU utilization

### Context Extraction

Automatically extracts trace context from:
- SQS MessageAttributes
- SNS MessageAttributes (including nested format)
- Custom message attributes

## Performance Considerations

### Batch Processing

- Configurable batch sizes and intervals
- Automatic batching for traces, metrics, and logs
- Optimized for high-throughput scenarios

### Lambda Optimization

- Automatic flushing before function freeze
- Minimal cold start impact
- Efficient memory usage
- Configurable timeout handling

## Export Formats

### Supported Exporters

- **OTLP/gRPC**: Primary export format for production
- **Console**: Available for local development and debugging

## Thread Safety

All components are thread-safe and can be used in multi-threaded applications:
- Singleton pattern ensures single initialization
- Thread-safe metric recording
- Concurrent span creation support

## Resource Attributes

Automatically includes:
- Service name and version
- Python runtime version
- Deployment environment
- Custom resource attributes via environment

## Error Handling

- Graceful degradation when OTLP endpoint unavailable
- Non-blocking telemetry operations
- Automatic retry with exponential backoff
- Comprehensive error logging

## Compatibility

- Python 3.7+
- AWS Lambda runtime support
- Compatible with OpenTelemetry Collector
- Works with any OTLP-compatible backend

## Examples

### Lambda - Send SNS / SQS message
```python
import os
import json
import boto3
from rebrandly_otel import otel, lambda_handler, logger

sqs = boto3.client('sqs')
QUEUE_URL = os.environ.get('SQS_URL')

@lambda_handler("sqs_sender")
def handler(event, context):
    logger.info("Starting SQS message send")

    # Get trace context for propagation
    trace_attrs = otel.tracer.get_attributes_for_aws_from_context()

    # Send message with trace context
    response = sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps({"data": "test message"}),
        MessageAttributes=trace_attrs
    )

    logger.info(f"Sent SQS message: {response['MessageId']}")

    return {
        'statusCode': 200,
        'body': json.dumps({'messageId': response['MessageId']})
    }
```

### Lambda Receive SQS message
```python
import json
from rebrandly_otel import lambda_handler, logger, aws_message_span

@lambda_handler(name="sqs_receiver")
def handler(event, context):
    for record in event['Records']:
        # Process each message with trace context
        process_message(record)

def process_message(record):
    with aws_message_span("process_message_sqs_receiver", message=record) as s:
        logger.info(f"Processing message: {record['messageId']}")

        # Parse message body
        body = json.loads(record['body'])
        logger.info(f"Message data: {body}")
```

### Lambda Receive SNS message (record specific event)
```python
import json
from rebrandly_otel import lambda_handler, logger, aws_message_span

@lambda_handler(name="sns_receiver")
def handler(event, context):
    for record in event['Records']:
        # Process each message with trace context
        process_message(record)

def process_message(record):
    message = json.loads(record['Sns']['Message'])
    if message['event'] == 'whitelisted-event':
        with aws_message_span("process_message_sns_receiver", message=record) as s:
            logger.info(f"Processing message: {record['messageId']}")
    
            # Parse message body
            body = json.loads(record['body'])
            logger.info(f"Message data: {body}")
```

###
Flask

```python

from flask import Flask, jsonify
from src.rebrandly_otel import otel, logger, app_before_request, app_after_request, flask_error_handler
from datetime import datetime

app = Flask(__name__)

# Register the centralized OTEL handlers
app.before_request(app_before_request)
app.after_request(app_after_request)
app.register_error_handler(Exception, flask_error_handler)

@app.route('/health')
def health():
    logger.info("Health check requested")
    return jsonify({"status": "healthy"}), 200

@app.route('/process', methods=['POST', 'GET'])
def process():
    with otel.span("process_request"):
        logger.info("Processing POST request")

        # Simulate processing
        result = {"processed": True, "timestamp": datetime.now().isoformat()}

        logger.info(f"Returning result: {result}")
        return jsonify(result), 200

@app.route('/error')
def error():
    logger.error("Error endpoint called")
    raise Exception("Simulated error")

if __name__ == '__main__':
    app.run(debug=True)
```

###
FastAPI

```python

# main_fastapi.py
from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager
from src.rebrandly_otel import otel, logger, force_flush
from src.fastapi_support import setup_fastapi, get_current_span
from datetime import datetime
from typing import Optional
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("FastAPI application starting up")
    yield
    # Shutdown
    logger.info("FastAPI application shutting down")
    force_flush()

app = FastAPI(title="FastAPI OTEL Example", lifespan=lifespan)

# Setup FastAPI with OTEL
setup_fastapi(otel, app)

@app.get("/health")
async def health():
    """Health check endpoint."""
    logger.info("Health check requested")
    return {"status": "healthy"}

@app.post("/process")
@app.get("/process")
async def process(span = Depends(get_current_span)):
    """Process endpoint with custom span."""
    with otel.span("process_request"):
        logger.info("Processing request")

        # You can also use the injected span directly
        if span:
            span.add_event("custom_processing_event", {
                "timestamp": datetime.now().isoformat()
            })

        # Simulate some processing
        result = {
            "processed": True,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"Returning result: {result}")
        return result

@app.get("/error")
async def error():
    """Endpoint that raises an error."""
    logger.error("Error endpoint called")
    raise HTTPException(status_code=400, detail="Simulated error")

@app.get("/exception")
async def exception():
    """Endpoint that raises an unhandled exception."""
    logger.error("Exception endpoint called")
    raise ValueError("Simulated unhandled exception")

@app.get("/items/{item_id}")
async def get_item(item_id: int, q: Optional[str] = None):
    """Example endpoint with path and query parameters."""
    with otel.span("fetch_item", attributes={"item_id": item_id, "query": q}):
        logger.info(f"Fetching item {item_id} with query: {q}")

        if item_id == 999:
            raise HTTPException(status_code=404, detail="Item not found")

        return {
            "item_id": item_id,
            "name": f"Item {item_id}",
            "query": q
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### PyMySQL Database Instrumentation

The SDK provides connection-level instrumentation for PyMySQL that automatically traces all queries without requiring you to instrument each query individually.

```python
import pymysql
from rebrandly_otel import otel, logger, instrument_pymysql

# Initialize OTEL
otel.initialize()

# Create and instrument your connection
connection = pymysql.connect(
    host='localhost',
    user='your_user',
    password='your_password',
    database='your_database'
)

# Instrument the connection - all queries are now automatically traced
connection = instrument_pymysql(otel, connection, options={
    'slow_query_threshold_ms': 1000,  # Queries over 1s flagged as slow
    'capture_bindings': False  # Set True to capture query parameters
})

# Use normally - all queries automatically traced
with connection.cursor() as cursor:
    cursor.execute("SELECT * FROM users WHERE id = %s", (123,))
    result = cursor.fetchone()
    logger.info(f"Found user: {result}")

connection.close()
otel.force_flush()
```

Features:
- Automatic span creation for all queries
- Query operation detection (SELECT, INSERT, UPDATE, etc.)
- Slow query detection and flagging
- Duration tracking
- Error recording with exception details
- Optional query parameter capture (disabled by default for security)

Environment configuration:
- `PYMYSQL_SLOW_QUERY_THRESHOLD_MS`: Threshold for slow query detection (default: 1500ms)

### More examples
You can find More examples [here](examples)

## Testing

### Running Tests

The test suite uses [pytest](https://docs.pytest.org/).

Run all tests:
```bash
pytest
```

Run specific test file:
```bash
pytest tests/test_flask_support.py -v
pytest tests/test_fastapi_support.py -v
pytest tests/test_usage.py -v
pytest tests/test_pymysql_instrumentation.py -v
pytest tests/test_metrics_and_logs.py -v
pytest tests/test_decorators.py -v
```

Run with coverage:
```bash
pytest --cov=src --cov-report=html
```

### Test Coverage

The test suite includes:
- **Integration tests** (`test_usage.py`): Core OTEL functionality, Lambda handlers, message processing
- **Flask integration tests** (`test_flask_support.py`): Flask setup and hooks
- **FastAPI integration tests** (`test_fastapi_support.py`): FastAPI setup and middleware
- **PyMySQL instrumentation tests** (`test_pymysql_instrumentation.py`): Database connection instrumentation, query tracing, helper functions
- **Metrics and logs tests** (`test_metrics_and_logs.py`): Custom metrics creation (counter, histogram, gauge), logging levels (info, warning, debug, error)
- **Decorators tests** (`test_decorators.py`): Lambda handler decorator, AWS message handler decorator, traces decorator, aws_message_span context manager

## License

Rebrandly Python SDK is released under the MIT License.

## Build and Deploy

```bash
brew install pipx
pipx ensurepath
pipx install build
pipx install twine
```

> build
> 
> twine upload dist/*

If `build` gives you an error, try:

> pyproject-build
>
> twine upload dist/*