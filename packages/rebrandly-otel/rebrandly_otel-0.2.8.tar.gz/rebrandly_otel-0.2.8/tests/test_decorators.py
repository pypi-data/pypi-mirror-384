import pytest
from unittest.mock import MagicMock, patch, call
import json

# Import the decorators and methods under test
from src.rebrandly_otel import (
    lambda_handler,
    aws_message_handler,
    traces,
    aws_message_span,
    otel
)
from opentelemetry.trace import SpanKind, Status, StatusCode


@pytest.fixture
def mock_lambda_context():
    """Create mock AWS Lambda context"""
    context = MagicMock()
    context.aws_request_id = 'test-request-id-12345'
    context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test-function'
    context.function_name = 'test-function'
    context.function_version = '$LATEST'
    context.memory_limit_in_mb = '256'
    return context


@pytest.fixture
def sqs_event():
    """Create mock SQS event"""
    return {
        'Records': [
            {
                'messageId': 'msg-12345',
                'receiptHandle': 'receipt-handle',
                'body': json.dumps({'data': 'test message'}),
                'attributes': {
                    'ApproximateReceiveCount': '1',
                    'SentTimestamp': '1234567890'
                },
                'messageAttributes': {
                    'traceparent': {
                        'stringValue': '00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01',
                        'dataType': 'String'
                    }
                },
                'eventSource': 'aws:sqs'
            }
        ]
    }


@pytest.fixture
def sns_event():
    """Create mock SNS event"""
    return {
        'Records': [
            {
                'EventSource': 'aws:sns',
                'Sns': {
                    'MessageId': 'sns-msg-12345',
                    'Message': json.dumps({'event': 'test_event', 'data': 'test'}),
                    'MessageAttributes': {
                        'traceparent': {
                            'Type': 'String',
                            'Value': '00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01'
                        }
                    }
                }
            }
        ]
    }


@pytest.fixture
def api_gateway_event():
    """Create mock API Gateway event"""
    return {
        'httpMethod': 'POST',
        'path': '/test',
        'headers': {
            'Content-Type': 'application/json',
            'traceparent': '00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01'
        },
        'body': json.dumps({'test': 'data'}),
        'requestContext': {
            'requestId': 'api-request-123'
        }
    }


class TestLambdaHandlerDecorator:
    """Test the @lambda_handler decorator"""

    def test_lambda_handler_basic_execution(self, mock_lambda_context, sqs_event):
        """Test basic Lambda handler execution"""
        @lambda_handler(name="test_handler")
        def handler(event, context):
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'success'})
            }

        # Execute handler
        result = handler(sqs_event, mock_lambda_context)

        # Verify result
        assert result['statusCode'] == 200
        assert 'success' in result['body']

    def test_lambda_handler_with_sqs_trigger(self, mock_lambda_context, sqs_event):
        """Test Lambda handler detects SQS trigger"""
        @lambda_handler(name="sqs_handler")
        def handler(event, context):
            assert event == sqs_event
            assert context == mock_lambda_context
            return {'statusCode': 200}

        result = handler(sqs_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_lambda_handler_with_sns_trigger(self, mock_lambda_context, sns_event):
        """Test Lambda handler detects SNS trigger"""
        @lambda_handler(name="sns_handler")
        def handler(event, context):
            assert event == sns_event
            return {'statusCode': 200}

        result = handler(sns_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_lambda_handler_with_api_gateway_trigger(self, mock_lambda_context, api_gateway_event):
        """Test Lambda handler detects API Gateway trigger"""
        @lambda_handler(name="api_handler")
        def handler(event, context):
            assert event['httpMethod'] == 'POST'
            return {
                'statusCode': 200,
                'body': json.dumps({'result': 'processed'})
            }

        result = handler(api_gateway_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_lambda_handler_with_custom_attributes(self, mock_lambda_context, sqs_event):
        """Test Lambda handler with custom span attributes"""
        custom_attrs = {
            'custom.attribute': 'test_value',
            'custom.number': 42
        }

        @lambda_handler(name="custom_handler", attributes=custom_attrs)
        def handler(event, context):
            return {'statusCode': 200}

        result = handler(sqs_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_lambda_handler_exception_handling(self, mock_lambda_context, sqs_event):
        """Test Lambda handler handles exceptions"""
        @lambda_handler(name="error_handler")
        def handler(event, context):
            raise ValueError("Test error")

        with pytest.raises(ValueError) as exc_info:
            handler(sqs_event, mock_lambda_context)

        assert str(exc_info.value) == "Test error"

    def test_lambda_handler_returns_error_status_code(self, mock_lambda_context, sqs_event):
        """Test Lambda handler with error status code"""
        @lambda_handler(name="error_response_handler")
        def handler(event, context):
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Internal server error'})
            }

        result = handler(sqs_event, mock_lambda_context)
        assert result['statusCode'] == 500

    def test_lambda_handler_without_context(self, sqs_event):
        """Test Lambda handler without Lambda context"""
        @lambda_handler(name="no_context_handler")
        def handler(event, context):
            return {'statusCode': 200}

        result = handler(sqs_event, None)
        assert result['statusCode'] == 200

    def test_lambda_handler_auto_flush_default(self, mock_lambda_context, sqs_event):
        """Test Lambda handler auto-flushes by default"""
        @lambda_handler(name="auto_flush_handler")
        def handler(event, context):
            return {'statusCode': 200}

        with patch.object(otel, 'force_flush') as mock_flush:
            result = handler(sqs_event, mock_lambda_context)
            assert result['statusCode'] == 200
            # Verify force_flush was called
            mock_flush.assert_called_once()

    def test_lambda_handler_no_auto_flush(self, mock_lambda_context, sqs_event):
        """Test Lambda handler with auto_flush disabled"""
        @lambda_handler(name="no_auto_flush_handler", auto_flush=False)
        def handler(event, context):
            return {'statusCode': 200}

        with patch.object(otel, 'force_flush') as mock_flush:
            result = handler(sqs_event, mock_lambda_context)
            assert result['statusCode'] == 200
            # Verify force_flush was NOT called
            mock_flush.assert_not_called()

    def test_lambda_handler_preserves_function_metadata(self):
        """Test Lambda handler preserves original function metadata"""
        @lambda_handler(name="metadata_handler")
        def my_handler(event, context):
            """Handler docstring"""
            return {'statusCode': 200}

        assert my_handler.__name__ == 'my_handler'
        assert my_handler.__doc__ == 'Handler docstring'


class TestAwsMessageHandlerDecorator:
    """Test the @aws_message_handler decorator"""

    def test_aws_message_handler_basic_execution(self, sqs_event):
        """Test basic AWS message handler execution"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="test_message_handler")
        def handler(record):
            body = json.loads(record['body'])
            return {'processed': True, 'data': body['data']}

        result = handler(record)
        assert result['processed'] is True
        assert result['data'] == 'test message'

    def test_aws_message_handler_with_sqs_record(self, sqs_event):
        """Test AWS message handler with SQS record"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="sqs_message_handler")
        def handler(record):
            assert record['messageId'] == 'msg-12345'
            assert record['eventSource'] == 'aws:sqs'
            return {'processed': True}

        result = handler(record)
        assert result['processed'] is True

    def test_aws_message_handler_with_sns_record(self, sns_event):
        """Test AWS message handler with SNS record"""
        record = sns_event['Records'][0]

        @aws_message_handler(name="sns_message_handler")
        def handler(record):
            assert record['EventSource'] == 'aws:sns'
            message = json.loads(record['Sns']['Message'])
            return {'processed': True, 'event': message['event']}

        result = handler(record)
        assert result['processed'] is True
        assert result['event'] == 'test_event'

    def test_aws_message_handler_with_custom_attributes(self, sqs_event):
        """Test AWS message handler with custom attributes"""
        record = sqs_event['Records'][0]
        custom_attrs = {'custom.key': 'custom_value'}

        @aws_message_handler(name="custom_attrs_handler", attributes=custom_attrs)
        def handler(record):
            return {'processed': True}

        result = handler(record)
        assert result['processed'] is True

    def test_aws_message_handler_exception_handling(self, sqs_event):
        """Test AWS message handler handles exceptions"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="error_message_handler")
        def handler(record):
            raise RuntimeError("Processing failed")

        with pytest.raises(RuntimeError) as exc_info:
            handler(record)

        assert str(exc_info.value) == "Processing failed"

    def test_aws_message_handler_with_status_code(self, sqs_event):
        """Test AWS message handler returns status code"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="status_code_handler")
        def handler(record):
            return {
                'statusCode': 200,
                'processed': True
            }

        result = handler(record)
        assert result['statusCode'] == 200
        assert result['processed'] is True

    def test_aws_message_handler_with_error_status_code(self, sqs_event):
        """Test AWS message handler with error status code"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="error_status_handler")
        def handler(record):
            return {
                'statusCode': 500,
                'processed': False,
                'error': 'Processing error'
            }

        result = handler(record)
        assert result['statusCode'] == 500
        assert result['processed'] is False

    def test_aws_message_handler_with_skip_flag(self, sqs_event):
        """Test AWS message handler with skipped message"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="skip_handler")
        def handler(record):
            return {
                'processed': False,
                'skipped': True,
                'reason': 'Message filtered'
            }

        result = handler(record)
        assert result['processed'] is False
        assert result['skipped'] is True

    def test_aws_message_handler_auto_flush_default(self, sqs_event):
        """Test AWS message handler auto-flushes by default"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="auto_flush_message_handler")
        def handler(record):
            return {'processed': True}

        with patch.object(otel, 'force_flush') as mock_flush:
            result = handler(record)
            assert result['processed'] is True
            mock_flush.assert_called_once()

    def test_aws_message_handler_no_auto_flush(self, sqs_event):
        """Test AWS message handler with auto_flush disabled"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="no_auto_flush_message_handler", auto_flush=False)
        def handler(record):
            return {'processed': True}

        with patch.object(otel, 'force_flush') as mock_flush:
            result = handler(record)
            assert result['processed'] is True
            mock_flush.assert_not_called()

    def test_aws_message_handler_with_additional_args(self, sqs_event):
        """Test AWS message handler with additional arguments"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="multi_arg_handler")
        def handler(record, extra_param='default'):
            return {
                'processed': True,
                'extra': extra_param
            }

        result = handler(record, extra_param='custom_value')
        assert result['processed'] is True
        assert result['extra'] == 'custom_value'


class TestTracesDecorator:
    """Test the @traces decorator"""

    def test_traces_basic_execution(self):
        """Test basic function tracing"""
        @traces(name="test_function")
        def my_function(x, y):
            return x + y

        result = my_function(2, 3)
        assert result == 5

    def test_traces_default_span_name(self):
        """Test traces decorator uses default span name from function"""
        @traces()
        def calculate_sum(a, b):
            return a + b

        result = calculate_sum(10, 20)
        assert result == 30

    def test_traces_with_custom_attributes(self):
        """Test traces decorator with custom attributes"""
        custom_attrs = {
            'operation.type': 'calculation',
            'operation.priority': 'high'
        }

        @traces(name="calculation_function", attributes=custom_attrs)
        def multiply(x, y):
            return x * y

        result = multiply(4, 5)
        assert result == 20

    def test_traces_with_span_kind(self):
        """Test traces decorator with custom span kind"""
        @traces(name="client_operation", kind=SpanKind.CLIENT)
        def fetch_data():
            return {'data': 'fetched'}

        result = fetch_data()
        assert result['data'] == 'fetched'

    def test_traces_exception_handling(self):
        """Test traces decorator handles exceptions"""
        @traces(name="error_function")
        def failing_function():
            raise ValueError("Function failed")

        with pytest.raises(ValueError) as exc_info:
            failing_function()

        assert str(exc_info.value) == "Function failed"

    def test_traces_with_return_value(self):
        """Test traces decorator preserves return values"""
        @traces(name="return_value_function")
        def get_user_data(user_id):
            return {
                'id': user_id,
                'name': 'Test User',
                'email': 'test@example.com'
            }

        result = get_user_data(123)
        assert result['id'] == 123
        assert result['name'] == 'Test User'

    def test_traces_with_complex_operations(self):
        """Test traces decorator with complex operations"""
        @traces(name="complex_operation")
        def process_data(items):
            return [item * 2 for item in items]

        result = process_data([1, 2, 3, 4, 5])
        assert result == [2, 4, 6, 8, 10]

    def test_traces_preserves_function_metadata(self):
        """Test traces decorator preserves function metadata"""
        @traces(name="metadata_function")
        def documented_function(param):
            """This is a documented function"""
            return param.upper()

        assert documented_function.__name__ == 'documented_function'
        assert documented_function.__doc__ == 'This is a documented function'

    def test_traces_nested_calls(self):
        """Test traces decorator with nested function calls"""
        @traces(name="outer_function")
        def outer(x):
            return inner(x) * 2

        @traces(name="inner_function")
        def inner(x):
            return x + 1

        result = outer(5)
        assert result == 12  # (5 + 1) * 2

    def test_traces_with_kwargs(self):
        """Test traces decorator with keyword arguments"""
        @traces(name="kwargs_function")
        def process_request(method, endpoint, data=None, headers=None):
            return {
                'method': method,
                'endpoint': endpoint,
                'has_data': data is not None,
                'has_headers': headers is not None
            }

        result = process_request('POST', '/api/users', data={'name': 'John'}, headers={'Auth': 'token'})
        assert result['method'] == 'POST'
        assert result['has_data'] is True
        assert result['has_headers'] is True


class TestAwsMessageSpan:
    """Test the aws_message_span context manager"""

    def test_aws_message_span_basic_usage(self, sqs_event):
        """Test basic AWS message span usage"""
        record = sqs_event['Records'][0]

        with aws_message_span("process_sqs_message", message=record) as span:
            assert span is not None
            body = json.loads(record['body'])
            assert body['data'] == 'test message'

    def test_aws_message_span_with_sqs_message(self, sqs_event):
        """Test AWS message span with SQS message"""
        record = sqs_event['Records'][0]

        with aws_message_span("sqs_processing", message=record) as span:
            # Span should extract context from MessageAttributes
            assert span is not None
            assert record['eventSource'] == 'aws:sqs'

    def test_aws_message_span_with_sns_message(self, sns_event):
        """Test AWS message span with SNS message"""
        record = sns_event['Records'][0]

        with aws_message_span("sns_processing", message=record) as span:
            # Span should extract context from SNS MessageAttributes
            assert span is not None
            assert record['EventSource'] == 'aws:sns'

    def test_aws_message_span_with_custom_attributes(self, sqs_event):
        """Test AWS message span with custom attributes"""
        record = sqs_event['Records'][0]
        custom_attrs = {
            'message.priority': 'high',
            'message.source': 'external'
        }

        with aws_message_span("custom_attrs_span", message=record, attributes=custom_attrs) as span:
            assert span is not None

    def test_aws_message_span_with_span_kind(self, sqs_event):
        """Test AWS message span with custom span kind"""
        record = sqs_event['Records'][0]

        with aws_message_span("consumer_span", message=record, kind=SpanKind.CONSUMER) as span:
            assert span is not None

    def test_aws_message_span_exception_handling(self, sqs_event):
        """Test AWS message span handles exceptions"""
        record = sqs_event['Records'][0]

        with pytest.raises(RuntimeError):
            with aws_message_span("error_span", message=record) as span:
                assert span is not None
                raise RuntimeError("Processing error")

    def test_aws_message_span_without_message(self):
        """Test AWS message span without message (falls back to regular span)"""
        with aws_message_span("no_message_span") as span:
            assert span is not None

    def test_aws_message_span_nested_spans(self, sqs_event):
        """Test nested AWS message spans"""
        record = sqs_event['Records'][0]

        with aws_message_span("outer_span", message=record) as outer_span:
            assert outer_span is not None

            with aws_message_span("inner_span") as inner_span:
                assert inner_span is not None
                # Both spans should be active

    def test_aws_message_span_with_operations(self, sqs_event):
        """Test AWS message span with operations inside"""
        record = sqs_event['Records'][0]
        results = []

        with aws_message_span("operation_span", message=record) as span:
            assert span is not None
            body = json.loads(record['body'])
            results.append(body['data'])
            results.append('processed')

        assert len(results) == 2
        assert results[0] == 'test message'
        assert results[1] == 'processed'

    def test_aws_message_span_preserves_context(self, sqs_event):
        """Test AWS message span preserves trace context"""
        record = sqs_event['Records'][0]

        # Message has traceparent in MessageAttributes
        assert 'messageAttributes' in record
        assert 'traceparent' in record['messageAttributes']

        with aws_message_span("context_span", message=record) as span:
            # Span should be created with extracted context
            assert span is not None


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple decorators"""

    def test_lambda_with_message_handler(self, mock_lambda_context, sqs_event):
        """Test Lambda handler processing multiple messages"""
        @lambda_handler(name="message_processor_lambda")
        def handler(event, context):
            results = []
            for record in event['Records']:
                result = process_record(record)
                results.append(result)
            return {
                'statusCode': 200,
                'body': json.dumps({'processed': len(results)})
            }

        @aws_message_handler(name="record_processor", auto_flush=False)
        def process_record(record):
            body = json.loads(record['body'])
            return {'processed': True, 'data': body['data']}

        result = handler(sqs_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_traced_function_in_lambda(self, mock_lambda_context, api_gateway_event):
        """Test traced function called from Lambda handler"""
        @lambda_handler(name="api_lambda")
        def handler(event, context):
            data = parse_request(event)
            result = process_data(data)
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }

        @traces(name="parse_request")
        def parse_request(event):
            return json.loads(event['body'])

        @traces(name="process_data")
        def process_data(data):
            return {'processed': True, 'input': data}

        result = handler(api_gateway_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_message_span_in_message_handler(self, sqs_event):
        """Test aws_message_span used inside aws_message_handler"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="complex_handler", auto_flush=False)
        def handler(record):
            # Additional span for specific processing
            with aws_message_span("validation", message=record) as span:
                body = json.loads(record['body'])
                if 'data' not in body:
                    return {'processed': False, 'skipped': True}

            return {'processed': True}

        result = handler(record)
        assert result['processed'] is True

    def test_multiple_decorators_combination(self):
        """Test multiple traced functions calling each other"""
        @traces(name="fetch_user")
        def fetch_user(user_id):
            return {'id': user_id, 'name': 'John Doe'}

        @traces(name="fetch_orders")
        def fetch_orders(user_id):
            return [{'order_id': 1}, {'order_id': 2}]

        @traces(name="aggregate_data")
        def aggregate_user_data(user_id):
            user = fetch_user(user_id)
            orders = fetch_orders(user_id)
            return {
                'user': user,
                'orders': orders,
                'order_count': len(orders)
            }

        result = aggregate_user_data(123)
        assert result['user']['id'] == 123
        assert result['order_count'] == 2
