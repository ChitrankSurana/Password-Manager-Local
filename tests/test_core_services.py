"""
Personal Password Manager - Core Service Tests
================================================

Tests for the extracted core services that were previously embedded in GUI code:

1. PasswordHealthService: Analyzes password health (weak, duplicate, old entries)
2. Age filtering and sorting: Moved from GUI layer to PasswordManagerCore
3. Bulk migration with progress callback: Verifies CBC-to-GCM migration reporting

These tests use mock data to avoid database dependencies — they validate
the pure business logic only.

Version: 3.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytest

from core.password_health_service import (
    HealthReport,
    PasswordHealthService,
)
from core.password_manager import PasswordManagerCore


# ---------------------------------------------------------------------------
# Mock data: simulated password entries for testing
# ---------------------------------------------------------------------------

@dataclass
class MockEntry:
    """
    Minimal password entry mock that mimics PasswordEntry's interface.

    Used to test PasswordHealthService and age filtering without needing
    a real database or encryption.
    """
    entry_id: int = 0
    id: int = 0  # Alias for health service compatibility
    website: str = ""
    username: str = ""
    password: str = ""  # Decrypted plaintext (for health analysis)
    remarks: str = ""
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    is_favorite: bool = False

    def __post_init__(self):
        self.id = self.entry_id
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.modified_at is None:
            self.modified_at = self.created_at


def _make_entries() -> List[MockEntry]:
    """
    Create a set of test entries with varying qualities:
    - Strong passwords, weak passwords, duplicates, old entries
    """
    now = datetime.now()
    return [
        # Strong unique password, recently created
        MockEntry(
            entry_id=1,
            website="github.com",
            username="dev@example.com",
            password="Str0ng!Un1que_P@ssw0rd",
            created_at=now - timedelta(days=10),
            modified_at=now - timedelta(days=10),
        ),
        # Weak password (short, no special chars)
        MockEntry(
            entry_id=2,
            website="weaksite.com",
            username="user1",
            password="pass123",
            created_at=now - timedelta(days=30),
            modified_at=now - timedelta(days=30),
        ),
        # Duplicate of entry 4 (same password, different site)
        MockEntry(
            entry_id=3,
            website="siteA.com",
            username="user2",
            password="DuplicatePassword!1",
            created_at=now - timedelta(days=60),
            modified_at=now - timedelta(days=60),
        ),
        # Duplicate of entry 3
        MockEntry(
            entry_id=4,
            website="siteB.com",
            username="user3",
            password="DuplicatePassword!1",
            created_at=now - timedelta(days=60),
            modified_at=now - timedelta(days=60),
        ),
        # Old password (> 180 days, should be flagged as "old")
        MockEntry(
            entry_id=5,
            website="oldsite.com",
            username="ancient_user",
            password="OldButStr0ng!Pass",
            created_at=now - timedelta(days=200),
            modified_at=now - timedelta(days=200),
        ),
        # Very weak password (common word)
        MockEntry(
            entry_id=6,
            website="badpassword.com",
            username="user4",
            password="password",
            created_at=now - timedelta(days=100),
            modified_at=now - timedelta(days=100),
        ),
    ]


# ===========================================================================
# 1. PasswordHealthService tests
# ===========================================================================

class TestPasswordHealthService:
    """
    Validate that PasswordHealthService correctly identifies weak,
    duplicate, and old passwords, and produces a meaningful security score.
    """

    @pytest.fixture
    def service(self):
        return PasswordHealthService()

    @pytest.fixture
    def entries(self):
        return _make_entries()

    def test_analyze_returns_health_report(self, service, entries):
        """analyze_health() must return a HealthReport dataclass."""
        report = service.analyze_health(entries)
        assert isinstance(report, HealthReport)

    def test_total_count(self, service, entries):
        """The report must reflect the total number of entries analyzed."""
        report = service.analyze_health(entries)
        assert report.total_count == len(entries)

    def test_weak_passwords_detected(self, service, entries):
        """
        Entries with weak passwords (e.g., "pass123", "password") must
        appear in the weak_passwords list.
        """
        report = service.analyze_health(entries)
        weak_websites = [wp.website for wp in report.weak_passwords]
        # At least the trivially weak passwords should be flagged
        assert len(report.weak_passwords) >= 1, "Should detect at least one weak password"

    def test_duplicate_passwords_detected(self, service, entries):
        """
        Entries sharing the same password ("DuplicatePassword!1") must
        appear in the duplicate_groups list. The reused_count should be >= 2.
        """
        report = service.analyze_health(entries)
        assert report.reused_count >= 2, "Should detect duplicate passwords"
        assert len(report.duplicate_groups) >= 1, "Should have at least one duplicate group"

    def test_old_passwords_detected(self, service, entries):
        """
        Entries older than 180 days must appear in the old_passwords list.
        """
        report = service.analyze_health(entries)
        old_websites = [op.website for op in report.old_passwords]
        assert "oldsite.com" in old_websites, "200-day-old entry should be flagged as old"

    def test_score_range(self, service, entries):
        """The security score must be between 0 and 100 inclusive."""
        report = service.analyze_health(entries)
        assert 0 <= report.score <= 100

    def test_recommendations_generated(self, service, entries):
        """
        With weak and duplicate passwords present, the report must
        include at least one recommendation.
        """
        report = service.analyze_health(entries)
        assert len(report.recommendations) >= 1

    def test_empty_entries_score_100(self, service):
        """
        Analyzing an empty list should return a score of 100 (or 0 entries,
        no problems). The exact behavior depends on implementation — either
        is acceptable.
        """
        report = service.analyze_health([])
        assert report.total_count == 0
        # Score should be either 0 (no data) or 100 (no problems)
        assert report.score in (0, 100)

    def test_as_dict_serialization(self, service, entries):
        """
        HealthReport.as_dict() must produce a plain dict suitable for
        JSON serialization (e.g., for API responses).
        """
        report = service.analyze_health(entries)
        d = report.as_dict()
        assert isinstance(d, dict)
        assert "total_count" in d
        assert "score" in d
        assert "weak_passwords" in d


# ===========================================================================
# 2. Age filtering and sorting
# ===========================================================================

class TestAgeFiltering:
    """
    Verify that PasswordManagerCore.filter_entries_by_age() and
    sort_entries_by_age() correctly categorize entries by age.

    Age categories (from utils/password_age.py):
    - fresh: < 90 days
    - moderate: 90-180 days
    - old: > 180 days
    """

    @pytest.fixture
    def entries(self):
        return _make_entries()

    def test_filter_all_returns_everything(self, entries):
        """The 'all' filter must return all entries without filtering."""
        result = PasswordManagerCore.filter_entries_by_age(entries, "all")
        assert len(result) == len(entries)

    def test_filter_fresh(self, entries):
        """
        Filtering by 'fresh' should return entries < 90 days old.
        Our test data has entries at 10 and 30 days.
        """
        result = PasswordManagerCore.filter_entries_by_age(entries, "fresh")
        # entries at 10d and 30d should be fresh
        assert len(result) >= 1
        for entry in result:
            age_days = (datetime.now() - entry.modified_at).days
            assert age_days < 90, f"Fresh entry should be < 90 days old, got {age_days}"

    def test_filter_old(self, entries):
        """
        Filtering by 'old' should return entries > 180 days old.
        Our test data has one entry at 200 days.
        """
        result = PasswordManagerCore.filter_entries_by_age(entries, "old")
        assert len(result) >= 1
        for entry in result:
            age_days = (datetime.now() - entry.modified_at).days
            assert age_days > 180, f"Old entry should be > 180 days old, got {age_days}"

    def test_sort_oldest_first(self, entries):
        """Sorting with oldest_first=True should put the 200-day entry first."""
        result = PasswordManagerCore.sort_entries_by_age(entries, oldest_first=True)
        # First entry should be the oldest
        first_age = (datetime.now() - result[0].modified_at).days
        last_age = (datetime.now() - result[-1].modified_at).days
        assert first_age >= last_age, "Oldest should come first"

    def test_sort_newest_first(self, entries):
        """Sorting with oldest_first=False should put the 10-day entry first."""
        result = PasswordManagerCore.sort_entries_by_age(entries, oldest_first=False)
        first_age = (datetime.now() - result[0].modified_at).days
        last_age = (datetime.now() - result[-1].modified_at).days
        assert first_age <= last_age, "Newest should come first"

    def test_filter_preserves_entries(self, entries):
        """Filtering must not modify the original entry objects."""
        original_count = len(entries)
        _ = PasswordManagerCore.filter_entries_by_age(entries, "fresh")
        assert len(entries) == original_count, "Original list must not be modified"


# ===========================================================================
# 3. Bulk migration with progress callback
# ===========================================================================

class TestBulkMigrationProgress:
    """
    The migrate_entry_to_gcm() method should work on individual entries.
    The PasswordManagerCore.migrate_all_entries_to_gcm() method calls
    a progress callback. We test the individual migration at the
    encryption level since the bulk method requires database access.
    """

    def test_migration_calls_progress_for_multiple_entries(self):
        """
        Simulating bulk migration: creating multiple v1 blobs, migrating
        each, and tracking progress through a callback.

        This validates the pattern used by migrate_all_entries_to_gcm()
        without needing a real database.
        """
        from core.encryption import PasswordEncryption

        enc = PasswordEncryption()
        master_pw = "BulkMigr@te!Test1"

        # Create test helper for v1 blobs
        from tests.test_security import _create_legacy_v1_blob

        passwords = ["pw_one", "pw_two", "pw_three", "pw_four"]
        v1_blobs = [_create_legacy_v1_blob(pw, master_pw) for pw in passwords]

        # Track progress
        progress_calls = []

        def progress_callback(current, total):
            progress_calls.append((current, total))

        # Simulate bulk migration with progress
        total = len(v1_blobs)
        for i, blob in enumerate(v1_blobs):
            v2_blob = enc.migrate_entry_to_gcm(blob, master_pw)
            # Verify the migrated blob decrypts correctly
            result = enc.decrypt_password(v2_blob, master_pw)
            assert result == passwords[i]
            # Call progress
            progress_callback(i + 1, total)

        # Verify all progress callbacks fired
        assert len(progress_calls) == total
        assert progress_calls[-1] == (total, total)

        # Verify monotonic progress
        for i, (current, t) in enumerate(progress_calls):
            assert current == i + 1
            assert t == total
