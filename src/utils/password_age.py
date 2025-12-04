#!/usr/bin/env python3
"""
Personal Password Manager - Password Age Utilities
==================================================

Utilities for calculating and formatting password age, including
age-based categorization and color coding for UI display.

Author: Personal Password Manager
Version: 2.2.0
"""

from datetime import datetime
from typing import Literal, Tuple

# Age thresholds in days
AGE_THRESHOLD_FRESH = 90  # < 90 days = fresh (green)
AGE_THRESHOLD_MODERATE = 180  # 90-180 days = moderate (yellow)
# > 180 days = old (red)

AgeCategory = Literal["fresh", "moderate", "old"]


def calculate_age_days(created_at: datetime, modified_at: datetime) -> int:
    """
    Calculate the age of a password in days.

    Uses the most recent timestamp between created_at and modified_at,
    since password changes reset the age.

    Args:
        created_at: When the password entry was created
        modified_at: When the password was last modified

    Returns:
        Number of days since password was last changed

    Example:
        >>> from datetime import datetime, timedelta
        >>> created = datetime.now() - timedelta(days=100)
        >>> modified = datetime.now() - timedelta(days=50)
        >>> calculate_age_days(created, modified)
        50
    """
    # Use the most recent timestamp (modified takes precedence)
    most_recent = max(created_at, modified_at)
    age = datetime.now() - most_recent
    return age.days


def format_age_human_readable(age_days: int) -> str:
    """
    Format password age in human-readable format.

    Args:
        age_days: Age in days

    Returns:
        Human-readable age string

    Examples:
        >>> format_age_human_readable(0)
        'Today'
        >>> format_age_human_readable(1)
        '1 day ago'
        >>> format_age_human_readable(30)
        '30 days ago'
        >>> format_age_human_readable(100)
        '3 months ago'
        >>> format_age_human_readable(400)
        '1 year ago'
    """
    if age_days == 0:
        return "Today"
    elif age_days == 1:
        return "1 day ago"
    elif age_days < 7:
        return f"{age_days} days ago"
    elif age_days < 30:
        weeks = age_days // 7
        return f"{weeks} {'week' if weeks == 1 else 'weeks'} ago"
    elif age_days < 365:
        months = age_days // 30
        return f"{months} {'month' if months == 1 else 'months'} ago"
    else:
        years = age_days // 365
        remaining_months = (age_days % 365) // 30
        if remaining_months == 0:
            return f"{years} {'year' if years == 1 else 'years'} ago"
        else:
            return f"{years}y {remaining_months}m ago"


def get_age_category(age_days: int) -> AgeCategory:
    """
    Categorize password age into fresh, moderate, or old.

    Args:
        age_days: Age in days

    Returns:
        Age category: "fresh", "moderate", or "old"

    Categories:
        - fresh: < 90 days (recommended rotation period)
        - moderate: 90-180 days (should consider updating)
        - old: > 180 days (should update soon)

    Examples:
        >>> get_age_category(50)
        'fresh'
        >>> get_age_category(120)
        'moderate'
        >>> get_age_category(200)
        'old'
    """
    if age_days < AGE_THRESHOLD_FRESH:
        return "fresh"
    elif age_days < AGE_THRESHOLD_MODERATE:
        return "moderate"
    else:
        return "old"


def get_age_color(age_category: AgeCategory, theme_mode: str = "dark") -> Tuple[str, str]:
    """
    Get foreground and background colors for age display based on category.

    Args:
        age_category: Age category ("fresh", "moderate", "old")
        theme_mode: Theme mode ("dark" or "light")

    Returns:
        Tuple of (text_color, background_color) in hex format

    Color Scheme:
        - Fresh: Green tones
        - Moderate: Yellow/Orange tones
        - Old: Red tones

    Examples:
        >>> get_age_color("fresh", "dark")
        ('#FFFFFF', '#2D5F2E')
        >>> get_age_color("old", "light")
        ('#8B0000', '#FFE4E4')
    """
    if theme_mode == "dark":
        colors = {
            "fresh": ("#FFFFFF", "#2D5F2E"),  # White text on dark green
            "moderate": ("#000000", "#F59E0B"),  # Black text on amber
            "old": ("#FFFFFF", "#991B1B"),  # White text on dark red
        }
    else:  # light mode
        colors = {
            "fresh": ("#155724", "#D4EDDA"),  # Dark green text on light green
            "moderate": ("#856404", "#FFF3CD"),  # Dark yellow text on light yellow
            "old": ("#8B0000", "#FFE4E4"),  # Dark red text on light red
        }

    return colors.get(age_category, ("#FFFFFF", "#6B7280"))  # Default gray


def get_age_icon(age_category: AgeCategory) -> str:
    """
    Get an emoji icon representing the age category.

    Args:
        age_category: Age category ("fresh", "moderate", "old")

    Returns:
        Emoji icon as string

    Examples:
        >>> get_age_icon("fresh")
        '🟢'
        >>> get_age_icon("moderate")
        '🟡'
        >>> get_age_icon("old")
        '🔴'
    """
    icons = {
        "fresh": "🟢",  # Green circle
        "moderate": "🟡",  # Yellow circle
        "old": "🔴",  # Red circle
    }
    return icons.get(age_category, "⚪")  # Default white circle


def should_update_password(age_days: int, threshold_days: int = 180) -> bool:
    """
    Determine if a password should be updated based on age.

    Args:
        age_days: Age of password in days
        threshold_days: Threshold for recommending update (default: 180)

    Returns:
        True if password should be updated, False otherwise

    Examples:
        >>> should_update_password(100)
        False
        >>> should_update_password(200)
        True
        >>> should_update_password(100, threshold_days=90)
        True
    """
    return age_days >= threshold_days


def calculate_age_statistics(age_days_list: list[int]) -> dict:
    """
    Calculate statistics about password ages in a vault.

    Args:
        age_days_list: List of password ages in days

    Returns:
        Dictionary with age statistics:
        - average_age: Average age in days
        - oldest_age: Oldest password age in days
        - newest_age: Newest password age in days
        - fresh_count: Number of fresh passwords
        - moderate_count: Number of moderate age passwords
        - old_count: Number of old passwords
        - old_percentage: Percentage of old passwords

    Example:
        >>> ages = [30, 60, 90, 120, 180, 200]
        >>> stats = calculate_age_statistics(ages)
        >>> stats['average_age']
        113
        >>> stats['old_count']
        1
    """
    if not age_days_list:
        return {
            "average_age": 0,
            "oldest_age": 0,
            "newest_age": 0,
            "fresh_count": 0,
            "moderate_count": 0,
            "old_count": 0,
            "old_percentage": 0.0,
        }

    total = len(age_days_list)
    fresh_count = sum(1 for age in age_days_list if age < AGE_THRESHOLD_FRESH)
    moderate_count = sum(
        1 for age in age_days_list if AGE_THRESHOLD_FRESH <= age < AGE_THRESHOLD_MODERATE
    )
    old_count = sum(1 for age in age_days_list if age >= AGE_THRESHOLD_MODERATE)

    return {
        "average_age": sum(age_days_list) // total,
        "oldest_age": max(age_days_list),
        "newest_age": min(age_days_list),
        "fresh_count": fresh_count,
        "moderate_count": moderate_count,
        "old_count": old_count,
        "old_percentage": (old_count / total) * 100 if total > 0 else 0.0,
    }


# Export all functions
__all__ = [
    "calculate_age_days",
    "format_age_human_readable",
    "get_age_category",
    "get_age_color",
    "get_age_icon",
    "should_update_password",
    "calculate_age_statistics",
    "AGE_THRESHOLD_FRESH",
    "AGE_THRESHOLD_MODERATE",
    "AgeCategory",
]
