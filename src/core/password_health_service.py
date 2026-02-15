#!/usr/bin/env python3
"""
Personal Password Manager - Password Health Service
====================================================

This module provides UI-independent password health analysis. It extracts the
business logic that was previously duplicated in the GUI (password_health.py)
and Flask (app.py) layers into a single, reusable service.

Both the Flet UI and any future interfaces should call this service instead
of implementing their own analysis logic — ensuring consistent scoring,
duplicate detection, and recommendations everywhere.

Key Features:
- Overall security score calculation (0-100)
- Weak password detection with per-password issue lists
- Duplicate password identification via SHA-256 hashing
- Old password tracking using age utilities
- Password strength distribution statistics
- Actionable security recommendations sorted by priority
- Age statistics (average, oldest, newest)

Usage:
    from core.password_health_service import PasswordHealthService

    service = PasswordHealthService()
    report = service.analyze_health(password_entries)
    score = report.score
    recommendations = report.recommendations

Author: Personal Password Manager
Version: 3.0.0
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .logging_config import get_logger

logger = get_logger(__name__)

# Try to import the advanced strength checker; fall back to built-in analysis
# if the utility module is unavailable (e.g., during minimal/core-only tests).
try:
    from ..utils.password_age import (
        calculate_age_days,
        calculate_age_statistics,
        format_age_human_readable,
        get_age_category,
        get_age_icon,
    )

    _HAS_AGE_UTILS = True
except ImportError:
    _HAS_AGE_UTILS = False
    logger.warning("password_age utilities not available — age analysis disabled")

try:
    from ..utils.strength_checker import AdvancedPasswordStrengthChecker

    _HAS_STRENGTH_CHECKER = True
except ImportError:
    _HAS_STRENGTH_CHECKER = False
    logger.warning(
        "AdvancedPasswordStrengthChecker not available — using simple fallback"
    )


# ===========================================================================
# DATA CLASSES
# ===========================================================================


@dataclass
class WeakPasswordInfo:
    """Details about a weak password entry."""

    entry_id: int
    website: str
    username: str
    strength: str  # "very_weak" | "weak"
    issues: List[str] = field(default_factory=list)


@dataclass
class DuplicatePasswordInfo:
    """Details about a duplicate password entry."""

    entry_id: int
    website: str
    username: str
    duplicate_of_website: str  # Website of the first occurrence
    duplicate_of_id: int  # Entry ID of the first occurrence


@dataclass
class OldPasswordInfo:
    """Details about an old password entry."""

    entry_id: int
    website: str
    username: str
    age_category: str  # "moderate" | "old"
    age_days: int
    age_text: str  # Human-readable age (e.g., "6 months")
    age_icon: str  # Emoji icon for the age category
    last_modified: str  # ISO-format date string


@dataclass
class Recommendation:
    """A security recommendation for the user."""

    rec_type: str  # "weak_passwords" | "duplicates" | "old_passwords" | "excellent"
    priority: str  # "high" | "medium" | "low"
    title: str
    description: str
    icon: str = ""


@dataclass
class StrengthDistribution:
    """Distribution of password strength levels across all entries."""

    very_weak: int = 0
    weak: int = 0
    fair: int = 0
    good: int = 0
    strong: int = 0
    very_strong: int = 0

    def as_dict(self) -> Dict[str, int]:
        """Return the distribution as a plain dictionary."""
        return {
            "very_weak": self.very_weak,
            "weak": self.weak,
            "fair": self.fair,
            "good": self.good,
            "strong": self.strong,
            "very_strong": self.very_strong,
        }


@dataclass
class HealthReport:
    """
    Complete password health analysis report.

    This is the primary output of PasswordHealthService.analyze_health().
    It contains all the data needed to render a health dashboard in any UI.

    Attributes:
        total_count: Total number of passwords analyzed
        weak_passwords: List of weak password details
        duplicate_groups: List of duplicate password details
        old_passwords: List of old password details
        reused_count: Number of passwords that are reused (duplicated)
        average_strength: Average strength level as a string
        score: Overall security score (0-100)
        strength_distribution: Breakdown by strength level
        recommendations: Actionable recommendations sorted by priority
        age_statistics: Aggregate age statistics (average, oldest, newest, etc.)
    """

    total_count: int = 0
    weak_passwords: List[WeakPasswordInfo] = field(default_factory=list)
    duplicate_groups: List[DuplicatePasswordInfo] = field(default_factory=list)
    old_passwords: List[OldPasswordInfo] = field(default_factory=list)
    reused_count: int = 0
    average_strength: str = "unknown"
    score: int = 0
    strength_distribution: StrengthDistribution = field(
        default_factory=StrengthDistribution
    )
    recommendations: List[Recommendation] = field(default_factory=list)
    age_statistics: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        """
        Serialize the report to a plain dictionary.

        Useful for JSON serialization (e.g., Flask API responses) and for
        passing data to template engines.
        """
        return {
            "total_count": self.total_count,
            "weak_passwords": [
                {
                    "id": wp.entry_id,
                    "website": wp.website,
                    "username": wp.username,
                    "strength": wp.strength,
                    "issues": wp.issues,
                }
                for wp in self.weak_passwords
            ],
            "duplicate_passwords": [
                {
                    "id": dp.entry_id,
                    "website": dp.website,
                    "username": dp.username,
                    "duplicate_of": dp.duplicate_of_website,
                    "duplicate_id": dp.duplicate_of_id,
                }
                for dp in self.duplicate_groups
            ],
            "old_passwords": [
                {
                    "id": op.entry_id,
                    "website": op.website,
                    "username": op.username,
                    "age_category": op.age_category,
                    "age_days": op.age_days,
                    "age_text": op.age_text,
                    "age_icon": op.age_icon,
                    "last_modified": op.last_modified,
                }
                for op in self.old_passwords
            ],
            "reused_count": self.reused_count,
            "average_strength": self.average_strength,
            "score": self.score,
            "security_score": self.score,  # Alias for backward compat
            "statistics": self.strength_distribution.as_dict(),
            "recommendations": [
                {
                    "type": r.rec_type,
                    "priority": r.priority,
                    "title": r.title,
                    "description": r.description,
                    "icon": r.icon,
                }
                for r in self.recommendations
            ],
            "age_statistics": self.age_statistics,
        }


# ===========================================================================
# SERVICE CLASS
# ===========================================================================


class PasswordHealthService:
    """
    UI-independent service for analyzing password health.

    This service takes a list of password entries (with decrypted passwords)
    and produces a HealthReport containing:
    - Weak password identification
    - Duplicate detection (via SHA-256 hashing of plaintext)
    - Age-based staleness tracking
    - An overall security score (0-100)
    - Prioritized recommendations

    The service has no dependency on any UI framework (Tkinter, Flask, Flet).
    It only depends on core utilities (strength_checker, password_age).
    """

    def __init__(self):
        """Initialize the service with an optional advanced strength checker."""
        self._strength_checker = (
            AdvancedPasswordStrengthChecker() if _HAS_STRENGTH_CHECKER else None
        )
        logger.info("PasswordHealthService initialized")

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def analyze_health(self, entries: List[Any]) -> HealthReport:
        """
        Perform a comprehensive health analysis on a list of password entries.

        Each entry is expected to have the following attributes (matching the
        PasswordEntry type from core.types or core.password_manager):
          - id / entry_id (int)
          - website (str)
          - username (str)
          - password (str) — the decrypted plaintext password
          - created_at (datetime | str | None)
          - modified_at / last_modified (datetime | str | None)

        The method is safe to call with an empty list — it returns a zeroed
        report in that case.

        Args:
            entries: List of password entry objects/dicts with decrypted passwords

        Returns:
            HealthReport with all analysis results
        """
        report = HealthReport(total_count=len(entries))

        if not entries:
            return report

        # --- Pass 1: Analyze each entry ---
        # Track password hashes to detect duplicates. We hash the plaintext
        # password with SHA-256 so we can compare without storing the actual
        # password twice. SHA-256 is sufficient here because we only need
        # collision resistance for grouping, not preimage resistance.
        password_hashes: Dict[str, Dict[str, Any]] = {}
        strength_scores: List[int] = []
        age_days_list: List[int] = []

        for entry in entries:
            # Normalize entry access (support both dict and object)
            entry_id = _get(entry, "id", _get(entry, "entry_id", 0))
            website = _get(entry, "website", "")
            username = _get(entry, "username", "")
            password = _get(entry, "password", "")
            created_at = _get(entry, "created_at", None)
            modified_at = _get(
                entry, "modified_at", _get(entry, "last_modified", None)
            )

            # --- Strength analysis ---
            strength = self._analyze_strength(password)
            strength_score = self._strength_to_score(strength)
            strength_scores.append(strength_score)

            # Update distribution
            dist = report.strength_distribution
            if strength == "very_weak":
                dist.very_weak += 1
            elif strength == "weak":
                dist.weak += 1
            elif strength == "fair":
                dist.fair += 1
            elif strength == "good":
                dist.good += 1
            elif strength == "strong":
                dist.strong += 1
            elif strength == "very_strong":
                dist.very_strong += 1

            # Record weak passwords
            if strength in ("very_weak", "weak"):
                issues = self._get_password_issues(password)
                report.weak_passwords.append(
                    WeakPasswordInfo(
                        entry_id=entry_id,
                        website=website,
                        username=username,
                        strength=strength,
                        issues=issues,
                    )
                )

            # --- Age analysis ---
            if _HAS_AGE_UTILS and (created_at or modified_at):
                try:
                    created_date = _parse_datetime(created_at)
                    modified_date = _parse_datetime(modified_at)

                    if created_date or modified_date:
                        # Use the most recent of created/modified
                        age_days = calculate_age_days(
                            created_date or modified_date,
                            modified_date or created_date,
                        )
                        age_category = get_age_category(age_days)
                        age_days_list.append(age_days)

                        if age_category in ("moderate", "old"):
                            ref_date = max(
                                filter(None, [created_date, modified_date])
                            )
                            report.old_passwords.append(
                                OldPasswordInfo(
                                    entry_id=entry_id,
                                    website=website,
                                    username=username,
                                    age_category=age_category,
                                    age_days=age_days,
                                    age_text=format_age_human_readable(age_days),
                                    age_icon=get_age_icon(age_category),
                                    last_modified=ref_date.strftime(
                                        "%Y-%m-%d %H:%M"
                                    ),
                                )
                            )
                except Exception as e:
                    logger.warning(
                        f"Failed to calculate age for entry {entry_id}: {e}"
                    )

            # --- Duplicate detection ---
            pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
            if pw_hash in password_hashes:
                existing = password_hashes[pw_hash]
                report.duplicate_groups.append(
                    DuplicatePasswordInfo(
                        entry_id=entry_id,
                        website=website,
                        username=username,
                        duplicate_of_website=existing["website"],
                        duplicate_of_id=existing["id"],
                    )
                )
            else:
                password_hashes[pw_hash] = {"id": entry_id, "website": website}

        # --- Pass 2: Aggregate statistics ---
        report.reused_count = len(report.duplicate_groups)

        # Average strength
        if strength_scores:
            avg_score = sum(strength_scores) / len(strength_scores)
            report.average_strength = self._score_to_strength(avg_score)

        # Age statistics
        if _HAS_AGE_UTILS and age_days_list:
            report.age_statistics = calculate_age_statistics(age_days_list)

        # --- Pass 3: Calculate score and recommendations ---
        report.score = self._calculate_security_score(report)
        report.recommendations = self._generate_recommendations(report)

        logger.info(
            f"Health analysis complete: {report.total_count} entries, "
            f"score={report.score}, weak={len(report.weak_passwords)}, "
            f"dupes={report.reused_count}, old={len(report.old_passwords)}"
        )

        return report

    def get_security_score(self, report: HealthReport) -> int:
        """
        Get the security score from a health report.

        This is a convenience accessor — the score is already computed during
        analyze_health(). Use this when you need to recalculate from a
        modified report.

        Args:
            report: A HealthReport instance

        Returns:
            int: Security score from 0 (worst) to 100 (best)
        """
        return self._calculate_security_score(report)

    def get_recommendations(self, report: HealthReport) -> List[Recommendation]:
        """
        Get recommendations from a health report.

        Like get_security_score(), this is a convenience accessor — the
        recommendations are already populated during analyze_health().

        Args:
            report: A HealthReport instance

        Returns:
            List of Recommendation objects sorted by priority (high first)
        """
        return self._generate_recommendations(report)

    # ------------------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------------------

    def _analyze_strength(self, password: str) -> str:
        """
        Determine the strength level of a password.

        Uses the AdvancedPasswordStrengthChecker if available, otherwise
        falls back to a simple heuristic-based analysis.

        Args:
            password: Plaintext password to analyze

        Returns:
            str: One of "very_weak", "weak", "fair", "good", "strong",
                 "very_strong"
        """
        if self._strength_checker:
            try:
                metrics = self._strength_checker.analyze_password(password)
                return metrics.strength_level.value
            except Exception:
                pass  # Fall through to simple analysis

        return self._simple_strength_analysis(password)

    @staticmethod
    def _simple_strength_analysis(password: str) -> str:
        """
        Simple heuristic-based password strength analysis.

        This is the fallback when AdvancedPasswordStrengthChecker is not
        available. It scores passwords based on length and character variety.

        Scoring:
        - Length >= 12: +25, >= 8: +15, >= 6: +5
        - Has lowercase: +10
        - Has uppercase: +10
        - Has digits: +10
        - Has special chars: +15
        - Is a common password: -30

        Args:
            password: Plaintext password to analyze

        Returns:
            str: Strength level string
        """
        score = 0
        length = len(password)

        # Length scoring — longer passwords have exponentially more entropy
        if length >= 12:
            score += 25
        elif length >= 8:
            score += 15
        elif length >= 6:
            score += 5

        # Character variety scoring — each class roughly adds
        # log2(class_size) bits of entropy per character
        if any(c.islower() for c in password):
            score += 10
        if any(c.isupper() for c in password):
            score += 10
        if any(c.isdigit() for c in password):
            score += 10
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 15

        # Common password penalty — these are in every dictionary attack list
        if password.lower() in [
            "password",
            "123456",
            "qwerty",
            "abc123",
            "letmein",
            "password123",
        ]:
            score -= 30

        if score >= 60:
            return "very_strong"
        elif score >= 50:
            return "strong"
        elif score >= 40:
            return "good"
        elif score >= 30:
            return "fair"
        elif score >= 20:
            return "weak"
        else:
            return "very_weak"

    @staticmethod
    def _get_password_issues(password: str) -> List[str]:
        """
        Identify specific issues with a password.

        Returns a human-readable list of problems that explain why a
        password is considered weak. Used in the UI to show actionable
        details next to each weak entry.

        Args:
            password: Plaintext password to check

        Returns:
            List of issue descriptions
        """
        issues = []

        if len(password) < 8:
            issues.append("Too short (less than 8 characters)")

        if not any(c.islower() for c in password):
            issues.append("No lowercase letters")

        if not any(c.isupper() for c in password):
            issues.append("No uppercase letters")

        if not any(c.isdigit() for c in password):
            issues.append("No numbers")

        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("No special characters")

        if password.lower() in [
            "password",
            "123456",
            "qwerty",
            "abc123",
            "letmein",
            "password123",
        ]:
            issues.append("Common/dictionary password")

        return issues

    @staticmethod
    def _strength_to_score(strength: str) -> int:
        """Map a strength level string to a numeric score (0-100)."""
        mapping = {
            "very_weak": 10,
            "weak": 25,
            "fair": 45,
            "good": 65,
            "strong": 80,
            "very_strong": 95,
        }
        return mapping.get(strength, 0)

    @staticmethod
    def _score_to_strength(score: float) -> str:
        """Map a numeric score back to a strength level string."""
        if score >= 85:
            return "very_strong"
        elif score >= 70:
            return "strong"
        elif score >= 55:
            return "good"
        elif score >= 35:
            return "fair"
        elif score >= 18:
            return "weak"
        else:
            return "very_weak"

    @staticmethod
    def _calculate_security_score(report: HealthReport) -> int:
        """
        Calculate an overall security score (0-100) from a health report.

        Scoring formula:
        - Start at 100 points
        - Deduct up to 40 points proportionally for weak passwords
        - Deduct up to 30 points proportionally for old passwords
        - Deduct up to 20 points proportionally for duplicates
        - Bonus +10 if > 80% of passwords are good/strong/very_strong

        The score is clamped to [0, 100].

        Args:
            report: HealthReport with populated analysis data

        Returns:
            int: Security score between 0 and 100
        """
        total = report.total_count
        if total == 0:
            return 0

        score = 100.0

        weak_count = len(report.weak_passwords)
        old_count = len(report.old_passwords)
        dupe_count = report.reused_count

        # Proportional deductions — the more issues relative to total
        # passwords, the more points are deducted.
        score -= (weak_count / total) * 40
        score -= (old_count / total) * 30
        score -= (dupe_count / total) * 20

        # Bonus for having predominantly strong passwords
        dist = report.strength_distribution
        strong_count = dist.good + dist.strong + dist.very_strong
        if strong_count / total > 0.8:
            score += 10

        return max(0, min(100, int(score)))

    @staticmethod
    def _generate_recommendations(report: HealthReport) -> List[Recommendation]:
        """
        Generate prioritized security recommendations based on the report.

        Recommendations are sorted by priority: high > medium > low.

        Args:
            report: HealthReport with populated analysis data

        Returns:
            List of Recommendation objects
        """
        recommendations = []

        weak_count = len(report.weak_passwords)
        dupe_count = report.reused_count
        old_count = len(report.old_passwords)

        if weak_count > 0:
            recommendations.append(
                Recommendation(
                    rec_type="weak_passwords",
                    priority="high",
                    title=(
                        f"Update {weak_count} weak "
                        f'password{"s" if weak_count != 1 else ""}'
                    ),
                    description=(
                        "Replace weak passwords with strong, randomly "
                        "generated ones using the built-in generator."
                    ),
                    icon="warning",
                )
            )

        if dupe_count > 0:
            recommendations.append(
                Recommendation(
                    rec_type="duplicates",
                    priority="high",
                    title=(
                        f"Fix {dupe_count} duplicate "
                        f'password{"s" if dupe_count != 1 else ""}'
                    ),
                    description=(
                        "Use unique passwords for each account. If one "
                        "account is breached, shared passwords expose "
                        "all linked accounts."
                    ),
                    icon="duplicate",
                )
            )

        if old_count > 0:
            recommendations.append(
                Recommendation(
                    rec_type="old_passwords",
                    priority="medium",
                    title=(
                        f"Update {old_count} old "
                        f'password{"s" if old_count != 1 else ""}'
                    ),
                    description=(
                        "Regularly updating passwords reduces the window of "
                        "exposure from undetected breaches."
                    ),
                    icon="calendar",
                )
            )

        # Positive feedback when everything is good
        if (
            report.score >= 80
            and weak_count == 0
            and dupe_count == 0
        ):
            recommendations.append(
                Recommendation(
                    rec_type="excellent",
                    priority="low",
                    title="Excellent password security!",
                    description=(
                        "Your passwords are in great shape. Keep up the "
                        "good work and continue using strong, unique passwords."
                    ),
                    icon="check",
                )
            )

        # Sort by priority: high first
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 99))

        return recommendations


# ===========================================================================
# HELPER FUNCTIONS
# ===========================================================================


def _get(obj: Any, key: str, default: Any = None) -> Any:
    """
    Get an attribute or dict key from an object.

    Supports both dict-like and object-like access so the service works
    with PasswordEntry TypedDicts, dataclasses, and plain dicts.

    Args:
        obj: The object to read from
        key: Attribute or key name
        default: Value to return if not found

    Returns:
        The value, or default if not found
    """
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _parse_datetime(value: Any) -> Optional[datetime]:
    """
    Parse a value into a datetime object.

    Handles:
    - datetime objects (returned as-is)
    - ISO-format strings (with or without timezone)
    - None (returns None)

    Args:
        value: The value to parse

    Returns:
        datetime or None if parsing fails
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    return None


# ===========================================================================
# FACTORY FUNCTION
# ===========================================================================


def create_password_health_service() -> PasswordHealthService:
    """
    Factory function to create a PasswordHealthService instance.

    Returns:
        PasswordHealthService: Configured service instance
    """
    return PasswordHealthService()
