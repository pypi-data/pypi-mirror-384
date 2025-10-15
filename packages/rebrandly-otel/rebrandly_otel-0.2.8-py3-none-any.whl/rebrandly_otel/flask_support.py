# flask_integration.py
"""Flask integration for Rebrandly OTEL SDK."""

import json
from opentelemetry.trace import Status, StatusCode, SpanKind
from .http_utils import filter_important_headers

from flask import request, jsonify
from werkzeug.exceptions import HTTPException


def setup_flask(otel, app):
    """
    Setup Flask application with OTEL instrumentation.

    Example:
        from flask import Flask
        from rebrandly_otel import otel
        from rebrandly_otel.flask_integration import setup_flask
        
        app = Flask(__name__)
        setup_flask(otel, app)
    """
    app.before_request(lambda: app_before_request(otel))
    app.after_request(lambda response: app_after_request(otel, response))
    app.register_error_handler(Exception, lambda e: flask_error_handler(otel, e))
    return app

def app_before_request(otel):
    """
    Setup tracing for incoming Flask request.
    To be used with Flask's before_request hook.
    """

    # Extract trace context from headers
    headers = dict(request.headers)
    token = otel.attach_context(headers)
    request.trace_token = token

    # Determine span name - use route if available, otherwise just method
    # Route will be available after request routing is done
    span_name = f"{request.method} {request.path}"

    # Filter headers to keep only important ones
    filtered_headers = filter_important_headers(headers)

    # Build attributes dict, excluding None values
    attributes = {
        # Required HTTP attributes per semantic conventions
        "http.request.method": request.method,
        "http.request.headers": json.dumps(filtered_headers, default=str),
        "url.full": request.url,
        "url.scheme": request.scheme,
        "url.path": request.path,
        "http.route": request.path,  # Flask doesn't expose route pattern easily
        "network.protocol.version": request.environ.get('SERVER_PROTOCOL', 'HTTP/1.1').split('/')[-1],
        "server.address": request.host.split(':')[0],
        "server.port": request.host.split(':')[1] if ':' in request.host else (443 if request.scheme == 'https' else 80),
    }

    # Add optional attributes only if they have values
    if request.query_string:
        attributes["url.query"] = request.query_string.decode('utf-8')

    if request.user_agent and request.user_agent.string:
        attributes["user_agent.original"] = request.user_agent.string

    if request.remote_addr:
        attributes["client.address"] = request.remote_addr

    # Start span for request using start_as_current_span to make it the active span
    span = otel.tracer.tracer.start_as_current_span(
        span_name,
        attributes=attributes,
        kind=SpanKind.SERVER
    )
    # Store both the span context manager and the span itself
    request.span_context = span
    request.span = span.__enter__()  # This activates the span and returns the span object

    # Log request start
    otel.logger.logger.info(f"Request started: {request.method} {request.path}",
                            extra={"http.method": request.method, "http.path": request.path})

def app_after_request(otel, response):
    """
    Cleanup tracing after Flask request completes.
    To be used with Flask's after_request hook.
    """

    # Check if we have a span and it's still recording
    if hasattr(request, 'span') and request.span.is_recording():
        # Update both new and old attribute names for compatibility
        request.span.set_attribute("http.response.status_code", response.status_code)

        # Set span status based on HTTP status code
        if response.status_code >= 400:
            request.span.set_status(Status(StatusCode.ERROR, f"HTTP {response.status_code}"))
        else:
            request.span.set_status(Status(StatusCode.OK))

        # Properly close the span context manager
        if hasattr(request, 'span_context'):
            request.span_context.__exit__(None, None, None)
        else:
            # Fallback if we don't have the context manager
            request.span.end()

    # Detach context
    if hasattr(request, 'trace_token'):
        otel.detach_context(request.trace_token)

    # Log request completion
    otel.logger.logger.info(f"Request completed: {response.status_code}",
                            extra={"http.status_code": response.status_code})

    otel.force_flush(timeout_millis=100)
    return response

def flask_error_handler(otel, exception):
    """
    Handle Flask exceptions and record them in the current span.
    To be used with Flask's errorhandler decorator.
    """

    # Determine the status code
    if isinstance(exception, HTTPException):
        status_code = exception.code
    elif hasattr(exception, 'status_code'):
        status_code = exception.status_code
    elif hasattr(exception, 'code'):
        status_code = exception.code if isinstance(exception.code, int) else 500
    else:
        status_code = 500

    # Record exception in span if available and still recording
    if hasattr(request, 'span') and request.span.is_recording():
        request.span.set_attribute("http.response.status_code", status_code)
        request.span.set_attribute("error.type", type(exception).__name__)

        request.span.record_exception(exception)
        request.span.set_status(Status(StatusCode.ERROR, str(exception)))
        request.span.add_event("exception", {
            "exception.type": type(exception).__name__,
            "exception.message": str(exception)
        })

        # Only close the span if it's still recording (not already ended)
        if hasattr(request, 'span_context'):
            request.span_context.__exit__(type(exception), exception, None)
        else:
            request.span.end()

    # Log the error with status code
    otel.logger.logger.error(f"Unhandled exception: {exception} (status: {status_code})",
                             exc_info=True,
                             extra={
                                 "exception.type": type(exception).__name__,
                                 "http.status_code": status_code
                             })

    # Return error response with the determined status code
    return jsonify({
        "error": str(exception),
        "type": type(exception).__name__
    }), status_code