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
from tkinter import messagebox, filedialog
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        self.entry_widgets = []
        
        # Configure scrollable frame
        self.configure(label_font=self.theme.get_fonts()["heading_small"])
    
    def update_entries(self, entries: List[PasswordEntry]):
        """
        Update the displayed password entries
        
        Args:
            entries: List of password entries to display
        """
        # Clear existing widgets
        for widget in self.entry_widgets:
            widget.destroy()
        self.entry_widgets.clear()
        
        # Add new entries
        for i, entry in enumerate(entries):
            entry_widget = PasswordEntryWidget(self, entry, self.main_window)
            entry_widget.pack(fill="x", padx=10, pady=5)
            self.entry_widgets.append(entry_widget)
        
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

class MainWindow(ctk.CTk):
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
                 auth_manager: AuthenticationManager):
        """
        Initialize the main window
        
        Args:
            session_id: Valid session ID
            username: Authenticated username
            password_manager: Password management system
            auth_manager: Authentication manager
        """
        super().__init__()
        
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
        
        # Logout button
        logout_btn = create_themed_button(
            actions_frame,
            text="🚪 Logout",
            style="button_secondary",
            command=self._logout
        )
        logout_btn.pack(side="right")
    
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
        
        # Generate password button
        generate_btn = create_themed_button(
            actions_frame,
            text="🎲 Generate",
            style="button_secondary",
            command=self._show_password_generator
        )
        generate_btn.pack(side="right", padx=(spacing["padding_sm"], 0))
        
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

# Dialog classes will be implemented in separate files
class AddPasswordDialog:
    """Placeholder for add password dialog"""
    def __init__(self, parent, session_id, password_manager, on_success):
        messagebox.showinfo("Add Password", "Add password dialog would open here")
        on_success()

class EditPasswordDialog:
    """Placeholder for edit password dialog"""
    def __init__(self, parent, session_id, password_manager, entry, on_success):
        messagebox.showinfo("Edit Password", f"Edit password dialog for {entry.website} would open here")
        on_success()

class SettingsDialog:
    """Placeholder for settings dialog"""
    def __init__(self, parent, theme):
        messagebox.showinfo("Settings", "Settings dialog would open here")

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