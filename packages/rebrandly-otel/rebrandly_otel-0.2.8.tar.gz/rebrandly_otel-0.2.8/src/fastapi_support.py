# fastapi_integration.py
"""FastAPI integration for Rebrandly OTEL SDK."""
import json
from opentelemetry.trace import Status, StatusCode, SpanKind
from .http_utils import filter_important_headers
from fastapi import HTTPException, Depends
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

import time

def setup_fastapi(otel , app):
    """
    Setup FastAPI application with OTEL instrumentation.

    Example:
        from fastapi import FastAPI
        from rebrandly_otel import otel
        from rebrandly_otel.fastapi_integration import setup_fastapi

        app = FastAPI()
        setup_fastapi(otel, app)
    """

    # Add middleware
    add_otel_middleware(otel, app)

    # Add exception handlers
    app.add_exception_handler(HTTPException, lambda request, exc: fastapi_exception_handler(otel, request, exc))
    app.add_exception_handler(Exception, lambda request, exc: fastapi_exception_handler(otel, request, exc))

    return app

def add_otel_middleware(otel, app):
    """
    Add OTEL middleware to FastAPI application.
    """

    class OTELMiddleware(BaseHTTPMiddleware):
        def __init__(self, app):
            super().__init__(app)
            self.otel = otel

        async def dispatch(self, request: Request, call_next):
            # Extract trace context from headers
            headers = dict(request.headers)
            token = self.otel.attach_context(headers)

            # Start span for request
            span_name = f"{request.method} {request.url.path}"

            # Filter headers to keep only important ones
            filtered_headers = filter_important_headers(headers)

            # Build attributes dict, excluding None values
            attributes = {
                # Required HTTP attributes per semantic conventions
                "http.request.method": request.method,
                "http.request.headers": json.dumps(filtered_headers, default=str),
                "url.full": str(request.url),
                "url.scheme": request.url.scheme,
                "url.path": request.url.path,
                "network.protocol.version": "1.1",  # FastAPI/Starlette typically uses HTTP/1.1
                "server.address": request.url.hostname,
                "server.port": request.url.port or (443 if request.url.scheme == 'https' else 80),
            }

            # Add optional attributes only if they have values
            if request.url.query:
                attributes["url.query"] = request.url.query

            user_agent = request.headers.get("user-agent")
            if user_agent:
                attributes["user_agent.original"] = user_agent

            if request.client and request.client.host:
                attributes["client.address"] = request.client.host

            # Use start_as_current_span for proper context propagation
            with self.otel.tracer.tracer.start_as_current_span(
                    span_name,
                    attributes=attributes,
                    kind=SpanKind.SERVER
            ) as span:
                # Log request start
                self.otel.logger.logger.info(f"Request started: {request.method} {request.url.path}",
                                             extra={"http.method": request.method, "http.path": request.url.path})

                # Store span in request state for access in routes
                request.state.span = span
                request.state.trace_token = token

                start_time = time.time()

                try:
                    # Process request
                    response = await call_next(request)

                    # After routing, update span name and route if available
                    if hasattr(request, 'scope') and 'path' in request.scope:
                        route = request.scope.get('path', request.url.path)
                        span.update_name(f"{request.method} {route}")
                        span.set_attribute("http.route", route)

                    # Set response attributes using new semantic conventions
                    span.set_attribute("http.response.status_code", response.status_code)
                    span.set_attribute("http.status_code", response.status_code)  # Deprecated

                    # Set span status based on HTTP status code
                    if response.status_code >= 400:
                        span.set_status(Status(StatusCode.ERROR, f"HTTP {response.status_code}"))
                    else:
                        span.set_status(Status(StatusCode.OK))

                    # Log request completion
                    self.otel.logger.logger.info(f"Request completed: {response.status_code}",
                                                 extra={"http.status_code": response.status_code})
                    otel.force_flush(timeout_millis=100)
                    return response

                except Exception as e:
                    # Record exception
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.add_event("exception", {
                        "exception.type": type(e).__name__,
                        "exception.message": str(e)
                    })

                    # Log error
                    self.otel.logger.logger.error(f"Unhandled exception: {e}",
                                                  exc_info=True,
                                                  extra={"exception.type": type(e).__name__})

                    raise

                finally:
                    # Detach context
                    self.otel.detach_context(token)

    # Add middleware to app
    app.add_middleware(OTELMiddleware)

def fastapi_exception_handler(otel, request, exc):
    """
    Handle FastAPI exceptions and record them in the current span.
    """

    # Determine the status code
    if isinstance(exc, HTTPException):
        status_code = exc.status_code
        error_detail = exc.detail
    elif hasattr(exc, 'status_code'):
        status_code = exc.status_code
        error_detail = str(exc)
    elif hasattr(exc, 'code'):
        status_code = exc.code if isinstance(exc.code, int) else 500
        error_detail = str(exc)
    else:
        status_code = 500
        error_detail = str(exc)

    # Record exception in span if available and still recording
    if hasattr(request.state, 'span') and request.state.span.is_recording():
        # Update both new and old attribute names for compatibility
        request.state.span.set_attribute("http.response.status_code", status_code)
        request.state.span.set_attribute("error.type", type(exc).__name__)

        request.state.span.record_exception(exc)
        request.state.span.set_status(Status(StatusCode.ERROR, str(exc)))
        request.state.span.add_event("exception", {
            "exception.type": type(exc).__name__,
            "exception.message": str(exc)
        })

    # Log the error
    otel.logger.logger.error(f"Unhandled exception: {exc} (status: {status_code})",
                             exc_info=True,
                             extra={
                                 "exception.type": type(exc).__name__,
                                 "http.status_code": status_code
                             })

    # Return error response
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_detail,
            "type": type(exc).__name__
        }
    )

# Optional: Dependency injection helper for accessing the span in routes
def get_current_span(request: Request):
    """
    FastAPI dependency to get the current span in route handlers.

    Example:
        from fastapi import Depends
        from rebrandly_otel.fastapi_integration import get_current_span

        @app.get("/example")
        async def example(span = Depends(get_current_span)):
            if span:
                span.add_event("custom_event", {"key": "value"})
            return {"status": "ok"}
    """
    if hasattr(request.state, 'span'):
        return request.state.span
    return None