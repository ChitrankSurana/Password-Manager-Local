# Error Handling & Logging Guide

**Personal Password Manager - Professional Error Handling System**

This guide explains the comprehensive error handling and logging system.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Exception Hierarchy](#exception-hierarchy)
3. [Logging System](#logging-system)
4. [Error Handler Decorators](#error-handler-decorators)
5. [User-Friendly Error Dialogs](#user-friendly-error-dialogs)
6. [Best Practices](#best-practices)
7. [Examples](#examples)

---

## Quick Start

### Basic Usage

```python
from src.core.exceptions import DatabaseException, AuthenticationError
from src.core.logging_config import get_logger, log_exception
from src.core.error_handlers import handle_errors

# Get logger
logger = get_logger(__name__)

# Use custom exceptions
@handle_errors("Failed to load user")
def load_user(user_id):
    if not user_id:
        raise ValidationException("User ID required", field="user_id")

    # Your code...
    logger.info(f"Loaded user {user_id}")

# Log exceptions properly
try:
    risky_operation()
except Exception as e:
    log_exception(logger, e, "Operation failed", {"user_id": 123})
```

---

## Exception Hierarchy

### Structure

```
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
│   ├── SessionExpiredError
│   └── InvalidMasterPasswordError
├── ValidationException
│   ├── InvalidInputError
│   ├── InvalidPasswordError
│   └── InvalidConfigurationError
├── ConfigurationException
│   ├── MissingConfigError
│   └── InvalidConfigValueError
└── ImportExportException
    ├── ImportError
    └── ExportError
```

### Using Custom Exceptions

```python
from src.core.exceptions import (
    DatabaseException,
    AuthenticationError,
    ValidationException
)

# Simple usage
raise AuthenticationError("Invalid credentials")

# With details
raise DatabaseException(
    "Failed to save password",
    error_code="DB002",
    details={"table": "passwords", "operation": "INSERT"},
    user_message="Could not save password. Please try again."
)

# With recovery information
raise ValidationException(
    "Password too weak",
    error_code="VAL002",
    requirements=["8+ characters", "1 uppercase", "1 number"],
    recoverable=True
)
```

### Exception Attributes

Every custom exception has:
- `message`: Technical message (for logs)
- `error_code`: Unique code (e.g., "DB001", "SEC002")
- `details`: Dictionary with additional context
- `user_message`: User-friendly message
- `recoverable`: Whether error is recoverable

```python
try:
    operation()
except PasswordManagerException as e:
    print(f"Error Code: {e.error_code}")
    print(f"Message: {e.message}")
    print(f"User Message: {e.user_message}")
    print(f"Details: {e.details}")
    print(f"Recoverable: {e.recoverable}")
```

---

## Logging System

### Log Files

Four separate log files:
- `logs/app.log` - General application logs
- `logs/security.log` - Security events only
- `logs/error.log` - Errors and exceptions
- `logs/audit.log` - User actions audit trail

### Setup Logging

```python
from src.core.logging_config import setup_logging

# Basic setup (done automatically on import)
setup_logging()

# With options
setup_logging(
    log_level="DEBUG",      # Override config
    use_json=True,          # JSON formatting
    use_colors=True         # Colored console output
)
```

### Get Loggers

```python
from src.core.logging_config import (
    get_logger,             # General logger
    get_security_logger,    # Security events
    get_audit_logger        # Audit trail
)

# Module logger
logger = get_logger(__name__)
logger.info("App started")
logger.warning("Low disk space")
logger.error("Failed to connect", exc_info=True)

# Security logger
security_logger = get_security_logger()
security_logger.warning("Failed login attempt")

# Audit logger
audit_logger = get_audit_logger()
audit_logger.info("User created password")
```

### Log Levels

| Level | When to Use |
|-------|-------------|
| `DEBUG` | Detailed diagnostic info |
| `INFO` | General informational messages |
| `WARNING` | Warning messages (app continues) |
| `ERROR` | Error messages (operation failed) |
| `CRITICAL` | Critical errors (app may crash) |

### Logging Helpers

```python
from src.core.logging_config import (
    log_exception,
    log_security_event,
    log_audit_event,
    mask_sensitive
)

# Log exception with context
try:
    operation()
except Exception as e:
    log_exception(
        logger,
        e,
        "Operation failed",
        extra={"user_id": 123, "context": "startup"}
    )

# Log security event
log_security_event(
    event_type="LOGIN_FAILED",
    message="Failed login attempt for user123",
    user_id=123,
    severity="WARNING",
    ip_address="192.168.1.1"
)

# Log audit event
log_audit_event(
    action="CREATE_PASSWORD",
    user_id=123,
    details={"website": "example.com"}
)

# Mask sensitive data
logger.info(f"Password: {mask_sensitive(password)}")
```

### Sensitive Data Masking

Automatically masks:
- Passwords (`password=***MASKED***`)
- Secrets (`secret=***MASKED***`)
- Tokens (`token=***MASKED***`)
- API keys (`api_key=***MASKED***`)
- Credit card numbers
- Email addresses (partial)

```python
# These will be masked automatically
logger.info("password=mysecret123")  # → password=***MASKED***
logger.info("api_key=abc123xyz")     # → api_key=***MASKED***
logger.info("email@example.com")     # → ***@example.com
```

---

## Error Handler Decorators

### Generic Error Handler

```python
from src.core.error_handlers import handle_errors

@handle_errors(
    error_message="Failed to save settings",
    show_dialog=True,      # Show GUI error dialog
    reraise=False,         # Don't re-raise exception
    default_return=None,   # Return value on error
    log_level="ERROR"
)
def save_settings(settings):
    # Your code...
    pass
```

### Database Error Handler

```python
from src.core.error_handlers import handle_db_errors

@handle_db_errors("Failed to create user", show_dialog=True)
def create_user(username, password):
    # Database operations...
    pass
```

### Security Error Handler

```python
from src.core.error_handlers import handle_security_errors

@handle_security_errors("Encryption failed", show_dialog=True)
def encrypt_password(password, key):
    # Encryption code...
    pass
```

### Validation Error Handler

```python
from src.core.error_handlers import handle_validation_errors

@handle_validation_errors("Invalid password format", show_dialog=True)
def validate_password(password):
    if len(password) < 8:
        raise InvalidPasswordError(
            "Password too short",
            requirements=["Minimum 8 characters"]
        )
```

### Retry Decorator

```python
from src.core.error_handlers import retry_on_error
from src.core.exceptions import DatabaseException

@retry_on_error(
    max_attempts=3,
    exceptions=(DatabaseException, ConnectionError),
    delay=1.0,
    backoff=2.0  # 1s, 2s, 4s delays
)
def connect_to_database():
    # Connection code...
    pass
```

### Audit Decorator

```python
from src.core.error_handlers import audit_action

@audit_action(
    action="CREATE_PASSWORD",
    get_user_id=lambda args, kwargs: kwargs.get("user_id")
)
def create_password(user_id, website, password):
    # Your code...
    pass
```

### Performance Monitor

```python
from src.core.error_handlers import monitor_performance

@monitor_performance(threshold_ms=500)
def slow_operation():
    # Logs warning if takes > 500ms
    pass
```

### Error Context Manager

```python
from src.core.error_handlers import error_context

with error_context("Failed to save data", show_dialog=True):
    save_data()
    process_data()
    cleanup()
```

---

## User-Friendly Error Dialogs

### Simple Error Dialog

```python
from src.gui.error_dialog import show_error

show_error(
    title="Save Failed",
    message="Could not save your password."
)
```

### Error with Details

```python
show_error(
    title="Database Error",
    message="Failed to connect to the database.",
    details="Connection timeout after 30 seconds\nFile: password_manager.db",
    suggestions=[
        "Check if database file exists",
        "Verify file permissions",
        "Restore from backup"
    ]
)
```

### Warning Dialog

```python
from src.gui.error_dialog import show_warning

show_warning(
    title="Weak Password",
    message="Your password is weak.",
    suggestions=["Use at least 12 characters", "Include special characters"]
)
```

### Critical Error

```python
from src.gui.error_dialog import show_critical_error

show_critical_error(
    title="Fatal Error",
    message="Application cannot continue.",
    details="Corrupted database file detected",
    suggestions=["Restore from backup", "Contact support"]
)
```

### Exception Dialog

```python
from src.gui.error_dialog import show_exception_dialog

try:
    operation()
except Exception as e:
    show_exception_dialog(e, title="Operation Failed")
```

---

## Best Practices

### 1. Always Use Custom Exceptions

```python
# ✗ Bad
raise Exception("User not found")

# ✓ Good
raise RecordNotFoundError("User not found", record_type="user")
```

### 2. Provide User-Friendly Messages

```python
# ✗ Bad
raise DatabaseException("Foreign key constraint violated")

# ✓ Good
raise DatabaseException(
    message="Foreign key constraint violated on users table",
    user_message="This user has associated data. Delete the data first."
)
```

### 3. Use Appropriate Log Levels

```python
logger.debug("Entering function")       # Development only
logger.info("User logged in")           # Normal operations
logger.warning("Disk space low")        # Potential issues
logger.error("Failed to save", exc_info=True)  # Errors
logger.critical("Database corrupted")   # Critical failures
```

### 4. Include Context in Logs

```python
# ✗ Bad
logger.error("Operation failed")

# ✓ Good
logger.error(
    "Failed to save password",
    extra={
        "user_id": user_id,
        "website": website,
        "operation": "INSERT"
    }
)
```

### 5. Use Decorators for Consistent Handling

```python
# ✗ Bad
def save_data(data):
    try:
        # operation
        pass
    except Exception as e:
        logger.error(f"Failed: {e}")
        messagebox.showerror("Error", "Failed")

# ✓ Good
@handle_errors("Failed to save data", show_dialog=True)
def save_data(data):
    # operation
    pass
```

### 6. Mask Sensitive Data

```python
# ✗ Bad
logger.info(f"User password: {password}")

# ✓ Good
logger.info(f"User password: {mask_sensitive(password)}")
```

### 7. Use Audit Logging for Security Events

```python
from src.core.logging_config import log_audit_event

log_audit_event(
    action="DELETE_PASSWORD",
    user_id=user_id,
    details={"password_id": pwd_id, "website": website}
)
```

---

## Examples

### Complete Example: Database Operation

```python
from src.core.exceptions import DatabaseException, RecordNotFoundError
from src.core.logging_config import get_logger, log_exception
from src.core.error_handlers import handle_db_errors, audit_action

logger = get_logger(__name__)

@handle_db_errors("Failed to create password", show_dialog=True)
@audit_action("CREATE_PASSWORD", lambda args, kwargs: args[1])
def create_password(self, user_id, website, password):
    """
    Create a new password entry

    Args:
        user_id: User ID
        website: Website name
        password: Password to store

    Raises:
        DatabaseException: If database operation fails
    """
    logger.info(f"Creating password for user {user_id}, website {website}")

    try:
        # Database operation
        cursor.execute(
            "INSERT INTO passwords (user_id, website, password) VALUES (?, ?, ?)",
            (user_id, website, password)
        )
        conn.commit()

        logger.info(f"Password created successfully: ID={cursor.lastrowid}")
        return cursor.lastrowid

    except sqlite3.IntegrityError as e:
        raise DatabaseIntegrityError(
            f"Integrity constraint violated: {e}",
            constraint="unique_user_website",
            details={"user_id": user_id, "website": website}
        )
```

### Complete Example: Security Operation

```python
from src.core.exceptions import EncryptionError, InvalidMasterPasswordError
from src.core.logging_config import get_security_logger
from src.core.error_handlers import handle_security_errors, retry_on_error

security_logger = get_security_logger()

@handle_security_errors("Encryption failed", show_dialog=True)
@retry_on_error(max_attempts=2, exceptions=(EncryptionError,))
def encrypt_password(password, master_password):
    """
    Encrypt a password

    Args:
        password: Password to encrypt
        master_password: Master password for encryption

    Returns:
        Encrypted password bytes

    Raises:
        EncryptionError: If encryption fails
        InvalidMasterPasswordError: If master password is invalid
    """
    security_logger.info("Encrypting password")

    try:
        # Derive key from master password
        key = derive_key(master_password)

        # Encrypt
        encrypted = aes_encrypt(password, key)

        security_logger.info("Password encrypted successfully")
        return encrypted

    except ValueError as e:
        raise EncryptionError(
            f"Encryption failed: {e}",
            details={"algorithm": "AES-256-CBC"}
        )
```

---

## Summary

### Key Components

| Component | Purpose | File |
|-----------|---------|------|
| Exceptions | Structured error types | `src/core/exceptions.py` |
| Logging | Multi-file logging system | `src/core/logging_config.py` |
| Decorators | Consistent error handling | `src/core/error_handlers.py` |
| Dialogs | User-friendly error UI | `src/gui/error_dialog.py` |

### Quick Reference

```python
# Import exceptions
from src.core.exceptions import DatabaseException, AuthenticationError

# Import logging
from src.core.logging_config import get_logger, log_exception

# Import decorators
from src.core.error_handlers import handle_errors, handle_db_errors

# Import dialogs
from src.gui.error_dialog import show_error

# Use them together
logger = get_logger(__name__)

@handle_errors("Operation failed", show_dialog=True)
def my_function():
    try:
        # Your code
        pass
    except SomeError as e:
        log_exception(logger, e, "Detailed error message")
        raise DatabaseException("User-friendly message")
```

---

**Your application now has enterprise-grade error handling!** 🎉
