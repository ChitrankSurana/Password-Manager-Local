#!/usr/bin/env python3
"""
Personal Password Manager - Login Window
========================================

This module provides the login interface for the password manager, featuring
a modern design with user authentication, account creation, and secure session
management. It serves as the entry point to the application.

Key Features:
- Modern Windows 11-style login interface
- User account selection and creation
- Secure password entry with show/hide toggle
- Account lockout indication and handling
- Responsive design with error handling
- Integration with authentication system
- Remember last user functionality
- Accessibility considerations

Security Features:
- No password storage or caching
- Account lockout status display
- Failed attempt indication
- Secure session initiation
- Input validation and sanitization

Author: Personal Password Manager
Version: 1.0.0
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import logging
from typing import Optional, Callable, Dict, Any
from pathlib import Path
import json
from datetime import datetime

# Import our modules
from .themes import get_theme, apply_window_theme, create_themed_button, create_themed_entry, create_themed_label
from ..core.auth import AuthenticationManager, AuthenticationError, AccountLockedError, UserAlreadyExistsError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ToolTip:
    """Create a tooltip for a given widget"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

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

class LoginWindow(ctk.CTkToplevel):
    """
    Modern login window with authentication features
    
    This class provides a secure and user-friendly login interface with support
    for user account management, authentication, and session initiation. It features
    a modern design with proper error handling and accessibility.
    
    Features:
    - User account selection from existing accounts
    - Secure password entry with visibility toggle
    - Account creation workflow
    - Account lockout status display
    - Remember last user functionality
    - Loading states and progress indication
    - Comprehensive error handling and user feedback
    """
    
    def __init__(self, auth_manager: AuthenticationManager, 
                 on_login_success: Callable[[str, str], None],
                 parent=None):
        """
        Initialize the login window
        
        Args:
            auth_manager (AuthenticationManager): Authentication system
            on_login_success (Callable): Callback for successful login
            parent: Parent window (optional)
        """
        super().__init__(parent)
        
        self.auth_manager = auth_manager
        self.on_login_success = on_login_success
        self.theme = get_theme()
        
        # Window state
        self.current_username = ""
        self.is_loading = False
        self.remember_user = True
        
        # UI components
        self.username_var = ctk.StringVar()
        self.password_var = ctk.StringVar()
        self.show_password_var = ctk.BooleanVar()
        self.remember_user_var = ctk.BooleanVar(value=True)
        
        # Load user preferences
        self.user_prefs = self._load_user_preferences()
        
        # Setup window
        self._setup_window()
        self._create_ui()
        self._load_last_user()
        
        # Focus on appropriate field
        self._set_initial_focus()
        
        logger.info("Login window initialized")
    
    def _setup_window(self):
        """Configure window properties and theming"""
        # Window properties
        self.title("Personal Password Manager - Login")
        self.geometry("400x550")
        self.resizable(False, False)
        
        # Center window on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # Apply theme
        apply_window_theme(self)
        
        # Window behavior
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)
        self.grab_set()  # Make window modal
        self.focus_force()
        
        # Bind keyboard events
        self.bind("<Return>", lambda e: self._handle_login())
        self.bind("<Escape>", lambda e: self._on_window_close())
    
    def _create_ui(self):
        """Create the user interface"""
        colors = self.theme.get_colors()
        fonts = self.theme.get_fonts()
        spacing = self.theme.get_spacing()
        
        # Main container
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=spacing["padding_xl"], pady=spacing["padding_xl"])
        
        # Header section
        self._create_header()
        
        # Login form
        self._create_login_form()
        
        # Action buttons
        self._create_action_buttons()
        
        # Footer
        self._create_footer()
        
        # Status area
        self._create_status_area()
    
    def _create_header(self):
        """Create the header section with logo and title"""
        colors = self.theme.get_colors()
        fonts = self.theme.get_fonts()
        spacing = self.theme.get_spacing()
        
        # Header frame
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, spacing["section_gap"]))
        
        # Logo/Icon placeholder (you could add an actual icon here)
        logo_frame = ctk.CTkFrame(
            header_frame,
            width=60,
            height=60,
            fg_color=colors["primary"],
            corner_radius=spacing["radius_xl"]
        )
        logo_frame.pack(anchor="center", pady=(0, spacing["padding_md"]))
        
        # Logo text
        logo_label = ctk.CTkLabel(
            logo_frame,
            text="🔐",
            font=("Segoe UI", 24),
            text_color="white"
        )
        logo_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Title
        title_label = create_themed_label(
            header_frame,
            text="Personal Password Manager",
            style="label"
        )
        title_label.configure(font=fonts["heading_medium"])
        title_label.pack(anchor="center")
        
        # Subtitle
        subtitle_label = create_themed_label(
            header_frame,
            text="Secure • Local • Private",
            style="label_secondary"
        )
        subtitle_label.pack(anchor="center", pady=(spacing["padding_xs"], 0))
    
    def _create_login_form(self):
        """Create the login form with username and password fields"""
        spacing = self.theme.get_spacing()
        
        # Form frame
        self.form_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.form_frame.pack(fill="x", pady=spacing["section_gap"])
        
        # Username section
        username_label = create_themed_label(
            self.form_frame,
            text="Username",
            style="label"
        )
        username_label.pack(anchor="w", pady=(0, spacing["padding_xs"]))
        
        self.username_entry = create_themed_entry(
            self.form_frame,
            placeholder_text="Enter your username",
            textvariable=self.username_var
        )
        self.username_entry.pack(fill="x", pady=(0, spacing["padding_md"]))
        
        # Password section
        password_label = create_themed_label(
            self.form_frame,
            text="Master Password",
            style="label"
        )
        password_label.pack(anchor="w", pady=(0, spacing["padding_xs"]))
        
        # Password frame (for entry + toggle)
        password_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        password_frame.pack(fill="x", pady=(0, spacing["padding_md"]))
        
        self.password_entry = create_themed_entry(
            password_frame,
            placeholder_text="Enter your master password",
            textvariable=self.password_var,
            style="entry_password",
            show="*"
        )
        self.password_entry.pack(side="left", fill="both", expand=True)
        
        # Show/hide password toggle
        self.toggle_password_btn = create_themed_button(
            password_frame,
            text="👁",
            style="button_secondary",
            width=40,
            command=self._toggle_password_visibility
        )
        self.toggle_password_btn.pack(side="right", padx=(spacing["padding_xs"], 0))
        ToolTip(self.toggle_password_btn, "Show or hide password")
        
        # Remember user checkbox
        self.remember_checkbox = ctk.CTkCheckBox(
            self.form_frame,
            text="Remember username",
            variable=self.remember_user_var,
            font=self.theme.get_fonts()["body_small"]
        )
        self.theme.apply_component_style(self.remember_checkbox, "checkbox")
        self.remember_checkbox.pack(anchor="w", pady=(0, spacing["padding_md"]))
        
        # Account status area
        self.status_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.status_frame.pack(fill="x")
        
        self.status_label = create_themed_label(
            self.status_frame,
            text="",
            style="label_secondary"
        )
        self.status_label.pack(anchor="w")
    
    def _create_action_buttons(self):
        """Create login and account creation buttons"""
        spacing = self.theme.get_spacing()
        
        # Button frame
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=spacing["section_gap"])
        
        # Login button
        self.login_btn = create_themed_button(
            button_frame,
            text="Sign In",
            style="button_primary",
            command=self._handle_login
        )
        self.login_btn.pack(fill="x", pady=(0, spacing["padding_sm"]))
        ToolTip(self.login_btn, "Sign in with your username and master password")

        # Create account button
        self.create_account_btn = create_themed_button(
            button_frame,
            text="Create New Account",
            style="button_secondary",
            command=self._show_create_account_dialog
        )
        self.create_account_btn.pack(fill="x")
        ToolTip(self.create_account_btn, "Create a new user account")
    
    def _create_footer(self):
        """Create footer with additional options"""
        spacing = self.theme.get_spacing()
        colors = self.theme.get_colors()
        
        # Separator
        separator = ctk.CTkFrame(
            self.main_frame,
            height=1,
            fg_color=colors["border"]
        )
        separator.pack(fill="x", pady=spacing["section_gap"])
        
        # Footer frame
        footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        footer_frame.pack(fill="x")
        
        # Help text
        help_label = create_themed_label(
            footer_frame,
            text="First time? Create an account to get started.",
            style="label_secondary"
        )
        help_label.pack(anchor="center")
    
    def _create_status_area(self):
        """Create status area for loading and messages"""
        spacing = self.theme.get_spacing()
        
        self.status_area = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.status_area.pack(fill="x", pady=(spacing["padding_md"], 0))
        
        # Progress bar (hidden by default)
        self.progress_bar = ctk.CTkProgressBar(self.status_area)
        self.theme.apply_component_style(self.progress_bar, "progressbar")
        # Don't pack by default - will be shown during loading
        
        # Status message
        self.message_label = create_themed_label(
            self.status_area,
            text="",
            style="label_secondary"
        )
        # Don't pack by default - will be shown when needed
    
    def _toggle_password_visibility(self):
        """Toggle password field visibility"""
        if self.password_entry.cget("show") == "*":
            self.password_entry.configure(show="")
            self.toggle_password_btn.configure(text="🙈")
        else:
            self.password_entry.configure(show="*")
            self.toggle_password_btn.configure(text="👁")
    
    def _handle_login(self):
        """Handle login button click"""
        if self.is_loading:
            return
        
        username = self.username_var.get().strip()
        password = self.password_var.get()
        
        # Validate input
        if not username:
            self._show_error("Please enter your username")
            self.username_entry.focus()
            return
        
        if not password:
            self._show_error("Please enter your master password")
            self.password_entry.focus()
            return
        
        # Start login process
        self._start_loading("Authenticating...")
        
        # Run authentication in background thread
        threading.Thread(
            target=self._authenticate_user,
            args=(username, password),
            daemon=True
        ).start()
    
    def _authenticate_user(self, username: str, password: str):
        """
        Authenticate user in background thread
        
        Args:
            username (str): Username to authenticate
            password (str): Master password
        """
        try:
            # Attempt authentication
            session_id = self.auth_manager.authenticate_user(
                username, password,
                login_ip="127.0.0.1",
                user_agent="Desktop Application"
            )
            
            # Authentication successful - pass password to cache it
            self.after(0, self._on_authentication_success, session_id, username, password)
            
        except AccountLockedError as e:
            self.after(0, self._on_authentication_error, f"Account locked: {str(e)}")
        except AuthenticationError as e:
            self.after(0, self._on_authentication_error, str(e))
        except Exception as e:
            logger.error(f"Login error: {e}")
            self.after(0, self._on_authentication_error, "An unexpected error occurred")
    
    def _on_authentication_success(self, session_id: str, username: str, password: str):
        """
        Handle successful authentication
        
        Args:
            session_id (str): Session ID from authentication
            username (str): Authenticated username
            password (str): Master password for caching
        """
        self._stop_loading()
        
        # Save user preferences
        if self.remember_user_var.get():
            self.user_prefs["last_username"] = username
            self._save_user_preferences()
        
        # Clear password field for security
        self.password_var.set("")
        
        # Call success callback with master password for caching
        try:
            self.on_login_success(session_id, username, password)
            self.destroy()
        except Exception as e:
            logger.error(f"Login success callback error: {e}")
            self._show_error("Failed to complete login process")
    
    def _on_authentication_error(self, error_message: str):
        """
        Handle authentication error
        
        Args:
            error_message (str): Error message to display
        """
        self._stop_loading()
        self._show_error(error_message)
        
        # Clear password field
        self.password_var.set("")
        self.password_entry.focus()
    
    def _show_create_account_dialog(self):
        """Show create account dialog"""
        CreateAccountDialog(self, self.auth_manager, self._on_account_created)
    
    def _on_account_created(self, username: str):
        """
        Handle successful account creation
        
        Args:
            username (str): Created username
        """
        self.username_var.set(username)
        self.password_entry.focus()
        self._show_success(f"Account '{username}' created successfully! Please sign in.")
    
    def _start_loading(self, message: str = "Loading..."):
        """
        Start loading state
        
        Args:
            message (str): Loading message
        """
        self.is_loading = True
        
        # Disable inputs
        self.username_entry.configure(state="disabled")
        self.password_entry.configure(state="disabled")
        self.login_btn.configure(state="disabled", text="Signing In...")
        self.create_account_btn.configure(state="disabled")
        
        # Show progress bar
        self.progress_bar.pack(fill="x", pady=(0, self.theme.get_spacing()["padding_sm"]))
        self.progress_bar.set(0)
        self.progress_bar.start()
        
        # Show message
        self.message_label.configure(text=message)
        self.message_label.pack(anchor="center")
    
    def _stop_loading(self):
        """Stop loading state"""
        self.is_loading = False
        
        # Re-enable inputs
        self.username_entry.configure(state="normal")
        self.password_entry.configure(state="normal")
        self.login_btn.configure(state="normal", text="Sign In")
        self.create_account_btn.configure(state="normal")
        
        # Hide progress bar
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        
        # Hide message
        self.message_label.pack_forget()
    
    def _show_error(self, message: str):
        """
        Show error message
        
        Args:
            message (str): Error message
        """
        colors = self.theme.get_colors()
        self.status_label.configure(text=message, text_color=colors["error"])
    
    def _show_success(self, message: str):
        """
        Show success message
        
        Args:
            message (str): Success message
        """
        colors = self.theme.get_colors()
        self.status_label.configure(text=message, text_color=colors["success"])
    
    def _clear_status(self):
        """Clear status message"""
        self.status_label.configure(text="")
    
    def _load_last_user(self):
        """Load last used username if remember is enabled and user exists in database"""
        if self.user_prefs.get("remember_user", True):
            last_username = self.user_prefs.get("last_username", "")
            if last_username:
                # Validate that this user actually exists in the current database
                # This prevents showing usernames from other databases or fresh installs
                if self.auth_manager.db_manager.user_exists(last_username):
                    self.username_var.set(last_username)
                else:
                    # Clear the invalid preference
                    logger.info(f"Last user '{last_username}' not found in database, clearing preference")
                    self.user_prefs["last_username"] = ""
                    self._save_user_preferences()
    
    def _set_initial_focus(self):
        """Set initial focus to appropriate field"""
        if self.username_var.get():
            self.password_entry.focus()
        else:
            self.username_entry.focus()
    
    def _load_user_preferences(self) -> Dict[str, Any]:
        """Load user preferences from file"""
        prefs_path = Path("data/login_preferences.json")
        
        default_prefs = {
            "remember_user": True,
            "last_username": "",
            "window_position": None
        }
        
        if prefs_path.exists():
            try:
                with open(prefs_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load login preferences: {e}")
        
        return default_prefs
    
    def _save_user_preferences(self):
        """Save user preferences to file"""
        try:
            prefs_path = Path("data/login_preferences.json")
            prefs_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.user_prefs.update({
                "remember_user": self.remember_user_var.get(),
                "last_username": self.username_var.get() if self.remember_user_var.get() else "",
                "saved_at": datetime.now().isoformat()
            })
            
            with open(prefs_path, 'w', encoding='utf-8') as f:
                json.dump(self.user_prefs, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save login preferences: {e}")
    
    def _on_window_close(self):
        """Handle window close event"""
        if not self.is_loading:
            self.destroy()

class CreateAccountDialog(ctk.CTkToplevel):
    """
    Dialog for creating new user accounts
    
    This dialog provides a secure interface for creating new user accounts
    with password validation and confirmation.
    """
    
    def __init__(self, parent, auth_manager: AuthenticationManager, 
                 on_success: Callable[[str], None]):
        """
        Initialize create account dialog
        
        Args:
            parent: Parent window
            auth_manager: Authentication manager
            on_success: Success callback
        """
        super().__init__(parent)
        
        self.auth_manager = auth_manager
        self.on_success = on_success
        self.theme = get_theme()
        
        # Variables
        self.username_var = ctk.StringVar()
        self.password_var = ctk.StringVar()
        self.confirm_password_var = ctk.StringVar()
        
        # Setup dialog
        self._setup_dialog()
        self._create_dialog_ui()
        
        # Focus on username field
        self.username_entry.focus()
    
    def _setup_dialog(self):
        """Setup dialog properties"""
        self.title("Create New Account")
        self.geometry("350x400")
        self.resizable(False, False)
        
        # Center on parent
        if self.master:
            x = self.master.winfo_x() + (self.master.winfo_width() // 2) - 175
            y = self.master.winfo_y() + (self.master.winfo_height() // 2) - 200
            self.geometry(f"350x400+{x}+{y}")
        
        # Apply theme
        apply_window_theme(self)
        
        # Make modal
        self.transient(self.master)
        self.grab_set()
        
        # Bind events
        self.bind("<Return>", lambda e: self._create_account())
        self.bind("<Escape>", lambda e: self.destroy())
    
    def _create_dialog_ui(self):
        """Create dialog user interface"""
        spacing = self.theme.get_spacing()
        
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=spacing["padding_xl"], pady=spacing["padding_xl"])
        
        # Title
        title_label = create_themed_label(
            main_frame,
            text="Create New Account",
            style="label"
        )
        title_label.configure(font=self.theme.get_fonts()["heading_small"])
        title_label.pack(anchor="center", pady=(0, spacing["section_gap"]))
        
        # Username field
        username_label = create_themed_label(main_frame, text="Username", style="label")
        username_label.pack(anchor="w", pady=(0, spacing["padding_xs"]))
        
        self.username_entry = create_themed_entry(
            main_frame,
            placeholder_text="Enter username",
            textvariable=self.username_var
        )
        self.username_entry.pack(fill="x", pady=(0, spacing["padding_md"]))
        
        # Password field
        password_label = create_themed_label(main_frame, text="Master Password", style="label")
        password_label.pack(anchor="w", pady=(0, spacing["padding_xs"]))
        
        self.password_entry = create_themed_entry(
            main_frame,
            placeholder_text="Enter master password",
            textvariable=self.password_var,
            style="entry_password",
            show="*"
        )
        self.password_entry.pack(fill="x", pady=(0, spacing["padding_md"]))
        
        # Confirm password field
        confirm_label = create_themed_label(main_frame, text="Confirm Password", style="label")
        confirm_label.pack(anchor="w", pady=(0, spacing["padding_xs"]))
        
        self.confirm_password_entry = create_themed_entry(
            main_frame,
            placeholder_text="Confirm master password",
            textvariable=self.confirm_password_var,
            style="entry_password",
            show="*"
        )
        self.confirm_password_entry.pack(fill="x", pady=(0, spacing["padding_md"]))
        
        # Status area
        self.status_label = create_themed_label(main_frame, text="", style="label_secondary")
        self.status_label.pack(anchor="w", pady=(0, spacing["padding_md"]))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=spacing["padding_md"])
        
        self.create_btn = create_themed_button(
            button_frame,
            text="Create Account",
            style="button_primary",
            command=self._create_account
        )
        self.create_btn.pack(side="right", padx=(spacing["padding_xs"], 0))
        ToolTip(self.create_btn, "Create new account with entered credentials")

        cancel_btn = create_themed_button(
            button_frame,
            text="Cancel",
            style="button_secondary",
            command=self.destroy
        )
        cancel_btn.pack(side="right")
        ToolTip(cancel_btn, "Cancel account creation and return to login")
    
    def _create_account(self):
        """Handle account creation"""
        username = self.username_var.get().strip()
        password = self.password_var.get()
        confirm_password = self.confirm_password_var.get()
        
        # Validate input
        if not username:
            self._show_error("Please enter a username")
            self.username_entry.focus()
            return
        
        if len(username) < 3:
            self._show_error("Username must be at least 3 characters")
            self.username_entry.focus()
            return
        
        if not password:
            self._show_error("Please enter a master password")
            self.password_entry.focus()
            return
        
        if len(password) < 8:
            self._show_error("Master password must be at least 8 characters")
            self.password_entry.focus()
            return
        
        if password != confirm_password:
            self._show_error("Passwords do not match")
            self.confirm_password_entry.focus()
            return
        
        # Attempt to create account
        try:
            self.create_btn.configure(state="disabled", text="Creating...")
            
            user_id = self.auth_manager.create_user_account(username, password)
            
            # Success
            self.on_success(username)
            self.destroy()
            
        except UserAlreadyExistsError:
            self._show_error("Username already exists")
            self.username_entry.focus()
        except Exception as e:
            logger.error(f"Account creation error: {e}")
            self._show_error("Failed to create account")
        finally:
            self.create_btn.configure(state="normal", text="Create Account")
    
    def _show_error(self, message: str):
        """Show error message"""
        colors = self.theme.get_colors()
        self.status_label.configure(text=message, text_color=colors["error"])

if __name__ == "__main__":
    # Test the login window
    print("Testing Personal Password Manager Login Window...")
    
    try:
        from ..core.auth import create_auth_manager
        
        # Initialize theme
        from .themes import setup_theme
        setup_theme()
        
        # Create test app
        app = ctk.CTk()
        app.withdraw()  # Hide main window
        
        # Create auth manager
        auth_manager = create_auth_manager("test_login.db")
        
        def on_login_success(session_id: str, username: str):
            print(f"✓ Login successful: {username} (Session: {session_id[:8]}...)")
            app.quit()
        
        # Create login window
        login_window = LoginWindow(auth_manager, on_login_success, app)
        
        # Run app
        app.mainloop()
        
        print("✓ Login window test completed!")
        
    except Exception as e:
        print(f"❌ Login window test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test database
        import os
        if os.path.exists("test_login.db"):
            os.remove("test_login.db")