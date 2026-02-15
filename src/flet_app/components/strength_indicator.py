"""
Password Strength Indicator Component
=======================================

A visual progress bar that shows password strength with color coding.
Used in the add/edit page and password generator to give real-time
feedback as the user types or generates a password.

Color mapping:
    Very Weak  -> Red
    Weak       -> Deep Orange
    Fair       -> Orange
    Good       -> Yellow-Green
    Strong     -> Light Green
    Very Strong-> Green

Version: 3.0.0
"""

import flet as ft
from typing import Optional


# Strength level -> (progress fraction, color, label)
STRENGTH_CONFIG = {
    "very_weak": (0.1, ft.Colors.RED, "Very Weak"),
    "weak": (0.25, ft.Colors.DEEP_ORANGE, "Weak"),
    "fair": (0.45, ft.Colors.ORANGE, "Fair"),
    "good": (0.65, ft.Colors.YELLOW_GREEN_700, "Good"),
    "strong": (0.8, ft.Colors.LIGHT_GREEN, "Strong"),
    "very_strong": (1.0, ft.Colors.GREEN, "Very Strong"),
}


class StrengthIndicator(ft.Column):
    """
    Visual password strength indicator with progress bar and label.

    Updates reactively when set_strength() is called with a new level.

    Args:
        initial_strength: Starting strength level (default: empty/hidden)
    """

    def __init__(self, initial_strength: Optional[str] = None):
        self._progress_bar = ft.ProgressBar(
            width=300,
            height=8,
            value=0,
            color=ft.Colors.GREY,
            bgcolor=ft.Colors.GREY_800,
        )

        self._label = ft.Text(
            value="",
            size=12,
            weight=ft.FontWeight.W_500,
        )

        super().__init__(
            controls=[self._progress_bar, self._label],
            spacing=4,
            visible=initial_strength is not None,
        )

        if initial_strength:
            self.set_strength(initial_strength)

    def set_strength(self, strength: str) -> None:
        """
        Update the indicator to reflect a new strength level.

        Args:
            strength: One of "very_weak", "weak", "fair", "good",
                      "strong", "very_strong"
        """
        config = STRENGTH_CONFIG.get(strength, STRENGTH_CONFIG["very_weak"])
        progress, color, label = config

        self._progress_bar.value = progress
        self._progress_bar.color = color
        self._label.value = label
        self._label.color = color
        self.visible = True
        self.update()

    def hide(self) -> None:
        """Hide the indicator (e.g., when the password field is empty)."""
        self.visible = False
        self.update()
