"""
Utility decorators for error handling and logging.

This module provides decorator functions for common cross-cutting concerns
such as error logging, API endpoint error handling, and exception management
throughout the data exchange agent application.
"""

import functools

from collections.abc import Callable

from flask import jsonify

from data_exchange_agent import custom_exceptions
from data_exchange_agent.utils.sf_logger import SFLogger


# Global logger instance - SFLogger is implemented as a singleton
_logger = SFLogger()


def log_error(func=None) -> Callable:
    """
    Log any exceptions raised by the decorated function.

    Args:
        func: The function to decorate

    Returns:
        wrapper: The wrapped function that includes error logging

    """

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                try:
                    _logger.error(f"Error in {f.__name__}: {str(e)}", exception=e)
                except Exception as log_err:
                    print(f"Error logging error in {f.__name__}: {log_err}")
                raise  # Re-raise the exception after logging

        return wrapper

    if func is None:
        # Decorator was called with arguments: @log_error()
        return decorator
    else:
        # Decorator was called without arguments: @log_error
        return decorator(func)


def print_error_with_message(error_message=None) -> Callable:
    """
    Print any exceptions raised by the decorated function with a custom message.

    Args:
        error_message: Optional custom error message to display

    Returns:
        decorator: The decorator function

    """

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except custom_exceptions.ConfigurationError as e:
                print(error_message)
                print(f"Configuration file error: {e}")
            except Exception:
                print(error_message)

        return wrapper

    return decorator


def api_endpoint_error(func=None) -> Callable:
    """
    Log any exceptions raised by the decorated function.

    Args:
        func: The function to decorate

    Returns:
        wrapper: The wrapped function that includes error logging

    """

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        return wrapper

    if func is None:
        # Decorator was called with arguments: @api_endpoint_error()
        return decorator
    else:
        # Decorator was called without arguments: @api_endpoint_error
        return decorator(func)
