#!/usr/bin/env python3
"""
Personal Password Manager - First Time Setup Wizard
====================================================

This module provides a welcome wizard for new users to configure their
initial preferences when logging in for the first time.

Key Features:
- Welcome message and application introduction
- Font size selection with live preview
- User-friendly onboarding experience
- Preference storage integration

Author: Personal Password Manager
Version: 2.2.0
"""

from typing import Callable, Optional

import customtkinter as ctk

from ..core.logging_config import get_logger
from ..core.settings_service import SettingsService
from .themes import get_theme

logger = get_logger(__name__)


class FirstTimeSetupWizard(ctk.CTkToplevel):
    """
    First-time setup wizard for new users

    This dialog appears on the first login and guides users through
    essential configuration options like font size selection.
    """

    def __init__(
        self,
        parent,
        user_id: int,
        settings_service: SettingsService,
        on_complete_callback: Optional[Callable] = None,
    ):
        """
        Initialize the first-time setup wizard

        Args:
            parent: Parent window
            user_id: User ID for storing preferences
            settings_service: Settings service for saving preferences
            on_complete_callback: Callback function when setup completes
        """
        super().__init__(parent)

        self.user_id = user_id
        self.settings_service = settings_service
        self.on_complete_callback = on_complete_callback
        self.theme = get_theme()
        self.selected_font_size = "medium"

        self.title("Welcome to Password Manager")
        self.geometry("700x550")
        self.resizable(False, False)

        # Make window modal
        self.transient(parent)
        self.grab_set()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.winfo_screenheight() // 2) - (550 // 2)
        self.geometry(f"700x550+{x}+{y}")

        # Create UI
        self._create_ui()

        logger.info(f"First-time setup wizard opened for user {user_id}")

    def _create_ui(self):
        """Create the wizard UI"""
        colors = self.theme.get_colors()

        # Main container
        main_frame = ctk.CTkFrame(self, fg_color=colors["background"])
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # Header with icon
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        welcome_icon = ctk.CTkLabel(header_frame, text="👋", font=("Segoe UI", 48))
        welcome_icon.pack(pady=(0, 10))

        welcome_title = ctk.CTkLabel(
            header_frame,
            text="Welcome to Password Manager!",
            font=("Segoe UI", 28, "bold"),
            text_color=colors["text_primary"],
        )
        welcome_title.pack()

        welcome_subtitle = ctk.CTkLabel(
            header_frame,
            text="Let's customize your experience",
            font=("Segoe UI", 14),
            text_color=colors["text_secondary"],
        )
        welcome_subtitle.pack(pady=(5, 0))

        # Content area
        content_frame = ctk.CTkFrame(main_frame, fg_color=colors["surface"], corner_radius=12)
        content_frame.pack(fill="both", expand=True, pady=20)

        # Font size section
        font_section = ctk.CTkFrame(content_frame, fg_color="transparent")
        font_section.pack(fill="x", padx=30, pady=20)

        font_title = ctk.CTkLabel(
            font_section,
            text="🔤 Choose Your Font Size",
            font=("Segoe UI", 18, "bold"),
            text_color=colors["text_primary"],
            anchor="w",
        )
        font_title.pack(fill="x", pady=(0, 10))

        font_description = ctk.CTkLabel(
            font_section,
            text="Select a font size that's comfortable for you. You can always change this later in Settings.",
            font=("Segoe UI", 12),
            text_color=colors["text_secondary"],
            anchor="w",
            wraplength=600,
        )
        font_description.pack(fill="x", pady=(0, 20))

        # Font size options
        font_options_frame = ctk.CTkFrame(font_section, fg_color="transparent")
        font_options_frame.pack(fill="x")

        font_sizes = [
            ("Small", "small", "90% - Compact"),
            ("Medium", "medium", "100% - Default"),
            ("Large", "large", "110% - Comfortable"),
            ("Extra Large", "extra_large", "120% - Maximum"),
        ]

        self.font_buttons = []

        for i, (display_name, value, description) in enumerate(font_sizes):
            # Create button card
            button_card = ctk.CTkFrame(
                font_options_frame, fg_color=colors["background"], corner_radius=8
            )
            button_card.grid(row=i // 2, column=i % 2, padx=8, pady=8, sticky="ew")

            button = ctk.CTkButton(
                button_card,
                text=display_name,
                font=("Segoe UI", 14, "bold"),
                command=lambda v=value: self._on_font_size_selected(v),
                width=280,
                height=50,
            )
            button.pack(padx=10, pady=(10, 5))
            self.font_buttons.append((button, value))

            desc_label = ctk.CTkLabel(
                button_card,
                text=description,
                font=("Segoe UI", 10),
                text_color=colors["text_secondary"],
            )
            desc_label.pack(pady=(0, 10))

        font_options_frame.grid_columnconfigure(0, weight=1)
        font_options_frame.grid_columnconfigure(1, weight=1)

        # Preview section
        preview_frame = ctk.CTkFrame(content_frame, fg_color=colors["background"], corner_radius=8)
        preview_frame.pack(fill="x", padx=30, pady=(0, 20))

        preview_title = ctk.CTkLabel(
            preview_frame,
            text="Preview",
            font=("Segoe UI", 12, "bold"),
            text_color=colors["text_secondary"],
        )
        preview_title.pack(pady=(10, 5))

        self.preview_label = ctk.CTkLabel(
            preview_frame,
            text="The quick brown fox jumps over the lazy dog",
            font=("Segoe UI", 14),
            text_color=colors["text_primary"],
        )
        self.preview_label.pack(pady=(5, 10))

        # Bottom buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

        skip_button = ctk.CTkButton(
            button_frame,
            text="Skip for Now",
            command=self._on_skip,
            fg_color=colors.get("secondary", "#6B7280"),
            hover_color=colors.get("secondary_hover", "#4B5563"),
            width=150,
            height=40,
        )
        skip_button.pack(side="left")

        self.continue_button = ctk.CTkButton(
            button_frame, text="Continue", command=self._on_continue, width=150, height=40
        )
        self.continue_button.pack(side="right")

        # Initially select medium
        self._on_font_size_selected("medium")

    def _on_font_size_selected(self, font_size: str):
        """Handle font size selection"""
        self.selected_font_size = font_size
        colors = self.theme.get_colors()

        # Update button states
        for button, value in self.font_buttons:
            if value == font_size:
                button.configure(
                    fg_color=colors.get("primary", "#3B82F6"),
                    hover_color=colors.get("primary_hover", "#2563EB"),
                )
            else:
                button.configure(
                    fg_color=colors.get("secondary", "#6B7280"),
                    hover_color=colors.get("secondary_hover", "#4B5563"),
                )

        # Update preview
        font_size_map = {"small": 13, "medium": 14, "large": 15, "extra_large": 17}

        preview_size = font_size_map.get(font_size, 14)
        self.preview_label.configure(font=("Segoe UI", preview_size))

        logger.debug(f"Font size selected: {font_size}")

    def _on_skip(self):
        """Handle skip button click"""
        # Use default medium font size
        self._complete_setup("medium")

    def _on_continue(self):
        """Handle continue button click"""
        self._complete_setup(self.selected_font_size)

    def _complete_setup(self, font_size: str):
        """Complete the setup and save preferences"""
        try:
            # Save font size preference
            self.settings_service.set_user_setting(
                self.user_id, "ui_preferences", "font_size", font_size
            )

            # Mark first-time setup as completed
            self.settings_service.set_user_setting(
                self.user_id, "ui_preferences", "first_time_setup_completed", True
            )

            logger.info(
                f"First-time setup completed for user {self.user_id} with font size: {font_size}"
            )

            # Call completion callback
            if self.on_complete_callback:
                self.on_complete_callback(font_size)

            # Close the wizard
            self.destroy()

        except Exception as e:
            logger.error(f"Error completing first-time setup: {e}")
            # Still close the wizard even if saving fails
            self.destroy()


if __name__ == "__main__":
    # Test the wizard
    print("First-time setup wizard module loaded successfully")
