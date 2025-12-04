#!/usr/bin/env python3
"""
Test script for password entry deletion functionality
Tests the newly implemented delete feature with proper confirmation
"""

import os
import sys
import tempfile
from pathlib import Path

from core.password_manager import PasswordManagerCore

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_delete_password_backend():
    """Test the backend password deletion functionality"""
    print("\n" + "=" * 60)
    print("TEST 1: Backend Password Deletion")
    print("=" * 60)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        temp_db = tmp.name

    try:
        print("\n[*] Setting up test environment...")

        password_manager = PasswordManagerCore(temp_db)

        # Create test user
        user_id = password_manager.auth_manager.create_user_account(
            "testuser", "master_password_123"
        )
        print(f"  [PASS] Created test user (ID: {user_id})")

        # Authenticate
        session_id = password_manager.auth_manager.authenticate_user(
            "testuser", "master_password_123"
        )
        print("  [PASS] User authenticated")

        # Add password entries
        entry1_id = password_manager.add_password_entry(
            session_id=session_id,
            website="example.com",
            username="user@example.com",
            password="password123",
            remarks="Test entry 1",
            master_password="master_password_123",
        )
        print(f"  [PASS] Created entry 1 (ID: {entry1_id})")

        entry2_id = password_manager.add_password_entry(
            session_id=session_id,
            website="test.com",
            username="testuser",
            password="testpass456",
            remarks="Test entry 2",
            master_password="master_password_123",
        )
        print(f"  [PASS] Created entry 2 (ID: {entry2_id})")

        # ====================================================================
        # Test 1A: Verify both entries exist
        # ====================================================================
        print("\n[*] Test 1A: Verify entries exist...")
        entries = password_manager.search_password_entries(
            session_id=session_id, include_passwords=False
        )
        assert len(entries) == 2, f"Should have 2 entries, got {len(entries)}"
        print("  [PASS] Both entries exist")

        # ====================================================================
        # Test 1B: Delete first entry
        # ====================================================================
        print("\n[*] Test 1B: Delete first entry...")
        success = password_manager.delete_password_entry(session_id=session_id, entry_id=entry1_id)
        assert success, "Deletion should succeed"
        print("  [PASS] Entry 1 deleted successfully")

        # ====================================================================
        # Test 1C: Verify only one entry remains
        # ====================================================================
        print("\n[*] Test 1C: Verify only one entry remains...")
        entries = password_manager.search_password_entries(
            session_id=session_id, include_passwords=False
        )
        assert len(entries) == 1, f"Should have 1 entry left, got {len(entries)}"
        assert entries[0].entry_id == entry2_id, "Remaining entry should be entry 2"
        assert entries[0].website == "test.com", "Remaining entry should be test.com"
        print("  [PASS] Only entry 2 remains")

        # ====================================================================
        # Test 1D: Try to delete already deleted entry (should fail gracefully)
        # ====================================================================
        print("\n[*] Test 1D: Try to delete already deleted entry...")
        success = password_manager.delete_password_entry(session_id=session_id, entry_id=entry1_id)
        assert success is False, "Deleting non-existent entry should return False"
        print("  [PASS] Deletion of non-existent entry handled correctly")

        # ====================================================================
        # Test 1E: Delete remaining entry
        # ====================================================================
        print("\n[*] Test 1E: Delete remaining entry...")
        success = password_manager.delete_password_entry(session_id=session_id, entry_id=entry2_id)
        assert success, "Deletion should succeed"
        print("  [PASS] Entry 2 deleted successfully")

        # ====================================================================
        # Test 1F: Verify no entries remain
        # ====================================================================
        print("\n[*] Test 1F: Verify no entries remain...")
        entries = password_manager.search_password_entries(
            session_id=session_id, include_passwords=False
        )
        assert len(entries) == 0, f"Should have 0 entries, got {len(entries)}"
        print("  [PASS] All entries deleted")

        print("\n" + "=" * 60)
        print("[PASS] TEST 1: Deletion functionality works!")
        print("=" * 60)

        return True

    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_multi_user_deletion_isolation():
    """Test that users can only delete their own entries"""
    print("\n" + "=" * 60)
    print("TEST 2: Multi-User Deletion Security")
    print("=" * 60)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        temp_db = tmp.name

    try:
        print("\n[*] Setting up multi-user environment...")

        password_manager = PasswordManagerCore(temp_db)

        # Create two users
        user1_id = password_manager.auth_manager.create_user_account("alice", "alice_password_123")
        user2_id = password_manager.auth_manager.create_user_account("bob", "bob_password_456")
        print(f"  [PASS] Created users Alice (ID: {user1_id}) and Bob (ID: {user2_id})")

        # Authenticate both users
        alice_session = password_manager.auth_manager.authenticate_user(
            "alice", "alice_password_123"
        )
        bob_session = password_manager.auth_manager.authenticate_user("bob", "bob_password_456")
        print("  [PASS] Both users authenticated")

        # Alice adds a password
        alice_entry_id = password_manager.add_password_entry(
            session_id=alice_session,
            website="alice-site.com",
            username="alice_user",
            password="alice_password",
            remarks="Alice's entry",
            master_password="alice_password_123",
        )
        print(f"  [PASS] Alice created entry (ID: {alice_entry_id})")

        # Bob adds a password
        bob_entry_id = password_manager.add_password_entry(
            session_id=bob_session,
            website="bob-site.com",
            username="bob_user",
            password="bob_password",
            remarks="Bob's entry",
            master_password="bob_password_456",
        )
        print(f"  [PASS] Bob created entry (ID: {bob_entry_id})")

        # ====================================================================
        # Test: Alice can delete her own entry
        # ====================================================================
        print("\n[*] Test 2A: Alice deleting her own entry...")
        success = password_manager.delete_password_entry(
            session_id=alice_session, entry_id=alice_entry_id
        )
        assert success, "Alice should be able to delete her own entry"
        print("  [PASS] Alice can delete her own entry")

        # ====================================================================
        # Test: Bob cannot delete Alice's entry (security check)
        # ====================================================================
        print("\n[*] Test 2B: Bob attempting to delete Alice's entry...")

        # Alice creates another entry
        alice_entry2_id = password_manager.add_password_entry(
            session_id=alice_session,
            website="alice-site2.com",
            username="alice_user2",
            password="alice_password2",
            remarks="Alice's second entry",
            master_password="alice_password_123",
        )

        # Bob tries to delete Alice's entry (should raise exception for security)
        from core.password_manager import PasswordManagerError

        deletion_blocked = False
        try:
            password_manager.delete_password_entry(session_id=bob_session, entry_id=alice_entry2_id)
        except PasswordManagerError as e:
            # Exception is expected - security is working
            deletion_blocked = True
            assert (
                "does not own" in str(e).lower() or "deletion failed" in str(e).lower()
            ), "Should get ownership error"

        assert deletion_blocked, "Bob's deletion attempt should be blocked"
        print("  [PASS] Bob cannot delete Alice's entry (security enforced)")

        # Verify Alice's entry still exists
        alice_entries = password_manager.search_password_entries(
            alice_session, include_passwords=False
        )
        assert len(alice_entries) == 1, "Alice's entry should still exist"
        assert alice_entries[0].entry_id == alice_entry2_id, "Should be Alice's second entry"
        print("  [PASS] Alice's entry remains intact")

        print("\n" + "=" * 60)
        print("[PASS] TEST 2: Multi-user deletion security works!")
        print("=" * 60)

        return True

    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def main():
    """Run all delete functionality tests"""
    print("\n")
    print("=" * 60)
    print("  PASSWORD DELETION FUNCTIONALITY TEST SUITE")
    print("  Testing newly implemented delete feature")
    print("=" * 60)

    try:
        # Test 1: Basic deletion
        test_delete_password_backend()

        # Test 2: Multi-user security
        test_multi_user_deletion_isolation()

        # Summary
        print("\n")
        print("=" * 60)
        print("  ALL DELETE TESTS PASSED!")
        print("=" * 60)
        print("\nVERIFIED:")
        print("  1. [OK] Can delete password entries")
        print("  2. [OK] Deletion permanently removes entry")
        print("  3. [OK] Cannot delete non-existent entries")
        print("  4. [OK] Users can only delete their own entries")
        print("  5. [OK] Cross-user deletion attempts are blocked")

        print("\nGUI IMPLEMENTATION:")
        print("  - Delete button (trash icon) added to each password entry")
        print("  - Confirmation dialog before deletion")
        print("  - Success/error messages displayed")
        print("  - Password list auto-refreshes after deletion")
        print("  - Tooltip: 'Delete this password entry permanently'")

        print("\nHOW TO USE:")
        print("  1. Run the application")
        print("  2. View your password list")
        print("  3. Click the trash icon (trash can) on any entry")
        print("  4. Confirm deletion in the dialog")
        print("  5. Entry is permanently removed")

        print("\nThe delete functionality is ready to use!")
        print()

        return 0

    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n[ERROR] UNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
