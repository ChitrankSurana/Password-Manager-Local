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
Version: 1.0.0
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
        
        # Website/service name
        website_label = create_themed_label(
            header_frame,
            text=self.entry.website,
            style="label"
        )
        website_label.configure(font=fonts["body_large"])
        website_label.pack(side="left", anchor="w")
        
        # Favorite indicator
        if self.entry.is_favorite:
            favorite_label = create_themed_label(
                header_frame,
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
        
        # View/Edit button
        edit_btn = create_themed_button(
            actions_frame,
            text="✏️",
            style="button_secondary",
            width=30,
            command=self._edit_entry
        )
        edit_btn.pack(side="right", padx=(spacing["padding_xs"], 0))
        
        # Expand/collapse button
        self.expand_btn = create_themed_button(
            actions_frame,
            text="▼" if self.is_expanded else "▶",
            style="button_secondary",
            width=30,
            command=self._toggle_expand
        )
        self.expand_btn.pack(side="right")
        
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
        """Toggle password visibility"""
        if self.password_display.cget("text").startswith("*"):
            if self.entry.password:
                self.password_display.configure(text=self.entry.password)
                self.show_password_btn.configure(text="🙈")
        else:
            self.password_display.configure(text="*" * 12)
            self.show_password_btn.configure(text="👁")
    
    def _copy_password(self):
        """Copy password to clipboard"""
        if self.entry.password:
            try:
                pyperclip.copy(self.entry.password)
                self.main_window._show_temporary_message("Password copied to clipboard", "success")
            except Exception as e:
                logger.error(f"Failed to copy password: {e}")
                self.main_window._show_temporary_message("Failed to copy password", "error")
        else:
            self.main_window._show_temporary_message("Password not loaded", "warning")
    
    def _edit_entry(self):
        """Edit this password entry"""
        self.main_window._edit_password_entry(self.entry)

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
                 parent=None):
        """
        Initialize the main window
        
        Args:
            session_id: Valid session ID
            username: Authenticated username
            password_manager: Password management system
            auth_manager: Authentication manager
            parent: Parent window (optional)
        """
        super().__init__(parent)
        
        self.session_id = session_id
        self.username = username
        self.password_manager = password_manager
        self.auth_manager = auth_manager
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
        BackupManagerDialog(self, self.session_id, self.password_manager)
    
    def _show_settings(self):
        """Show settings dialog"""
        SettingsDialog(self, self.theme)
    
    def _logout(self):
        """Logout and return to login screen"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            try:
                self.auth_manager.logout_user(self.session_id)
            except Exception as e:
                logger.error(f"Logout error: {e}")
            
            self.destroy()
    
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
        self.destroy()
    
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
                on_success=lambda: self._load_password_entries()
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
        self.website_entry.focus()
    
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
                remarks=remarks
            )
            
            # Success
            self.on_success()
            self.destroy()
            
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}")
            self.add_btn.configure(state="normal", text="Add Password")

class EditPasswordDialog:
    """Placeholder for edit password dialog"""
    def __init__(self, parent, session_id, password_manager, entry, on_success):
        messagebox.showinfo("Edit Password", f"Edit password dialog for {entry.website} would open here")
        on_success()

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
            text="Personal Password Manager v1.0.0\n"
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
    """CSV Import dialog for importing passwords from files"""
    def __init__(self, parent, session_id, password_manager, csv_file_path, on_success):
        super().__init__(parent)
        
        self.session_id = session_id
        self.password_manager = password_manager
        self.csv_file_path = csv_file_path
        self.on_success = on_success
        self.preview_data = []
        self.column_mapping = {}
        
        # Configure dialog
        self.title("Import Passwords from CSV")
        self.geometry("700x500")
        self.minsize(600, 400)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        # Center dialog
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (700 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (500 // 2)
        self.geometry(f"700x500+{x}+{y}")
        
        self._load_csv_preview()
        self._create_ui()
    
    def _load_csv_preview(self):
        """Load and preview CSV file"""
        try:
            import csv
            import chardet
            
            # Detect encoding
            with open(self.csv_file_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding']
            
            # Read CSV file
            with open(self.csv_file_path, 'r', encoding=encoding, newline='') as f:
                dialect = csv.Sniffer().sniff(f.read(1024))
                f.seek(0)
                reader = csv.reader(f, dialect)
                
                self.headers = next(reader, [])
                self.preview_data = []
                
                # Load first 10 rows for preview
                for i, row in enumerate(reader):
                    if i >= 10:
                        break
                    self.preview_data.append(row)
                        
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to read CSV file: {e}", parent=self)
            self.destroy()
    
    def _create_ui(self):
        """Create import dialog UI"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(main_frame, text="📄 Import Passwords from CSV", font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Instructions
        instructions = ctk.CTkLabel(
            main_frame,
            text="Map the CSV columns to password fields. Preview shows first 10 rows.",
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
        for field in ["Website", "Username", "Password", "Remarks"]:
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
                    (field_lower == "website" and any(x in header_lower for x in ["url", "site", "domain"])) or
                    (field_lower == "username" and any(x in header_lower for x in ["user", "email", "login"])) or
                    (field_lower == "password" and "pass" in header_lower) or
                    (field_lower == "remarks" and any(x in header_lower for x in ["note", "comment", "remark"]))):
                    var.set(header)
                    break
        
        # Preview frame with scrollable content
        preview_frame = ctk.CTkFrame(main_frame)
        preview_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        preview_title = ctk.CTkLabel(preview_frame, text="Preview", font=("Arial", 14, "bold"))
        preview_title.pack(pady=(10, 5))
        
        # Scrollable preview
        preview_scroll = ctk.CTkScrollableFrame(preview_frame)
        preview_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Headers
        header_frame = ctk.CTkFrame(preview_scroll, fg_color="gray20")
        header_frame.pack(fill="x", pady=(0, 5))
        
        for header in self.headers[:6]:  # Limit to 6 columns for display
            ctk.CTkLabel(header_frame, text=header, font=("Arial", 10, "bold"), width=100).pack(side="left", padx=5, pady=5)
        
        # Preview rows
        for row in self.preview_data[:5]:  # Show first 5 rows
            row_frame = ctk.CTkFrame(preview_scroll, fg_color="transparent")
            row_frame.pack(fill="x", pady=1)
            
            for i, cell in enumerate(row[:6]):  # Limit to 6 columns
                text = str(cell)[:20] + "..." if len(str(cell)) > 20 else str(cell)
                ctk.CTkLabel(row_frame, text=text, font=("Arial", 9), width=100).pack(side="left", padx=5, pady=2)
        
        # Status
        self.status_label = ctk.CTkLabel(main_frame, text="", text_color="red")
        self.status_label.pack(pady=(0, 10))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=self.destroy, fg_color="gray")
        cancel_btn.pack(side="right", padx=(10, 0))
        ToolTip(cancel_btn, "Cancel import and close dialog")
        
        self.import_btn = ctk.CTkButton(button_frame, text="Import Passwords", command=self._import_passwords)
        self.import_btn.pack(side="right")
        ToolTip(self.import_btn, "Import passwords from the CSV file")
    
    def _import_passwords(self):
        """Import passwords from CSV"""
        try:
            # Validate mapping
            required_fields = ["website", "username", "password"]
            missing_fields = []
            
            for field in required_fields:
                if self.mapping_vars[field].get() == "<Not mapped>":
                    missing_fields.append(field.title())
            
            if missing_fields:
                self.status_label.configure(text=f"Please map: {', '.join(missing_fields)}")
                return
            
            self.import_btn.configure(state="disabled", text="Importing...")
            
            # Create column index mapping
            column_map = {}
            for field, var in self.mapping_vars.items():
                header = var.get()
                if header != "<Not mapped>" and header in self.headers:
                    column_map[field] = self.headers.index(header)
            
            # Import CSV data
            import csv
            import chardet
            
            # Detect encoding again
            with open(self.csv_file_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding']
            
            success_count = 0
            error_count = 0
            
            with open(self.csv_file_path, 'r', encoding=encoding, newline='') as f:
                dialect = csv.Sniffer().sniff(f.read(1024))
                f.seek(0)
                reader = csv.reader(f, dialect)
                next(reader)  # Skip headers
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        # Extract data based on mapping
                        website = row[column_map["website"]] if "website" in column_map else ""
                        username = row[column_map["username"]] if "username" in column_map else ""
                        password = row[column_map["password"]] if "password" in column_map else ""
                        remarks = row[column_map["remarks"]] if "remarks" in column_map else ""
                        
                        # Skip empty rows
                        if not website or not username or not password:
                            continue
                        
                        # Add password entry
                        self.password_manager.add_password_entry(
                            session_id=self.session_id,
                            website=website.strip(),
                            username=username.strip(),
                            password=password,
                            remarks=remarks.strip() if remarks else ""
                        )
                        success_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to import row {row_num}: {e}")
                        error_count += 1
                        continue
            
            # Show results
            if success_count > 0:
                message = f"Successfully imported {success_count} passwords"
                if error_count > 0:
                    message += f" ({error_count} errors)"
                messagebox.showinfo("Import Complete", message, parent=self)
                self.on_success()
                self.destroy()
            else:
                messagebox.showerror("Import Failed", "No passwords were imported. Please check your CSV file and column mapping.", parent=self)
                self.import_btn.configure(state="normal", text="Import Passwords")
                
        except Exception as e:
            logger.error(f"CSV import failed: {e}")
            messagebox.showerror("Import Error", f"Failed to import passwords: {e}", parent=self)
            self.import_btn.configure(state="normal", text="Import Passwords")

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