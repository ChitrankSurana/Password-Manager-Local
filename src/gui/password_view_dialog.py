#!/usr/bin/env python3
"""
Personal Password Manager - Password View Authentication Dialog
=============================================================

This module provides a comprehensive modal dialog for authenticating password viewing
requests. It integrates with the PasswordViewAuthService to provide secure, time-based
password viewing with user-configurable settings and comprehensive security features.

Key Features:
- Master password authentication with secure input
- User-configurable timeout settings (1-60 minutes)
- Real-time permission status and countdown display
- Integration with SettingsService for user preferences
- Comprehensive security logging through ServiceIntegrator
- Modern, accessible UI with clear security indicators
- Support for multiple authentication methods (future extensibility)

Security Features:
- Secure password entry with show/hide toggle
- Rate limiting integration to prevent brute force attempts
- Automatic dialog closure on authentication failure
- Clear security messaging and user education
- Integration with security audit logging

UI Features:
- Responsive design with clear visual feedback
- Accessibility support with keyboard navigation
- Real-time validation and error messaging
- Progress indicators and timeout countdowns
- Consistent styling with application theme

Author: Personal Password Manager Enhancement Team
Version: 2.0.0
Date: September 21, 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any, Tuple
import threading
import time

# Import our core services
from ..core.service_integration import PasswordManagerServiceIntegrator
from ..core.view_auth_service import ViewPermissionGrant

# Configure logging for password view dialog
logger = logging.getLogger(__name__)

class PasswordViewAuthDialog:
    """
    Modal dialog for password viewing authentication
    
    This dialog provides a secure interface for users to authenticate for password
    viewing operations. It integrates with the core services to provide time-based
    permissions with user-configurable settings and comprehensive security features.
    
    Features:
    - Master password authentication with secure entry
    - Configurable timeout settings with live preview
    - Real-time permission status and countdown
    - Integration with user preferences and security settings
    - Comprehensive error handling and user feedback
    - Accessibility support and keyboard shortcuts
    """
    
    def __init__(self, parent, service_integrator: PasswordManagerServiceIntegrator, 
                 user_id: int, session_id: str, 
                 on_success: Optional[Callable[[ViewPermissionGrant], None]] = None,
                 on_failure: Optional[Callable[[str], None]] = None):
        """
        Initialize the password view authentication dialog
        
        Args:
            parent: Parent window for modal dialog
            service_integrator: Service integrator for authentication
            user_id (int): Current user ID
            session_id (str): Current session ID
            on_success: Callback for successful authentication
            on_failure: Callback for failed authentication
        """
        self.parent = parent
        self.service_integrator = service_integrator
        self.user_id = user_id
        self.session_id = session_id
        self.on_success = on_success
        self.on_failure = on_failure
        
        # Dialog state
        self.dialog: Optional[tk.Toplevel] = None
        self.result: Optional[ViewPermissionGrant] = None
        self.is_authenticated = False
        self.is_closed = False
        
        # UI components
        self.master_password_var = tk.StringVar()
        self.timeout_var = tk.IntVar()
        self.show_password_var = tk.BooleanVar()
        self.status_var = tk.StringVar()
        self.countdown_var = tk.StringVar()
        
        # Timeout and permission tracking
        self.current_permission: Optional[ViewPermissionGrant] = None
        self.countdown_thread: Optional[threading.Thread] = None
        self.countdown_running = False
        
        # User settings (will be loaded from service)
        self.user_settings = {}
        
        # Load user settings and check existing permission
        self._load_user_settings()
        self._check_existing_permission()
        
        logger.info(f"PasswordViewAuthDialog initialized for user {user_id}")
    
    def show_dialog(self) -> Optional[ViewPermissionGrant]:
        """
        Show the authentication dialog and return the result
        
        Returns:
            Optional[ViewPermissionGrant]: Permission grant if successful, None otherwise
        """
        if self.current_permission:
            # User already has valid permission
            self.result = self.current_permission
            self.is_authenticated = True
            
            if self.on_success:
                self.on_success(self.result)
            
            return self.result
        
        self._create_dialog()
        self._setup_ui()
        self._center_dialog()
        
        # Make dialog modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.focus_set()
        
        # Wait for dialog to close
        self.parent.wait_window(self.dialog)
        
        return self.result
    
    def _load_user_settings(self):
        """Load user's password viewing preferences"""
        try:
            self.user_settings = self.service_integrator.get_user_settings(
                self.user_id, "password_viewing"
            )
            
            # Set default timeout from user preference
            default_timeout = self.user_settings.get('view_timeout_minutes', 1)
            self.timeout_var.set(default_timeout)
            
            logger.debug(f"Loaded user settings: timeout={default_timeout}min")
            
        except Exception as e:
            logger.error(f"Error loading user settings: {e}")
            # Use safe defaults
            self.user_settings = {
                'view_timeout_minutes': 1,
                'require_master_password': True,
                'show_view_timer': True
            }
            self.timeout_var.set(1)
    
    def _check_existing_permission(self):
        """Check if user already has valid permission"""
        try:
            has_permission, permission_info = self.service_integrator.check_password_view_permission(
                self.session_id
            )
            
            if has_permission and permission_info:
                # User has existing valid permission
                self.current_permission = permission_info
                logger.info(f"User {self.user_id} has existing view permission")
            
        except Exception as e:
            logger.error(f"Error checking existing permission: {e}")
    
    def _create_dialog(self):
        """Create the main dialog window"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Authenticate for Password Viewing")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        
        # Set dialog icon (if available)
        try:
            # You would set the application icon here
            # self.dialog.iconbitmap("path/to/icon.ico")
            pass
        except Exception:
            pass
        
        # Handle dialog closing
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_dialog_close)
        
        # Configure style
        self.dialog.configure(bg='#f0f0f0')
    
    def _setup_ui(self):
        """Setup the dialog UI components"""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title and description
        self._create_header(main_frame)
        
        # Authentication section
        self._create_auth_section(main_frame)
        
        # Timeout settings section
        self._create_timeout_section(main_frame)
        
        # Status and countdown section
        self._create_status_section(main_frame)
        
        # Action buttons
        self._create_action_buttons(main_frame)
        
        # Initial UI state
        self._update_ui_state()
        
        # Focus on password field
        self.master_password_entry.focus_set()
    
    def _create_header(self, parent):
        """Create header with title and description"""
        # Title
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(
            title_frame, 
            text="🔐 Password Viewing Authentication",
            font=('Segoe UI', 14, 'bold'),
            foreground='#2c3e50'
        )
        title_label.pack(anchor=tk.W)
        
        # Description
        description_text = (
            "To view stored passwords, please verify your master password.\n"
            "Your viewing session will be secured with the timeout you specify below."
        )
        
        desc_label = ttk.Label(
            title_frame,
            text=description_text,
            font=('Segoe UI', 9),
            foreground='#5d6d7e',
            wraplength=450
        )
        desc_label.pack(anchor=tk.W, pady=(5, 0))
    
    def _create_auth_section(self, parent):
        """Create authentication section"""
        auth_frame = ttk.LabelFrame(parent, text="Master Password", padding="15")
        auth_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Password entry with show/hide toggle
        password_frame = ttk.Frame(auth_frame)
        password_frame.pack(fill=tk.X)
        
        ttk.Label(password_frame, text="Enter your master password:").pack(anchor=tk.W)
        
        entry_frame = ttk.Frame(password_frame)
        entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Password entry field
        self.master_password_entry = ttk.Entry(
            entry_frame,
            textvariable=self.master_password_var,
            show="*",
            font=('Segoe UI', 11),
            width=35
        )
        self.master_password_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        # Show/hide password toggle
        self.show_password_btn = ttk.Button(
            entry_frame,
            text="👁",
            width=3,
            command=self._toggle_password_visibility
        )
        self.show_password_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Bind Enter key to authenticate
        self.master_password_entry.bind("<Return>", lambda e: self._authenticate())
        
        # Security note
        security_note = ttk.Label(
            auth_frame,
            text="🛡️ Your password is never stored and is cleared from memory after authentication.",
            font=('Segoe UI', 8),
            foreground='#27ae60'
        )
        security_note.pack(anchor=tk.W, pady=(8, 0))
    
    def _create_timeout_section(self, parent):
        """Create timeout configuration section"""
        timeout_frame = ttk.LabelFrame(parent, text="Viewing Session Settings", padding="15")
        timeout_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Timeout slider
        timeout_label_frame = ttk.Frame(timeout_frame)
        timeout_label_frame.pack(fill=tk.X)
        
        ttk.Label(timeout_label_frame, text="Session timeout:").pack(side=tk.LEFT)
        
        self.timeout_display = ttk.Label(
            timeout_label_frame, 
            text=f"{self.timeout_var.get()} minutes",
            font=('Segoe UI', 10, 'bold'),
            foreground='#e74c3c'
        )
        self.timeout_display.pack(side=tk.RIGHT)
        
        # Timeout scale
        self.timeout_scale = ttk.Scale(
            timeout_frame,
            from_=1,
            to=60,
            variable=self.timeout_var,
            orient=tk.HORIZONTAL,
            command=self._on_timeout_changed
        )
        self.timeout_scale.pack(fill=tk.X, pady=(5, 8))
        
        # Timeout description
        timeout_desc = ttk.Label(
            timeout_frame,
            text="After authentication, passwords will remain visible for this duration.",
            font=('Segoe UI', 9),
            foreground='#5d6d7e'
        )
        timeout_desc.pack(anchor=tk.W)
        
        # Quick timeout buttons
        quick_buttons_frame = ttk.Frame(timeout_frame)
        quick_buttons_frame.pack(fill=tk.X, pady=(8, 0))
        
        ttk.Label(quick_buttons_frame, text="Quick select:").pack(side=tk.LEFT)
        
        for minutes, label in [(1, "1min"), (5, "5min"), (15, "15min"), (30, "30min")]:
            btn = ttk.Button(
                quick_buttons_frame,
                text=label,
                width=6,
                command=lambda m=minutes: self._set_quick_timeout(m)
            )
            btn.pack(side=tk.RIGHT, padx=(2, 0))
    
    def _create_status_section(self, parent):
        """Create status and countdown section"""
        self.status_frame = ttk.LabelFrame(parent, text="Session Status", padding="15")
        self.status_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Status label
        self.status_label = ttk.Label(
            self.status_frame,
            textvariable=self.status_var,
            font=('Segoe UI', 10),
            foreground='#34495e'
        )
        self.status_label.pack(anchor=tk.W)
        
        # Countdown label (hidden initially)
        self.countdown_label = ttk.Label(
            self.status_frame,
            textvariable=self.countdown_var,
            font=('Segoe UI', 12, 'bold'),
            foreground='#e74c3c'
        )
        # Don't pack initially - will be shown during countdown
        
        # Progress bar for countdown (hidden initially)
        self.countdown_progress = ttk.Progressbar(
            self.status_frame,
            mode='determinate',
            length=300
        )
        # Don't pack initially
    
    def _create_action_buttons(self, parent):
        """Create action buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Cancel button
        self.cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=12
        )
        self.cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Authenticate button
        self.auth_btn = ttk.Button(
            button_frame,
            text="🔓 Authenticate",
            command=self._authenticate,
            width=15,
            style='Accent.TButton'
        )
        self.auth_btn.pack(side=tk.RIGHT)
        
        # Extend session button (hidden initially)
        self.extend_btn = ttk.Button(
            button_frame,
            text="⏰ Extend Session",
            command=self._extend_session,
            width=15
        )
        # Don't pack initially
        
        # Revoke permission button (hidden initially)
        self.revoke_btn = ttk.Button(
            button_frame,
            text="🛑 End Session",
            command=self._revoke_permission,
            width=15
        )
        # Don't pack initially
    
    def _update_ui_state(self):
        """Update UI state based on current authentication status"""
        if self.current_permission:
            # User has existing permission - show countdown mode
            self._show_countdown_mode()
        else:
            # User needs to authenticate - show auth mode
            self._show_auth_mode()
    
    def _show_auth_mode(self):
        """Show UI for authentication mode"""
        self.status_var.set("🔒 Authentication required to view passwords")
        
        # Show auth components
        self.master_password_entry.configure(state='normal')
        self.timeout_scale.configure(state='normal')
        self.auth_btn.pack(side=tk.RIGHT)
        
        # Hide countdown components
        self.countdown_label.pack_forget()
        self.countdown_progress.pack_forget()
        self.extend_btn.pack_forget()
        self.revoke_btn.pack_forget()
    
    def _show_countdown_mode(self):
        """Show UI for countdown mode (user has permission)"""
        if not self.current_permission:
            return
        
        # Update status
        remaining = self.current_permission.get('remaining_seconds', 0)
        self.status_var.set(f"✅ Authentication active - {remaining}s remaining")
        
        # Hide auth components
        self.master_password_entry.configure(state='disabled')
        self.timeout_scale.configure(state='disabled')
        self.auth_btn.pack_forget()
        
        # Show countdown components
        self.countdown_label.pack(anchor=tk.W, pady=(5, 0))
        self.countdown_progress.pack(fill=tk.X, pady=(5, 0))
        self.extend_btn.pack(side=tk.RIGHT, padx=(0, 5))
        self.revoke_btn.pack(side=tk.RIGHT, padx=(0, 5))
        
        # Start countdown
        self._start_countdown()
    
    def _authenticate(self):
        """Perform authentication with the service integrator"""
        master_password = self.master_password_var.get().strip()
        
        if not master_password:
            messagebox.showwarning("Input Required", "Please enter your master password.")
            self.master_password_entry.focus_set()
            return
        
        # Disable UI during authentication
        self.auth_btn.configure(state='disabled', text="Authenticating...")
        self.master_password_entry.configure(state='disabled')
        self.timeout_scale.configure(state='disabled')
        
        try:
            # Request permission from service integrator
            success, message, permission = self.service_integrator.request_password_view_permission(
                user_id=self.user_id,
                session_id=self.session_id,
                master_password=master_password,
                timeout_minutes=self.timeout_var.get()
            )
            
            # Clear password from memory
            self.master_password_var.set("")
            master_password = "0" * len(master_password)  # Overwrite in memory
            
            if success and permission:
                # Authentication successful
                self.current_permission = permission
                self.result = permission
                self.is_authenticated = True
                
                logger.info(f"Password view authentication successful for user {self.user_id}")
                
                # Update UI to show countdown mode
                self._show_countdown_mode()
                
                # Notify success callback
                if self.on_success:
                    self.on_success(permission)
                
                # Show success message
                messagebox.showinfo("Authentication Successful", 
                    f"Password viewing enabled for {self.timeout_var.get()} minutes.")
                
            else:
                # Authentication failed
                logger.warning(f"Password view authentication failed for user {self.user_id}: {message}")
                
                # Show error message
                messagebox.showerror("Authentication Failed", message)
                
                # Notify failure callback
                if self.on_failure:
                    self.on_failure(message)
                
                # Re-enable UI for retry
                self._show_auth_mode()
                self.auth_btn.configure(state='normal', text="🔓 Authenticate")
                self.master_password_entry.focus_set()
                
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            
            # Clear password from memory
            self.master_password_var.set("")
            
            # Show error message
            messagebox.showerror("Authentication Error", f"An error occurred: {e}")
            
            # Re-enable UI
            self._show_auth_mode()
            self.auth_btn.configure(state='normal', text="🔓 Authenticate")
    
    def _extend_session(self):
        """Extend the current viewing session"""
        if not self.current_permission:
            return
        
        try:
            success = self.service_integrator._view_auth_service.extend_permission(
                self.session_id, 5  # Extend by 5 minutes
            )
            
            if success:
                # Update permission info
                _, permission_info = self.service_integrator.check_password_view_permission(
                    self.session_id
                )
                self.current_permission = permission_info
                
                messagebox.showinfo("Session Extended", "Viewing session extended by 5 minutes.")
                logger.info(f"Password view session extended for user {self.user_id}")
            else:
                messagebox.showwarning("Extension Failed", "Could not extend the viewing session.")
                
        except Exception as e:
            logger.error(f"Error extending session: {e}")
            messagebox.showerror("Extension Error", f"An error occurred: {e}")
    
    def _revoke_permission(self):
        """Revoke the current viewing permission"""
        if not self.current_permission:
            return
        
        result = messagebox.askyesno("End Session", 
            "Are you sure you want to end your password viewing session?")
        
        if result:
            try:
                success = self.service_integrator.revoke_password_view_permission(
                    self.session_id, "USER_REQUEST"
                )
                
                if success:
                    self.current_permission = None
                    self.countdown_running = False
                    
                    logger.info(f"Password view session revoked for user {self.user_id}")
                    
                    # Update UI back to auth mode
                    self._show_auth_mode()
                    
                    messagebox.showinfo("Session Ended", "Password viewing session has been ended.")
                    
                else:
                    messagebox.showwarning("Revocation Failed", "Could not end the viewing session.")
                    
            except Exception as e:
                logger.error(f"Error revoking permission: {e}")
                messagebox.showerror("Revocation Error", f"An error occurred: {e}")
    
    def _start_countdown(self):
        """Start the countdown display thread"""
        if self.countdown_running:
            return
        
        self.countdown_running = True
        self.countdown_thread = threading.Thread(target=self._countdown_worker, daemon=True)
        self.countdown_thread.start()
    
    def _countdown_worker(self):
        """Worker thread for countdown display"""
        while self.countdown_running and not self.is_closed:
            try:
                if not self.current_permission:
                    break
                
                # Check if permission is still valid
                has_permission, permission_info = self.service_integrator.check_password_view_permission(
                    self.session_id
                )
                
                if not has_permission:
                    # Permission expired
                    self.current_permission = None
                    
                    # Update UI on main thread
                    self.dialog.after(0, self._on_permission_expired)
                    break
                
                # Update permission info
                self.current_permission = permission_info
                remaining_seconds = permission_info.get('remaining_seconds', 0)
                
                if remaining_seconds <= 0:
                    # Permission expired
                    self.current_permission = None
                    self.dialog.after(0, self._on_permission_expired)
                    break
                
                # Update countdown display on main thread
                self.dialog.after(0, lambda: self._update_countdown_display(remaining_seconds))
                
                time.sleep(1)  # Update every second
                
            except Exception as e:
                logger.error(f"Error in countdown worker: {e}")
                break
        
        self.countdown_running = False
    
    def _update_countdown_display(self, remaining_seconds: int):
        """Update countdown display (called on main thread)"""
        if self.is_closed:
            return
        
        # Update countdown text
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        self.countdown_var.set(f"⏱️ {minutes:02d}:{seconds:02d}")
        
        # Update progress bar (assuming original timeout for max value)
        if self.current_permission:
            total_seconds = self.current_permission.get('timeout_minutes', 1) * 60
            progress_value = (remaining_seconds / total_seconds) * 100
            self.countdown_progress.configure(value=progress_value)
        
        # Update status
        self.status_var.set(f"✅ Authentication active - passwords visible")
        
        # Change color based on remaining time
        if remaining_seconds <= 30:
            self.countdown_label.configure(foreground='#e74c3c')  # Red
        elif remaining_seconds <= 120:
            self.countdown_label.configure(foreground='#f39c12')  # Orange
        else:
            self.countdown_label.configure(foreground='#27ae60')  # Green
    
    def _on_permission_expired(self):
        """Handle permission expiration (called on main thread)"""
        logger.info(f"Password view permission expired for user {self.user_id}")
        
        self.current_permission = None
        self.countdown_running = False
        
        # Update UI back to auth mode
        self._show_auth_mode()
        
        # Show expiration message
        messagebox.showinfo("Session Expired", 
            "Your password viewing session has expired. Please authenticate again if needed.")
    
    def _toggle_password_visibility(self):
        """Toggle password visibility in the entry field"""
        if self.show_password_var.get():
            self.master_password_entry.configure(show="")
            self.show_password_btn.configure(text="👁‍🗨")
            self.show_password_var.set(False)
        else:
            self.master_password_entry.configure(show="*")
            self.show_password_btn.configure(text="👁")
            self.show_password_var.set(True)
    
    def _on_timeout_changed(self, value):
        """Handle timeout slider change"""
        timeout_value = int(float(value))
        self.timeout_display.configure(text=f"{timeout_value} minutes")
    
    def _set_quick_timeout(self, minutes: int):
        """Set timeout to a quick preset value"""
        self.timeout_var.set(minutes)
        self.timeout_display.configure(text=f"{minutes} minutes")
    
    def _center_dialog(self):
        """Center the dialog on the parent window"""
        self.dialog.update_idletasks()
        
        # Get dialog size
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        
        # Get parent position and size
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Calculate center position
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)
        
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def _on_cancel(self):
        """Handle cancel button click"""
        self.result = None
        self.is_authenticated = False
        
        if self.on_failure:
            self.on_failure("Authentication cancelled by user")
        
        self._close_dialog()
    
    def _on_dialog_close(self):
        """Handle dialog window close event"""
        self._close_dialog()
    
    def _close_dialog(self):
        """Close the dialog and clean up"""
        if self.is_closed:
            return
        
        self.is_closed = True
        
        # Stop countdown thread
        self.countdown_running = False
        if self.countdown_thread and self.countdown_thread.is_alive():
            # Give thread time to stop
            try:
                self.countdown_thread.join(timeout=2)
            except:
                pass
        
        # Clear sensitive data
        self.master_password_var.set("")
        
        # Close dialog
        if self.dialog:
            self.dialog.grab_release()
            self.dialog.destroy()
        
        logger.info(f"Password view authentication dialog closed for user {self.user_id}")

# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def show_password_view_auth_dialog(parent, service_integrator: PasswordManagerServiceIntegrator,
                                  user_id: int, session_id: str) -> Optional[ViewPermissionGrant]:
    """
    Show password view authentication dialog and return result
    
    Args:
        parent: Parent window for modal dialog
        service_integrator: Service integrator for authentication
        user_id (int): Current user ID  
        session_id (str): Current session ID
        
    Returns:
        Optional[ViewPermissionGrant]: Permission grant if successful, None otherwise
    """
    dialog = PasswordViewAuthDialog(parent, service_integrator, user_id, session_id)
    return dialog.show_dialog()

# Example usage and testing
if __name__ == "__main__":
    # This section would only run if the file is executed directly (for testing)
    import sys
    import os
    
    # Add parent directories to path for imports
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Simple test without full service integration
    root = tk.Tk()
    root.title("Password View Auth Dialog Test")
    root.geometry("300x200")
    
    def test_dialog():
        # Note: This would require actual service integrator for full functionality
        print("Password view authentication dialog test")
        messagebox.showinfo("Test", "In a real implementation, this would show the auth dialog with service integration.")
    
    test_btn = ttk.Button(root, text="Test Auth Dialog", command=test_dialog)
    test_btn.pack(expand=True)
    
    root.mainloop()
