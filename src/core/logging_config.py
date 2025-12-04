#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Structured Logging Configuration
Personal Password Manager - Comprehensive Logging System

This module provides a centralized logging configuration with:
- Multiple log files (app, security, error, audit)
- Rotating file handlers
- Console and file output
- Sensitive data masking
- JSON formatting option
- Different log levels per handler

Usage:
    from src.core.logging_config import setup_logging, get_logger

    # Setup logging (call once at app startup)
    setup_logging()

    # Get logger for your module
    logger = get_logger(__name__)

    # Use logger
    logger.info("Application started")
    logger.warning("Low disk space")
    logger.error("Failed to connect", exc_info=True)
    logger.debug("User input: %s", mask_sensitive(user_input))
"""

import json
import logging
import logging.handlers
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Import configuration
try:
    from .config import config
except ImportError:
    # Fallback if config not available
    class FallbackConfig:
        LOG_LEVEL = "INFO"
        LOG_DIR = Path("logs")
        LOG_FILE_APP = "logs/app.log"
        LOG_FILE_SECURITY = "logs/security.log"
        LOG_FILE_ERROR = "logs/error.log"
        LOG_FILE_AUDIT = "logs/audit.log"
        LOG_MAX_BYTES = 10485760  # 10MB
        LOG_BACKUP_COUNT = 5
        LOG_TO_CONSOLE = True
        LOG_TO_FILE = True
        LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
        MASK_PASSWORDS_IN_LOGS = True
        MASK_ENCRYPTION_KEYS_IN_LOGS = True

    config = FallbackConfig()


# =============================================================================
# SENSITIVE DATA MASKING
# =============================================================================


class SensitiveDataFilter(logging.Filter):
    """
    Filter to mask sensitive data in log messages

    Masks passwords, encryption keys, tokens, and other sensitive data
    before they are written to log files.
    """

    # Patterns to mask (case-insensitive)
    SENSITIVE_PATTERNS = [
        (r"password['\"]?\s*[:=]\s*['\"]?([^'\"}\s,]+)", "password=***MASKED***"),
        (r"passwd['\"]?\s*[:=]\s*['\"]?([^'\"}\s,]+)", "passwd=***MASKED***"),
        (r"secret['\"]?\s*[:=]\s*['\"]?([^'\"}\s,]+)", "secret=***MASKED***"),
        (r"token['\"]?\s*[:=]\s*['\"]?([^'\"}\s,]+)", "token=***MASKED***"),
        (r"api[_-]?key['\"]?\s*[:=]\s*['\"]?([^'\"}\s,]+)", "api_key=***MASKED***"),
        (r"auth['\"]?\s*[:=]\s*['\"]?([^'\"}\s,]+)", "auth=***MASKED***"),
        (r"key['\"]?\s*[:=]\s*['\"]?([^'\"}\s,]+)", "key=***MASKED***"),
        # Credit card numbers
        (r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", "****-****-****-****"),
        # Email addresses (partial masking)
        (r"([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", r"***@\2"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter and mask sensitive data from log record

        Args:
            record: Log record to filter

        Returns:
            True (record is always kept, just modified)
        """
        if config.MASK_PASSWORDS_IN_LOGS or config.MASK_ENCRYPTION_KEYS_IN_LOGS:
            # Mask message
            record.msg = self.mask_sensitive_data(str(record.msg))

            # Mask args if present
            if record.args:
                if isinstance(record.args, dict):
                    record.args = {
                        k: self.mask_sensitive_data(str(v)) for k, v in record.args.items()
                    }
                elif isinstance(record.args, tuple):
                    record.args = tuple(self.mask_sensitive_data(str(arg)) for arg in record.args)

        return True

    def mask_sensitive_data(self, text: str) -> str:
        """
        Mask sensitive data in text

        Args:
            text: Text to mask

        Returns:
            Text with sensitive data masked
        """
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text


# =============================================================================
# JSON FORMATTER
# =============================================================================


class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs log records as JSON

    Useful for structured logging and log aggregation systems.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id
        if hasattr(record, "error_code"):
            log_data["error_code"] = record.error_code

        return json.dumps(log_data)


# =============================================================================
# CUSTOM FORMATTERS
# =============================================================================


class ColoredFormatter(logging.Formatter):
    """
    Formatter that adds colors to console output

    Different colors for different log levels (only for console output).
    """

    # Color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors

        Args:
            record: Log record to format

        Returns:
            Colored log string
        """
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"

        # Format the record
        result = super().format(record)

        # Reset levelname (don't modify the original record)
        record.levelname = levelname

        return result


# =============================================================================
# LOGGING SETUP
# =============================================================================


def setup_logging(
    log_level: Optional[str] = None,
    use_json: bool = False,
    use_colors: bool = True,
) -> None:
    """
    Setup comprehensive logging configuration

    Creates multiple log files with rotating handlers:
    - app.log: General application logs
    - security.log: Security-related events
    - error.log: Errors and exceptions only
    - audit.log: User actions and audit trail

    Args:
        log_level: Override default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Use JSON formatting for file logs
        use_colors: Use colored output for console (if supported)
    """
    # Determine log level
    level_str = log_level or config.LOG_LEVEL
    level = getattr(logging, level_str.upper(), logging.INFO)

    # Ensure log directory exists
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create formatters
    if use_json:
        file_formatter = JSONFormatter()
    else:
        file_formatter = logging.Formatter(config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT)

    if use_colors and sys.stdout.isatty():
        console_formatter = ColoredFormatter(config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT)
    else:
        console_formatter = logging.Formatter(config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT)

    # Create sensitive data filter
    sensitive_filter = SensitiveDataFilter()

    # =============================================================================
    # CONSOLE HANDLER
    # =============================================================================

    if config.LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(sensitive_filter)
        root_logger.addHandler(console_handler)

    # =============================================================================
    # FILE HANDLERS
    # =============================================================================

    if config.LOG_TO_FILE:
        # APP LOG - General application logs
        app_handler = logging.handlers.RotatingFileHandler(
            config.LOG_FILE_APP,
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        app_handler.setLevel(level)
        app_handler.setFormatter(file_formatter)
        app_handler.addFilter(sensitive_filter)
        root_logger.addHandler(app_handler)

        # SECURITY LOG - Security events only
        security_handler = logging.handlers.RotatingFileHandler(
            config.LOG_FILE_SECURITY,
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        security_handler.setLevel(logging.INFO)
        security_handler.setFormatter(file_formatter)
        security_handler.addFilter(sensitive_filter)
        security_handler.addFilter(lambda record: "security" in record.name.lower())
        root_logger.addHandler(security_handler)

        # ERROR LOG - Errors and exceptions only
        error_handler = logging.handlers.RotatingFileHandler(
            config.LOG_FILE_ERROR,
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        error_handler.addFilter(sensitive_filter)
        root_logger.addHandler(error_handler)

        # AUDIT LOG - User actions and audit trail
        audit_handler = logging.handlers.RotatingFileHandler(
            config.LOG_FILE_AUDIT,
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(file_formatter)
        audit_handler.addFilter(lambda record: "audit" in record.name.lower())
        root_logger.addHandler(audit_handler)

    # Log startup message
    root_logger.info(
        f"Logging configured: level={level_str}, console={config.LOG_TO_CONSOLE}, "
        f"file={config.LOG_TO_FILE}, json={use_json}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for the specified name

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Message")
    """
    return logging.getLogger(name)


def get_security_logger() -> logging.Logger:
    """
    Get logger for security events

    Returns:
        Security logger instance
    """
    return logging.getLogger("security")


def get_audit_logger() -> logging.Logger:
    """
    Get logger for audit events

    Returns:
        Audit logger instance
    """
    return logging.getLogger("audit")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def mask_sensitive(text: str) -> str:
    """
    Mask sensitive data in text (for manual masking)

    Args:
        text: Text to mask

    Returns:
        Masked text

    Example:
        logger.info("Password: %s", mask_sensitive(password))
    """
    filter_instance = SensitiveDataFilter()
    return filter_instance.mask_sensitive_data(str(text))


def log_exception(
    logger: logging.Logger,
    exception: Exception,
    message: str = "An error occurred",
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an exception with full stack trace

    Args:
        logger: Logger instance
        exception: Exception to log
        message: Custom message
        extra: Extra fields to include

    Example:
        try:
            risky_operation()
        except Exception as e:
            log_exception(logger, e, "Operation failed", {"user_id": 123})
    """
    extra_fields = extra or {}

    # Add exception type and message to extra
    extra_fields["exception_type"] = type(exception).__name__
    extra_fields["exception_message"] = str(exception)

    # Log with full stack trace
    logger.error(message, exc_info=True, extra=extra_fields)


def log_security_event(
    event_type: str,
    message: str,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    severity: str = "INFO",
    **kwargs,
) -> None:
    """
    Log a security event

    Args:
        event_type: Type of security event (LOGIN, LOGOUT, etc.)
        message: Event message
        user_id: User ID if applicable
        session_id: Session ID if applicable
        severity: Log level (INFO, WARNING, ERROR)
        **kwargs: Additional fields

    Example:
        log_security_event(
            "LOGIN_FAILED",
            "Failed login attempt",
            user_id=123,
            ip_address="192.168.1.1"
        )
    """
    security_logger = get_security_logger()

    # Prepare extra fields
    extra = {
        "event_type": event_type,
        "user_id": user_id,
        "session_id": session_id,
        **kwargs,
    }

    # Log at appropriate level
    level = getattr(logging, severity.upper(), logging.INFO)
    security_logger.log(level, message, extra=extra)


def log_audit_event(
    action: str,
    user_id: int,
    details: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> None:
    """
    Log an audit event (user action)

    Args:
        action: Action performed (CREATE_PASSWORD, DELETE_PASSWORD, etc.)
        user_id: User who performed the action
        details: Additional details
        **kwargs: Additional fields

    Example:
        log_audit_event(
            "CREATE_PASSWORD",
            user_id=123,
            details={"website": "example.com"}
        )
    """
    audit_logger = get_audit_logger()

    # Prepare extra fields
    extra = {
        "action": action,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        **kwargs,
    }

    if details:
        extra["details"] = details

    audit_logger.info(f"User action: {action}", extra=extra)


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

# Auto-setup logging when module is imported (can be disabled by calling setup_logging manually)
_logging_initialized = False


def ensure_logging_initialized():
    """Ensure logging is initialized (called automatically)"""
    global _logging_initialized
    if not _logging_initialized:
        try:
            setup_logging()
            _logging_initialized = True
        except Exception as e:
            print(f"Warning: Failed to initialize logging: {e}", file=sys.stderr)


# Initialize on import
ensure_logging_initialized()


# Export public API
__all__ = [
    "setup_logging",
    "get_logger",
    "get_security_logger",
    "get_audit_logger",
    "mask_sensitive",
    "log_exception",
    "log_security_event",
    "log_audit_event",
    "JSONFormatter",
    "ColoredFormatter",
    "SensitiveDataFilter",
]
