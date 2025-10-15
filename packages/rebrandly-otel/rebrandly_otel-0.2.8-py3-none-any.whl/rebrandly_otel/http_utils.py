# http_utils.py
"""Shared HTTP utilities for Rebrandly OTEL SDK."""


def filter_important_headers(headers):
    """
    Filter headers to keep only important ones for observability.
    Excludes sensitive headers like authorization, cookies, and tokens.
    """
    important_headers = [
        'content-type',
        'content-length',
        'accept',
        'accept-encoding',
        'accept-language',
        'host',
        'x-forwarded-for',
        'x-forwarded-proto',
        'x-request-id',
        'x-correlation-id',
        'x-trace-id',
        'user-agent'
    ]

    filtered = {}
    for key, value in headers.items():
        if key.lower() in important_headers:
            filtered[key] = value
    return filtered
