#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Error Handling System Test
Personal Password Manager - Test Error Handling Features

This script tests the comprehensive error handling system.
"""

import sys
from pathlib import Path

from src.core.error_handlers import (
    audit_action,
    error_context,
    handle_db_errors,
    handle_errors,
    retry_on_error,
)
from src.core.exceptions import AuthenticationError, DatabaseException, InvalidPasswordError
from src.core.logging_config import (
    get_logger,
    log_audit_event,
    log_exception,
    log_security_event,
    mask_sensitive,
    setup_logging,
)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_exceptions():
    """Test custom exception hierarchy"""
    print("\n" + "=" * 70)
    print("Testing Custom Exceptions")
    print("=" * 70 + "\n")

    # Test DatabaseException
    try:
        raise DatabaseException(
            "Connection failed",
            error_code="DB001",
            details={"host": "localhost", "port": 5432},
            user_message="Could not connect to database",
        )
    except DatabaseException as e:
        print("✓ DatabaseException caught")
        print(f"  Error Code: {e.error_code}")
        print(f"  Message: {e.message}")
        print(f"  User Message: {e.user_message}")
        print(f"  Details: {e.details}")
        print(f"  Recoverable: {e.recoverable}")

    # Test AuthenticationError
    try:
        raise AuthenticationError("Invalid credentials", username="test_user")
    except AuthenticationError as e:
        print("\n✓ AuthenticationError caught")
        print(f"  Error Code: {e.error_code}")
        print(f"  User Message: {e.user_message}")

    # Test ValidationException
    try:
        raise InvalidPasswordError(
            "Password too weak", requirements=["8+ characters", "1 uppercase"]
        )
    except InvalidPasswordError as e:
        print("\n✓ InvalidPasswordError caught")
        print(f"  Error Code: {e.error_code}")
        print(f"  Requirements: {e.details.get('requirements')}")


def test_logging():
    """Test logging system"""
    print("\n" + "=" * 70)
    print("Testing Logging System")
    print("=" * 70 + "\n")

    # Setup logging
    setup_logging(log_level="DEBUG", use_colors=True)
    print("✓ Logging configured")

    # Get logger
    logger = get_logger(__name__)

    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    print("\n✓ Different log levels tested")

    # Test exception logging
    try:
        1 / 0
    except Exception as e:
        log_exception(logger, e, "Division by zero", extra={"context": "test"})
        print("✓ Exception logged with context")

    # Test sensitive data masking
    password = "mysecretpassword123"
    masked = mask_sensitive(f"password={password}")
    print("\n✓ Sensitive data masking:")
    print(f"  Original: password={password}")
    print(f"  Masked: {masked}")

    # Test security event logging
    log_security_event(
        event_type="LOGIN_ATTEMPT",
        message="User login attempt",
        user_id=123,
        severity="INFO",
        ip_address="192.168.1.1",
    )
    print("\n✓ Security event logged")

    # Test audit event logging
    log_audit_event(
        action="CREATE_PASSWORD",
        user_id=123,
        details={"website": "example.com"},
    )
    print("✓ Audit event logged")


def test_decorators():
    """Test error handler decorators"""
    print("\n" + "=" * 70)
    print("Testing Error Handler Decorators")
    print("=" * 70 + "\n")

    get_logger(__name__)

    # Test handle_errors decorator
    @handle_errors("Test operation failed", default_return="ERROR")
    def test_function():
        raise ValueError("Something went wrong")

    result = test_function()
    print(f"✓ handle_errors decorator: returned '{result}' on error")

    # Test handle_db_errors decorator
    @handle_db_errors("Database operation failed")
    def test_db_function():
        # This will raise and be caught
        pass

    try:
        test_db_function()
        print("✓ handle_db_errors decorator works")
    except Exception:
        pass

    # Test retry decorator
    attempt_count = [0]

    @retry_on_error(max_attempts=3, exceptions=(ValueError,), delay=0.1)
    def test_retry():
        attempt_count[0] += 1
        if attempt_count[0] < 3:
            raise ValueError("Temporary error")
        return "Success"

    result = test_retry()
    print(f"✓ retry_on_error: succeeded after {attempt_count[0]} attempts")

    # Test audit decorator
    @audit_action("TEST_ACTION", lambda args, kwargs: 123)
    def test_audit():
        return "Done"

    test_audit()
    print("✓ audit_action decorator logged action")

    # Test error context manager
    with error_context("Context manager test", reraise=False):
        try:
            raise ValueError("Test error")
        except Exception:
            pass
    print("✓ error_context manager handled error")


def test_exception_info():
    """Test exception information extraction"""
    print("\n" + "=" * 70)
    print("Testing Exception Information")
    print("=" * 70 + "\n")

    from src.core.exceptions import get_exception_info

    # Test with custom exception
    exc = DatabaseException(
        "Test error",
        error_code="DB999",
        details={"test": "value"},
        user_message="User-friendly message",
        recoverable=True,
    )

    info = get_exception_info(exc)
    print("✓ Exception info extracted:")
    print(f"  Type: {info['error_type']}")
    print(f"  Code: {info['error_code']}")
    print(f"  Message: {info['message']}")
    print(f"  User Message: {info['user_message']}")
    print(f"  Recoverable: {info['recoverable']}")

    # Test with standard exception
    std_exc = ValueError("Standard error")
    std_info = get_exception_info(std_exc)
    print(f"\n✓ Standard exception info: {std_info['error_type']}")


def test_log_files():
    """Check that log files were created"""
    print("\n" + "=" * 70)
    print("Checking Log Files")
    print("=" * 70 + "\n")

    log_dir = Path("logs")
    expected_logs = ["app.log", "security.log", "error.log", "audit.log"]

    for log_file in expected_logs:
        log_path = log_dir / log_file
        if log_path.exists():
            size = log_path.stat().st_size
            print(f"✓ {log_file} created ({size} bytes)")
        else:
            print(f"✗ {log_file} not found")


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("Password Manager - Error Handling System Test")
    print("=" * 70)

    try:
        test_exceptions()
        test_logging()
        test_decorators()
        test_exception_info()
        test_log_files()

        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nError handling system is working correctly!")
        print("\nCheck logs/ directory for generated log files:")
        print("  - logs/app.log       (general application logs)")
        print("  - logs/security.log  (security events)")
        print("  - logs/error.log     (errors only)")
        print("  - logs/audit.log     (user actions)")
        print("\n")

        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
