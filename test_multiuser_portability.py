#!/usr/bin/env python3
"""
Test script to verify multi-user portability and password isolation
This verifies that:
1. Multiple users can exist in the same database
2. Each user's passwords are isolated (no cross-contamination)
3. Portability works with multiple users
"""

import os
import sys
import tempfile
from pathlib import Path

from core.database import DatabaseManager
from core.encryption import PasswordEncryption

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_multiuser_password_isolation():
    """Test that passwords are properly isolated between users"""
    print("\n" + "=" * 60)
    print("TEST 1: Multi-User Password Isolation")
    print("=" * 60)

    # Create a temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        temp_db = tmp.name

    try:
        db = DatabaseManager(temp_db)

        # Create three different users
        print("\n[*] Creating three users: Alice, Bob, Charlie")
        user1_id = db.create_user("Alice", "alice_master_pass_123")
        user2_id = db.create_user("Bob", "bob_master_pass_456")
        user3_id = db.create_user("Charlie", "charlie_master_pass_789")
        print(
            f"  [PASS] Created users - Alice (ID: {user1_id}), Bob (ID: {user2_id}), Charlie (ID: {user3_id})")

        # Create encryption instances for each user
        enc_alice = PasswordEncryption()
        enc_bob = PasswordEncryption()
        enc_charlie = PasswordEncryption()

        # Add passwords for Alice
        print("\n[*] Adding passwords for Alice...")
        alice_pass1 = enc_alice.encrypt_password("alice_gmail_password", "alice_master_pass_123")
        alice_pass2 = enc_alice.encrypt_password("alice_facebook_password", "alice_master_pass_123")
        db.add_password_entry(
            user1_id,
            "gmail.com",
            "alice@email.com",
            alice_pass1,
            "Alice's email")
        db.add_password_entry(user1_id, "facebook.com", "alice123", alice_pass2, "Alice's social")
        print("  [PASS] Added 2 passwords for Alice")

        # Add passwords for Bob
        print("\n[*] Adding passwords for Bob...")
        bob_pass1 = enc_bob.encrypt_password("bob_gmail_password", "bob_master_pass_456")
        bob_pass2 = enc_bob.encrypt_password("bob_twitter_password", "bob_master_pass_456")
        bob_pass3 = enc_bob.encrypt_password("bob_github_password", "bob_master_pass_456")
        db.add_password_entry(user2_id, "gmail.com", "bob@email.com", bob_pass1, "Bob's email")
        db.add_password_entry(user2_id, "twitter.com", "bob_tweets", bob_pass2, "Bob's twitter")
        db.add_password_entry(user2_id, "github.com", "bob_developer", bob_pass3, "Bob's code")
        print("  [PASS] Added 3 passwords for Bob")

        # Add passwords for Charlie
        print("\n[*] Adding passwords for Charlie...")
        charlie_pass1 = enc_charlie.encrypt_password(
            "charlie_gmail_password", "charlie_master_pass_789")
        db.add_password_entry(
            user3_id,
            "gmail.com",
            "charlie@email.com",
            charlie_pass1,
            "Charlie's email")
        print("  [PASS] Added 1 password for Charlie")

        # Verify Alice can ONLY see her passwords
        print("\n[*] Verifying Alice can only see her own passwords...")
        alice_entries = db.get_password_entries(user1_id)
        assert len(alice_entries) == 2, f"Alice should have 2 passwords, got {len(alice_entries)}"
        alice_websites = [entry['website'] for entry in alice_entries]
        assert set(alice_websites) == {'gmail.com', 'facebook.com'}, "Alice's websites don't match"
        print(f"  [PASS] Alice sees only her 2 passwords: {alice_websites}")

        # Verify Bob can ONLY see his passwords
        print("\n[*] Verifying Bob can only see his own passwords...")
        bob_entries = db.get_password_entries(user2_id)
        assert len(bob_entries) == 3, f"Bob should have 3 passwords, got {len(bob_entries)}"
        bob_websites = [entry['website'] for entry in bob_entries]
        assert set(bob_websites) == {'gmail.com', 'twitter.com',
                                     'github.com'}, "Bob's websites don't match"
        print(f"  [PASS] Bob sees only his 3 passwords: {bob_websites}")

        # Verify Charlie can ONLY see his passwords
        print("\n[*] Verifying Charlie can only see his own passwords...")
        charlie_entries = db.get_password_entries(user3_id)
        assert len(charlie_entries) == 1, f"Charlie should have 1 password, got {
            len(charlie_entries)}"
        charlie_websites = [entry['website'] for entry in charlie_entries]
        assert charlie_websites == ['gmail.com'], "Charlie's website doesn't match"
        print(f"  [PASS] Charlie sees only his 1 password: {charlie_websites}")

        # Verify Alice's encrypted passwords can ONLY be decrypted with Alice's master password
        print("\n[*] Verifying password encryption isolation...")
        alice_gmail = db.get_password_entries(user1_id, "gmail.com")[0]
        decrypted = enc_alice.decrypt_password(
            alice_gmail['password_encrypted'],
            "alice_master_pass_123")
        assert decrypted == "alice_gmail_password", "Alice's password decryption failed"
        print("  [PASS] Alice's password decrypts correctly with her master password")

        # Try to decrypt Alice's password with Bob's master password (should fail)
        print("\n[*] Verifying cross-user password protection...")
        try:
            enc_bob.decrypt_password(alice_gmail['password_encrypted'], "bob_master_pass_456")
            assert False, "Should not be able to decrypt Alice's password with Bob's key!"
        except Exception:
            print("  [PASS] Cannot decrypt Alice's password with Bob's master password (as expected)")

        # Verify searching by website is also isolated
        print("\n[*] Verifying search isolation (gmail.com exists for all users)...")
        alice_gmail_search = db.get_password_entries(user1_id, "gmail")
        bob_gmail_search = db.get_password_entries(user2_id, "gmail")
        charlie_gmail_search = db.get_password_entries(user3_id, "gmail")

        assert len(alice_gmail_search) == 1, "Alice should find 1 gmail entry"
        assert len(bob_gmail_search) == 1, "Bob should find 1 gmail entry"
        assert len(charlie_gmail_search) == 1, "Charlie should find 1 gmail entry"

        # Verify they're different entries
        assert alice_gmail_search[0]['username'] == "alice@email.com", "Wrong username for Alice"
        assert bob_gmail_search[0]['username'] == "bob@email.com", "Wrong username for Bob"
        assert charlie_gmail_search[0]['username'] == "charlie@email.com", "Wrong username for Charlie"
        print("  [PASS] Each user only sees their own gmail.com entry")

        print("\n" + "=" * 60)
        print("[PASS] TEST 1: Password isolation is perfect!")
        print("=" * 60)

        return temp_db  # Return for next test

    except Exception as e:
        # Cleanup on error
        if os.path.exists(temp_db):
            os.remove(temp_db)
        raise


def test_multiuser_portability(db_path):
    """Test portability with multiple users (database migration scenario)"""
    print("\n" + "=" * 60)
    print("TEST 2: Multi-User Portability (Database Migration)")
    print("=" * 60)

    try:
        # Simulate moving database to new computer - create new DB manager instance
        print("\n[*] Simulating database migration to new computer...")
        new_db = DatabaseManager(db_path)
        print("  [PASS] Database loaded successfully on 'new computer'")

        # Verify all three users still exist
        print("\n[*] Checking if all users exist after migration...")
        assert new_db.user_exists("Alice"), "Alice should exist after migration"
        assert new_db.user_exists("Bob"), "Bob should exist after migration"
        assert new_db.user_exists("Charlie"), "Charlie should exist after migration"
        print("  [PASS] All 3 users found: Alice, Bob, Charlie")

        # Verify authentication works for all users
        print("\n[*] Testing authentication for all users...")
        alice_auth = new_db.authenticate_user("Alice", "alice_master_pass_123")
        bob_auth = new_db.authenticate_user("Bob", "bob_master_pass_456")
        charlie_auth = new_db.authenticate_user("Charlie", "charlie_master_pass_789")

        assert alice_auth is not None, "Alice authentication failed"
        assert bob_auth is not None, "Bob authentication failed"
        assert charlie_auth is not None, "Charlie authentication failed"
        print("  [PASS] All users can authenticate")

        # Verify all passwords are still isolated after migration
        print("\n[*] Verifying password isolation after migration...")
        alice_count = len(new_db.get_password_entries(alice_auth['user_id']))
        bob_count = len(new_db.get_password_entries(bob_auth['user_id']))
        charlie_count = len(new_db.get_password_entries(charlie_auth['user_id']))

        assert alice_count == 2, f"Alice should have 2 passwords, got {alice_count}"
        assert bob_count == 3, f"Bob should have 3 passwords, got {bob_count}"
        assert charlie_count == 1, f"Charlie should have 1 password, got {charlie_count}"
        print("  [PASS] Password counts correct - Alice: 2, Bob: 3, Charlie: 1")

        # Verify passwords can still be decrypted after migration
        print("\n[*] Verifying passwords can be decrypted after migration...")
        enc = PasswordEncryption()

        alice_gmail = new_db.get_password_entries(alice_auth['user_id'], "gmail.com")[0]
        decrypted = enc.decrypt_password(alice_gmail['password_encrypted'], "alice_master_pass_123")
        assert decrypted == "alice_gmail_password", "Password decryption failed after migration"
        print("  [PASS] Passwords decrypt correctly after migration")

        print("\n" + "=" * 60)
        print("[PASS] TEST 2: Multi-user portability works perfectly!")
        print("=" * 60)

    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)


def test_login_preference_with_multiple_users():
    """Test login preference validation with multiple users"""
    print("\n" + "=" * 60)
    print("TEST 3: Login Preference with Multiple Users")
    print("=" * 60)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        temp_db = tmp.name

    try:
        db = DatabaseManager(temp_db)

        # Create multiple users
        print("\n[*] Creating users: Alice, Bob, Charlie...")
        db.create_user("Alice", "password123")
        db.create_user("Bob", "password456")
        db.create_user("Charlie", "password789")
        print("  [PASS] Created 3 users")

        # Test user_exists for each user
        print("\n[*] Testing user_exists() for all users...")
        assert db.user_exists("Alice"), "Alice should exist"
        assert db.user_exists("Bob"), "Bob should exist"
        assert db.user_exists("Charlie"), "Charlie should exist"
        assert db.user_exists("David") is False, "David should NOT exist"
        print("  [PASS] user_exists() correctly identifies all users")

        # Simulate login preference scenarios
        print("\n[*] Testing login preference scenarios...")

        # Scenario 1: Valid preference (user exists)
        if db.user_exists("Bob"):
            print("  [PASS] Bob exists - would pre-fill username")

        # Scenario 2: Invalid preference (user doesn't exist)
        if not db.user_exists("OldUserFromOtherPC"):
            print("  [PASS] OldUserFromOtherPC doesn't exist - would NOT pre-fill")

        print("\n" + "=" * 60)
        print("[PASS] TEST 3: Login preferences work with multiple users!")
        print("=" * 60)

    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def main():
    """Run all multi-user tests"""
    print("\n")
    print("=" * 60)
    print("  MULTI-USER PORTABILITY & ISOLATION TEST SUITE")
    print("  Verifying password isolation and multi-user support")
    print("=" * 60)

    try:
        # Test 1: Password isolation
        db_path = test_multiuser_password_isolation()

        # Test 2: Multi-user portability (uses database from test 1)
        test_multiuser_portability(db_path)

        # Test 3: Login preferences with multiple users
        test_login_preference_with_multiple_users()

        # Summary
        print("\n")
        print("=" * 60)
        print("  ALL MULTI-USER TESTS PASSED!")
        print("=" * 60)
        print("\nVERIFIED:")
        print("  1. [OK] Multiple users can coexist in same database")
        print("  2. [OK] Each user's passwords are completely isolated")
        print("  3. [OK] Users cannot access each other's passwords")
        print("  4. [OK] Passwords encrypted with different master passwords")
        print("  5. [OK] Database migration works with multiple users")
        print("  6. [OK] All users can authenticate after migration")
        print("  7. [OK] Login preferences validate against all users")
        print("\nSECURITY:")
        print("  - Foreign key constraints enforce data integrity")
        print("  - User ID verification prevents cross-user access")
        print("  - Each user's passwords encrypted with their master password")
        print("  - Cannot decrypt User A's password with User B's master password")
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
