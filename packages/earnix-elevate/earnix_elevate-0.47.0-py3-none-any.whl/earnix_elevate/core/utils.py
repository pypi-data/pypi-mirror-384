"""
Utility functions and helpers for the Earnix Elevate SDK.

This module provides common utility functions, decorators, and helpers
that are used across multiple modules to reduce code duplication.
"""

import functools
import time
from typing import Any, Callable, Dict, Optional, TypeVar
from urllib.parse import urljoin

from .const import SERVER_TPL

# Type variable for generic functions
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


def build_server_url(server: str, route: str = "") -> str:
    """
    Build a complete server URL from server name and optional route.

    :param server: The server name (e.g., "dev", "production")
    :type server: str
    :param route: Optional route to append (e.g., "/api/data")
    :type route: str
    :returns: Complete server URL
    :rtype: str
    :raises ValueError: If server is not a string or route is not a string

    Example:
        >>> build_server_url("dev", "/api/data")
        'https://dev.e2.earnix.com/api/data'
    """
    # Input validation
    if not isinstance(server, str):
        raise ValueError(f"Server must be a string, got {type(server).__name__}")

    if not isinstance(route, str):
        raise ValueError(f"Route must be a string, got {type(route).__name__}")

    base_url = SERVER_TPL.format(server)
    if route:
        return urljoin(base_url, route.lstrip("/"))
    return base_url


def create_error_context(operation: str, **kwargs: Any) -> Dict[str, Any]:
    """
    Create a standardized error context dictionary.

    This function works in conjunction with format_error_message to provide
    comprehensive error reporting with contextual information.

    :param operation: The operation that failed
    :type operation: str
    :param kwargs: Additional context key-value pairs
    :returns: Error context dictionary
    :rtype: Dict[str, Any]
    """
    context = {"operation": operation}
    context.update(kwargs)
    return context


def retry_on_exception(
    max_retries: int = 3,
    exceptions: tuple = (Exception,),
    delay: float = 1.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to retry a function on specific exceptions.

    :param max_retries: Maximum number of retries
    :type max_retries: int
    :param exceptions: Tuple of exceptions to catch and retry on
    :type exceptions: tuple
    :param delay: Delay between retries in seconds
    :type delay: float
    :returns: Decorated function
    :rtype: Callable
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(delay)
                        continue
                    break

            # This should only happen if all retries failed
            if last_exception is not None:
                raise last_exception

            # This should never be reached, but satisfies type checker
            raise RuntimeError("Retry decorator failed without capturing exception")

        return wrapper

    return decorator


def format_error_message(
    base_message: str,
    context: Optional[Dict[str, Any]] = None,
    include_context: bool = True,
) -> str:
    """
    Format an error message with optional context information.

    :param base_message: The base error message
    :type base_message: str
    :param context: Optional context dictionary
    :type context: Optional[Dict[str, Any]]
    :param include_context: Whether to include context in the message
    :type include_context: bool
    :returns: Formatted error message
    :rtype: str
    """
    if not include_context or not context:
        return base_message

    context_parts = []
    for key, value in context.items():
        if value is not None:
            context_parts.append(f"{key}={value}")

    if context_parts:
        context_str = ", ".join(context_parts)
        return f"{base_message} (Context: {context_str})"

    return base_message
