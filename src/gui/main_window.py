#!/usr/bin/env python3
"""
Personal Password Manager - Main Application Window
==================================================

This module provides the main application interface for the password manager,
featuring a modern dashboard with password management, search functionality,
and comprehensive user controls. It serves as the primary interface after login.

Key Features:
- Modern dashboard with password list and management
- Advanced search and filtering capabilities
- Password generation and strength analysis
- Settings and preferences management
- Backup and export functionality
- Real-time password strength indicators
- Context menus and keyboard shortcuts
- Responsive design with drag-and-drop support

Security Features:
- Session-based access control
- Secure password display with masking
- Automatic session timeout handling
- Secure clipboard operations
- Memory-safe password operations

Author: Personal Password Manager
Version: 2.2.0
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import threading
import logging
import pyperclip
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
import json
from pathlib import Path

# Import our modules
from .themes import get_theme, apply_window_theme, create_themed_button, create_themed_entry, create_themed_label
from .components.password_generator import PasswordGeneratorDialog
from .components.strength_checker import PasswordStrengthIndicator
from .components.backup_manager import BackupManagerDialog
from ..core.password_manager import PasswordManagerCore, PasswordEntry, SearchCriteria
from ..core.auth import AuthenticationManager, InvalidSessionError, SessionExpiredError
from ..utils.password_generator import PasswordGenerator, GenerationMethod, GenerationOptions
from ..utils.strength_checker import AdvancedPasswordStrengthChecker

class ToolTip:
    """Create a tooltip for a given widget"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
    
    def enter(self, event=None):
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        # Create tooltip window
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tooltip, text=self.text, background="lightyellow",
                        relief="solid", borderwidth=1, font=("Arial", 9))
        label.pack()
    
    def leave(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebsiteGroupWidget(ctk.CTkFrame):
    """Widget that groups password entries by website with collapse/expand"""
    def __init__(self, parent, website, entries, main_window):
        super().__init__(parent)
        
        self.website = website
        self.entries = entries
        self.main_window = main_window
        self.expanded = True
        self.entry_widgets = []
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the group UI"""
        colors = get_theme().get_colors()
        
        # Header frame with collapse/expand button
        header_frame = ctk.CTkFrame(self, fg_color=colors["surface"], corner_radius=8)
        header_frame.pack(fill="x", padx=5, pady=2)
        
        # Collapse/expand button
        self.toggle_btn = ctk.CTkButton(
            header_frame,
            text="▼" if self.expanded else "►",
            width=30,
            height=30,
            command=self._toggle_expanded,
            fg_color="transparent",
            text_color=colors["text_primary"]
        )
        self.toggle_btn.pack(side="left", padx=(10, 5), pady=5)
        ToolTip(self.toggle_btn, "Click to expand/collapse this group")
        
        # Website name and count
        count = len(self.entries)
        website_text = f"{self.website.title()} ({count} {'entry' if count == 1 else 'entries'})"
        self.website_label = ctk.CTkLabel(
            header_frame,
            text=website_text,
            font=("Arial", 14, "bold"),
            text_color=colors["text_primary"]
        )
        self.website_label.pack(side="left", padx=(0, 10), pady=5, fill="x", expand=True)
        
        # Entries container
        self.entries_container = ctk.CTkFrame(self, fg_color="transparent")
        if self.expanded:
            self.entries_container.pack(fill="x", padx=10, pady=(0, 5))
        
        # Add entry widgets
        self._create_entry_widgets()
    
    def _create_entry_widgets(self):
        """Create widgets for individual entries"""
        # Clear existing
        for widget in self.entry_widgets:
            widget.destroy()
        self.entry_widgets.clear()
        
        if self.expanded:
            for entry in self.entries:
                entry_widget = PasswordEntryWidget(self.entries_container, entry, self.main_window)
                entry_widget.pack(fill="x", pady=2)
                self.entry_widgets.append(entry_widget)
    
    def _toggle_expanded(self):
        """Toggle the expanded state"""
        self.expanded = not self.expanded
        
        # Update button text
        self.toggle_btn.configure(text="▼" if self.expanded else "►")
        
        if self.expanded:
            self.entries_container.pack(fill="x", padx=10, pady=(0, 5))
            self._create_entry_widgets()
        else:
            self.entries_container.pack_forget()
            # Clear entry widgets to save memory
            for widget in self.entry_widgets:
                widget.destroy()
            self.entry_widgets.clear()

class PasswordListFrame(ctk.CTkScrollableFrame):
    """
    Scrollable frame for displaying password entries
    
    This frame provides a modern, scrollable list of password entries with
    search, filtering, and management capabilities.
    """
    
    def __init__(self, parent, main_window):
        """
        Initialize password list frame
        
        Args:
            parent: Parent widget
            main_window: Reference to main window
        """
        super().__init__(parent, label_text="Password Entries")
        
        self.main_window = main_window
        self.theme = get_theme()
        self.website_groups = {}  # Store grouped entries
        self.expanded_groups = set()  # Track which groups are expanded
        self.entry_widgets = []
        
        # Configure scrollable frame
        self.configure(label_font=self.theme.get_fonts()["heading_small"])
    
    def update_entries(self, entries: List[PasswordEntry]):
        """
        Update the displayed password entries, grouped by website
        
        Args:
            entries: List of password entries to display
        """
        # Clear existing widgets
        for widget in self.entry_widgets:
            widget.destroy()
        self.entry_widgets.clear()
        self.website_groups.clear()
        
        # Group entries by website
        from collections import defaultdict
        grouped_entries = defaultdict(list)
        for entry in entries:
            website = entry.website.lower().replace('www.', '').replace('https://', '').replace('http://', '')
            grouped_entries[website].append(entry)
        
        # Create website group widgets
        for website, website_entries in grouped_entries.items():
            group_widget = WebsiteGroupWidget(self, website, website_entries, self.main_window)
            group_widget.pack(fill="x", padx=10, pady=2)
            self.entry_widgets.append(group_widget)
        
        # Show message if no entries
        if not entries:
            no_entries_label = create_themed_label(
                self,
                text="No password entries found. Click 'Add Password' to create your first entry.",
                style="label_secondary"
            )
            no_entries_label.pack(pady=20)
            self.entry_widgets.append(no_entries_label)

class PasswordEntryWidget(ctk.CTkFrame):
    """
    Widget representing a single password entry
    
    This widget displays password information with options to view, edit,
    copy, and manage individual password entries.
    """
    
    def __init__(self, parent, entry: PasswordEntry, main_window):
        """
        Initialize password entry widget

        Args:
            parent: Parent widget
            entry: Password entry data
            main_window: Reference to main window
        """
        super().__init__(parent)

        self.entry = entry
        self.main_window = main_window
        self.theme = get_theme()
        self.is_expanded = False

        # ====================================================================
        # Secure Password Viewing Variables (NEW)
        # ====================================================================
        # Variables for timed password viewing with master password verification

        self.password_visible = False  # Track if password is currently visible
        self.view_timer_id = None  # Timer ID for auto-hide countdown
        self.view_time_remaining = 0  # Seconds remaining before auto-hide
        self.view_timeout = 30  # Default timeout in seconds (configurable)

        # Configure frame
        colors = self.theme.get_colors()
        self.configure(
            fg_color=colors["surface"],
            border_color=colors["border"],
            border_width=1,
            corner_radius=8
        )

        self._create_entry_ui()
    
    def _create_entry_ui(self):
        """Create the password entry user interface"""
        spacing = self.theme.get_spacing()
        colors = self.theme.get_colors()
        fonts = self.theme.get_fonts()
        
        # Main content frame
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=spacing["padding_md"], pady=spacing["padding_md"])
        
        # Header frame (always visible)
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(fill="x")

        # Left side - Name/Website and Favorite
        left_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_frame.pack(side="left", fill="x", expand=True)

        # Display name if available, otherwise website
        if self.entry.entry_name:
            # Custom name as primary heading
            name_label = create_themed_label(
                left_frame,
                text=self.entry.entry_name,
                style="label"
            )
            name_label.configure(font=fonts["body_large"])
            name_label.pack(side="top", anchor="w")

            # Website as secondary info below name
            website_sublabel = create_themed_label(
                left_frame,
                text=f"📧 {self.entry.website}",
                style="label_secondary"
            )
            website_sublabel.configure(font=fonts["body_small"])
            website_sublabel.pack(side="top", anchor="w")
        else:
            # No custom name - show website as heading (legacy behavior)
            website_label = create_themed_label(
                left_frame,
                text=self.entry.website,
                style="label"
            )
            website_label.configure(font=fonts["body_large"])
            website_label.pack(side="top", anchor="w")

        # Favorite indicator
        if self.entry.is_favorite:
            favorite_label = create_themed_label(
                left_frame,
                text="⭐",
                style="label"
            )
            favorite_label.pack(side="left", padx=(spacing["padding_sm"], 0))
        
        # Action buttons frame
        actions_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_frame.pack(side="right")

        # Copy password button
        copy_btn = create_themed_button(
            actions_frame,
            text="📋",
            style="button_secondary",
            width=30,
            command=self._copy_password
        )
        copy_btn.pack(side="right", padx=(spacing["padding_xs"], 0))
        ToolTip(copy_btn, "Copy password to clipboard (requires master password verification)")

        # Delete button
        delete_btn = create_themed_button(
            actions_frame,
            text="🗑️",
            style="button_secondary",
            width=30,
            command=self._delete_entry
        )
        delete_btn.pack(side="right", padx=(spacing["padding_xs"], 0))
        ToolTip(delete_btn, "Delete this password entry permanently (requires master password)")

        # View/Edit button
        edit_btn = create_themed_button(
            actions_frame,
            text="✏️",
            style="button_secondary",
            width=30,
            command=self._edit_entry
        )
        edit_btn.pack(side="right", padx=(spacing["padding_xs"], 0))
        ToolTip(edit_btn, "Edit this password entry")

        # Expand/collapse button
        self.expand_btn = create_themed_button(
            actions_frame,
            text="▼" if self.is_expanded else "▶",
            style="button_secondary",
            width=30,
            command=self._toggle_expand
        )
        self.expand_btn.pack(side="right")
        ToolTip(self.expand_btn, "Expand or collapse to show/hide details")
        
        # Username (always visible)
        username_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        username_frame.pack(fill="x", pady=(spacing["padding_xs"], 0))
        
        username_label = create_themed_label(
            username_frame,
            text=f"Username: {self.entry.username}",
            style="label_secondary"
        )
        username_label.pack(side="left", anchor="w")
        
        # Expandable details frame
        self.details_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        if self.is_expanded:
            self.details_frame.pack(fill="x", pady=(spacing["padding_sm"], 0))
        
        self._create_details_ui()
    
    def _create_details_ui(self):
        """Create the expandable details section"""
        spacing = self.theme.get_spacing()
        
        # Clear existing details
        for widget in self.details_frame.winfo_children():
            widget.destroy()
        
        # Password field with show/hide
        password_frame = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        password_frame.pack(fill="x", pady=(0, spacing["padding_xs"]))
        
        password_label = create_themed_label(
            password_frame,
            text="Password:",
            style="label_secondary"
        )
        password_label.pack(side="left", anchor="w")
        
        self.password_display = create_themed_label(
            password_frame,
            text="*" * 12 if self.entry.password else "[Not loaded]",
            style="label"
        )
        self.password_display.configure(font=self.theme.get_fonts()["code"])
        self.password_display.pack(side="left", anchor="w", padx=(spacing["padding_sm"], 0))
        
        # Show/hide password button
        self.show_password_btn = create_themed_button(
            password_frame,
            text="👁",
            style="button_secondary",
            width=30,
            command=self._toggle_password_visibility
        )
        self.show_password_btn.pack(side="right")
        ToolTip(self.show_password_btn, "View password (requires master password verification)")

        # ====================================================================
        # Timer Label (NEW)
        # ====================================================================
        # Shows countdown when password is visible

        self.password_timer_label = create_themed_label(
            self.details_frame,
            text="",
            style="label_secondary"
        )
        self.password_timer_label.configure(font=("Arial", 9))
        self.password_timer_label.pack(fill="x", anchor="w", pady=(0, spacing["padding_xs"]))

        # Remarks (if any)
        if self.entry.remarks:
            remarks_label = create_themed_label(
                self.details_frame,
                text=f"Notes: {self.entry.remarks}",
                style="label_secondary"
            )
            remarks_label.pack(fill="x", anchor="w", pady=(0, spacing["padding_xs"]))
        
        # Timestamps
        timestamps_frame = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        timestamps_frame.pack(fill="x")
        
        if self.entry.created_at:
            created_label = create_themed_label(
                timestamps_frame,
                text=f"Created: {self.entry.created_at.strftime('%Y-%m-%d %H:%M')}",
                style="label_secondary"
            )
            created_label.pack(side="left", anchor="w")
        
        if self.entry.modified_at and self.entry.modified_at != self.entry.created_at:
            modified_label = create_themed_label(
                timestamps_frame,
                text=f"Modified: {self.entry.modified_at.strftime('%Y-%m-%d %H:%M')}",
                style="label_secondary"
            )
            modified_label.pack(side="right", anchor="e")
    
    def _toggle_expand(self):
        """Toggle expanded view"""
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.details_frame.pack(fill="x", pady=(self.theme.get_spacing()["padding_sm"], 0))
            self.expand_btn.configure(text="▼")
        else:
            self.details_frame.pack_forget()
            self.expand_btn.configure(text="▶")
    
    def _toggle_password_visibility(self):
        """
        Toggle password visibility with secure master password verification

        This method implements secure password viewing with these steps:
        1. If password is currently visible → hide it immediately
        2. If password is hidden → prompt for master password
        3. If verified → retrieve password from database and show with timed auto-hide
        4. Start countdown timer (30 seconds default)

        Security features:
        - Requires master password verification before viewing
        - Retrieves password from database on-demand (not cached in list)
        - Time-limited viewing (auto-hide after timeout)
        - Visual countdown indicator
        - Manual hide option at any time
        """
        # If password is currently visible, hide it
        if self.password_visible:
            self._hide_password()
            return

        # Password is hidden - need to verify master password before showing
        # Get username and session info from main window
        try:
            username = self.main_window.username
            auth_manager = self.main_window.auth_manager
            session_id = self.main_window.session_id
            password_manager = self.main_window.password_manager
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            self.main_window._show_temporary_message("Cannot verify master password", "error")
            return

        # Prompt for master password
        logger.info("Prompting for master password to view password in list")

        prompt = MasterPasswordPrompt(
            self.main_window,
            auth_manager,
            session_id,
            username,
            max_attempts=3
        )

        # Wait for dialog to close (modal)
        self.main_window.wait_window(prompt)

        # Get result
        verified, master_password = prompt.get_result()

        if verified and master_password:
            # Master password verified! Now retrieve the password from database
            logger.info("Master password verified - retrieving password from database")

            try:
                # Retrieve the password entry with decrypted password
                entry = password_manager.get_password_entry(
                    session_id=session_id,
                    entry_id=self.entry.entry_id,
                    master_password=master_password
                )

                if entry and entry.password:
                    # Show the password
                    self.password_display.configure(text=entry.password)
                    self.show_password_btn.configure(text="🔒")

                    # Mark as visible
                    self.password_visible = True

                    # Start the timer
                    self.view_time_remaining = self.view_timeout
                    self._start_password_timer()

                    # Update timer display
                    self._update_password_timer_display()

                    logger.info("Password displayed successfully with timer")
                else:
                    logger.error("Failed to retrieve password from database")
                    self.main_window._show_temporary_message("Failed to retrieve password", "error")

            except Exception as e:
                logger.error(f"Error retrieving password: {e}")
                self.main_window._show_temporary_message(f"Error: {str(e)}", "error")

        else:
            # Verification failed or cancelled
            logger.info("Master password verification failed or cancelled")

    def _hide_password(self):
        """
        Immediately hide the password and stop the timer

        This method is called when:
        - User clicks the hide button (🔒)
        - Timer expires
        - Entry is collapsed
        - Widget is destroyed

        It clears the password display and resets the UI to the secure state.
        """
        logger.debug("Hiding password in list view")

        # Stop the timer if running
        if self.view_timer_id:
            self.after_cancel(self.view_timer_id)
            self.view_timer_id = None

        # Hide the password
        self.password_display.configure(text="*" * 12)
        self.show_password_btn.configure(text="👁")

        # Mark as not visible
        self.password_visible = False
        self.view_time_remaining = 0

        # Clear timer display
        if hasattr(self, 'password_timer_label'):
            self.password_timer_label.configure(text="")

    def _start_password_timer(self):
        """
        Start the countdown timer for auto-hide

        This timer automatically hides the password after the configured
        timeout period. It updates every second to show the countdown.
        """
        if self.view_timer_id:
            # Cancel existing timer
            self.after_cancel(self.view_timer_id)

        # Start new timer (tick every second)
        self._password_timer_tick()

    def _password_timer_tick(self):
        """
        Timer tick method - called every second

        This method:
        - Decrements the remaining time
        - Updates the visual countdown display
        - Auto-hides password when time expires
        - Changes color as time runs out (green → yellow → red)
        """
        if self.view_time_remaining > 0:
            # Decrement time
            self.view_time_remaining -= 1

            # Update display
            self._update_password_timer_display()

            # Schedule next tick in 1 second
            self.view_timer_id = self.after(1000, self._password_timer_tick)

        else:
            # Time expired - auto-hide password
            logger.info("Password view timer expired in list - auto-hiding")
            self._hide_password()

    def _update_password_timer_display(self):
        """
        Update the timer display label with current remaining time

        Color coding:
        - Green: > 20 seconds remaining
        - Yellow: 10-20 seconds remaining
        - Orange: 5-10 seconds remaining
        - Red: < 5 seconds remaining
        """
        seconds = self.view_time_remaining

        if seconds > 0 and hasattr(self, 'password_timer_label'):
            # Determine color based on remaining time
            if seconds > 20:
                color = "#44dd88"  # Green
            elif seconds > 10:
                color = "#ffbb00"  # Yellow
            elif seconds > 5:
                color = "#ff8800"  # Orange
            else:
                color = "#ff4444"  # Red

            # Format text
            text = f"⏱️ Password visible for {seconds} second{'s' if seconds != 1 else ''}"

            self.password_timer_label.configure(text=text, text_color=color)
        else:
            if hasattr(self, 'password_timer_label'):
                self.password_timer_label.configure(text="")

    def destroy(self):
        """
        Override destroy to clean up timer

        This ensures the timer is properly cancelled when the widget
        is destroyed, preventing memory leaks and orphaned timers.
        """
        # Stop timer if running
        if self.view_timer_id:
            self.after_cancel(self.view_timer_id)
            self.view_timer_id = None

        # Call parent destroy
        super().destroy()

    def _copy_password(self):
        """
        Copy password to clipboard with master password verification

        For security, passwords aren't loaded in the list by default.
        This method:
        1. Prompts for master password
        2. Retrieves password from database after verification
        3. Copies to clipboard
        4. Shows success message
        """
        # Get session info from main window
        try:
            username = self.main_window.username
            auth_manager = self.main_window.auth_manager
            session_id = self.main_window.session_id
            password_manager = self.main_window.password_manager
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            self.main_window._show_temporary_message("Cannot verify master password", "error")
            return

        # Prompt for master password
        logger.info("Prompting for master password to copy password")

        prompt = MasterPasswordPrompt(
            self.main_window,
            auth_manager,
            session_id,
            username,
            max_attempts=3
        )

        # Wait for dialog to close (modal)
        self.main_window.wait_window(prompt)

        # Get result
        verified, master_password = prompt.get_result()

        if verified and master_password:
            # Master password verified! Now retrieve the password from database
            logger.info("Master password verified - retrieving password for clipboard")

            try:
                # Retrieve the password entry with decrypted password
                entry = password_manager.get_password_entry(
                    session_id=session_id,
                    entry_id=self.entry.entry_id,
                    master_password=master_password
                )

                if entry and entry.password:
                    # Copy to clipboard
                    try:
                        pyperclip.copy(entry.password)
                        self.main_window._show_temporary_message("Password copied to clipboard", "success")
                        logger.info("Password copied to clipboard successfully")
                    except Exception as e:
                        logger.error(f"Failed to copy to clipboard: {e}")
                        self.main_window._show_temporary_message("Failed to copy password", "error")
                else:
                    logger.error("Failed to retrieve password from database")
                    self.main_window._show_temporary_message("Failed to retrieve password", "error")

            except Exception as e:
                logger.error(f"Error retrieving password: {e}")
                self.main_window._show_temporary_message(f"Error: {str(e)}", "error")
        else:
            # Verification failed or cancelled
            logger.info("Master password verification failed or cancelled - copy aborted")
    
    def _edit_entry(self):
        """Edit this password entry"""
        self.main_window._edit_password_entry(self.entry)

    def _delete_entry(self):
        """
        Delete this password entry with confirmation and master password verification

        Security flow:
        1. Show confirmation dialog with entry details
        2. If confirmed, prompt for master password
        3. If master password verified, proceed with deletion
        4. Show success/error message and refresh list

        This action cannot be undone.
        """
        # Step 1: Show confirmation dialog
        from tkinter import messagebox

        result = messagebox.askyesno(
            "Delete Password Entry",
            f"Are you sure you want to permanently delete this password entry?\n\n"
            f"Website: {self.entry.website}\n"
            f"Username: {self.entry.username}\n\n"
            f"This action cannot be undone!\n\n"
            f"You will be asked to verify your master password.",
            icon='warning'
        )

        if not result:
            # User cancelled deletion
            logger.info(f"Password entry deletion cancelled by user: {self.entry.website}")
            return

        # Step 2: User confirmed - now verify master password for security
        try:
            username = self.main_window.username
            auth_manager = self.main_window.auth_manager
            session_id = self.main_window.session_id
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            self.main_window._show_temporary_message("Cannot verify master password", "error")
            return

        # Prompt for master password
        logger.info("Prompting for master password to delete entry")

        prompt = MasterPasswordPrompt(
            self.main_window,
            auth_manager,
            session_id,
            username,
            max_attempts=3
        )

        # Wait for dialog to close (modal)
        self.main_window.wait_window(prompt)

        # Get result
        verified, master_password = prompt.get_result()

        if not verified or not master_password:
            # Master password verification failed or cancelled
            logger.info("Master password verification failed or cancelled - deletion aborted")
            self.main_window._show_temporary_message("Deletion cancelled - master password not verified", "warning")
            return

        # Step 3: Master password verified - proceed with deletion
        logger.info("Master password verified - proceeding with deletion")

        try:
            success = self.main_window.password_manager.delete_password_entry(
                session_id=self.main_window.session_id,
                entry_id=self.entry.entry_id
            )

            if success:
                logger.info(f"Password entry deleted: {self.entry.website} (ID: {self.entry.entry_id})")
                self.main_window._show_temporary_message(
                    f"Password entry for '{self.entry.website}' deleted successfully",
                    "success"
                )

                # Refresh the password list to remove the deleted entry
                self.main_window._load_password_entries()
            else:
                logger.error(f"Failed to delete password entry: {self.entry.entry_id}")
                self.main_window._show_temporary_message(
                    "Failed to delete password entry",
                    "error"
                )

        except Exception as e:
            logger.error(f"Error deleting password entry: {e}")
            self.main_window._show_temporary_message(
                f"Error deleting entry: {str(e)}",
                "error"
            )

class MainWindow(ctk.CTkToplevel):
    """
    Main application window for the password manager
    
    This class provides the primary interface for password management after
    successful authentication. It includes a dashboard, search functionality,
    password management tools, and application settings.
    
    Features:
    - Modern dashboard with password list
    - Advanced search and filtering
    - Password generation and analysis
    - Settings and preferences
    - Backup and export tools
    - Session management
    - Keyboard shortcuts and accessibility
    """
    
    def __init__(self, session_id: str, username: str,
                 password_manager: PasswordManagerCore,
                 auth_manager: AuthenticationManager,
                 parent=None,
                 on_logout_callback=None):
        """
        Initialize the main window

        Args:
            session_id: Valid session ID
            username: Authenticated username
            password_manager: Password management system
            auth_manager: Authentication manager
            parent: Parent window (optional)
            on_logout_callback: Callback function to execute on logout (optional)
        """
        super().__init__(parent)

        self.session_id = session_id
        self.username = username
        self.password_manager = password_manager
        self.auth_manager = auth_manager
        self.on_logout_callback = on_logout_callback
        self.theme = get_theme()
        
        # Window state
        self.current_entries = []
        self.search_criteria = SearchCriteria()
        self.is_loading = False
        
        # UI components
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self._on_search_change)
        
        # Setup window
        self._setup_window()
        self._create_ui()
        self._load_password_entries()
        
        # Start session monitoring
        self._start_session_monitor()
        
        logger.info(f"Main window initialized for user: {username}")
    
    def _setup_window(self):
        """Configure main window properties"""
        self.title(f"Personal Password Manager - {self.username}")
        self.geometry("1200x800")
        self.minsize(900, 600)

        # Center window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Maximize window
        try:
            self.state('zoomed')  # Windows/Linux
        except:
            try:
                self.attributes('-zoomed', True)  # Alternative for some Linux systems
            except:
                pass  # If maximizing fails, just use the centered geometry

        # Apply theme
        apply_window_theme(self)

        # Protocol handlers
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # Keyboard bindings
        self.bind("<Control-n>", lambda e: self._add_password_entry())
        self.bind("<Control-f>", lambda e: self.search_entry.focus())
        self.bind("<Control-s>", lambda e: self._show_settings())
        self.bind("<Control-b>", lambda e: self._show_backup_manager())
        self.bind("<F5>", lambda e: self._refresh_entries())
    
    def _create_ui(self):
        """Create the main user interface"""
        spacing = self.theme.get_spacing()
        
        # Main container
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=spacing["padding_lg"], pady=spacing["padding_lg"])
        
        # Create sections
        self._create_header(main_container)
        self._create_toolbar(main_container)
        self._create_main_content(main_container)
        self._create_status_bar(main_container)
    
    def _create_header(self, parent):
        """Create the header section"""
        spacing = self.theme.get_spacing()
        colors = self.theme.get_colors()
        fonts = self.theme.get_fonts()
        
        # Header frame
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, spacing["section_gap"]))
        
        # Title and user info
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)
        
        title_label = create_themed_label(
            title_frame,
            text="Password Manager",
            style="label"
        )
        title_label.configure(font=fonts["heading_large"])
        title_label.pack(anchor="w")
        
        user_label = create_themed_label(
            title_frame,
            text=f"Welcome back, {self.username}",
            style="label_secondary"
        )
        user_label.pack(anchor="w")
        
        # Header actions
        actions_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_frame.pack(side="right")
        
        # Settings button
        settings_btn = create_themed_button(
            actions_frame,
            text="⚙️ Settings",
            style="button_secondary",
            command=self._show_settings
        )
        settings_btn.pack(side="right", padx=(spacing["padding_sm"], 0))
        ToolTip(settings_btn, "Open application settings and preferences")
        
        # Logout button
        logout_btn = create_themed_button(
            actions_frame,
            text="🚪 Logout",
            style="button_secondary",
            command=self._logout
        )
        logout_btn.pack(side="right")
        ToolTip(logout_btn, "Log out and return to login screen")
    
    def _create_toolbar(self, parent):
        """Create the toolbar with search and actions"""
        spacing = self.theme.get_spacing()
        
        # Toolbar frame
        toolbar_frame = ctk.CTkFrame(parent)
        toolbar_frame.pack(fill="x", pady=(0, spacing["section_gap"]))
        
        # Configure toolbar frame
        colors = self.theme.get_colors()
        toolbar_frame.configure(
            fg_color=colors["surface"],
            corner_radius=spacing["radius_md"]
        )
        
        # Toolbar content
        toolbar_content = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        toolbar_content.pack(fill="both", expand=True, padx=spacing["padding_md"], pady=spacing["padding_md"])
        
        # Search section
        search_frame = ctk.CTkFrame(toolbar_content, fg_color="transparent")
        search_frame.pack(side="left", fill="x", expand=True)
        
        search_label = create_themed_label(
            search_frame,
            text="🔍",
            style="label"
        )
        search_label.pack(side="left", padx=(0, spacing["padding_sm"]))
        
        self.search_entry = create_themed_entry(
            search_frame,
            placeholder_text="Search passwords...",
            textvariable=self.search_var
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        
        # Action buttons
        actions_frame = ctk.CTkFrame(toolbar_content, fg_color="transparent")
        actions_frame.pack(side="right")
        
        # Add password button
        add_btn = create_themed_button(
            actions_frame,
            text="➕ Add Password",
            style="button_primary",
            command=self._add_password_entry
        )
        add_btn.pack(side="right", padx=(spacing["padding_sm"], 0))
        ToolTip(add_btn, "Add a new password entry")
        
        # Generate password button
        generate_btn = create_themed_button(
            actions_frame,
            text="🎲 Generate",
            style="button_secondary",
            command=self._show_password_generator
        )
        generate_btn.pack(side="right", padx=(spacing["padding_sm"], 0))
        ToolTip(generate_btn, "Generate a secure random password")
        
        # Import CSV button
        import_btn = create_themed_button(
            actions_frame,
            text="📄 Import CSV",
            style="button_secondary",
            command=self._import_csv
        )
        import_btn.pack(side="right", padx=(spacing["padding_sm"], 0))
        ToolTip(import_btn, "Import passwords from a CSV file")
        
        # Backup button
        backup_btn = create_themed_button(
            actions_frame,
            text="💾 Backup",
            style="button_secondary",
            command=self._show_backup_manager
        )
        backup_btn.pack(side="right")
        ToolTip(backup_btn, "Create or restore database backups")
    
    def _create_main_content(self, parent):
        """Create the main content area"""
        spacing = self.theme.get_spacing()
        
        # Main content frame
        content_frame = ctk.CTkFrame(parent, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        
        # Password list
        self.password_list = PasswordListFrame(content_frame, self)
        self.password_list.pack(fill="both", expand=True)
    
    def _create_status_bar(self, parent):
        """Create the status bar"""
        spacing = self.theme.get_spacing()
        colors = self.theme.get_colors()
        
        # Status bar frame
        status_frame = ctk.CTkFrame(parent)
        status_frame.pack(fill="x", pady=(spacing["padding_md"], 0))
        
        # Configure status bar
        status_frame.configure(
            fg_color=colors["bg_secondary"],
            corner_radius=spacing["radius_sm"],
            height=30
        )
        
        # Status content
        status_content = ctk.CTkFrame(status_frame, fg_color="transparent")
        status_content.pack(fill="both", expand=True, padx=spacing["padding_md"], pady=spacing["padding_xs"])
        
        # Status message
        self.status_label = create_themed_label(
            status_content,
            text="Ready",
            style="label_secondary"
        )
        self.status_label.pack(side="left")
        
        # Entry count
        self.count_label = create_themed_label(
            status_content,
            text="0 entries",
            style="label_secondary"
        )
        self.count_label.pack(side="right")
    
    def _load_password_entries(self, decrypt_passwords: bool = False):
        """Load password entries from the database"""
        if self.is_loading:
            return
        
        self.is_loading = True
        self._show_status("Loading passwords...")
        
        # Run in background thread
        threading.Thread(
            target=self._load_entries_background,
            args=(decrypt_passwords,),
            daemon=True
        ).start()
    
    def _load_entries_background(self, decrypt_passwords: bool):
        """Load entries in background thread"""
        try:
            # Get entries from password manager
            entries = self.password_manager.search_password_entries(
                self.session_id,
                criteria=self.search_criteria,
                include_passwords=decrypt_passwords
            )
            
            # Update UI on main thread
            self.after(0, self._on_entries_loaded, entries)
            
        except (InvalidSessionError, SessionExpiredError):
            self.after(0, self._handle_session_expired)
        except Exception as e:
            logger.error(f"Failed to load entries: {e}")
            self.after(0, self._show_error, f"Failed to load passwords: {str(e)}")
    
    def _on_entries_loaded(self, entries: List[PasswordEntry]):
        """Handle successful entry loading"""
        self.current_entries = entries
        self.password_list.update_entries(entries)
        
        # Update status
        entry_count = len(entries)
        self.count_label.configure(text=f"{entry_count} {'entry' if entry_count == 1 else 'entries'}")
        self._show_status("Ready")
        
        self.is_loading = False
    
    def _on_search_change(self, *args):
        """Handle search text change"""
        search_text = self.search_var.get().strip()
        
        if search_text:
            self.search_criteria.website = search_text
        else:
            self.search_criteria.website = None
        
        # Debounce search (simple implementation)
        self.after(300, self._perform_search)
    
    def _perform_search(self):
        """Perform the actual search"""
        self._load_password_entries()
    
    def _refresh_entries(self):
        """Refresh password entries"""
        self._load_password_entries()
    
    def _add_password_entry(self):
        """Show add password entry dialog"""
        AddPasswordDialog(self, self.session_id, self.password_manager, self._on_entry_added)
    
    def _edit_password_entry(self, entry: PasswordEntry):
        """Edit an existing password entry"""
        EditPasswordDialog(self, self.session_id, self.password_manager, entry, self._on_entry_updated)
    
    def _on_entry_added(self):
        """Handle successful entry addition"""
        self._refresh_entries()
        self._show_temporary_message("Password entry added successfully", "success")
    
    def _on_entry_updated(self):
        """Handle successful entry update"""
        self._refresh_entries()
        self._show_temporary_message("Password entry updated successfully", "success")
    
    def _show_password_generator(self):
        """Show password generator dialog"""
        PasswordGeneratorDialog(self)
    
    def _show_backup_manager(self):
        """Show backup manager dialog"""
        BackupManagerDialog(self, self.session_id, self.password_manager, self.auth_manager)
    
    def _show_settings(self):
        """Show settings dialog"""
        SettingsDialog(self, self.theme)
    
    def _logout(self):
        """Logout and return to login screen"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            try:
                self.auth_manager.logout_user(self.session_id)
                logger.info(f"User '{self.username}' logged out successfully")
            except Exception as e:
                logger.error(f"Logout error: {e}")

            # Destroy main window
            self.destroy()

            # Call logout callback to reopen login window
            if self.on_logout_callback:
                self.on_logout_callback()
    
    def _start_session_monitor(self):
        """Start monitoring session validity"""
        self.after(60000, self._check_session)  # Check every minute
    
    def _check_session(self):
        """Check if session is still valid"""
        try:
            self.auth_manager.validate_session(self.session_id)
            # Schedule next check
            self.after(60000, self._check_session)
        except (InvalidSessionError, SessionExpiredError):
            self._handle_session_expired()
    
    def _handle_session_expired(self):
        """Handle expired session"""
        messagebox.showerror(
            "Session Expired",
            "Your session has expired. Please login again."
        )
        logger.warning(f"Session expired for user '{self.username}'")

        # Destroy main window
        self.destroy()

        # Call logout callback to reopen login window
        if self.on_logout_callback:
            self.on_logout_callback()
    
    def _show_status(self, message: str):
        """Show status message"""
        self.status_label.configure(text=message)
    
    def _show_error(self, message: str):
        """Show error message"""
        colors = self.theme.get_colors()
        self.status_label.configure(text=message, text_color=colors["error"])
    
    def _show_temporary_message(self, message: str, msg_type: str = "info"):
        """Show temporary message that disappears after a few seconds"""
        colors = self.theme.get_colors()
        
        if msg_type == "success":
            color = colors["success"]
        elif msg_type == "error":
            color = colors["error"]
        elif msg_type == "warning":
            color = colors["warning"]
        else:
            color = colors["text_secondary"]
        
        self.status_label.configure(text=message, text_color=color)
        
        # Reset after 3 seconds
        self.after(3000, lambda: self.status_label.configure(text="Ready", text_color=colors["text_secondary"]))
    
    def _on_window_close(self):
        """Handle window close event"""
        try:
            # Logout cleanly
            self.auth_manager.logout_user(self.session_id)
        except Exception as e:
            logger.error(f"Error during window close: {e}")
        
        self.destroy()
    
    def _add_password_entry(self):
        """Show add password dialog"""
        try:
            def on_add_success():
                """Callback when password is added successfully"""
                self._load_password_entries()
            
            # Create and show add password dialog
            AddPasswordDialog(
                parent=self,
                session_id=self.session_id,
                password_manager=self.password_manager,
                on_success=on_add_success
            )
        except Exception as e:
            logger.error(f"Failed to show add password dialog: {e}")
            self._show_error("Failed to open add password dialog")
    
    def _show_settings(self):
        """Show settings dialog"""
        try:
            # Create and show settings dialog
            SettingsDialog(
                parent=self,
                theme=self.theme
            )
        except Exception as e:
            logger.error(f"Failed to show settings dialog: {e}")
            self._show_error("Failed to open settings dialog")
    
    def _show_password_generator(self):
        """Show password generator dialog"""
        try:
            from .components.password_generator import PasswordGeneratorDialog
            
            def on_password_generated(password):
                """Callback when password is generated"""
                # Could copy to clipboard or show in add dialog
                import pyperclip
                pyperclip.copy(password)
                self._show_temporary_message("Password copied to clipboard!", "success")
            
            # Create and show password generator dialog
            dialog = PasswordGeneratorDialog(
                parent=self,
                on_password_generated=on_password_generated
            )
        except ImportError:
            messagebox.showinfo("Password Generator", "Password generator would open here")
        except Exception as e:
            logger.error(f"Failed to show password generator: {e}")
            self._show_error("Failed to open password generator")
    
    def _edit_password_entry(self, entry: PasswordEntry):
        """Edit an existing password entry"""
        try:
            def on_edit_success():
                """Callback when password is edited successfully"""
                self._load_password_entries()
            
            # Create and show edit password dialog
            EditPasswordDialog(
                parent=self,
                session_id=self.session_id,
                password_manager=self.password_manager,
                entry=entry,
                on_success=on_edit_success
            )
        except Exception as e:
            logger.error(f"Failed to show edit password dialog: {e}")
            self._show_error("Failed to open edit password dialog")
    
    def _import_csv(self):
        """Import passwords from CSV file"""
        try:
            # Show file dialog
            file_path = filedialog.askopenfilename(
                title="Select CSV file to import",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                parent=self
            )

            if not file_path:
                return

            # Create and show CSV import dialog
            CSVImportDialog(
                parent=self,
                session_id=self.session_id,
                password_manager=self.password_manager,
                csv_file_path=file_path,
                on_success=lambda: self._load_password_entries(),
                auth_manager=self.auth_manager,  # Pass auth_manager for master password verification
                username=self.username  # Pass username for master password verification
            )
        except Exception as e:
            logger.error(f"Failed to show CSV import dialog: {e}")
            self._show_error("Failed to open CSV import dialog")

# Dialog classes will be implemented in separate files
class AddPasswordDialog(ctk.CTkToplevel):
    """Add password dialog"""
    def __init__(self, parent, session_id, password_manager, on_success):
        super().__init__(parent)
        
        self.session_id = session_id
        self.password_manager = password_manager
        self.on_success = on_success
        
        # Configure dialog
        self.title("Add Password")
        self.geometry("450x500")
        self.minsize(400, 450)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        # Center dialog
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (450 // 2)
        self.geometry(f"400x450+{x}+{y}")
        
        # Variables
        self.entry_name_var = ctk.StringVar()
        self.website_var = ctk.StringVar()
        self.username_var = ctk.StringVar()
        self.password_var = ctk.StringVar()
        self.remarks_var = ctk.StringVar()

        self._create_ui()

    def _create_ui(self):
        """Create dialog UI"""
        # Main container with scrollable frame
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(main_frame, text="Add New Password", font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 20))

        # Name field (optional)
        ctk.CTkLabel(main_frame, text="Name (Optional):", anchor="w").pack(fill="x", pady=(0, 5))
        self.entry_name_entry = ctk.CTkEntry(main_frame, textvariable=self.entry_name_var, placeholder_text="e.g., Work Email, My Bank, Netflix...")
        self.entry_name_entry.pack(fill="x", pady=(0, 5))

        # Help text for name field
        help_label = ctk.CTkLabel(main_frame, text="💡 Give this entry a friendly name",
                                 anchor="w", font=("Arial", 10), text_color="gray")
        help_label.pack(fill="x", pady=(0, 15))

        # Website field
        ctk.CTkLabel(main_frame, text="Website:", anchor="w").pack(fill="x", pady=(0, 5))
        self.website_entry = ctk.CTkEntry(main_frame, textvariable=self.website_var, placeholder_text="e.g., google.com")
        self.website_entry.pack(fill="x", pady=(0, 15))
        
        # Username field
        ctk.CTkLabel(main_frame, text="Username:", anchor="w").pack(fill="x", pady=(0, 5))
        self.username_entry = ctk.CTkEntry(main_frame, textvariable=self.username_var, placeholder_text="Your username or email")
        self.username_entry.pack(fill="x", pady=(0, 15))
        
        # Password field
        ctk.CTkLabel(main_frame, text="Password:", anchor="w").pack(fill="x", pady=(0, 5))
        password_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        password_frame.pack(fill="x", pady=(0, 15))
        
        self.password_entry = ctk.CTkEntry(password_frame, textvariable=self.password_var, show="*", placeholder_text="Enter password")
        self.password_entry.pack(side="left", fill="x", expand=True)
        
        generate_btn = ctk.CTkButton(password_frame, text="🎲", width=40, command=self._generate_password)
        generate_btn.pack(side="right", padx=(5, 0))
        ToolTip(generate_btn, "Generate a secure random password")
        
        # Remarks field
        ctk.CTkLabel(main_frame, text="Remarks (optional):", anchor="w").pack(fill="x", pady=(0, 5))
        self.remarks_entry = ctk.CTkEntry(main_frame, textvariable=self.remarks_var, placeholder_text="Additional notes")
        self.remarks_entry.pack(fill="x", pady=(0, 20))
        
        # Status label
        self.status_label = ctk.CTkLabel(main_frame, text="", text_color="red")
        self.status_label.pack(pady=(0, 10))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=self.destroy, fg_color="gray")
        cancel_btn.pack(side="right", padx=(10, 0))
        ToolTip(cancel_btn, "Cancel and close dialog without saving")
        
        self.add_btn = ctk.CTkButton(button_frame, text="Add Password", command=self._add_password)
        self.add_btn.pack(side="right")
        ToolTip(self.add_btn, "Save this password entry")

        # Focus on first field
        self.entry_name_entry.focus()
    
    def _generate_password(self):
        """Generate a random password"""
        import secrets
        import string
        
        # Generate strong password
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(chars) for _ in range(12))
        self.password_var.set(password)
    
    def _add_password(self):
        """Add the password entry"""
        entry_name = self.entry_name_var.get().strip() or None  # Convert empty to None
        website = self.website_var.get().strip()
        username = self.username_var.get().strip()
        password = self.password_var.get()
        remarks = self.remarks_var.get().strip()

        # Validate input
        if not website:
            self.status_label.configure(text="Please enter a website")
            self.website_entry.focus()
            return

        if not username:
            self.status_label.configure(text="Please enter a username")
            self.username_entry.focus()
            return

        if not password:
            self.status_label.configure(text="Please enter a password")
            self.password_entry.focus()
            return

        try:
            self.add_btn.configure(state="disabled", text="Adding...")

            # Add password entry (using session, no master password needed)
            entry_id = self.password_manager.add_password_entry(
                session_id=self.session_id,
                website=website,
                username=username,
                password=password,
                remarks=remarks,
                entry_name=entry_name
            )
            
            # Success
            self.on_success()
            self.destroy()
            
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}")
            self.add_btn.configure(state="normal", text="Add Password")

# ============================================================================
# MasterPasswordPrompt - Secure Password Verification Dialog
# ============================================================================
# This dialog prompts the user to enter their master password for verification
# before allowing sensitive operations like viewing existing passwords.
#
# Security Features:
# - Password field with show/hide toggle
# - Attempt tracking (max 3 attempts)
# - Session-based verification
# - Auto-close on too many failures
# - Secure password entry (masked by default)
#
# Use Cases:
# - Viewing existing passwords in edit dialog
# - Sensitive operations requiring re-authentication
# - Password change verification
# ============================================================================

class MasterPasswordPrompt(ctk.CTkToplevel):
    """
    Secure dialog for master password verification

    This dialog provides a simple, secure interface for prompting the user
    to enter their master password for verification purposes. It includes
    attempt tracking and automatic lockout after too many failed attempts.

    Attributes:
        parent: Parent window for modal behavior
        auth_manager: AuthenticationManager for verification
        session_id: Current user session identifier
        username: Username for verification
        max_attempts: Maximum number of failed attempts (default: 3)
    """

    def __init__(self, parent, auth_manager, session_id, username, max_attempts=3):
        """
        Initialize the master password prompt

        Args:
            parent: Parent window (for centering and modal behavior)
            auth_manager: AuthenticationManager instance for verification
            session_id: Active session ID
            username: Username to verify against
            max_attempts: Maximum failed attempts before closing (default: 3)
        """
        super().__init__(parent)

        self.auth_manager = auth_manager
        self.session_id = session_id
        self.username = username
        self.max_attempts = max_attempts
        self.attempts_made = 0
        self.verified = False  # Set to True if password is verified
        self.master_password = None  # Store verified password

        # Track password visibility
        self.password_visible = False

        # ====================================================================
        # Window Configuration
        # ====================================================================

        self.title("Master Password Required")
        self.geometry("400x250")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        if parent:
            parent_x = parent.winfo_x()
            parent_y = parent.winfo_y()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()
            x = parent_x + (parent_width // 2) - 200
            y = parent_y + (parent_height // 2) - 125
            self.geometry(f"400x250+{x}+{y}")

        # Password variable
        self.password_var = ctk.StringVar()

        # Create UI
        self._create_ui()

        # Bind keyboard shortcuts
        self.bind("<Return>", lambda e: self._verify_password())
        self.bind("<Escape>", lambda e: self._cancel())

        # Focus on password field
        self.after(100, lambda: self.password_entry.focus())

        logger.info("Master password prompt opened")

    def _create_ui(self):
        """Create the prompt user interface"""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # ====================================================================
        # Icon and Title
        # ====================================================================

        icon_label = ctk.CTkLabel(
            main_frame,
            text="🔐",
            font=("Arial", 32)
        )
        icon_label.pack(pady=(0, 10))

        title_label = ctk.CTkLabel(
            main_frame,
            text="Enter Master Password",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 5))

        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Required to view existing password",
            font=("Arial", 11),
            text_color="gray"
        )
        subtitle_label.pack(pady=(0, 20))

        # ====================================================================
        # Password Field
        # ====================================================================

        password_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        password_frame.pack(fill="x", pady=(0, 10))

        self.password_entry = ctk.CTkEntry(
            password_frame,
            textvariable=self.password_var,
            placeholder_text="Enter your master password",
            show="*",
            height=35
        )
        self.password_entry.pack(side="left", fill="x", expand=True)
        ToolTip(self.password_entry, "Enter your master password")

        # Show/hide toggle button
        self.toggle_btn = ctk.CTkButton(
            password_frame,
            text="👁",
            width=40,
            height=35,
            command=self._toggle_visibility
        )
        self.toggle_btn.pack(side="right", padx=(5, 0))
        ToolTip(self.toggle_btn, "Show/hide password")

        # ====================================================================
        # Status Label
        # ====================================================================

        self.status_label = ctk.CTkLabel(
            main_frame,
            text="",
            text_color="red",
            font=("Arial", 10)
        )
        self.status_label.pack(pady=(0, 15))

        # ====================================================================
        # Action Buttons
        # ====================================================================

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._cancel,
            fg_color="gray",
            hover_color="darkgray",
            height=35
        )
        cancel_btn.pack(side="right", padx=(10, 0))
        ToolTip(cancel_btn, "Cancel and close")

        self.verify_btn = ctk.CTkButton(
            button_frame,
            text="Verify",
            command=self._verify_password,
            height=35
        )
        self.verify_btn.pack(side="right")
        ToolTip(self.verify_btn, "Verify master password")

    def _toggle_visibility(self):
        """Toggle password field visibility"""
        self.password_visible = not self.password_visible

        if self.password_visible:
            self.password_entry.configure(show="")
            self.toggle_btn.configure(text="🙈")
        else:
            self.password_entry.configure(show="*")
            self.toggle_btn.configure(text="👁")

    def _verify_password(self):
        """
        Verify the entered master password

        This method checks the entered password against the user's actual
        master password. It tracks failed attempts and closes the dialog
        after too many failures for security.
        """
        password = self.password_var.get()

        if not password:
            self.status_label.configure(text="Please enter your master password")
            return

        # Disable button during verification
        self.verify_btn.configure(state="disabled", text="Verifying...")

        try:
            # Verify the password by attempting authentication
            # We use the auth manager to verify credentials
            user_data = self.auth_manager.db_manager.authenticate_user(
                self.username,
                password
            )

            if user_data:
                # Password is correct!
                self.verified = True
                self.master_password = password
                logger.info("Master password verified successfully")
                self.destroy()
            else:
                # Password is incorrect
                self.attempts_made += 1
                remaining = self.max_attempts - self.attempts_made

                if remaining > 0:
                    self.status_label.configure(
                        text=f"Incorrect password. {remaining} attempt(s) remaining."
                    )
                    self.password_var.set("")
                    self.verify_btn.configure(state="normal", text="Verify")
                    logger.warning(f"Failed master password attempt ({self.attempts_made}/{self.max_attempts})")
                else:
                    # Too many failed attempts
                    self.status_label.configure(text="Too many failed attempts. Access denied.")
                    logger.warning("Master password prompt closed: too many failed attempts")
                    self.after(1500, self.destroy)  # Close after showing message

        except Exception as e:
            logger.error(f"Error verifying master password: {e}")
            self.status_label.configure(text="Verification error occurred")
            self.verify_btn.configure(state="normal", text="Verify")

    def _cancel(self):
        """Cancel the prompt without verification"""
        self.verified = False
        self.master_password = None
        logger.info("Master password prompt cancelled by user")
        self.destroy()

    def get_result(self):
        """
        Get the verification result

        Returns:
            tuple: (verified: bool, password: str or None)
        """
        return (self.verified, self.master_password)

# ============================================================================
# EditPasswordDialog - Full-Featured Password Entry Editor
# ============================================================================
# This dialog provides a comprehensive interface for editing existing password
# entries. It includes all fields from the add dialog plus additional metadata
# display, real-time password strength analysis, and favorite toggle.
#
# Key Features:
# - Pre-populated fields with existing password data
# - Password visibility toggle (show/hide)
# - Integrated password generator
# - Real-time strength indicator with visual feedback
# - Favorite toggle for bookmarking important passwords
# - Created/Modified timestamp display
# - Full input validation and error handling
# - Session-based security with master password caching
#
# The dialog maintains consistency with the application's Windows 11-inspired
# design language and provides helpful tooltips for user guidance.
# ============================================================================

class EditPasswordDialog(ctk.CTkToplevel):
    """
    Dialog for editing existing password entries

    This dialog provides a modern, user-friendly interface for modifying
    password entries with real-time feedback, validation, and security features.

    Attributes:
        parent: Parent window for modal behavior
        session_id: Active user session identifier
        password_manager: PasswordManagerCore instance for data operations
        entry: PasswordEntry object containing current data
        on_success: Callback function to execute after successful update
    """

    def __init__(self, parent, session_id, password_manager, entry, on_success):
        """
        Initialize the edit password dialog

        Args:
            parent: Parent window (MainWindow instance)
            session_id (str): Valid session token for authentication
            password_manager (PasswordManagerCore): Password manager instance
            entry (PasswordEntry): Existing password entry to edit
            on_success (Callable): Callback executed after successful update
        """
        super().__init__(parent)

        # Store references to dependencies
        self.session_id = session_id
        self.password_manager = password_manager
        self.entry = entry  # Store the original entry data
        self.on_success = on_success

        # Initialize password generator for the generate button
        self.password_generator = PasswordGenerator()
        self.strength_checker = AdvancedPasswordStrengthChecker()

        # Track password visibility state
        self.password_visible = False

        # ====================================================================
        # Timer and Security Features (NEW)
        # ====================================================================
        # Variables for secure timed password viewing

        self.original_password_visible = False  # Track if original password is shown
        self.view_timer_id = None  # Timer ID for auto-hide
        self.view_time_remaining = 0  # Seconds remaining before auto-hide
        self.view_timeout = 30  # Default timeout in seconds (configurable)
        self.stored_original_password = entry.password  # Store original for viewing

        # Get username for master password verification
        # We need to get this from the session
        try:
            session = password_manager.auth_manager.validate_session(session_id)
            self.username = session.username
            self.auth_manager = password_manager.auth_manager
        except Exception as e:
            logger.error(f"Error getting username from session: {e}")
            self.username = None
            self.auth_manager = None

        # ====================================================================
        # Window Configuration
        # ====================================================================
        # Configure the dialog window properties for optimal user experience

        self.title(f"Edit Password - {entry.website}")
        self.geometry("500x650")
        self.minsize(450, 600)
        self.resizable(True, True)
        self.transient(parent)  # Make dialog modal
        self.grab_set()  # Prevent interaction with parent until closed

        # Center dialog on parent window
        self.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = 500
        dialog_height = 650
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        self.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        # ====================================================================
        # Form Variables
        # ====================================================================
        # Initialize StringVar and BooleanVar for form fields
        # These are bound to UI widgets for automatic updates

        self.entry_name_var = ctk.StringVar()
        self.website_var = ctk.StringVar()
        self.username_var = ctk.StringVar()
        self.password_var = ctk.StringVar()
        self.remarks_var = ctk.StringVar()
        self.favorite_var = ctk.BooleanVar()

        # Bind password variable to strength checker for real-time updates
        self.password_var.trace('w', self._on_password_change)

        # Create the user interface
        self._create_ui()

        # Populate fields with existing entry data
        self._populate_fields()

        # Set keyboard shortcuts
        self.bind("<Return>", lambda e: self._update_password())
        self.bind("<Escape>", lambda e: self.destroy())

        logger.info(f"Edit dialog opened for entry ID {entry.entry_id} ({entry.website})")

    # ========================================================================
    # UI Creation Methods
    # ========================================================================

    def _create_ui(self):
        """
        Create the complete user interface for the edit dialog

        This method builds a scrollable form containing:
        - Title header
        - Website, username, password, and remarks input fields
        - Password visibility toggle and generator buttons
        - Password strength indicator with visual feedback
        - Favorite toggle checkbox
        - Metadata display (created/modified timestamps)
        - Status label for error messages
        - Action buttons (Cancel and Update)

        The layout uses a scrollable frame to accommodate all content
        and maintain usability on smaller screens.
        """
        # Main scrollable container to hold all form elements
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # ====================================================================
        # Title Section
        # ====================================================================

        title_label = ctk.CTkLabel(
            main_frame,
            text="✏️ Edit Password Entry",
            font=("Arial", 20, "bold")
        )
        title_label.pack(pady=(0, 20))

        # ====================================================================
        # Name Field (Optional)
        # ====================================================================
        # Custom friendly name for this password entry

        ctk.CTkLabel(
            main_frame,
            text="Name (Optional):",
            anchor="w",
            font=("Arial", 12, "bold")
        ).pack(fill="x", pady=(0, 5))

        self.entry_name_entry = ctk.CTkEntry(
            main_frame,
            textvariable=self.entry_name_var,
            placeholder_text="e.g., Work Email, My Bank, Netflix...",
            height=35
        )
        self.entry_name_entry.pack(fill="x", pady=(0, 5))
        ToolTip(self.entry_name_entry, "Give this entry a friendly name")

        # Help text for name field
        help_label = ctk.CTkLabel(
            main_frame,
            text="💡 Give this entry a friendly name that's easier to remember",
            anchor="w",
            font=("Arial", 10),
            text_color="gray"
        )
        help_label.pack(fill="x", pady=(0, 15))

        # ====================================================================
        # Website Field
        # ====================================================================
        # The website/service name for this password entry

        ctk.CTkLabel(
            main_frame,
            text="Website / Service:",
            anchor="w",
            font=("Arial", 12, "bold")
        ).pack(fill="x", pady=(0, 5))

        self.website_entry = ctk.CTkEntry(
            main_frame,
            textvariable=self.website_var,
            placeholder_text="e.g., google.com, Facebook, GitHub",
            height=35
        )
        self.website_entry.pack(fill="x", pady=(0, 15))
        ToolTip(self.website_entry, "Enter the website or service name")

        # ====================================================================
        # Username Field
        # ====================================================================
        # Username, email, or account identifier

        ctk.CTkLabel(
            main_frame,
            text="Username / Email:",
            anchor="w",
            font=("Arial", 12, "bold")
        ).pack(fill="x", pady=(0, 5))

        self.username_entry = ctk.CTkEntry(
            main_frame,
            textvariable=self.username_var,
            placeholder_text="Your username or email address",
            height=35
        )
        self.username_entry.pack(fill="x", pady=(0, 15))
        ToolTip(self.username_entry, "Enter your username or email for this account")

        # ====================================================================
        # Password Field with Controls
        # ====================================================================
        # Password input with visibility toggle and generator button

        ctk.CTkLabel(
            main_frame,
            text="Password:",
            anchor="w",
            font=("Arial", 12, "bold")
        ).pack(fill="x", pady=(0, 5))

        # Container frame for password entry and action buttons
        password_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        password_frame.pack(fill="x", pady=(0, 5))

        # Password entry field (masked by default)
        self.password_entry = ctk.CTkEntry(
            password_frame,
            textvariable=self.password_var,
            show="*",  # Mask password by default
            placeholder_text="Enter password",
            height=35
        )
        self.password_entry.pack(side="left", fill="x", expand=True)
        ToolTip(self.password_entry, "Enter the password for this account")

        # Password visibility toggle button (eye icon)
        self.toggle_password_btn = ctk.CTkButton(
            password_frame,
            text="👁",
            width=40,
            height=35,
            command=self._toggle_password_visibility
        )
        self.toggle_password_btn.pack(side="right", padx=(5, 0))
        ToolTip(self.toggle_password_btn, "Show/hide password")

        # Password generator button (dice icon)
        generate_btn = ctk.CTkButton(
            password_frame,
            text="🎲",
            width=40,
            height=35,
            command=self._generate_password
        )
        generate_btn.pack(side="right", padx=(5, 0))
        ToolTip(generate_btn, "Generate a secure random password")

        # View original password button (magnifying glass icon) - NEW
        self.view_original_btn = ctk.CTkButton(
            password_frame,
            text="🔍",
            width=40,
            height=35,
            command=self._view_original_password
        )
        self.view_original_btn.pack(side="right", padx=(5, 0))
        ToolTip(self.view_original_btn, "View the current saved password (requires master password)")

        # ====================================================================
        # Timer Label (NEW)
        # ====================================================================
        # Shows countdown when password is visible

        self.timer_label = ctk.CTkLabel(
            main_frame,
            text="",
            font=("Arial", 10),
            text_color="gray"
        )
        self.timer_label.pack(fill="x", pady=(2, 3))

        # ====================================================================
        # Password Strength Indicator
        # ====================================================================
        # Visual feedback showing password strength in real-time

        self.strength_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.strength_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            self.strength_frame,
            text="Strength:",
            font=("Arial", 10)
        ).pack(side="left", padx=(0, 10))

        # Strength bar (progress bar style)
        self.strength_bar = ctk.CTkProgressBar(self.strength_frame, width=200)
        self.strength_bar.pack(side="left", padx=(0, 10))
        self.strength_bar.set(0)

        # Strength label (text description)
        self.strength_label = ctk.CTkLabel(
            self.strength_frame,
            text="No password",
            font=("Arial", 10)
        )
        self.strength_label.pack(side="left")

        # ====================================================================
        # Remarks Field
        # ====================================================================
        # Optional notes or additional information

        ctk.CTkLabel(
            main_frame,
            text="Remarks (optional):",
            anchor="w",
            font=("Arial", 12, "bold")
        ).pack(fill="x", pady=(0, 5))

        self.remarks_entry = ctk.CTkEntry(
            main_frame,
            textvariable=self.remarks_var,
            placeholder_text="Additional notes or recovery info",
            height=35
        )
        self.remarks_entry.pack(fill="x", pady=(0, 15))
        ToolTip(self.remarks_entry, "Add any additional notes or information")

        # ====================================================================
        # Favorite Toggle
        # ====================================================================
        # Checkbox to mark this entry as a favorite for quick access

        self.favorite_check = ctk.CTkCheckBox(
            main_frame,
            text="⭐ Mark as Favorite",
            variable=self.favorite_var,
            font=("Arial", 12)
        )
        self.favorite_check.pack(anchor="w", pady=(0, 15))
        ToolTip(self.favorite_check, "Add to favorites for quick access")

        # ====================================================================
        # Metadata Display
        # ====================================================================
        # Show when the entry was created and last modified (read-only)

        metadata_frame = ctk.CTkFrame(main_frame)
        metadata_frame.pack(fill="x", pady=(0, 15))

        metadata_title = ctk.CTkLabel(
            metadata_frame,
            text="📋 Entry Information",
            font=("Arial", 12, "bold")
        )
        metadata_title.pack(anchor="w", padx=10, pady=(10, 5))

        # Created timestamp
        self.created_label = ctk.CTkLabel(
            metadata_frame,
            text="",
            font=("Arial", 10),
            anchor="w"
        )
        self.created_label.pack(anchor="w", padx=20, pady=2)

        # Modified timestamp
        self.modified_label = ctk.CTkLabel(
            metadata_frame,
            text="",
            font=("Arial", 10),
            anchor="w"
        )
        self.modified_label.pack(anchor="w", padx=20, pady=(2, 10))

        # ====================================================================
        # Status Label
        # ====================================================================
        # Display error messages and validation feedback

        self.status_label = ctk.CTkLabel(
            main_frame,
            text="",
            text_color="red",
            font=("Arial", 11)
        )
        self.status_label.pack(pady=(0, 10))

        # ====================================================================
        # Action Buttons
        # ====================================================================
        # Cancel and Update buttons at the bottom

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

        # Cancel button (gray, secondary action)
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            fg_color="gray",
            hover_color="darkgray",
            height=40
        )
        cancel_btn.pack(side="right", padx=(10, 0))
        ToolTip(cancel_btn, "Discard changes and close dialog")

        # Update button (primary action)
        self.update_btn = ctk.CTkButton(
            button_frame,
            text="💾 Update Password",
            command=self._update_password,
            height=40
        )
        self.update_btn.pack(side="right")
        ToolTip(self.update_btn, "Save changes to this password entry")

    # ========================================================================
    # Data Population Methods
    # ========================================================================

    def _populate_fields(self):
        """
        Populate form fields with existing entry data

        This method fills all input fields with the current values from
        the password entry being edited. It also formats and displays
        the created and modified timestamps.

        SECURITY NOTE: The password field is intentionally left EMPTY for
        security. Users must click "View Original Password" and verify their
        master password to view the existing password.
        """
        # Set form field values from the entry object
        self.entry_name_var.set(self.entry.entry_name or "")  # Set name if exists
        self.website_var.set(self.entry.website)
        self.username_var.set(self.entry.username)

        # SECURITY: Do NOT pre-populate password field
        # User must explicitly request to view original password
        # self.password_var.set(self.entry.password)  # REMOVED for security
        self.password_var.set("")  # Leave empty initially

        self.remarks_var.set(self.entry.remarks or "")
        self.favorite_var.set(self.entry.is_favorite)

        # Format and display metadata timestamps
        if self.entry.created_at:
            created_str = self._format_datetime(self.entry.created_at)
            self.created_label.configure(
                text=f"📅 Created: {created_str}"
            )

        if self.entry.modified_at:
            modified_str = self._format_datetime(self.entry.modified_at)
            self.modified_label.configure(
                text=f"🔄 Last Modified: {modified_str}"
            )

        # Update strength indicator for the current password
        self._update_strength_indicator()

        logger.debug(f"Fields populated for entry {self.entry.entry_id}")

    def _format_datetime(self, dt):
        """
        Format a datetime object for user-friendly display

        Args:
            dt: datetime object or ISO format string

        Returns:
            str: Formatted date string (e.g., "Jan 15, 2025 at 3:45 PM")
        """
        try:
            # Handle both datetime objects and ISO strings
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))

            return dt.strftime("%b %d, %Y at %I:%M %p")
        except Exception as e:
            logger.warning(f"Error formatting datetime: {e}")
            return str(dt)

    # ========================================================================
    # User Interaction Methods
    # ========================================================================

    def _toggle_password_visibility(self):
        """
        Toggle password field between masked and visible

        When toggled, the password field switches between showing asterisks
        and displaying the actual password characters. The button icon
        changes to reflect the current state.
        """
        self.password_visible = not self.password_visible

        if self.password_visible:
            # Show password in plain text
            self.password_entry.configure(show="")
            self.toggle_password_btn.configure(text="🙈")
            logger.debug("Password visibility: ON")
        else:
            # Hide password with asterisks
            self.password_entry.configure(show="*")
            self.toggle_password_btn.configure(text="👁")
            logger.debug("Password visibility: OFF")

    def _generate_password(self):
        """
        Generate a secure random password and populate the password field

        Creates a strong password using cryptographically secure random
        generation with a mix of uppercase, lowercase, digits, and symbols.
        The generated password is automatically placed in the password field
        and the strength indicator is updated.
        """
        try:
            # Configure generation options for a strong password
            options = GenerationOptions(
                length=16,
                include_lowercase=True,
                include_uppercase=True,
                include_digits=True,
                include_symbols=True,
                exclude_ambiguous=True  # Avoid confusing characters like 0/O, l/1
            )

            # Generate the password
            result = self.password_generator.generate_password(
                options,
                GenerationMethod.RANDOM
            )

            # Set the generated password in the field
            self.password_var.set(result.password)

            # Clear any error messages
            self.status_label.configure(text="")

            logger.info("Password generated successfully")

        except Exception as e:
            logger.error(f"Password generation error: {e}")
            self._show_error("Failed to generate password")

    def _on_password_change(self, *args):
        """
        Callback triggered when password field value changes

        This method is automatically called whenever the user types in
        the password field. It updates the strength indicator in real-time.

        Args:
            *args: Variable trace arguments (unused)
        """
        self._update_strength_indicator()

    def _update_strength_indicator(self):
        """
        Update the password strength indicator based on current password

        Analyzes the password currently in the field and updates both
        the progress bar and text label to reflect its strength.

        Strength levels:
        - Very Weak (0-20%): Red
        - Weak (20-40%): Orange
        - Fair (40-60%): Yellow
        - Good (60-80%): Light Green
        - Strong (80-90%): Green
        - Very Strong (90-100%): Dark Green
        """
        password = self.password_var.get()

        if not password:
            # No password entered
            self.strength_bar.set(0)
            self.strength_label.configure(text="No password", text_color="gray")
            return

        try:
            # Analyze password strength
            analysis = self.strength_checker.analyze_password(password)
            score = analysis.get('score', 0)
            strength = analysis.get('strength', 'Unknown')

            # Convert score to progress bar value (0.0 to 1.0)
            progress_value = score / 100.0
            self.strength_bar.set(progress_value)

            # Determine color based on strength level
            color_map = {
                'very weak': '#ff4444',    # Red
                'weak': '#ff8800',          # Orange
                'fair': '#ffbb00',          # Yellow
                'good': '#88dd44',          # Light Green
                'strong': '#44dd88',        # Green
                'very strong': '#00bb44'   # Dark Green
            }

            strength_lower = strength.lower()
            color = color_map.get(strength_lower, 'gray')

            # Update label with strength description and color
            self.strength_label.configure(
                text=strength.title(),
                text_color=color
            )

        except Exception as e:
            logger.error(f"Strength analysis error: {e}")
            self.strength_label.configure(text="Unknown", text_color="gray")

    # ========================================================================
    # Data Validation and Update Methods
    # ========================================================================

    def _update_password(self):
        """
        Validate input and update the password entry in the database

        This method performs the following steps:
        1. Validates all required fields are filled
        2. Checks if any changes were made
        3. Disables the update button to prevent double-submission
        4. Calls the password manager API to update the entry
        5. Handles success/error responses
        6. Invokes the success callback if update succeeds

        The method uses the session-based API which handles master password
        caching automatically, so no additional password prompt is needed.
        """
        # ====================================================================
        # Input Validation
        # ====================================================================

        entry_name = self.entry_name_var.get().strip() or None  # Convert empty to None
        website = self.website_var.get().strip()
        username = self.username_var.get().strip()
        password = self.password_var.get()
        remarks = self.remarks_var.get().strip()
        is_favorite = self.favorite_var.get()

        # Validate required fields
        if not website:
            self._show_error("Please enter a website or service name")
            self.website_entry.focus()
            return

        if not username:
            self._show_error("Please enter a username or email")
            self.username_entry.focus()
            return

        if not password:
            self._show_error("Please enter a password")
            self.password_entry.focus()
            return

        # ====================================================================
        # Change Detection
        # ====================================================================
        # Check if any fields were actually modified

        changes_made = (
            entry_name != self.entry.entry_name or
            website != self.entry.website or
            username != self.entry.username or
            password != self.entry.password or
            remarks != (self.entry.remarks or "") or
            is_favorite != self.entry.is_favorite
        )

        if not changes_made:
            self._show_error("No changes were made")
            return

        # ====================================================================
        # Update Process
        # ====================================================================

        try:
            # Disable update button to prevent double-submission
            self.update_btn.configure(state="disabled", text="Updating...")
            self.status_label.configure(text="")

            logger.info(f"Updating password entry ID {self.entry.entry_id}")

            # Call the password manager API to update the entry
            # The API handles encryption and master password management
            success = self.password_manager.update_password_entry(
                session_id=self.session_id,
                entry_id=self.entry.entry_id,
                entry_name=entry_name,
                website=website,
                username=username,
                password=password,
                remarks=remarks,
                is_favorite=is_favorite
            )

            if success:
                # Update successful
                logger.info(f"Password entry {self.entry.entry_id} updated successfully")

                # Invoke the success callback to refresh the parent window
                self.on_success()

                # Close the dialog
                self.destroy()
            else:
                # Update failed (entry not found or user doesn't own it)
                self._show_error("Failed to update password entry")
                self.update_btn.configure(state="normal", text="💾 Update Password")

        except Exception as e:
            # Handle any errors during the update process
            error_msg = str(e)
            logger.error(f"Error updating password entry: {error_msg}")

            # Show user-friendly error message
            if "session" in error_msg.lower():
                self._show_error("Session expired. Please login again.")
            elif "master password" in error_msg.lower():
                self._show_error("Master password required")
            else:
                self._show_error(f"Error: {error_msg}")

            # Re-enable the update button
            self.update_btn.configure(state="normal", text="💾 Update Password")

    def _show_error(self, message: str):
        """
        Display an error message in the status label

        Args:
            message (str): Error message to display to the user
        """
        self.status_label.configure(text=message, text_color="red")
        logger.warning(f"Edit dialog error: {message}")

    # ========================================================================
    # Secure Password Viewing Methods (NEW)
    # ========================================================================

    def _view_original_password(self):
        """
        View the original password with master password verification

        This method implements secure password viewing with the following steps:
        1. Prompt user for master password
        2. Verify credentials and retrieve password from database
        3. Display original password in field
        4. Start countdown timer for auto-hide
        5. Change button to "Hide Now" button

        Security features:
        - Requires master password verification
        - Retrieves password on-demand from database
        - Time-limited viewing (auto-hide after timeout)
        - Visual countdown indicator
        - Manual hide option
        """
        # Check if we have necessary data
        if not self.username or not self.auth_manager:
            self._show_error("Cannot verify master password")
            return

        # If password is already visible, just extend the timer
        if self.original_password_visible:
            self.view_time_remaining = self.view_timeout
            self._update_timer_display()
            logger.info("Password view time extended")
            return

        # Prompt for master password
        logger.info("Prompting for master password verification")

        prompt = MasterPasswordPrompt(
            self,
            self.auth_manager,
            self.session_id,
            self.username,
            max_attempts=3
        )

        # Wait for dialog to close (modal)
        self.wait_window(prompt)

        # Get result
        verified, master_password = prompt.get_result()

        if verified and master_password:
            # Master password verified! Now retrieve the password from database
            logger.info("Master password verified - retrieving password from database")

            try:
                # Retrieve the password entry with decrypted password
                entry = self.password_manager.get_password_entry(
                    session_id=self.session_id,
                    entry_id=self.entry.entry_id,
                    master_password=master_password
                )

                if entry and entry.password:
                    # Set the password in the field
                    self.password_var.set(entry.password)

                    # Store for future reference in this session
                    self.stored_original_password = entry.password

                    # Mark as visible
                    self.original_password_visible = True

                    # Start the timer
                    self.view_time_remaining = self.view_timeout
                    self._start_view_timer()

                    # Change the button to "Hide Now"
                    self.view_original_btn.configure(
                        text="🔒",
                        command=self._hide_password
                    )
                    ToolTip(self.view_original_btn, "Hide password immediately")

                    # Update timer display
                    self._update_timer_display()

                    # Clear any error messages
                    self.status_label.configure(text="")

                    logger.info("Original password displayed successfully")
                else:
                    logger.error("Failed to retrieve password from database")
                    self._show_error("Failed to retrieve original password")

            except Exception as e:
                logger.error(f"Error retrieving password: {e}")
                self._show_error(f"Error: {str(e)}")

        else:
            # Verification failed or cancelled
            logger.info("Master password verification failed or cancelled")
            if not verified:
                self._show_error("Master password verification cancelled")

    def _hide_password(self):
        """
        Immediately hide the password and stop the timer

        This method is called when:
        - User clicks the "Hide Now" button
        - Timer expires
        - Dialog is closed

        It clears the password field and resets the UI to the secure state.
        """
        logger.info("Hiding password")

        # Stop the timer if running
        if self.view_timer_id:
            self.after_cancel(self.view_timer_id)
            self.view_timer_id = None

        # Clear the password field
        self.password_var.set("")

        # Mark as not visible
        self.original_password_visible = False
        self.view_time_remaining = 0

        # Clear timer display
        self.timer_label.configure(text="")

        # Change button back to "View Original"
        self.view_original_btn.configure(
            text="🔍",
            command=self._view_original_password
        )
        ToolTip(self.view_original_btn, "View the current saved password (requires master password)")

        # Update strength indicator (will show "No password")
        self._update_strength_indicator()

    def _start_view_timer(self):
        """
        Start the countdown timer for auto-hide

        This timer automatically hides the password after the configured
        timeout period. It updates every second to show the countdown.
        """
        if self.view_timer_id:
            # Cancel existing timer
            self.after_cancel(self.view_timer_id)

        # Start new timer (tick every second)
        self._timer_tick()

    def _timer_tick(self):
        """
        Timer tick method - called every second

        This method:
        - Decrements the remaining time
        - Updates the visual countdown display
        - Auto-hides password when time expires
        - Changes color as time runs out (green → yellow → red)
        """
        if self.view_time_remaining > 0:
            # Decrement time
            self.view_time_remaining -= 1

            # Update display
            self._update_timer_display()

            # Schedule next tick in 1 second
            self.view_timer_id = self.after(1000, self._timer_tick)

        else:
            # Time expired - auto-hide password
            logger.info("Password view timer expired - auto-hiding")
            self._hide_password()

    def _update_timer_display(self):
        """
        Update the timer display label with current remaining time

        Color coding:
        - Green: > 20 seconds remaining
        - Yellow: 10-20 seconds remaining
        - Orange: 5-10 seconds remaining
        - Red: < 5 seconds remaining
        """
        seconds = self.view_time_remaining

        if seconds > 0:
            # Determine color based on remaining time
            if seconds > 20:
                color = "#44dd88"  # Green
            elif seconds > 10:
                color = "#ffbb00"  # Yellow
            elif seconds > 5:
                color = "#ff8800"  # Orange
            else:
                color = "#ff4444"  # Red

            # Format text
            text = f"⏱️ Password visible for {seconds} second{'s' if seconds != 1 else ''}"

            self.timer_label.configure(text=text, text_color=color)
        else:
            self.timer_label.configure(text="")

    def destroy(self):
        """
        Override destroy to clean up timer

        This ensures the timer is properly cancelled when the dialog
        is closed, preventing memory leaks and orphaned timers.
        """
        # Stop timer if running
        if self.view_timer_id:
            self.after_cancel(self.view_timer_id)
            self.view_timer_id = None

        # Call parent destroy
        super().destroy()

class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog"""
    def __init__(self, parent, theme):
        super().__init__(parent)
        
        self.parent_window = parent
        self.theme = theme
        self.original_settings = {}
        self.settings_changed = False
        
        # Configure dialog
        self.title("Settings")
        self.geometry("580x600")
        self.minsize(520, 500)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        # Center dialog
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (520 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (500 // 2)
        self.geometry(f"520x500+{x}+{y}")
        
        self._load_current_settings()
        self._create_ui()
    
    def _load_current_settings(self):
        """Load current application settings"""
        try:
            # Get current theme mode
            current_mode = ctk.get_appearance_mode()
            self.original_settings['theme_mode'] = current_mode
            
            # Get other settings from parent window if available
            if hasattr(self.parent_window, 'auth_manager'):
                self.original_settings['session_timeout'] = 8  # hours
            
            self.original_settings['auto_lock'] = True
            
        except Exception as e:
            logger.error(f"Failed to load current settings: {e}")
    
    def _create_ui(self):
        """Create settings UI"""
        # Main container with scrollable frame
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(main_frame, text="⚙️ Settings", font=("Arial", 20, "bold"))
        title_label.pack(pady=(0, 25))
        
        # Appearance section
        appearance_frame = ctk.CTkFrame(main_frame)
        appearance_frame.pack(fill="x", pady=(0, 15))
        
        appearance_title = ctk.CTkLabel(appearance_frame, text="🎨 Appearance", font=("Arial", 16, "bold"))
        appearance_title.pack(pady=(15, 15), anchor="w", padx=15)
        
        # Theme mode
        mode_frame = ctk.CTkFrame(appearance_frame, fg_color="transparent")
        mode_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(mode_frame, text="Theme Mode:", font=("Arial", 12, "bold")).pack(side="left")
        
        current_mode = ctk.get_appearance_mode()
        self.theme_var = ctk.StringVar(value=current_mode.title())
        self.theme_menu = ctk.CTkOptionMenu(
            mode_frame,
            variable=self.theme_var,
            values=["Light", "Dark", "System"],
            command=self._on_setting_change
        )
        self.theme_menu.pack(side="right")
        
        # Color scheme
        color_frame = ctk.CTkFrame(appearance_frame, fg_color="transparent")
        color_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(color_frame, text="Color Scheme:", font=("Arial", 12, "bold")).pack(side="left")
        
        self.color_var = ctk.StringVar(value="Blue")
        self.color_menu = ctk.CTkOptionMenu(
            color_frame,
            variable=self.color_var,
            values=["Blue", "Green", "Dark-blue"],
            command=self._on_setting_change
        )
        self.color_menu.pack(side="right")
        
        # Security section
        security_frame = ctk.CTkFrame(main_frame)
        security_frame.pack(fill="x", pady=(0, 15))
        
        security_title = ctk.CTkLabel(security_frame, text="🔒 Security", font=("Arial", 16, "bold"))
        security_title.pack(pady=(15, 15), anchor="w", padx=15)
        
        # Session timeout
        timeout_frame = ctk.CTkFrame(security_frame, fg_color="transparent")
        timeout_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(timeout_frame, text="Session Timeout:", font=("Arial", 12, "bold")).pack(side="left")
        
        current_timeout = self.original_settings.get('session_timeout', 8)
        timeout_text = f"{current_timeout} hours"
        if current_timeout < 1:
            timeout_text = f"{int(current_timeout * 60)} minutes"
        
        self.timeout_var = ctk.StringVar(value=timeout_text)
        self.timeout_menu = ctk.CTkOptionMenu(
            timeout_frame,
            variable=self.timeout_var,
            values=["15 minutes", "30 minutes", "1 hour", "2 hours", "4 hours", "8 hours", "Never"],
            command=self._on_setting_change
        )
        self.timeout_menu.pack(side="right")
        
        # Auto-lock checkbox
        self.autolock_var = ctk.BooleanVar(value=self.original_settings.get('auto_lock', True))
        autolock_check = ctk.CTkCheckBox(
            security_frame,
            text="🔐 Auto-lock when inactive",
            variable=self.autolock_var,
            command=self._on_setting_change,
            font=("Arial", 12)
        )
        autolock_check.pack(padx=15, pady=(0, 10), anchor="w")
        
        # Clear clipboard checkbox
        self.clear_clipboard_var = ctk.BooleanVar(value=True)
        clear_clipboard_check = ctk.CTkCheckBox(
            security_frame,
            text="🗑️ Clear clipboard after copying passwords",
            variable=self.clear_clipboard_var,
            command=self._on_setting_change,
            font=("Arial", 12)
        )
        clear_clipboard_check.pack(padx=15, pady=(0, 15), anchor="w")
        
        # Password Generation section
        password_frame = ctk.CTkFrame(main_frame)
        password_frame.pack(fill="x", pady=(0, 15))
        
        password_title = ctk.CTkLabel(password_frame, text="🎲 Password Generation", font=("Arial", 16, "bold"))
        password_title.pack(pady=(15, 15), anchor="w", padx=15)
        
        # Default password length
        length_frame = ctk.CTkFrame(password_frame, fg_color="transparent")
        length_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(length_frame, text="Default Length:", font=("Arial", 12, "bold")).pack(side="left")
        
        self.length_var = ctk.StringVar(value="16")
        length_entry = ctk.CTkEntry(length_frame, textvariable=self.length_var, width=80)
        length_entry.pack(side="right")
        length_entry.bind('<KeyRelease>', lambda e: self._on_setting_change())
        
        # Include symbols checkbox
        self.symbols_var = ctk.BooleanVar(value=True)
        symbols_check = ctk.CTkCheckBox(
            password_frame,
            text="Include special characters (!@#$%^&*)",
            variable=self.symbols_var,
            command=self._on_setting_change,
            font=("Arial", 12)
        )
        symbols_check.pack(padx=15, pady=(0, 15), anchor="w")
        
        # About section
        about_frame = ctk.CTkFrame(main_frame)
        about_frame.pack(fill="x", pady=(0, 15))
        
        about_title = ctk.CTkLabel(about_frame, text="ℹ️ About", font=("Arial", 16, "bold"))
        about_title.pack(pady=(15, 15), anchor="w", padx=15)
        
        about_text = ctk.CTkLabel(
            about_frame,
            text="Personal Password Manager v2.2.0\n"
                 "Secure local password storage with AES-256 encryption\n"
                 "PBKDF2 key derivation with 100,000+ iterations\n"
                 "Built with Python & CustomTkinter\n\n"
                 "🔐 Your passwords are encrypted locally and never transmitted\n"
                 "🛡️ Master password is never stored on disk\n"
                 "💾 SQLite database with secure foreign key constraints",
            justify="left",
            font=("Arial", 11)
        )
        about_text.pack(padx=15, pady=(0, 15), anchor="w")
        
        # Buttons frame - fixed at bottom
        button_container = ctk.CTkFrame(self, fg_color="transparent")
        button_container.pack(fill="x", padx=20, pady=(0, 20))
        
        button_frame = ctk.CTkFrame(button_container)
        button_frame.pack(fill="x")
        
        # Button container
        btn_inner = ctk.CTkFrame(button_frame, fg_color="transparent")
        btn_inner.pack(fill="x", padx=15, pady=10)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            btn_inner, 
            text="Cancel", 
            command=self._cancel_settings,
            fg_color="gray",
            hover_color="darkgray"
        )
        cancel_btn.pack(side="right", padx=(10, 0))
        ToolTip(cancel_btn, "Cancel changes and close dialog")
        
        # Apply button
        self.apply_btn = ctk.CTkButton(
            btn_inner, 
            text="Apply", 
            command=self._apply_settings,
            state="disabled"
        )
        self.apply_btn.pack(side="right", padx=(10, 0))
        ToolTip(self.apply_btn, "Apply changes without closing dialog")
        
        # Save & Close button
        save_btn = ctk.CTkButton(
            btn_inner, 
            text="Save & Close", 
            command=self._save_and_close,
            fg_color="green",
            hover_color="darkgreen"
        )
        save_btn.pack(side="right", padx=(10, 0))
        ToolTip(save_btn, "Save all settings and close dialog")
    
    def _on_setting_change(self, *args):
        """Called when any setting is changed"""
        self.settings_changed = True
        self.apply_btn.configure(state="normal")
    
    def _apply_settings(self):
        """Apply settings without closing dialog"""
        try:
            # Apply theme changes
            theme_mode = self.theme_var.get().lower()
            if theme_mode != ctk.get_appearance_mode():
                ctk.set_appearance_mode(theme_mode)
            
            # Apply color scheme
            color_scheme = self.color_var.get().lower()
            ctk.set_default_color_theme(color_scheme)
            
            # Show feedback
            self.apply_btn.configure(text="Applied!", state="disabled")
            self.after(1500, lambda: self.apply_btn.configure(text="Apply"))
            
            # Settings applied successfully
            self.settings_changed = False
            
            logger.info(f"Settings applied: Theme={theme_mode}, Color={color_scheme}")
            
        except Exception as e:
            logger.error(f"Failed to apply settings: {e}")
            messagebox.showerror("Error", f"Failed to apply settings: {e}", parent=self)
    
    def _save_and_close(self):
        """Save all settings and close dialog"""
        if self.settings_changed:
            self._apply_settings()
        
        # Here you could save settings to a config file
        try:
            self._save_settings_to_file()
            messagebox.showinfo("Settings", "Settings saved successfully!", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}", parent=self)
        
        self.destroy()
    
    def _cancel_settings(self):
        """Cancel changes and close dialog"""
        if self.settings_changed:
            result = messagebox.askyesno(
                "Unsaved Changes", 
                "You have unsaved changes. Are you sure you want to cancel?",
                parent=self
            )
            if not result:
                return
        
        self.destroy()
    
    def _save_settings_to_file(self):
        """Save settings to configuration file"""
        import json
        from pathlib import Path
        
        config_dir = Path("data")
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "settings.json"
        
        settings = {
            "theme_mode": self.theme_var.get().lower(),
            "color_scheme": self.color_var.get().lower(),
            "session_timeout": self.timeout_var.get(),
            "auto_lock": self.autolock_var.get(),
            "clear_clipboard": self.clear_clipboard_var.get(),
            "password_length": self.length_var.get(),
            "include_symbols": self.symbols_var.get(),
            "last_updated": datetime.now().isoformat()
        }
        
        with open(config_file, 'w') as f:
            json.dump(settings, f, indent=2)
        
        logger.info(f"Settings saved to {config_file}")

class CSVImportDialog(ctk.CTkToplevel):
    """CSV Import dialog for importing passwords from files with selection"""
    def __init__(self, parent, session_id, password_manager, csv_file_path, on_success, auth_manager, username):
        super().__init__(parent)

        self.session_id = session_id
        self.password_manager = password_manager
        self.csv_file_path = csv_file_path
        self.on_success = on_success
        self.auth_manager = auth_manager
        self.username = username
        self.all_data = []  # Store ALL rows, not just preview
        self.column_mapping = {}
        self.row_checkboxes = []  # Store checkbox variables
        self.step = 1  # Track current step (1=mapping, 2=selection)

        # Configure dialog
        self.title("Import Passwords from CSV - Step 1: Column Mapping")
        self.geometry("900x600")
        self.minsize(800, 500)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        # Center dialog
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (900 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (600 // 2)
        self.geometry(f"900x600+{x}+{y}")

        self._load_csv_data()
        self._create_mapping_ui()
    
    def _load_csv_data(self):
        """Load ALL data from CSV file"""
        try:
            import csv
            import chardet

            # Detect encoding
            with open(self.csv_file_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding']

            # Read CSV file - load ALL rows
            with open(self.csv_file_path, 'r', encoding=encoding, newline='') as f:
                dialect = csv.Sniffer().sniff(f.read(1024))
                f.seek(0)
                reader = csv.reader(f, dialect)

                self.headers = next(reader, [])
                self.all_data = list(reader)  # Load ALL rows

            logger.info(f"Loaded {len(self.all_data)} rows from CSV file")

        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to read CSV file: {e}", parent=self)
            self.destroy()
    
    def _create_mapping_ui(self):
        """Step 1: Create column mapping UI"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(main_frame, text="📄 Step 1: Map CSV Columns", font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 10))

        # Instructions
        instructions = ctk.CTkLabel(
            main_frame,
            text=f"Map the CSV columns to password fields. Found {len(self.all_data)} rows.",
            font=("Arial", 12)
        )
        instructions.pack(pady=(0, 15))

        # Column mapping frame
        mapping_frame = ctk.CTkFrame(main_frame)
        mapping_frame.pack(fill="x", pady=(0, 15))

        mapping_title = ctk.CTkLabel(mapping_frame, text="Column Mapping", font=("Arial", 14, "bold"))
        mapping_title.pack(pady=(10, 10))

        # Create mapping controls
        self.mapping_vars = {}
        for field in ["Name", "Website", "Username", "Password", "Remarks"]:
            field_frame = ctk.CTkFrame(mapping_frame, fg_color="transparent")
            field_frame.pack(fill="x", padx=15, pady=5)

            ctk.CTkLabel(field_frame, text=f"{field}:", font=("Arial", 12, "bold"), width=80).pack(side="left")

            var = ctk.StringVar()
            dropdown = ctk.CTkOptionMenu(
                field_frame,
                variable=var,
                values=["<Not mapped>"] + self.headers,
                width=200
            )
            dropdown.pack(side="left", padx=(10, 0))
            self.mapping_vars[field.lower()] = var

            # Auto-map common column names
            field_lower = field.lower()
            for header in self.headers:
                header_lower = header.lower()
                if (field_lower in header_lower or
                    (field_lower == "name" and any(x in header_lower for x in ["name", "title", "label", "entry_name"])) or
                    (field_lower == "website" and any(x in header_lower for x in ["url", "site", "domain"])) or
                    (field_lower == "username" and any(x in header_lower for x in ["user", "email", "login"])) or
                    (field_lower == "password" and "pass" in header_lower) or
                    (field_lower == "remarks" and any(x in header_lower for x in ["note", "comment", "remark"]))):
                    var.set(header)
                    break

        # Preview frame
        preview_frame = ctk.CTkFrame(main_frame)
        preview_frame.pack(fill="both", expand=True, pady=(0, 15))

        preview_title = ctk.CTkLabel(preview_frame, text="Preview (first 5 rows)", font=("Arial", 14, "bold"))
        preview_title.pack(pady=(10, 5))

        # Scrollable preview
        preview_scroll = ctk.CTkScrollableFrame(preview_frame, height=150)
        preview_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Headers
        header_frame = ctk.CTkFrame(preview_scroll, fg_color="gray20")
        header_frame.pack(fill="x", pady=(0, 5))

        for header in self.headers[:4]:  # Limit to 4 columns
            ctk.CTkLabel(header_frame, text=header, font=("Arial", 10, "bold"), width=150).pack(side="left", padx=5, pady=5)

        # Preview rows (first 5)
        for row in self.all_data[:5]:
            row_frame = ctk.CTkFrame(preview_scroll, fg_color="transparent")
            row_frame.pack(fill="x", pady=1)

            for i, cell in enumerate(row[:4]):  # Limit to 4 columns
                text = str(cell)[:30] + "..." if len(str(cell)) > 30 else str(cell)
                ctk.CTkLabel(row_frame, text=text, font=("Arial", 9), width=150).pack(side="left", padx=5, pady=2)

        # Status
        self.status_label = ctk.CTkLabel(main_frame, text="", text_color="red")
        self.status_label.pack(pady=(0, 10))

        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=self.destroy, fg_color="gray", width=100)
        cancel_btn.pack(side="right", padx=(10, 0))
        ToolTip(cancel_btn, "Cancel import and close dialog")

        next_btn = ctk.CTkButton(button_frame, text="Next: Select Passwords →", command=self._go_to_selection_step, width=180)
        next_btn.pack(side="right", padx=(10, 0))
        ToolTip(next_btn, "Proceed to select which passwords to import")

        import_all_btn = ctk.CTkButton(button_frame, text="📥 Import All Passwords", command=self._import_all_passwords, fg_color="#2B7A0B", hover_color="#3D9B1A", width=180)
        import_all_btn.pack(side="right")
        ToolTip(import_all_btn, "Import all passwords from CSV immediately")

    def _import_all_passwords(self):
        """Validate mapping and import all passwords immediately"""
        # Validate required fields are mapped
        required_fields = ["website", "username", "password"]
        missing_fields = []

        for field in required_fields:
            if self.mapping_vars[field].get() == "<Not mapped>":
                missing_fields.append(field.title())

        if missing_fields:
            self.status_label.configure(text=f"⚠️ Please map required fields: {', '.join(missing_fields)}")
            return

        # Create column index mapping
        self.column_map = {}
        for field, var in self.mapping_vars.items():
            header = var.get()
            if header != "<Not mapped>" and header in self.headers:
                self.column_map[field] = self.headers.index(header)

        logger.info(f"Column mapping validated. Importing all {len(self.all_data)} passwords.")

        # Prompt for master password
        prompt = MasterPasswordPrompt(
            self,
            self.auth_manager,
            self.session_id,
            self.username,
            max_attempts=3
        )

        self.wait_window(prompt)
        verified, master_password = prompt.get_result()

        if not verified or not master_password:
            logger.info("Master password verification failed or cancelled - import aborted")
            self.status_label.configure(text="⚠️ Import cancelled - master password not verified")
            return

        logger.info("Master password verified - proceeding with import of all passwords")

        # Import all passwords
        self._import_all_passwords_execute(master_password)

    def _import_all_passwords_execute(self, master_password):
        """Execute import of all passwords from CSV"""
        try:
            success_count = 0
            error_count = 0

            # Import ALL rows
            for row_idx, row in enumerate(self.all_data):
                try:
                    # Extract data based on mapping
                    entry_name = row[self.column_map["name"]] if "name" in self.column_map and len(row) > self.column_map["name"] else ""
                    website = row[self.column_map["website"]] if "website" in self.column_map and len(row) > self.column_map["website"] else ""
                    username = row[self.column_map["username"]] if "username" in self.column_map and len(row) > self.column_map["username"] else ""
                    password = row[self.column_map["password"]] if "password" in self.column_map and len(row) > self.column_map["password"] else ""
                    remarks = row[self.column_map["remarks"]] if "remarks" in self.column_map and len(row) > self.column_map["remarks"] else ""

                    # Skip empty rows
                    if not website or not username or not password:
                        error_count += 1
                        continue

                    # Add password entry with master password for encryption
                    self.password_manager.add_password_entry(
                        session_id=self.session_id,
                        entry_name=entry_name.strip() if entry_name else None,
                        website=website.strip(),
                        username=username.strip(),
                        password=password,
                        remarks=remarks.strip() if remarks else "",
                        master_password=master_password
                    )
                    success_count += 1

                except Exception as e:
                    logger.error(f"Failed to import row {row_idx}: {e}")
                    error_count += 1
                    continue

            # Show results
            if success_count > 0:
                message = f"✅ Successfully imported {success_count} password{'s' if success_count != 1 else ''}"
                if error_count > 0:
                    message += f"\n⚠️ {error_count} error{'s' if error_count != 1 else ''} occurred"

                messagebox.showinfo("Import Complete", message, parent=self)
                logger.info(f"Import complete: {success_count} success, {error_count} errors")

                # Refresh main window
                if self.on_success:
                    self.on_success()

                # Close dialog
                self.destroy()
            else:
                messagebox.showerror("Import Failed", f"Failed to import any passwords.\n{error_count} error(s) occurred.", parent=self)
                logger.error("Import failed - no passwords imported")

        except Exception as e:
            logger.error(f"Import execution failed: {e}")
            messagebox.showerror("Import Error", f"An error occurred during import:\n{str(e)}", parent=self)

    def _go_to_selection_step(self):
        """Validate mapping and go to step 2: password selection"""
        # Validate required fields are mapped
        required_fields = ["website", "username", "password"]
        missing_fields = []

        for field in required_fields:
            if self.mapping_vars[field].get() == "<Not mapped>":
                missing_fields.append(field.title())

        if missing_fields:
            self.status_label.configure(text=f"⚠️ Please map required fields: {', '.join(missing_fields)}")
            return

        # Create column index mapping
        self.column_map = {}
        for field, var in self.mapping_vars.items():
            header = var.get()
            if header != "<Not mapped>" and header in self.headers:
                self.column_map[field] = self.headers.index(header)

        logger.info(f"Column mapping validated. Proceeding to selection step.")

        # Clear current UI and show selection UI
        for widget in self.winfo_children():
            widget.destroy()

        self.step = 2
        self.title("Import Passwords from CSV - Step 2: Select Passwords")
        self._create_selection_ui()

    def _create_selection_ui(self):
        """Step 2: Create password selection UI with checkboxes"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(main_frame, text="✅ Step 2: Select Passwords to Import", font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 10))

        # Instructions
        instructions = ctk.CTkLabel(
            main_frame,
            text=f"Select which passwords you want to import ({len(self.all_data)} total rows found)",
            font=("Arial", 12)
        )
        instructions.pack(pady=(0, 10))

        # Select All / Deselect All buttons
        control_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        control_frame.pack(fill="x", pady=(0, 10))

        select_all_btn = ctk.CTkButton(control_frame, text="✓ Select All", command=self._select_all, width=120)
        select_all_btn.pack(side="left", padx=5)
        ToolTip(select_all_btn, "Select all passwords for import")

        deselect_all_btn = ctk.CTkButton(control_frame, text="✗ Deselect All", command=self._deselect_all, width=120, fg_color="gray")
        deselect_all_btn.pack(side="left", padx=5)
        ToolTip(deselect_all_btn, "Deselect all passwords")

        # Selection count label
        self.selection_count_label = ctk.CTkLabel(control_frame, text="0 selected", font=("Arial", 12, "bold"))
        self.selection_count_label.pack(side="left", padx=20)

        # Scrollable frame for password list
        scroll_frame = ctk.CTkScrollableFrame(main_frame, height=350)
        scroll_frame.pack(fill="both", expand=True, pady=(0, 15))

        # Header row
        header_frame = ctk.CTkFrame(scroll_frame, fg_color="gray20")
        header_frame.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(header_frame, text="", width=40).pack(side="left", padx=5)  # Checkbox column
        ctk.CTkLabel(header_frame, text="Website", font=("Arial", 10, "bold"), width=200).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Username", font=("Arial", 10, "bold"), width=200).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Remarks", font=("Arial", 10, "bold"), width=200).pack(side="left", padx=5)

        # Create checkbox for each row
        self.row_checkboxes = []
        for row_idx, row in enumerate(self.all_data):
            try:
                # Extract data based on mapping
                entry_name = row[self.column_map["name"]] if "name" in self.column_map and len(row) > self.column_map["name"] else ""
                website = row[self.column_map["website"]] if "website" in self.column_map and len(row) > self.column_map["website"] else ""
                username = row[self.column_map["username"]] if "username" in self.column_map and len(row) > self.column_map["username"] else ""
                remarks = row[self.column_map["remarks"]] if "remarks" in self.column_map and len(row) > self.column_map["remarks"] else ""
                password = row[self.column_map["password"]] if "password" in self.column_map and len(row) > self.column_map["password"] else ""

                # Skip rows with missing required fields
                if not website or not username or not password:
                    continue

                # Create row frame
                row_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=2)

                # Checkbox
                checkbox_var = ctk.BooleanVar(value=True)  # Default: selected
                checkbox = ctk.CTkCheckBox(row_frame, text="", variable=checkbox_var, width=40, command=self._update_selection_count)
                checkbox.pack(side="left", padx=5)

                # Store checkbox variable and row index
                self.row_checkboxes.append((checkbox_var, row_idx))

                # Website
                website_text = str(website)[:30] + "..." if len(str(website)) > 30 else str(website)
                ctk.CTkLabel(row_frame, text=website_text, font=("Arial", 9), width=200).pack(side="left", padx=5)

                # Username
                username_text = str(username)[:30] + "..." if len(str(username)) > 30 else str(username)
                ctk.CTkLabel(row_frame, text=username_text, font=("Arial", 9), width=200).pack(side="left", padx=5)

                # Remarks
                remarks_text = str(remarks)[:30] + "..." if len(str(remarks)) > 30 else str(remarks)
                ctk.CTkLabel(row_frame, text=remarks_text, font=("Arial", 9), width=200).pack(side="left", padx=5)

            except Exception as e:
                logger.error(f"Failed to create row {row_idx}: {e}")
                continue

        # Update initial count
        self._update_selection_count()

        # Status label
        self.status_label = ctk.CTkLabel(main_frame, text="", text_color="red")
        self.status_label.pack(pady=(0, 10))

        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        back_btn = ctk.CTkButton(button_frame, text="← Back to Mapping", command=self._back_to_mapping, fg_color="gray", width=150)
        back_btn.pack(side="left")
        ToolTip(back_btn, "Go back to column mapping step")

        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=self.destroy, fg_color="gray", width=100)
        cancel_btn.pack(side="right", padx=(10, 0))
        ToolTip(cancel_btn, "Cancel import and close dialog")

        self.import_btn = ctk.CTkButton(button_frame, text="Import Selected Passwords", command=self._import_with_master_password, width=180)
        self.import_btn.pack(side="right")
        ToolTip(self.import_btn, "Import selected passwords (requires master password)")

    def _select_all(self):
        """Select all checkboxes"""
        for checkbox_var, _ in self.row_checkboxes:
            checkbox_var.set(True)
        self._update_selection_count()

    def _deselect_all(self):
        """Deselect all checkboxes"""
        for checkbox_var, _ in self.row_checkboxes:
            checkbox_var.set(False)
        self._update_selection_count()

    def _update_selection_count(self):
        """Update the selection count label"""
        selected_count = sum(1 for checkbox_var, _ in self.row_checkboxes if checkbox_var.get())
        self.selection_count_label.configure(text=f"{selected_count} selected")

    def _back_to_mapping(self):
        """Go back to step 1: mapping"""
        # Clear current UI
        for widget in self.winfo_children():
            widget.destroy()

        self.step = 1
        self.title("Import Passwords from CSV - Step 1: Column Mapping")
        self._create_mapping_ui()

    def _import_with_master_password(self):
        """Prompt for master password and import selected passwords"""
        # Check if any passwords are selected
        selected_count = sum(1 for checkbox_var, _ in self.row_checkboxes if checkbox_var.get())
        if selected_count == 0:
            self.status_label.configure(text="⚠️ Please select at least one password to import")
            return

        logger.info(f"Prompting for master password to import {selected_count} passwords")

        # Prompt for master password
        prompt = MasterPasswordPrompt(
            self,
            self.auth_manager,
            self.session_id,
            self.username,
            max_attempts=3
        )

        self.wait_window(prompt)
        verified, master_password = prompt.get_result()

        if not verified or not master_password:
            logger.info("Master password verification failed or cancelled - import aborted")
            self.status_label.configure(text="⚠️ Import cancelled - master password not verified")
            return

        logger.info("Master password verified - proceeding with import")

        # Import selected passwords
        self._import_passwords(master_password)

    def _import_passwords(self, master_password):
        """Import selected passwords from CSV with master password"""
        try:
            self.import_btn.configure(state="disabled", text="Importing...")

            # Build set of selected row indices
            selected_indices = set()
            for checkbox_var, row_idx in self.row_checkboxes:
                if checkbox_var.get():
                    selected_indices.add(row_idx)

            logger.info(f"Importing {len(selected_indices)} selected passwords")

            success_count = 0
            error_count = 0

            # Import only selected rows
            for row_idx in selected_indices:
                try:
                    row = self.all_data[row_idx]

                    # Extract data based on mapping
                    entry_name = row[self.column_map["name"]] if "name" in self.column_map and len(row) > self.column_map["name"] else ""
                    website = row[self.column_map["website"]] if "website" in self.column_map and len(row) > self.column_map["website"] else ""
                    username = row[self.column_map["username"]] if "username" in self.column_map and len(row) > self.column_map["username"] else ""
                    password = row[self.column_map["password"]] if "password" in self.column_map and len(row) > self.column_map["password"] else ""
                    remarks = row[self.column_map["remarks"]] if "remarks" in self.column_map and len(row) > self.column_map["remarks"] else ""

                    # Skip empty rows (shouldn't happen as we filtered during UI creation)
                    if not website or not username or not password:
                        error_count += 1
                        continue

                    # Add password entry with master password for encryption
                    self.password_manager.add_password_entry(
                        session_id=self.session_id,
                        entry_name=entry_name.strip() if entry_name else None,
                        website=website.strip(),
                        username=username.strip(),
                        password=password,
                        remarks=remarks.strip() if remarks else "",
                        master_password=master_password  # Pass master password for encryption
                    )
                    success_count += 1

                except Exception as e:
                    logger.error(f"Failed to import row {row_idx}: {e}")
                    error_count += 1
                    continue

            # Show results
            if success_count > 0:
                message = f"✅ Successfully imported {success_count} password{'s' if success_count != 1 else ''}"
                if error_count > 0:
                    message += f"\n⚠️ {error_count} error{'s' if error_count != 1 else ''} occurred"
                messagebox.showinfo("Import Complete", message, parent=self)
                logger.info(f"Import completed: {success_count} successes, {error_count} errors")
                self.on_success()
                self.destroy()
            else:
                messagebox.showerror("Import Failed", "No passwords were imported. Please check your selections.", parent=self)
                self.import_btn.configure(state="normal", text="Import Selected Passwords")

        except Exception as e:
            logger.error(f"CSV import failed: {e}")
            messagebox.showerror("Import Error", f"Failed to import passwords: {e}", parent=self)
            self.import_btn.configure(state="normal", text="Import Selected Passwords")

if __name__ == "__main__":
    # Test the main window
    print("Testing Personal Password Manager Main Window...")
    
    try:
        from .themes import setup_theme
        from ..core.password_manager import create_password_manager
        from ..core.auth import create_auth_manager
        
        # Initialize theme
        setup_theme()
        
        # Create managers
        auth_manager = create_auth_manager("test_main.db")
        password_manager = create_password_manager("test_main.db")
        
        # Create test user and authenticate
        user_id = auth_manager.create_user_account("testuser", "testpassword123")
        session_id = auth_manager.authenticate_user("testuser", "testpassword123")
        
        # Create main window
        app = MainWindow(session_id, "testuser", password_manager, auth_manager)
        
        # Run app
        app.mainloop()
        
        print("✓ Main window test completed!")
        
    except Exception as e:
        print(f"❌ Main window test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test database
        import os
        if os.path.exists("test_main.db"):
            os.remove("test_main.db")