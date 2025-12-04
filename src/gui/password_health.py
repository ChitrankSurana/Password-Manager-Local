#!/usr/bin/env python3
"""
Personal Password Manager - Password Health Dashboard
======================================================

This module provides a comprehensive password health analysis dashboard
for the GUI application, analyzing password strength, detecting duplicates,
identifying old passwords, and providing security recommendations.

Key Features:
- Security score calculation with visual gauge
- Weak password detection with detailed issues
- Duplicate password identification
- Old password tracking (6+ months)
- Password strength distribution statistics
- Actionable security recommendations
- Visual charts and progress indicators

Author: Personal Password Manager
Version: 2.2.0
"""

import hashlib
from datetime import datetime
from tkinter import messagebox
from typing import Any, Dict, List

import customtkinter as ctk

from ..core.logging_config import get_logger
from ..core.password_manager import PasswordEntry, PasswordManagerCore
from ..utils.password_age import (
    AGE_THRESHOLD_FRESH,
    AGE_THRESHOLD_MODERATE,
    calculate_age_days,
    calculate_age_statistics,
    format_age_human_readable,
    get_age_category,
    get_age_color,
    get_age_icon,
)
from ..utils.strength_checker import AdvancedPasswordStrengthChecker
from .error_dialog import show_error, show_warning
from .themes import get_theme

logger = get_logger(__name__)


class PasswordHealthDashboard(ctk.CTkToplevel):
    """
    Password Health Analysis Dashboard

    Provides comprehensive analysis of user's password security including:
    - Overall security score
    - Weak password detection
    - Duplicate password identification
    - Old password tracking
    - Security recommendations
    """

    def __init__(self, parent, password_manager: PasswordManagerCore, session_id: str, theme=None):
        super().__init__(parent)

        self.password_manager = password_manager
        self.session_id = session_id
        self.theme = theme or get_theme()
        self.strength_checker = AdvancedPasswordStrengthChecker()

        self.title("Password Health Dashboard")
        self.geometry("900x700")

        # Make window modal
        self.transient(parent)
        self.grab_set()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"900x700+{x}+{y}")

        # Analysis data
        self.analysis_results = None
        self.passwords = []

        # Create UI
        self._create_ui()

        # Load and analyze passwords
        self._load_and_analyze()

    def _create_ui(self):
        """Create the dashboard UI"""
        colors = self.theme.get_colors()

        # Header
        header_frame = ctk.CTkFrame(self, fg_color=colors["surface"])
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        header_label = ctk.CTkLabel(
            header_frame,
            text="🛡️ Password Health Dashboard",
            font=("Segoe UI", 24, "bold"),
            text_color=colors["text_primary"],
        )
        header_label.pack(pady=15)

        subtitle = ctk.CTkLabel(
            header_frame,
            text="Comprehensive analysis of your password security",
            font=("Segoe UI", 12),
            text_color=colors["text_secondary"],
        )
        subtitle.pack(pady=(0, 15))

        # Main content area with tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)

        # Create tabs
        self.tab_overview = self.tabview.add("Overview")
        self.tab_weak = self.tabview.add("Weak Passwords")
        self.tab_duplicates = self.tabview.add("Duplicates")
        self.tab_old = self.tabview.add("Old Passwords")
        self.tab_stats = self.tabview.add("Statistics")

        # Create tab content (will be populated after analysis)
        self._create_overview_tab()
        self._create_weak_passwords_tab()
        self._create_duplicates_tab()
        self._create_old_passwords_tab()
        self._create_statistics_tab()

        # Bottom buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        refresh_btn = ctk.CTkButton(
            button_frame, text="🔄 Refresh Analysis", command=self._load_and_analyze, width=150
        )
        refresh_btn.pack(side="left", padx=5)

        close_btn = ctk.CTkButton(button_frame, text="Close", command=self.destroy, width=150)
        close_btn.pack(side="right", padx=5)

    def _create_overview_tab(self):
        """Create the overview tab"""
        colors = self.theme.get_colors()

        # Security score frame
        self.score_frame = ctk.CTkFrame(self.tab_overview, fg_color=colors["surface"])
        self.score_frame.pack(fill="x", padx=20, pady=20)

        score_title = ctk.CTkLabel(
            self.score_frame, text="Overall Security Score", font=("Segoe UI", 18, "bold")
        )
        score_title.pack(pady=(15, 10))

        # Score display (will be updated with actual score)
        self.score_label = ctk.CTkLabel(
            self.score_frame,
            text="--",
            font=("Segoe UI", 48, "bold"),
            text_color=colors["text_primary"],
        )
        self.score_label.pack(pady=10)

        # Progress bar for score
        self.score_progress = ctk.CTkProgressBar(self.score_frame, width=400, height=20)
        self.score_progress.pack(pady=10)
        self.score_progress.set(0)

        self.score_description = ctk.CTkLabel(
            self.score_frame,
            text="Analyzing...",
            font=("Segoe UI", 12),
            text_color=colors["text_secondary"],
        )
        self.score_description.pack(pady=(0, 15))

        # Quick stats frame
        self.stats_frame = ctk.CTkFrame(self.tab_overview, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=20, pady=10)

        # Will be populated with stats cards

        # Recommendations frame
        self.recommendations_frame = ctk.CTkFrame(self.tab_overview, fg_color=colors["surface"])
        self.recommendations_frame.pack(fill="both", expand=True, padx=20, pady=10)

        rec_title = ctk.CTkLabel(
            self.recommendations_frame,
            text="🎯 Security Recommendations",
            font=("Segoe UI", 16, "bold"),
        )
        rec_title.pack(pady=15, anchor="w", padx=20)

        # Scrollable recommendations list
        self.recommendations_list = ctk.CTkScrollableFrame(
            self.recommendations_frame, fg_color="transparent"
        )
        self.recommendations_list.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def _create_weak_passwords_tab(self):
        """Create the weak passwords tab"""
        colors = self.theme.get_colors()

        # Header
        header = ctk.CTkLabel(
            self.tab_weak, text="⚠️ Weak Passwords", font=("Segoe UI", 18, "bold")
        )
        header.pack(pady=15)

        description = ctk.CTkLabel(
            self.tab_weak,
            text="These passwords are vulnerable to attacks. Update them immediately.",
            font=("Segoe UI", 11),
            text_color=colors["text_secondary"],
        )
        description.pack(pady=(0, 15))

        # Scrollable list
        self.weak_passwords_list = ctk.CTkScrollableFrame(self.tab_weak, fg_color="transparent")
        self.weak_passwords_list.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def _create_duplicates_tab(self):
        """Create the duplicates tab"""
        colors = self.theme.get_colors()

        # Header
        header = ctk.CTkLabel(
            self.tab_duplicates, text="🔄 Duplicate Passwords", font=("Segoe UI", 18, "bold")
        )
        header.pack(pady=15)

        description = ctk.CTkLabel(
            self.tab_duplicates,
            text="These passwords are reused across multiple accounts. Use unique passwords for each account.",
            font=(
                "Segoe UI",
                11),
            text_color=colors["text_secondary"],
        )
        description.pack(pady=(0, 15))

        # Scrollable list
        self.duplicates_list = ctk.CTkScrollableFrame(self.tab_duplicates, fg_color="transparent")
        self.duplicates_list.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def _create_old_passwords_tab(self):
        """Create the old passwords tab"""
        colors = self.theme.get_colors()

        # Header
        header = ctk.CTkLabel(self.tab_old, text="📅 Old Passwords", font=("Segoe UI", 18, "bold"))
        header.pack(pady=15)

        description = ctk.CTkLabel(
            self.tab_old,
            text=f"Passwords older than {AGE_THRESHOLD_FRESH} days should be updated. Critical: {AGE_THRESHOLD_MODERATE}+ days old.",
            font=(
                "Segoe UI",
                11),
            text_color=colors["text_secondary"],
        )
        description.pack(pady=(0, 15))

        # Scrollable list
        self.old_passwords_list = ctk.CTkScrollableFrame(self.tab_old, fg_color="transparent")
        self.old_passwords_list.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def _create_statistics_tab(self):
        """Create the statistics tab"""
        self.theme.get_colors()

        # Header
        header = ctk.CTkLabel(
            self.tab_stats, text="📊 Password Strength Distribution", font=("Segoe UI", 18, "bold")
        )
        header.pack(pady=15)

        # Statistics will be displayed as a bar chart using progress bars
        self.stats_content = ctk.CTkFrame(self.tab_stats, fg_color="transparent")
        self.stats_content.pack(fill="both", expand=True, padx=40, pady=20)

    def _load_and_analyze(self):
        """Load passwords and perform analysis"""
        try:
            # Get all passwords for the user
            self.passwords = self.password_manager.get_password_entries(self.session_id)

            if not self.passwords:
                show_warning(
                    title="No Passwords",
                    message="You don't have any passwords stored yet.",
                    suggestions=["Add some passwords to see health analysis"],
                    parent=self,
                )
                return

            # Perform analysis
            self.analysis_results = self._analyze_password_health(self.passwords)

            # Update UI with results
            self._update_overview_tab()
            self._update_weak_passwords_tab()
            self._update_duplicates_tab()
            self._update_old_passwords_tab()
            self._update_statistics_tab()

            logger.info(f"Password health analysis completed for {len(self.passwords)} passwords")

        except Exception as e:
            logger.error(f"Failed to analyze password health: {e}")
            show_error(
                title="Analysis Failed",
                message="Failed to analyze password health",
                details=str(e),
                suggestions=["Try refreshing the analysis", "Check your session is still valid"],
                parent=self,
            )

    def _analyze_password_health(self, passwords: List[PasswordEntry]) -> Dict[str, Any]:
        """
        Analyze password health and return detailed report

        Args:
            passwords: List of password entries to analyze

        Returns:
            Dictionary containing analysis results
        """
        analysis = {
            "total_passwords": len(passwords),
            "weak_passwords": [],
            "duplicate_passwords": [],
            "old_passwords": [],
            "security_score": 0,
            "recommendations": [],
            "statistics": {
                "very_weak": 0,
                "weak": 0,
                "fair": 0,
                "good": 0,
                "strong": 0,
                "very_strong": 0,
            },
        }

        if not passwords:
            return analysis

        # Track password hashes to detect duplicates
        password_hashes = {}

        for password in passwords:
            # Analyze strength using advanced checker
            try:
                metrics = self.strength_checker.analyze_password(password.password)
                strength = metrics.strength_level.value
            except Exception:
                # Fallback to simple analysis
                strength = self._simple_strength_analysis(password.password)

            # Update statistics
            if strength in analysis["statistics"]:
                analysis["statistics"][strength] += 1

            # Check for weak passwords
            if strength in ["very_weak", "weak"]:
                issues = self._get_password_issues(password.password)
                analysis["weak_passwords"].append(
                    {
                        "id": password.id,
                        "website": password.website,
                        "username": password.username,
                        "strength": strength,
                        "issues": issues,
                    }
                )

            # Check for old passwords using new age utilities
            if password.created_at and password.last_modified:
                try:
                    # Parse datetime if it's a string
                    if isinstance(password.created_at, str):
                        created_date = datetime.fromisoformat(
                            password.created_at.replace("Z", "+00:00")
                        )
                    else:
                        created_date = password.created_at

                    if isinstance(password.last_modified, str):
                        modified_date = datetime.fromisoformat(
                            password.last_modified.replace("Z", "+00:00")
                        )
                    else:
                        modified_date = password.last_modified

                    # Calculate age using most recent timestamp
                    age_days = calculate_age_days(created_date, modified_date)
                    age_category = get_age_category(age_days)
                    age_text = format_age_human_readable(age_days)
                    age_icon = get_age_icon(age_category)

                    # Add to old passwords if moderate or old
                    if age_category in ["moderate", "old"]:
                        analysis["old_passwords"].append(
                            {
                                "id": password.id,
                                "website": password.website,
                                "username": password.username,
                                "age_category": age_category,
                                "age_days": age_days,
                                "age_text": age_text,
                                "age_icon": age_icon,
                                "last_modified": max(created_date, modified_date).strftime(
                                    "%Y-%m-%d %H:%M"
                                ),
                            }
                        )
                except Exception as e:
                    logger.warning(f"Failed to calculate age for password {password.id}: {e}")

            # Check for duplicate passwords
            password_hash = hashlib.sha256(password.password.encode()).hexdigest()
            if password_hash in password_hashes:
                # Found duplicate
                existing = password_hashes[password_hash]
                analysis["duplicate_passwords"].append(
                    {
                        "id": password.id,
                        "website": password.website,
                        "username": password.username,
                        "duplicate_o": existing["website"],
                        "duplicate_id": existing["id"],
                    }
                )
            else:
                password_hashes[password_hash] = {
                    "id": password.id,
                    "website": password.website,
                    "username": password.username,
                }

        # Calculate security score
        total = len(passwords)
        strong_count = (
            analysis["statistics"]["good"]
            + analysis["statistics"]["strong"]
            + analysis["statistics"]["very_strong"]
        )
        weak_count = len(analysis["weak_passwords"])
        old_count = len(analysis["old_passwords"])
        duplicate_count = len(analysis["duplicate_passwords"])

        # Base score
        security_score = 100

        # Deduct points for issues
        if total > 0:
            security_score -= (weak_count / total) * 40
            security_score -= (old_count / total) * 30
            security_score -= (duplicate_count / total) * 20

            # Bonus for having many strong passwords
            if strong_count / total > 0.8:
                security_score += 10

        analysis["security_score"] = max(0, min(100, int(security_score)))

        # Generate recommendations
        if weak_count > 0:
            analysis["recommendations"].append(
                {
                    "type": "weak_passwords",
                    "priority": "high",
                    "title": f'Update {weak_count} weak password{"s" if weak_count != 1 else ""}',
                    "description": "Replace weak passwords with strong, randomly generated ones.",
                    "icon": "⚠️",
                }
            )

        if duplicate_count > 0:
            analysis["recommendations"].append(
                {
                    "type": "duplicates",
                    "priority": "high",
                    "title": f'Fix {duplicate_count} duplicate password{
                        "s" if duplicate_count != 1 else ""}',
                    "description": "Use unique passwords for each account to improve security.",
                    "icon": "🔄",
                })

        if old_count > 0:
            analysis["recommendations"].append(
                {
                    "type": "old_passwords",
                    "priority": "medium",
                    "title": f'Update {old_count} old password{"s" if old_count != 1 else ""}',
                    "description": "Regularly updating passwords reduces security risks.",
                    "icon": "📅",
                }
            )

        if analysis["security_score"] >= 80 and weak_count == 0 and duplicate_count == 0:
            analysis["recommendations"].append(
                {
                    "type": "excellent",
                    "priority": "low",
                    "title": "🎉 Excellent password security!",
                    "description": "Your passwords are in great shape. Keep up the good work!",
                    "icon": "✅",
                }
            )

        # Calculate password age statistics
        age_days_list = []
        for password in passwords:
            if password.created_at and password.last_modified:
                try:
                    # Parse datetime if it's a string
                    if isinstance(password.created_at, str):
                        created_date = datetime.fromisoformat(
                            password.created_at.replace("Z", "+00:00")
                        )
                    else:
                        created_date = password.created_at

                    if isinstance(password.last_modified, str):
                        modified_date = datetime.fromisoformat(
                            password.last_modified.replace("Z", "+00:00")
                        )
                    else:
                        modified_date = password.last_modified

                    age_days = calculate_age_days(created_date, modified_date)
                    age_days_list.append(age_days)
                except Exception:
                    pass  # Skip passwords with invalid dates

        # Add age statistics to analysis
        analysis["age_statistics"] = calculate_age_statistics(age_days_list)

        return analysis

    def _simple_strength_analysis(self, password: str) -> str:
        """Simple password strength analysis (fallback)"""
        score = 0
        length = len(password)

        # Length scoring
        if length >= 12:
            score += 25
        elif length >= 8:
            score += 15
        elif length >= 6:
            score += 5

        # Character variety scoring
        if any(c.islower() for c in password):
            score += 10
        if any(c.isupper() for c in password):
            score += 10
        if any(c.isdigit() for c in password):
            score += 10
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 15

        # Common password penalty
        if password.lower() in ["password", "123456", "qwerty", "abc123"]:
            score -= 30

        # Convert score to strength level
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

    def _get_password_issues(self, password: str) -> List[str]:
        """Get specific issues with a password"""
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

        if password.lower() in ["password", "123456", "qwerty", "abc123", "letmein"]:
            issues.append("Common/dictionary password")

        return issues

    def _update_overview_tab(self):
        """Update the overview tab with analysis results"""
        if not self.analysis_results:
            return

        colors = self.theme.get_colors()
        score = self.analysis_results["security_score"]

        # Update score display
        self.score_label.configure(text=f"{score}")
        self.score_progress.set(score / 100)

        # Color code based on score
        if score >= 80:
            score_color = colors.get("success", "#4CAF50")
            description = "Excellent - Your passwords are secure!"
        elif score >= 60:
            score_color = colors.get("warning", "#FF9800")
            description = "Good - Some improvements recommended"
        elif score >= 40:
            score_color = colors.get("warning", "#FF9800")
            description = "Fair - Several security issues found"
        else:
            score_color = colors.get("error", "#F44336")
            description = "Poor - Immediate action required"

        self.score_label.configure(text_color=score_color)
        self.score_description.configure(text=description)

        # Clear and update stats cards
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        # Create stats cards
        stats = [
            ("Total Passwords", self.analysis_results["total_passwords"], "📝"),
            ("Weak Passwords", len(self.analysis_results["weak_passwords"]), "⚠️"),
            ("Duplicates", len(self.analysis_results["duplicate_passwords"]), "🔄"),
            ("Old Passwords", len(self.analysis_results["old_passwords"]), "📅"),
        ]

        for i, (title, value, icon) in enumerate(stats):
            card = self._create_stat_card(self.stats_frame, title, value, icon)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="ew")

        self.stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Password Age Statistics Section
        age_stats = self.analysis_results.get("age_statistics", {})
        if (
            age_stats
            and age_stats.get("fresh_count", 0)
            + age_stats.get("moderate_count", 0)
            + age_stats.get("old_count", 0)
            > 0
        ):
            # Create age statistics frame
            age_stats_frame = ctk.CTkFrame(self.tab_overview, fg_color=colors["surface"])
            age_stats_frame.pack(fill="x", padx=20, pady=10)

            age_stats_title = ctk.CTkLabel(
                age_stats_frame, text="📊 Password Age Distribution", font=("Segoe UI", 16, "bold")
            )
            age_stats_title.pack(pady=15, anchor="w", padx=20)

            # Age distribution stats
            age_dist_frame = ctk.CTkFrame(age_stats_frame, fg_color="transparent")
            age_dist_frame.pack(fill="x", padx=20, pady=(0, 10))

            # Fresh, Moderate, Old counts
            age_categories = [
                (
                    "🟢 Fresh",
                    age_stats.get("fresh_count", 0),
                    f"Less than {AGE_THRESHOLD_FRESH} days",
                    colors.get("success", "#4CAF50"),
                ),
                (
                    "🟡 Moderate",
                    age_stats.get("moderate_count", 0),
                    f"{AGE_THRESHOLD_FRESH}-{AGE_THRESHOLD_MODERATE} days",
                    colors.get("warning", "#FF9800"),
                ),
                (
                    "🔴 Old",
                    age_stats.get("old_count", 0),
                    f"More than {AGE_THRESHOLD_MODERATE} days",
                    colors.get("error", "#F44336"),
                ),
            ]

            for i, (label, count, description, color) in enumerate(age_categories):
                cat_frame = ctk.CTkFrame(age_dist_frame, fg_color=colors["background"])
                cat_frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")

                cat_label = ctk.CTkLabel(
                    cat_frame, text=label, font=("Segoe UI", 12, "bold"), text_color=color
                )
                cat_label.pack(pady=(10, 5))

                count_label = ctk.CTkLabel(
                    cat_frame, text=str(count), font=("Segoe UI", 24, "bold"), text_color=color
                )
                count_label.pack(pady=5)

                desc_label = ctk.CTkLabel(
                    cat_frame,
                    text=description,
                    font=("Segoe UI", 9),
                    text_color=colors["text_secondary"],
                )
                desc_label.pack(pady=(0, 10))

            age_dist_frame.grid_columnconfigure((0, 1, 2), weight=1)

            # Additional age info
            age_info_frame = ctk.CTkFrame(age_stats_frame, fg_color="transparent")
            age_info_frame.pack(fill="x", padx=20, pady=(0, 15))

            avg_age = age_stats.get("average_age", 0)
            oldest_age = age_stats.get("oldest_age", 0)
            newest_age = age_stats.get("newest_age", 0)

            info_items = [
                f"Average age: {avg_age} days ({format_age_human_readable(avg_age)})",
                f"Oldest: {oldest_age} days ({format_age_human_readable(oldest_age)})",
                f"Newest: {newest_age} days ({format_age_human_readable(newest_age)})",
            ]

            for info in info_items:
                info_label = ctk.CTkLabel(
                    age_info_frame,
                    text=f"• {info}",
                    font=("Segoe UI", 11),
                    text_color=colors["text_secondary"],
                    anchor="w",
                )
                info_label.pack(fill="x", pady=2)

        # Update recommendations
        for widget in self.recommendations_list.winfo_children():
            widget.destroy()

        if self.analysis_results["recommendations"]:
            for rec in self.analysis_results["recommendations"]:
                self._create_recommendation_card(rec)
        else:
            no_rec = ctk.CTkLabel(
                self.recommendations_list,
                text="No recommendations - your passwords are in great shape!",
                font=("Segoe UI", 12),
                text_color=colors["text_secondary"],
            )
            no_rec.pack(pady=20)

    def _create_stat_card(self, parent, title: str, value: int, icon: str):
        """Create a statistics card"""
        colors = self.theme.get_colors()

        card = ctk.CTkFrame(parent, fg_color=colors["surface"])

        icon_label = ctk.CTkLabel(card, text=icon, font=("Segoe UI", 24))
        icon_label.pack(pady=(10, 5))

        value_label = ctk.CTkLabel(card, text=str(value), font=("Segoe UI", 28, "bold"))
        value_label.pack(pady=5)

        title_label = ctk.CTkLabel(
            card, text=title, font=("Segoe UI", 11), text_color=colors["text_secondary"]
        )
        title_label.pack(pady=(0, 10))

        return card

    def _create_recommendation_card(self, rec: Dict[str, str]):
        """Create a recommendation card"""
        colors = self.theme.get_colors()

        card = ctk.CTkFrame(self.recommendations_list, fg_color=colors["surface"])
        card.pack(fill="x", pady=5)

        # Priority indicator color
        priority_colors = {
            "high": colors.get("error", "#F44336"),
            "medium": colors.get("warning", "#FF9800"),
            "low": colors.get("info", "#2196F3"),
        }

        priority_color = priority_colors.get(rec.get("priority", "low"), colors["text_secondary"])

        # Header with icon and title
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 5))

        icon_label = ctk.CTkLabel(header_frame, text=rec.get("icon", "•"), font=("Segoe UI", 16))
        icon_label.pack(side="left", padx=(0, 10))

        title_label = ctk.CTkLabel(
            header_frame,
            text=rec["title"],
            font=("Segoe UI", 13, "bold"),
            text_color=priority_color,
        )
        title_label.pack(side="left")

        # Description
        desc_label = ctk.CTkLabel(
            card,
            text=rec["description"],
            font=("Segoe UI", 11),
            text_color=colors["text_secondary"],
        )
        desc_label.pack(anchor="w", padx=15, pady=(0, 15))

    def _update_weak_passwords_tab(self):
        """Update the weak passwords tab"""
        for widget in self.weak_passwords_list.winfo_children():
            widget.destroy()

        colors = self.theme.get_colors()
        weak_passwords = self.analysis_results.get("weak_passwords", [])

        if not weak_passwords:
            no_weak = ctk.CTkLabel(
                self.weak_passwords_list,
                text="✅ No weak passwords found! Great job!",
                font=("Segoe UI", 14),
                text_color=colors.get("success", "#4CAF50"),
            )
            no_weak.pack(pady=40)
            return

        for pwd_data in weak_passwords:
            self._create_password_issue_card(self.weak_passwords_list, pwd_data, "weak")

    def _update_duplicates_tab(self):
        """Update the duplicates tab"""
        for widget in self.duplicates_list.winfo_children():
            widget.destroy()

        colors = self.theme.get_colors()
        duplicates = self.analysis_results.get("duplicate_passwords", [])

        if not duplicates:
            no_dupes = ctk.CTkLabel(
                self.duplicates_list,
                text="✅ No duplicate passwords found! Excellent!",
                font=("Segoe UI", 14),
                text_color=colors.get("success", "#4CAF50"),
            )
            no_dupes.pack(pady=40)
            return

        for pwd_data in duplicates:
            self._create_password_issue_card(self.duplicates_list, pwd_data, "duplicate")

    def _update_old_passwords_tab(self):
        """Update the old passwords tab"""
        for widget in self.old_passwords_list.winfo_children():
            widget.destroy()

        colors = self.theme.get_colors()
        old_passwords = self.analysis_results.get("old_passwords", [])

        if not old_passwords:
            no_old = ctk.CTkLabel(
                self.old_passwords_list,
                text="✅ All passwords are recent! Well done!",
                font=("Segoe UI", 14),
                text_color=colors.get("success", "#4CAF50"),
            )
            no_old.pack(pady=40)
            return

        for pwd_data in old_passwords:
            self._create_password_issue_card(self.old_passwords_list, pwd_data, "old")

    def _update_statistics_tab(self):
        """Update the statistics tab with distribution chart"""
        for widget in self.stats_content.winfo_children():
            widget.destroy()

        self.theme.get_colors()
        stats = self.analysis_results.get("statistics", {})
        total = self.analysis_results.get("total_passwords", 1)

        # Define strength levels with colors
        strength_levels = [
            ("Very Strong", stats.get("very_strong", 0), "#4CAF50"),
            ("Strong", stats.get("strong", 0), "#8BC34A"),
            ("Good", stats.get("good", 0), "#FFC107"),
            ("Fair", stats.get("fair", 0), "#FF9800"),
            ("Weak", stats.get("weak", 0), "#FF5722"),
            ("Very Weak", stats.get("very_weak", 0), "#F44336"),
        ]

        for i, (level, count, color) in enumerate(strength_levels):
            # Row frame
            row_frame = ctk.CTkFrame(self.stats_content, fg_color="transparent")
            row_frame.pack(fill="x", pady=10)

            # Label
            label = ctk.CTkLabel(
                row_frame, text=f"{level}:", font=("Segoe UI", 13), width=120, anchor="w"
            )
            label.pack(side="left", padx=(0, 10))

            # Progress bar
            progress_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            progress_frame.pack(side="left", fill="x", expand=True)

            progress = ctk.CTkProgressBar(
                progress_frame, width=400, height=25, progress_color=color
            )
            progress.pack(side="left", fill="x", expand=True)
            progress.set(count / total if total > 0 else 0)

            # Count label
            count_label = ctk.CTkLabel(
                row_frame,
                text=f"{count} ({count / total * 100:.1f}%)" if total > 0 else "0 (0%)",
                font=("Segoe UI", 12),
                width=100,
                anchor="e",
            )
            count_label.pack(side="left", padx=(10, 0))

    def _create_password_issue_card(self, parent, pwd_data: Dict, issue_type: str):
        """Create a card showing password with issues"""
        colors = self.theme.get_colors()

        card = ctk.CTkFrame(parent, fg_color=colors["surface"])
        card.pack(fill="x", pady=5, padx=10)

        # Website and username
        header = ctk.CTkLabel(
            card,
            text=f"🌐 {pwd_data['website']} - {pwd_data['username']}",
            font=("Segoe UI", 13, "bold"),
            anchor="w",
        )
        header.pack(fill="x", padx=15, pady=(15, 5))

        # Issue-specific information
        if issue_type == "weak":
            issues = pwd_data.get("issues", [])
            if issues:
                issues_text = "Issues: " + ", ".join(issues)
                issues_label = ctk.CTkLabel(
                    card,
                    text=issues_text,
                    font=("Segoe UI", 11),
                    text_color=colors.get("error", "#F44336"),
                    anchor="w",
                    wraplength=750,
                )
                issues_label.pack(fill="x", padx=15, pady=(0, 10))

        elif issue_type == "duplicate":
            dupe_text = (
                f"⚠️ Same password used for: {pwd_data.get('duplicate_of', 'another account')}"
            )
            dupe_label = ctk.CTkLabel(
                card,
                text=dupe_text,
                font=("Segoe UI", 11),
                text_color=colors.get("warning", "#FF9800"),
                anchor="w",
            )
            dupe_label.pack(fill="x", padx=15, pady=(0, 10))

        elif issue_type == "old":
            # Get age information
            age_category = pwd_data.get("age_category", "old")
            age_icon = pwd_data.get("age_icon", "📅")
            age_text = pwd_data.get("age_text", "Unknown age")
            age_days = pwd_data.get("age_days", 0)
            last_modified = pwd_data.get("last_modified", "Unknown date")

            # Get theme mode and age colors
            theme_mode = self.theme.get_mode()
            text_color, bg_color = get_age_color(age_category, theme_mode)

            # Age info frame
            age_info_frame = ctk.CTkFrame(card, fg_color="transparent")
            age_info_frame.pack(fill="x", padx=15, pady=(0, 10))

            # Age badge with color coding
            age_badge = ctk.CTkLabel(
                age_info_frame,
                text=f"{age_icon} {age_text}",
                fg_color=bg_color,
                text_color=text_color,
                corner_radius=12,
                padx=12,
                pady=4,
                font=("Segoe UI", 11, "bold"),
            )
            age_badge.pack(side="left", padx=(0, 10))

            # Detailed age info
            detail_text = f"Password age: {age_days} days • Last updated: {last_modified}"
            detail_label = ctk.CTkLabel(
                age_info_frame,
                text=detail_text,
                font=("Segoe UI", 10),
                text_color=colors["text_secondary"],
                anchor="w",
            )
            detail_label.pack(side="left", fill="x", expand=True)

        # Action button
        action_btn = ctk.CTkButton(
            card,
            text="Update Password",
            width=120,
            height=28,
            command=lambda: self._open_update_dialog(pwd_data["id"]),
        )
        action_btn.pack(padx=15, pady=(0, 15), anchor="w")

    def _open_update_dialog(self, password_id: int):
        """Open dialog to update a password"""
        # TODO: Integrate with main window's edit password functionality
        messagebox.showinfo(
            "Update Password",
            "Password update functionality will be integrated with the main window.\n\n"
            f"For now, please use the main password list to update password ID: {password_id}",
            parent=self,
        )


if __name__ == "__main__":
    # Test the dashboard
    print("Password Health Dashboard module loaded successfully")
