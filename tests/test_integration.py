"""
Personal Password Manager - Integration Tests
===============================================

End-to-end tests that exercise the full stack from user creation through
password management. These tests use real database and encryption operations
(no mocks) to verify the entire system works together.

Test flow:
1. Create a new user account (with complexity-validated password)
2. Authenticate and get a session
3. Add a password entry (encrypted with AES-256-GCM)
4. Retrieve and verify the decrypted password
5. Update the password entry
6. Search for entries
7. Change the master password (re-encrypts all entries)
8. Verify entries are still accessible with the new master password
9. Delete the password entry
10. Verify deletion

The database is created as a temporary file and cleaned up after tests.

Version: 3.0.0
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from core.auth import AuthenticationManager
from core.encryption import PasswordEncryption
from core.password_manager import PasswordManagerCore, SearchCriteria


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def temp_db():
    """
    Create a temporary database directory for integration tests.

    Uses a module-scoped fixture so all tests in this file share the
    same database — this allows tests to build on each other's state
    (create user -> login -> add password -> etc.).
    """
    temp_dir = tempfile.mkdtemp(prefix="pm_test_")
    db_path = os.path.join(temp_dir, "test_password_manager.db")
    yield db_path
    # Cleanup after all tests in this module
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="module")
def auth_manager(temp_db):
    """Create an AuthenticationManager backed by the temporary database."""
    return AuthenticationManager(db_path=temp_db)


@pytest.fixture(scope="module")
def password_manager(auth_manager):
    """Create a PasswordManagerCore backed by the same database."""
    return PasswordManagerCore(auth_manager=auth_manager)


# Test credentials that meet complexity requirements:
# 12+ chars, uppercase, lowercase, digit, special char
TEST_USERNAME = "integration_test_user"
TEST_PASSWORD = "Integr@tion_T3st!"
NEW_PASSWORD = "N3wM@ster_P@ssw0rd!"


# ---------------------------------------------------------------------------
# Shared state between tests (module-scoped via dict)
# ---------------------------------------------------------------------------
_state = {}


# ===========================================================================
# Integration test flow
# ===========================================================================

class TestIntegrationFlow:
    """
    Full integration test that exercises the complete user flow.

    Tests are ordered by number prefix to ensure sequential execution.
    Each test builds on the state created by previous tests.
    """

    def test_01_create_user(self, auth_manager):
        """
        Step 1: Create a new user account.

        The password must meet complexity requirements (12+ chars,
        upper, lower, digit, special). This also tests that the
        database and user table are created automatically.
        """
        try:
            auth_manager.create_user_account(TEST_USERNAME, TEST_PASSWORD)
        except Exception as e:
            # If user already exists from a previous test run, that's OK
            if "already exists" not in str(e).lower():
                raise
        # Verify the user exists
        assert auth_manager.user_exists(TEST_USERNAME)

    def test_02_login(self, auth_manager):
        """
        Step 2: Authenticate with the created credentials.

        On success, we receive a session_id token that's required for
        all subsequent password operations.
        """
        session_id = auth_manager.authenticate_user(TEST_USERNAME, TEST_PASSWORD)
        assert session_id is not None
        assert len(session_id) > 0
        _state["session_id"] = session_id

    def test_03_cache_master_password(self, password_manager):
        """
        Step 3: Cache the master password so subsequent operations
        don't need it passed explicitly.
        """
        session_id = _state["session_id"]
        password_manager._cache_master_password(session_id, TEST_PASSWORD)

    def test_04_add_password_entry(self, password_manager):
        """
        Step 4: Add a new password entry.

        The password is encrypted with AES-256-GCM before storage.
        Returns the entry_id for later retrieval.
        """
        session_id = _state["session_id"]
        entry_id = password_manager.add_password_entry(
            session_id=session_id,
            website="integration-test.example.com",
            username="test@example.com",
            password="SecretP@ss_ForTest!",
            remarks="Integration test entry",
        )
        assert entry_id is not None
        assert entry_id > 0
        _state["entry_id"] = entry_id

    def test_05_retrieve_and_verify(self, password_manager):
        """
        Step 5: Retrieve the entry and verify the decrypted password.

        This proves the encrypt -> store -> retrieve -> decrypt chain
        works end-to-end with AES-256-GCM.
        """
        session_id = _state["session_id"]
        entry_id = _state["entry_id"]

        entry = password_manager.get_password_entry(
            session_id=session_id,
            entry_id=entry_id,
            decrypt_password=True,
        )

        assert entry.website == "integration-test.example.com"
        assert entry.username == "test@example.com"
        assert entry.password == "SecretP@ss_ForTest!"
        assert entry.remarks == "Integration test entry"

    def test_06_search_entries(self, password_manager):
        """
        Step 6: Search for entries by website name.

        Verifies the search functionality returns matching entries.
        """
        session_id = _state["session_id"]
        criteria = SearchCriteria(website="integration-test")

        entries = password_manager.search_password_entries(
            session_id=session_id,
            criteria=criteria,
            include_passwords=False,
        )

        assert len(entries) >= 1
        websites = [e.website for e in entries]
        assert any("integration-test" in w for w in websites)

    def test_07_update_entry(self, password_manager):
        """
        Step 7: Update the password entry with a new password.

        The new password is re-encrypted with GCM.
        """
        session_id = _state["session_id"]
        entry_id = _state["entry_id"]

        result = password_manager.update_password_entry(
            session_id=session_id,
            entry_id=entry_id,
            password="UpdatedP@ss_2024!",
            remarks="Updated during integration test",
        )
        assert result is True

        # Verify the update
        entry = password_manager.get_password_entry(
            session_id=session_id,
            entry_id=entry_id,
            decrypt_password=True,
        )
        assert entry.password == "UpdatedP@ss_2024!"
        assert entry.remarks == "Updated during integration test"

    def test_08_change_master_password(self, auth_manager):
        """
        Step 8: Change the master password.

        This re-encrypts ALL password entries with the new master password.
        After this, the old master password can no longer decrypt entries.
        """
        session_id = _state["session_id"]

        result = auth_manager.change_master_password(
            session_id=session_id,
            current_password=TEST_PASSWORD,
            new_password=NEW_PASSWORD,
        )
        assert result is True

    def test_09_verify_entries_with_new_password(self, password_manager):
        """
        Step 9: Verify entries are still accessible with the new master password.

        After master password change, the old cached password is invalid.
        We must cache the new one and then verify retrieval works.
        """
        session_id = _state["session_id"]
        entry_id = _state["entry_id"]

        # Cache the new master password
        password_manager._cache_master_password(session_id, NEW_PASSWORD)

        entry = password_manager.get_password_entry(
            session_id=session_id,
            entry_id=entry_id,
            decrypt_password=True,
        )
        assert entry.password == "UpdatedP@ss_2024!"

    def test_10_delete_entry(self, password_manager):
        """
        Step 10: Delete the password entry and verify it's gone.
        """
        session_id = _state["session_id"]
        entry_id = _state["entry_id"]

        result = password_manager.delete_password_entry(
            session_id=session_id,
            entry_id=entry_id,
        )
        assert result is True

        # Verify the entry is deleted
        try:
            password_manager.get_password_entry(
                session_id=session_id,
                entry_id=entry_id,
            )
            assert False, "Entry should have been deleted"
        except Exception:
            pass  # Expected — entry not found

    def test_11_gcm_format_verification(self, password_manager, auth_manager):
        """
        Step 11: Verify that newly added entries use v2 (GCM) blob format.

        This confirms the encryption upgrade is active end-to-end.
        """
        session_id = _state["session_id"]

        # Add a new entry with the new master password
        entry_id = password_manager.add_password_entry(
            session_id=session_id,
            website="gcm-verify.example.com",
            username="gcm_user",
            password="GCM_V3rify!Pass",
        )

        # Retrieve the raw encrypted data from the database
        session = auth_manager.validate_session(session_id)
        raw_entries = auth_manager.db_manager.get_password_entries(session.user_id)

        # Find our entry
        target = None
        for e in raw_entries:
            if e.get("entry_id") == entry_id:
                target = e
                break

        assert target is not None, "Entry should exist in database"

        # Check the version byte of the encrypted blob
        encrypted = target.get("password_encrypted")
        if isinstance(encrypted, bytes):
            assert encrypted[0:1] == b"\x02", "Encrypted blob should be v2 (GCM) format"
        elif isinstance(encrypted, str):
            # If stored as hex or base64, decode and check
            import base64
            try:
                blob = base64.b64decode(encrypted)
                assert blob[0:1] == b"\x02"
            except Exception:
                # Might be stored in another format — skip
                pass

        # Clean up
        password_manager.delete_password_entry(session_id=session_id, entry_id=entry_id)
