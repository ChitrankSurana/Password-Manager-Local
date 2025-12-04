#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom Exception Hierarchy
Personal Password Manager - Structured Exception Handling

This module defines a comprehensive exception hierarchy for the password manager.
All custom exceptions inherit from PasswordManagerException base class.

Usage:
    from src.core.exceptions import DatabaseException, AuthenticationError

    try:
        # Some database operation
        pass
    except DatabaseException as e:
        logger.error(f"Database error: {e}")
        # Handle database-specific error

Exception Hierarchy:
    PasswordManagerException (base)
    ├── DatabaseException
    │   ├── DatabaseConnectionError
    │   ├── DatabaseIntegrityError
    │   ├── DatabaseMigrationError
    │   └── RecordNotFoundError
    ├── SecurityException
    │   ├── AuthenticationError
    │   ├── AuthorizationError
    │   ├── EncryptionError
    │   ├── DecryptionError
    │   ├── AccountLockedError
    │   └── SessionExpiredError
    ├── ValidationException
    │   ├── InvalidInputError
    │   ├── InvalidPasswordError
    │   └── InvalidConfigurationError
    └── ConfigurationException
        ├── MissingConfigError
        └── InvalidConfigValueError
"""

from typing import Any, Dict, Optional

# =============================================================================
# BASE EXCEPTION
# =============================================================================


class PasswordManagerException(Exception):
    """
    Base exception for all Password Manager exceptions

    All custom exceptions should inherit from this class.
    Provides common functionality for error handling and logging.

    Attributes:
        message: Human-readable error message
        error_code: Unique error code for categorization
        details: Additional context about the error
        user_message: User-friendly message (if different from technical message)
        recoverable: Whether the error is recoverable
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recoverable: bool = False,
    ):
        """
        Initialize base exception

        Args:
            message: Technical error message (for logs)
            error_code: Unique error code (e.g., "DB001", "SEC002")
            details: Additional context as dictionary
            user_message: User-friendly message (shown in UI)
            recoverable: Whether user can recover from this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.user_message = user_message or message
        self.recoverable = recoverable

    def __str__(self) -> str:
        """String representation of exception"""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary (useful for API responses)

        Returns:
            Dictionary with error information
        """
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "user_message": self.user_message,
            "details": self.details,
            "recoverable": self.recoverable,
        }


# =============================================================================
# DATABASE EXCEPTIONS
# =============================================================================


class DatabaseException(PasswordManagerException):
    """Base exception for all database-related errors"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code=kwargs.pop("error_code", "DB000"),
            user_message=kwargs.pop("user_message", "A database error occurred. Please try again."),
            **kwargs,
        )


class DatabaseConnectionError(DatabaseException):
    """Exception raised when database connection fails"""

    def __init__(self, message: str = "Failed to connect to database", **kwargs):
        super().__init__(
            message,
            error_code="DB001",
            user_message="Unable to connect to the database. Please check if the database file exists.",
            recoverable=True,
            **kwargs,
        )


class DatabaseIntegrityError(DatabaseException):
    """Exception raised when database integrity constraint is violated"""

    def __init__(
        self,
        message: str = "Database integrity constraint violated",
        constraint: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.pop("details", {})
        if constraint:
            details["constraint"] = constraint

        super().__init__(
            message,
            error_code="DB002",
            user_message="This operation would violate data integrity rules.",
            details=details,
            recoverable=False,
            **kwargs,
        )


class DatabaseMigrationError(DatabaseException):
    """Exception raised when database migration fails"""

    def __init__(
        self,
        message: str = "Database migration failed",
        from_version: Optional[int] = None,
        to_version: Optional[int] = None,
        **kwargs,
    ):
        details = kwargs.pop("details", {})
        if from_version:
            details["from_version"] = from_version
        if to_version:
            details["to_version"] = to_version

        super().__init__(
            message,
            error_code="DB003",
            user_message="Failed to upgrade database. Please restore from backup.",
            details=details,
            recoverable=False,
            **kwargs,
        )


class RecordNotFoundError(DatabaseException):
    """Exception raised when a database record is not found"""

    def __init__(
        self, message: str = "Record not found", record_type: Optional[str] = None, **kwargs
    ):
        details = kwargs.pop("details", {})
        if record_type:
            details["record_type"] = record_type

        super().__init__(
            message,
            error_code="DB004",
            user_message="The requested item was not found.",
            details=details,
            recoverable=True,
            **kwargs,
        )


# =============================================================================
# SECURITY EXCEPTIONS
# =============================================================================


class SecurityException(PasswordManagerException):
    """Base exception for all security-related errors"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code=kwargs.pop("error_code", "SEC000"),
            user_message=kwargs.pop("user_message", "A security error occurred."),
            **kwargs,
        )


class AuthenticationError(SecurityException):
    """Exception raised when authentication fails"""

    def __init__(
        self,
        message: str = "Authentication failed",
        username: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.pop("details", {})
        if username:
            details["username"] = username

        super().__init__(
            message,
            error_code="SEC001",
            user_message="Invalid username or password.",
            details=details,
            recoverable=True,
            **kwargs,
        )


class AuthorizationError(SecurityException):
    """Exception raised when user lacks required permissions"""

    def __init__(
        self, message: str = "Access denied", required_permission: Optional[str] = None, **kwargs
    ):
        details = kwargs.pop("details", {})
        if required_permission:
            details["required_permission"] = required_permission

        super().__init__(
            message,
            error_code="SEC002",
            user_message="You don't have permission to perform this action.",
            details=details,
            recoverable=False,
            **kwargs,
        )


class EncryptionError(SecurityException):
    """Exception raised when encryption fails"""

    def __init__(self, message: str = "Encryption failed", **kwargs):
        super().__init__(
            message,
            error_code="SEC003",
            user_message="Failed to encrypt data. Please try again.",
            details=kwargs.pop("details", {}),
            recoverable=True,
            **kwargs,
        )


class DecryptionError(SecurityException):
    """Exception raised when decryption fails"""

    def __init__(self, message: str = "Decryption failed", **kwargs):
        super().__init__(
            message,
            error_code="SEC004",
            user_message="Failed to decrypt data. The password may be incorrect.",
            details=kwargs.pop("details", {}),
            recoverable=True,
            **kwargs,
        )


class AccountLockedError(SecurityException):
    """Exception raised when user account is locked"""

    def __init__(
        self,
        message: str = "Account is locked",
        locked_until: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.pop("details", {})
        if locked_until:
            details["locked_until"] = locked_until

        super().__init__(
            message,
            error_code="SEC005",
            user_message="Your account is locked due to too many failed login attempts. Please try again later.",
            details=details,
            recoverable=True,
            **kwargs,
        )


class SessionExpiredError(SecurityException):
    """Exception raised when user session has expired"""

    def __init__(self, message: str = "Session expired", **kwargs):
        super().__init__(
            message,
            error_code="SEC006",
            user_message="Your session has expired. Please log in again.",
            details=kwargs.pop("details", {}),
            recoverable=True,
            **kwargs,
        )


class InvalidMasterPasswordError(SecurityException):
    """Exception raised when master password is incorrect"""

    def __init__(self, message: str = "Invalid master password", **kwargs):
        super().__init__(
            message,
            error_code="SEC007",
            user_message="Incorrect master password.",
            details=kwargs.pop("details", {}),
            recoverable=True,
            **kwargs,
        )


# =============================================================================
# VALIDATION EXCEPTIONS
# =============================================================================


class ValidationException(PasswordManagerException):
    """Base exception for all validation errors"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code=kwargs.pop("error_code", "VAL000"),
            user_message=kwargs.pop("user_message", "Invalid input provided."),
            **kwargs,
        )


class InvalidInputError(ValidationException):
    """Exception raised when user input is invalid"""

    def __init__(self, message: str = "Invalid input", field: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if field:
            details["field"] = field

        super().__init__(
            message,
            error_code="VAL001",
            user_message=f"Invalid input{': ' + field if field else ''}. Please check your input.",
            details=details,
            recoverable=True,
            **kwargs,
        )


class InvalidPasswordError(ValidationException):
    """Exception raised when password doesn't meet requirements"""

    def __init__(
        self,
        message: str = "Password doesn't meet requirements",
        requirements: Optional[list] = None,
        **kwargs,
    ):
        details = kwargs.pop("details", {})
        if requirements:
            details["requirements"] = requirements

        user_msg = "Password doesn't meet requirements."
        if requirements:
            user_msg += " Required: " + ", ".join(requirements)

        super().__init__(
            message,
            error_code="VAL002",
            user_message=user_msg,
            details=details,
            recoverable=True,
            **kwargs,
        )


class InvalidConfigurationError(ValidationException):
    """Exception raised when configuration is invalid"""

    def __init__(
        self, message: str = "Invalid configuration", config_key: Optional[str] = None, **kwargs
    ):
        details = kwargs.pop("details", {})
        if config_key:
            details["config_key"] = config_key

        super().__init__(
            message,
            error_code="VAL003",
            user_message="Invalid configuration detected. Please check settings.",
            details=details,
            recoverable=False,
            **kwargs,
        )


# =============================================================================
# CONFIGURATION EXCEPTIONS
# =============================================================================


class ConfigurationException(PasswordManagerException):
    """Base exception for configuration errors"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code=kwargs.pop("error_code", "CFG000"),
            user_message=kwargs.pop("user_message", "Configuration error."),
            **kwargs,
        )


class MissingConfigError(ConfigurationException):
    """Exception raised when required configuration is missing"""

    def __init__(
        self, message: str = "Required configuration missing", config_key: str = None, **kwargs
    ):
        details = kwargs.pop("details", {})
        if config_key:
            details["config_key"] = config_key

        user_msg = "Required configuration is missing."
        if config_key:
            user_msg += f" Please set {config_key}."

        super().__init__(
            message,
            error_code="CFG001",
            user_message=user_msg,
            details=details,
            recoverable=False,
            **kwargs,
        )


class InvalidConfigValueError(ConfigurationException):
    """Exception raised when configuration value is invalid"""

    def __init__(
        self,
        message: str = "Invalid configuration value",
        config_key: Optional[str] = None,
        expected_type: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.pop("details", {})
        if config_key:
            details["config_key"] = config_key
        if expected_type:
            details["expected_type"] = expected_type

        super().__init__(
            message,
            error_code="CFG002",
            user_message=f"Invalid configuration value{': ' + config_key if config_key else ''}.",
            details=details,
            recoverable=False,
            **kwargs,
        )


# =============================================================================
# IMPORT/EXPORT EXCEPTIONS
# =============================================================================


class ImportExportException(PasswordManagerException):
    """Base exception for import/export errors"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code=kwargs.pop("error_code", "IE000"),
            user_message=kwargs.pop("user_message", "Import/export error occurred."),
            **kwargs,
        )


class ImportError(ImportExportException):
    """Exception raised when data import fails"""

    def __init__(self, message: str = "Import failed", file_path: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if file_path:
            details["file_path"] = file_path

        super().__init__(
            message,
            error_code="IE001",
            user_message="Failed to import data. Please check the file format.",
            details=details,
            recoverable=True,
            **kwargs,
        )


class ExportError(ImportExportException):
    """Exception raised when data export fails"""

    def __init__(self, message: str = "Export failed", file_path: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if file_path:
            details["file_path"] = file_path

        super().__init__(
            message,
            error_code="IE002",
            user_message="Failed to export data. Please check file permissions.",
            details=details,
            recoverable=True,
            **kwargs,
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_exception_info(exception: Exception) -> Dict[str, Any]:
    """
    Extract information from an exception

    Args:
        exception: Exception instance

    Returns:
        Dictionary with exception information
    """
    if isinstance(exception, PasswordManagerException):
        return exception.to_dict()

    # For standard Python exceptions
    return {
        "error_type": type(exception).__name__,
        "error_code": None,
        "message": str(exception),
        "user_message": "An unexpected error occurred.",
        "details": {},
        "recoverable": False,
    }


# Export all exception classes
__all__ = [
    # Base
    "PasswordManagerException",
    # Database
    "DatabaseException",
    "DatabaseConnectionError",
    "DatabaseIntegrityError",
    "DatabaseMigrationError",
    "RecordNotFoundError",
    # Security
    "SecurityException",
    "AuthenticationError",
    "AuthorizationError",
    "EncryptionError",
    "DecryptionError",
    "AccountLockedError",
    "SessionExpiredError",
    "InvalidMasterPasswordError",
    # Validation
    "ValidationException",
    "InvalidInputError",
    "InvalidPasswordError",
    "InvalidConfigurationError",
    # Configuration
    "ConfigurationException",
    "MissingConfigError",
    "InvalidConfigValueError",
    # Import/Export
    "ImportExportException",
    "ImportError",
    "ExportError",
    # Helpers
    "get_exception_info",
]
