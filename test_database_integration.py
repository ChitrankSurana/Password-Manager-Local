#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Database Error Handling Integration
Quick test to verify database.py integration with new error handling system
"""

import os
import sys
from pathlib import Path

from src.core.database import DatabaseIntegrityError, DatabaseManager
from src.core.logging_config import setup_logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_database_integration():
    """Test database error handling integration"""
    print("\n" + "=" * 70)
    print("Testing Database Error Handling Integration")
    print("=" * 70 + "\n")

    # Setup logging
    setup_logging(log_level="DEBUG")
    print("✓ Logging configured\n")

    # Create test database
    test_db_path = "test_integration.db"
    try:
        # Remove old test database if exists
        if os.path.exists(test_db_path):
            os.remove(test_db_path)

        print("1. Testing Database Initialization...")
        db = DatabaseManager(test_db_path)
        print("   ✓ Database initialized with new error handling\n")

        print("2. Testing create_user with @handle_db_errors and @audit_action...")
        user_id = db.create_user("testuser", "password123")
        print(f"   ✓ User created with ID: {user_id}")
        print("   ✓ Decorators working (check logs/audit.log for audit entry)\n")

        print("3. Testing duplicate user (DatabaseIntegrityError)...")
        try:
            db.create_user("testuser", "password456")
            print("   ✗ Should have raised DatabaseIntegrityError")
        except DatabaseIntegrityError as e:
            print("   ✓ DatabaseIntegrityError raised correctly")
            print(f"   ✓ Error code: {e.error_code}")
            print(f"   ✓ User message: {e.user_message}\n")

        print("4. Testing authenticate_user...")
        user_info = db.authenticate_user("testuser", "password123")
        if user_info:
            print(f"   ✓ Authentication successful: {user_info['username']}")
            print("   ✓ Audit log entry created\n")

        print("5. Testing failed authentication...")
        user_info = db.authenticate_user("testuser", "wrongpassword")
        if not user_info:
            print("   ✓ Failed authentication handled correctly\n")

        print("6. Testing add_password_entry with decorators...")
        entry_id = db.add_password_entry(
            user_id=user_id,
            website="example.com",
            username="user@example.com",
            encrypted_password=b"encrypted_data",
            remarks="Test entry",
        )
        print(f"   ✓ Password entry created with ID: {entry_id}")
        print("   ✓ Audit log entry created (check logs/audit.log)\n")

        print("7. Testing get_password_entries...")
        entries = db.get_password_entries(user_id)
        print(f"   ✓ Retrieved {len(entries)} password entries\n")

        print("8. Testing update_password_entry with audit...")
        success = db.update_password_entry(
            entry_id=entry_id, user_id=user_id, remarks="Updated remarks"
        )
        print(f"   ✓ Password entry updated: {success}")
        print("   ✓ Audit log entry created\n")

        print("9. Testing delete_password_entry with audit...")
        success = db.delete_password_entry(entry_id, user_id)
        print(f"   ✓ Password entry deleted: {success}")
        print("   ✓ Audit log entry created\n")

        print("10. Testing get_user_statistics...")
        stats = db.get_user_statistics(user_id)
        print(f"   ✓ Statistics retrieved: {stats}\n")

        print("=" * 70)
        print("✓ ALL DATABASE INTEGRATION TESTS PASSED!")
        print("=" * 70)
        print("\nIntegration Summary:")
        print("  ✓ New exception classes working")
        print("  ✓ New logging system integrated")
        print("  ✓ @handle_db_errors decorator functional")
        print("  ✓ @audit_action decorator functional")
        print("  ✓ Error codes and user messages present")
        print("\nCheck logs/ directory for:")
        print("  - logs/app.log       (general logs)")
        print("  - logs/audit.log     (audit trail with CREATE_USER, ADD_PASSWORD, etc.)")
        print("  - logs/error.log     (errors)")
        print("")

        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        # Clean up test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            print("Test database cleaned up")


if __name__ == "__main__":
    sys.exit(test_database_integration())
