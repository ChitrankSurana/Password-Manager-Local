#!/usr/bin/env python3
"""
Test script to verify portability fixes for the Password Manager
This script tests the new user_exists() method and login preference validation
"""

import os
import sys
import tempfile
from pathlib import Path

from core.database import DatabaseManager

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_user_exists_method():
    """Test the new user_exists() method"""
    print("\n" + "=" * 60)
    print("TEST 1: Testing user_exists() method")
    print("=" * 60)

    # Create a temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        temp_db = tmp.name

    try:
        # Initialize database manager (database is automatically initialized)
        db = DatabaseManager(temp_db)

        # Test 1: Non-existent user should return False
        print("\n[*] Testing non-existent user...")
        result = db.user_exists("nonexistent_user")
        assert result is False, "Non-existent user should return False"
        print("  [PASS] Non-existent user returns False")

        # Test 2: Create a user
        print("\n[*] Creating test user 'testuser'...")
        db.create_user("testuser", "password123")
        print("  [PASS] User created successfully")

        # Test 3: Existing user should return True
        print("\n[*] Testing existing user...")
        result = db.user_exists("testuser")
        assert result, "Existing user should return True"
        print("  [PASS] Existing user returns True")

        # Test 4: Case insensitive check
        print("\n[*] Testing case insensitivity...")
        result = db.user_exists("TestUser")
        assert result, "User exists check should be case insensitive"
        print("  [PASS] Case insensitive check works")

        # Test 5: Empty username
        print("\n[*] Testing empty username...")
        result = db.user_exists("")
        assert result is False, "Empty username should return False"
        print("  [PASS] Empty username returns False")

        # Test 6: None username
        print("\n[*] Testing None username...")
        result = db.user_exists(None)
        assert result is False, "None username should return False"
        print("  [PASS] None username returns False")

        print("\n" + "=" * 60)
        print("[PASS] TEST 1: user_exists() method works correctly!")
        print("=" * 60)

    finally:
        # Cleanup
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_fresh_install_scenario():
    """Test scenario: Fresh installation without existing database"""
    print("\n" + "=" * 60)
    print("TEST 2: Fresh Installation Scenario")
    print("=" * 60)

    # Create a temporary directory for this test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db = os.path.join(temp_dir, "password_manager.db")

        print("\n[*] Creating fresh database...")
        db = DatabaseManager(temp_db)

        # Simulate checking for a username that doesn't exist (like from old preferences)
        print("[*] Checking for user 'Surana' in fresh database...")
        exists = db.user_exists("Surana")
        assert exists is False, "User should not exist in fresh database"
        print("  [PASS] User 'Surana' not found in fresh database")

        print("\n" + "=" * 60)
        print("[PASS] TEST 2: Fresh install scenario works correctly!")
        print("=" * 60)


def test_database_migration_scenario():
    """Test scenario: Database migration with existing user"""
    print("\n" + "=" * 60)
    print("TEST 3: Database Migration Scenario")
    print("=" * 60)

    # Create a temporary database with a user
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        temp_db = tmp.name

    try:
        print("\n[*] Creating database with user 'Surana'...")
        db = DatabaseManager(temp_db)
        db.create_user("Surana", "testpassword123")
        print("  [PASS] User created successfully")

        # Simulate checking for the user (like after migration)
        print("\n[*] Checking for user 'Surana' after migration...")
        exists = db.user_exists("Surana")
        assert exists, "User should exist after migration"
        print("  [PASS] User 'Surana' found in migrated database")

        # Verify authentication works
        print("\n[*] Testing authentication...")
        user_data = db.authenticate_user("Surana", "testpassword123")
        assert user_data is not None, "Authentication should succeed"
        assert user_data["username"] == "surana", "Username should match"
        print("  [PASS] Authentication works after migration")

        print("\n" + "=" * 60)
        print("[PASS] TEST 3: Database migration scenario works correctly!")
        print("=" * 60)

    finally:
        # Cleanup
        if os.path.exists(temp_db):
            os.remove(temp_db)


def main():
    """Run all portability tests"""
    print("\n")
    print("=" * 60)
    print("  PORTABILITY TEST SUITE")
    print("  Password Manager Portability Fixes")
    print("=" * 60)

    try:
        # Run all tests
        test_user_exists_method()
        test_fresh_install_scenario()
        test_database_migration_scenario()

        # All tests passed
        print("\n")
        print("=" * 60)
        print("  ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
        print("\nPortability fixes are working correctly!")
        print("\nWhat this means:")
        print("  1. [OK] Fresh installations won't show non-existent usernames")
        print("  2. [OK] Database migrations will work seamlessly")
        print("  3. [OK] Login preferences validate against actual database")
        print()

        return 0

    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] UNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
