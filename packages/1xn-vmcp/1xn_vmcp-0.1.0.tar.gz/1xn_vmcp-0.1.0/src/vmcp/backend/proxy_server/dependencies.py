"""
Proxy Server Dependencies
==========================

Helper functions for accessing request context in MCP handlers.
"""

from contextvars import ContextVar
from fastapi import Request
from typing import Optional

# Context variable to store current HTTP request
_request_context: ContextVar[Optional[Request]] = ContextVar('request_context', default=None)


def set_http_request(request: Request) -> None:
    """
    Store the current HTTP request in context.

    Args:
        request: FastAPI Request object
    """
    _request_context.set(request)


def get_http_request() -> Request:
    """
    Get the current HTTP request from context.

    Returns:
        Current FastAPI Request object

    Raises:
        RuntimeError: If called outside request context
    """
    request = _request_context.get()
    if request is None:
        raise RuntimeError("No HTTP request in current context")
    return request


def clear_http_request() -> None:
    """Clear the HTTP request from context."""
    _request_context.set(None)
