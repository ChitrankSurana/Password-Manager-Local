#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Error Handler Decorators
Personal Password Manager - Centralized Error Handling

This module provides decorators for consistent error handling across the application.
Decorators automatically log exceptions, provide user-friendly messages, and handle recovery.

Usage:
    from src.core.error_handlers import handle_errors, handle_db_errors

    @handle_errors("Failed to load user data")
    def load_user(user_id):
        # Function code
        pass

    @handle_db_errors
    def create_password(user_id, password):
        # Database operation
        pass
"""

import functools
import traceback
from tkinter import messagebox
from typing import Any, Callable, Optional, Tuple, Type

from .exceptions import (
    DatabaseException,
    PasswordManagerException,
    SecurityException,
    ValidationException,
    get_exception_info,
)
from .logging_config import get_logger, log_exception

# Get module logger
logger = get_logger(__name__)


# =============================================================================
# GENERIC ERROR HANDLER
# =============================================================================


def handle_errors(
    error_message: str = "An error occurred",
    show_dialog: bool = False,
    reraise: bool = False,
    default_return: Any = None,
    log_level: str = "ERROR",
):
    """
    Generic error handler decorator

    Args:
        error_message: Message to show/log on error
        show_dialog: Show error dialog to user (GUI only)
        reraise: Re-raise exception after handling
        default_return: Value to return on error (if not reraising)
        log_level: Log level for the error

    Example:
        @handle_errors("Failed to save settings", show_dialog=True)
        def save_settings(settings):
            # Your code here
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except PasswordManagerException as e:
                # Our custom exceptions - extract info
                log_exception(
                    logger,
                    e,
                    f"{error_message}: {e.message}",
                    extra={"error_code": e.error_code, "details": e.details},
                )

                if show_dialog:
                    _show_error_dialog(error_message, e.user_message)

                if reraise:
                    raise

                return default_return

            except Exception as e:
                # Standard exceptions
                log_exception(logger, e, error_message)

                if show_dialog:
                    _show_error_dialog(
                        error_message, "An unexpected error occurred. Please try again."
                    )

                if reraise:
                    raise

                return default_return

        return wrapper

    return decorator


# =============================================================================
# SPECIALIZED ERROR HANDLERS
# =============================================================================


def handle_db_errors(error_message: str = "Database operation failed", show_dialog: bool = False):
    """
    Decorator for database operations

    Handles database-specific errors with appropriate recovery.

    Example:
        @handle_db_errors("Failed to create user")
        def create_user(username, password):
            # Database code
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except DatabaseException as e:
                logger.error(
                    f"{error_message}: {e.message}",
                    extra={"error_code": e.error_code, "details": e.details},
                )

                if show_dialog:
                    _show_error_dialog(error_message, e.user_message)

                # Database errors are usually not recoverable in the same transaction
                raise

            except Exception as e:
                log_exception(logger, e, f"{error_message} (unexpected error)")

                if show_dialog:
                    _show_error_dialog(
                        error_message,
                        "An unexpected database error occurred. Please check the logs.",
                    )

                raise

        return wrapper

    return decorator


def handle_security_errors(
    error_message: str = "Security operation failed", show_dialog: bool = True
):
    """
    Decorator for security operations (encryption, authentication, etc.)

    Example:
        @handle_security_errors("Encryption failed")
        def encrypt_password(password, key):
            # Encryption code
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except SecurityException as e:
                # Log security errors to security log
                from .logging_config import log_security_event

                log_security_event(
                    event_type="SECURITY_ERROR",
                    message=f"{error_message}: {e.message}",
                    severity="ERROR",
                    error_code=e.error_code,
                    details=e.details,
                )

                if show_dialog:
                    _show_error_dialog(error_message, e.user_message)

                raise

            except Exception as e:
                log_exception(logger, e, f"{error_message} (unexpected error)")

                if show_dialog:
                    _show_error_dialog(
                        error_message,
                        "A security error occurred. Please try again or contact support.",
                    )

                raise

        return wrapper

    return decorator


def handle_validation_errors(
    error_message: str = "Validation failed", show_dialog: bool = True, reraise: bool = False
):
    """
    Decorator for input validation

    Example:
        @handle_validation_errors("Invalid password format")
        def validate_password(password):
            # Validation code
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except ValidationException as e:
                logger.warning(
                    f"{error_message}: {e.message}",
                    extra={"error_code": e.error_code, "details": e.details},
                )

                if show_dialog:
                    _show_error_dialog(error_message, e.user_message, error_type="warning")

                if reraise:
                    raise

                return None

            except Exception as e:
                log_exception(logger, e, f"{error_message} (unexpected error)")

                if show_dialog:
                    _show_error_dialog(error_message, "Invalid input. Please check your data.")

                if reraise:
                    raise

                return None

        return wrapper

    return decorator


# =============================================================================
# RETRY DECORATOR
# =============================================================================


def retry_on_error(
    max_attempts: int = 3,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    delay: float = 1.0,
    backoff: float = 2.0,
):
    """
    Retry decorator for transient errors

    Args:
        max_attempts: Maximum number of retry attempts
        exceptions: Tuple of exception types to catch and retry
        delay: Initial delay between retries (seconds)
        backoff: Backoff multiplier for delay

    Example:
        @retry_on_error(max_attempts=3, exceptions=(DatabaseException,))
        def connect_to_database():
            # Connection code
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(
                            f"Failed after {max_attempts} attempts: {func.__name__}",
                            exc_info=True,
                        )
                        raise

                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {current_delay}s..."
                    )

                    import time

                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper

    return decorator


# =============================================================================
# AUDIT LOGGING DECORATOR
# =============================================================================


def audit_action(action: str, get_user_id: Optional[Callable] = None):
    """
    Decorator to log user actions for audit trail

    Args:
        action: Action name (e.g., "CREATE_PASSWORD", "DELETE_USER")
        get_user_id: Function to extract user_id from args/kwargs

    Example:
        @audit_action("CREATE_PASSWORD", lambda args, kwargs: kwargs.get("user_id"))
        def create_password(user_id, website, password):
            # Your code
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user_id if function provided
            user_id = None
            if get_user_id:
                try:
                    user_id = get_user_id(args, kwargs)
                except Exception:
                    pass

            # Log audit event
            from .logging_config import log_audit_event

            try:
                result = func(*args, **kwargs)

                # Log successful action
                log_audit_event(
                    action=action,
                    user_id=user_id,
                    details={"status": "success", "function": func.__name__},
                )

                return result

            except Exception as e:
                # Log failed action
                log_audit_event(
                    action=f"{action}_FAILED",
                    user_id=user_id,
                    details={
                        "status": "failed",
                        "function": func.__name__,
                        "error": str(e),
                    },
                )
                raise

        return wrapper

    return decorator


# =============================================================================
# PERFORMANCE MONITORING DECORATOR
# =============================================================================


def monitor_performance(threshold_ms: float = 1000.0):
    """
    Decorator to monitor function performance

    Logs warning if function takes longer than threshold.

    Args:
        threshold_ms: Warning threshold in milliseconds

    Example:
        @monitor_performance(threshold_ms=500)
        def slow_operation():
            # Your code
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time

            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                return result

            finally:
                elapsed_ms = (time.time() - start_time) * 1000

                if elapsed_ms > threshold_ms:
                    logger.warning(
                        f"Performance: {func.__name__} took {elapsed_ms:.2f}ms "
                        f"(threshold: {threshold_ms}ms)"
                    )
                else:
                    logger.debug(f"Performance: {func.__name__} took {elapsed_ms:.2f}ms")

        return wrapper

    return decorator


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _show_error_dialog(
    title: str, message: str, error_type: str = "error", details: Optional[str] = None
):
    """
    Show error dialog to user (GUI only)

    Args:
        title: Dialog title
        message: Error message
        error_type: Type of dialog ('error', 'warning', 'info')
        details: Additional details (optional)
    """
    try:
        full_message = message
        if details:
            full_message += f"\n\nDetails: {details}"

        if error_type == "error":
            messagebox.showerror(title, full_message)
        elif error_type == "warning":
            messagebox.showwarning(title, full_message)
        else:
            messagebox.showinfo(title, full_message)

    except Exception as e:
        # Fallback if GUI not available
        logger.debug(f"Could not show error dialog: {e}")
        print(f"{error_type.upper()}: {title} - {message}")


def create_error_response(exception: Exception, include_traceback: bool = False) -> dict:
    """
    Create standardized error response dictionary

    Useful for API endpoints and web interface.

    Args:
        exception: Exception instance
        include_traceback: Include full traceback (debug mode only)

    Returns:
        Dictionary with error information

    Example:
        try:
            risky_operation()
        except Exception as e:
            return jsonify(create_error_response(e)), 500
    """
    error_info = get_exception_info(exception)

    response = {
        "success": False,
        "error": {
            "type": error_info["error_type"],
            "code": error_info["error_code"],
            "message": error_info["user_message"],
            "details": error_info["details"],
            "recoverable": error_info["recoverable"],
        },
    }

    if include_traceback:
        response["error"]["traceback"] = traceback.format_exc()

    return response


# =============================================================================
# CONTEXT MANAGERS
# =============================================================================


class error_context:
    """
    Context manager for error handling

    Usage:
        with error_context("Failed to save data", show_dialog=True):
            save_data()
    """

    def __init__(
        self,
        error_message: str = "Operation failed",
        show_dialog: bool = False,
        reraise: bool = True,
    ):
        self.error_message = error_message
        self.show_dialog = show_dialog
        self.reraise = reraise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # An exception occurred
            log_exception(logger, exc_val, self.error_message)

            if self.show_dialog:
                if isinstance(exc_val, PasswordManagerException):
                    _show_error_dialog(self.error_message, exc_val.user_message)
                else:
                    _show_error_dialog(self.error_message, "An unexpected error occurred.")

            # Return False to re-raise, True to suppress
            return not self.reraise

        return True


# Export public API
__all__ = [
    # Decorators
    "handle_errors",
    "handle_db_errors",
    "handle_security_errors",
    "handle_validation_errors",
    "retry_on_error",
    "audit_action",
    "monitor_performance",
    # Helpers
    "create_error_response",
    # Context managers
    "error_context",
]
