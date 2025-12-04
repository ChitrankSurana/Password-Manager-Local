#!/usr/bin/env python3
"""
Personal Password Manager - Enhanced Password List Component
==========================================================

This module provides an enhanced password list component with integrated password
viewing and deletion features. It extends the existing password list functionality
with secure authentication, time-based viewing permissions, and comprehensive
deletion confirmation workflows.

Key Features:
- Secure password viewing with authentication dialog integration
- Configurable deletion confirmation with multiple security levels
- Real-time password visibility timeout with countdown display
- Integration with PasswordViewAuthService and ServiceIntegrator
- Enhanced UI with contextual action buttons and security indicators
- Comprehensive audit logging of all password operations

Security Features:
- Time-based password viewing with automatic expiration
- Master password authentication for sensitive operations
- Configurable confirmation levels for password deletion
- Secure clipboard operations with automatic clearing
- Comprehensive security event logging and monitoring

UI Enhancements:
- Modern card-based design with contextual action buttons
- Real-time viewing status indicators with countdown timers
- Progressive disclosure of password information
- Accessibility support with keyboard navigation
- Responsive design with consistent theming

Author: Personal Password Manager Enhancement Team
Version: 2.2.0
Date: September 21, 2025
"""

import logging
import threading
import time
from datetime import datetime
from tkinter import messagebox
from typing import Any, Dict, List, Optional

import customtkinter as ctk
import pyperclip

from ..core.password_manager import PasswordEntry
from ..core.security_audit_logger import SecurityEventType

# Import our core services
from ..core.service_integration import PasswordManagerServiceIntegrator

# Import existing components
from .main_window import PasswordEntryWidget, PasswordListFrame, ToolTip
from .password_view_dialog import PasswordViewAuthDialog
from .themes import create_themed_button, create_themed_label

# Configure logging
logger = logging.getLogger(__name__)


class EnhancedPasswordEntryWidget(PasswordEntryWidget):
    """
    Enhanced password entry widget with integrated view/delete functionality

    This widget extends the basic password entry display with secure password
    viewing capabilities, enhanced deletion confirmation, and comprehensive
    security integration through the ServiceIntegrator.

    Features:
    - Secure password viewing with time-based authentication
    - Enhanced deletion with configurable confirmation levels
    - Real-time viewing status with countdown display
    - Integration with user preferences and security settings
    - Comprehensive audit logging of all operations
    """

    def __init__(self, parent, entry: PasswordEntry, main_window,
                 service_integrator: PasswordManagerServiceIntegrator,
                 user_id: int, session_id: str):
        """
        Initialize enhanced password entry widget

        Args:
            parent: Parent widget
            entry: Password entry data
            main_window: Reference to main window
            service_integrator: Service integrator for authentication and logging
            user_id: Current user ID
            session_id: Current session ID
        """
        # Initialize service integration
        self.service_integrator = service_integrator
        self.user_id = user_id
        self.session_id = session_id

        # View state tracking
        self.is_password_visible = False
        self.view_permission_active = False
        self.countdown_thread: Optional[threading.Thread] = None
        self.countdown_running = False

        # UI components for enhanced features
        self.password_display_label: Optional[ctk.CTkLabel] = None
        self.view_button: Optional[ctk.CTkButton] = None
        self.delete_button: Optional[ctk.CTkButton] = None
        self.view_status_label: Optional[ctk.CTkLabel] = None
        self.countdown_label: Optional[ctk.CTkLabel] = None

        # Initialize base class
        super().__init__(parent, entry, main_window)

        # Check if user already has view permission
        self._check_existing_view_permission()

        logger.debug(f"Enhanced password entry widget created for entry {entry.id}")

    def _create_entry_ui(self):
        """Override to create enhanced UI with view/delete functionality"""
        spacing = self.theme.get_spacing()
        self.theme.get_colors()
        fonts = self.theme.get_fonts()

        # Main content frame
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(
            fill="both",
            expand=True,
            padx=spacing["padding_md"],
            pady=spacing["padding_md"])

        # Header frame (always visible)
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(fill="x")

        # Left side - Entry information
        info_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        # Website/service name with security indicator
        website_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        website_frame.pack(anchor="w", fill="x")

        website_label = create_themed_label(
            website_frame,
            text=self.entry.website,
            style="label"
        )
        website_label.configure(font=fonts["body_large"])
        website_label.pack(side="left", anchor="w")

        # Security indicators
        security_indicators = self._get_security_indicators()
        for indicator in security_indicators:
            indicator_label = create_themed_label(
                website_frame,
                text=indicator["icon"],
                style="label"
            )
            indicator_label.pack(side="left", padx=(spacing["padding_xs"], 0))
            ToolTip(indicator_label, indicator["tooltip"])

        # Username display
        username_label = create_themed_label(
            info_frame,
            text=f"👤 {self.entry.username}",
            style="label_secondary"
        )
        username_label.pack(anchor="w")

        # Password display area (shows based on view permission)
        self._create_password_display(info_frame)

        # Right side - Action buttons
        actions_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_frame.pack(side="right")

        self._create_action_buttons(actions_frame)

        # Status and countdown area (shown when password is visible)
        self._create_status_area(content_frame)

        # Details frame (expandable)
        self._create_details_section(content_frame)

    def _create_password_display(self, parent):
        """Create password display area with dynamic visibility"""
        spacing = self.theme.get_spacing()

        # Password display frame
        password_frame = ctk.CTkFrame(parent, fg_color="transparent")
        password_frame.pack(anchor="w", fill="x", pady=(spacing["padding_xs"], 0))

        # Password label and display
        password_info_frame = ctk.CTkFrame(password_frame, fg_color="transparent")
        password_info_frame.pack(side="left", fill="x", expand=True)

        password_label = create_themed_label(
            password_info_frame,
            text="🔐 Password:",
            style="label_secondary"
        )
        password_label.pack(side="left")

        # Password display (will be updated based on view state)
        self.password_display_label = create_themed_label(
            password_info_frame,
            text="••••••••••••",
            style="label"
        )
        self.password_display_label.pack(side="left", padx=(spacing["padding_sm"], 0))

        # Copy password button (only shown when password is visible)
        self.copy_password_btn = create_themed_button(
            password_info_frame,
            text="📋",
            style="button_secondary",
            width=30,
            command=self._copy_password_secure
        )
        # Don't pack initially - will be shown when password is visible

    def _create_action_buttons(self, parent):
        """Create enhanced action buttons"""
        spacing = self.theme.get_spacing()

        # View password button
        self.view_button = create_themed_button(
            parent,
            text="👁 View",
            style="button_primary",
            width=80,
            command=self._toggle_password_view
        )
        self.view_button.pack(side="right", padx=(spacing["padding_xs"], 0))
        ToolTip(self.view_button, "View password with authentication")

        # Delete button
        self.delete_button = create_themed_button(
            parent,
            text="🗑 Delete",
            style="button_danger",
            width=80,
            command=self._delete_password_with_confirmation
        )
        self.delete_button.pack(side="right", padx=(spacing["padding_xs"], 0))
        ToolTip(self.delete_button, "Delete this password entry")

        # Edit button
        edit_btn = create_themed_button(
            parent,
            text="✏ Edit",
            style="button_secondary",
            width=80,
            command=self._edit_password
        )
        edit_btn.pack(side="right", padx=(spacing["padding_xs"], 0))
        ToolTip(edit_btn, "Edit password entry details")

        # Favorite toggle button
        favorite_text = "⭐" if self.entry.is_favorite else "☆"
        favorite_btn = create_themed_button(
            parent,
            text=favorite_text,
            style="button_secondary",
            width=30,
            command=self._toggle_favorite
        )
        favorite_btn.pack(side="right", padx=(spacing["padding_xs"], 0))
        ToolTip(favorite_btn, "Toggle favorite status")

    def _create_status_area(self, parent):
        """Create status area for view permission countdown"""
        self.theme.get_spacing()

        # Status frame (hidden initially)
        self.status_frame = ctk.CTkFrame(parent, fg_color="transparent")
        # Don't pack initially - will be shown when password is visible

        # View status label
        self.view_status_label = create_themed_label(
            self.status_frame,
            text="✅ Password visible",
            style="label_secondary"
        )
        self.view_status_label.pack(side="left")

        # Countdown label
        self.countdown_label = create_themed_label(
            self.status_frame,
            text="⏱ 0:00",
            style="label_secondary"
        )
        self.countdown_label.pack(side="right")

    def _create_details_section(self, parent):
        """Create expandable details section"""
        spacing = self.theme.get_spacing()

        # Details frame (expandable)
        details_frame = ctk.CTkFrame(parent, fg_color="transparent")
        details_frame.pack(fill="x", pady=(spacing["padding_sm"], 0))

        # Expand/collapse button
        self.expand_btn = create_themed_button(
            details_frame,
            text="▼ Details",
            style="button_text",
            command=self._toggle_details
        )
        self.expand_btn.pack(anchor="w")

        # Details content (hidden initially)
        self.details_content = ctk.CTkFrame(details_frame, fg_color="transparent")
        # Don't pack initially - will be shown when expanded

        # Add details content
        if self.entry.remarks:
            remarks_label = create_themed_label(
                self.details_content,
                text=f"📝 Remarks: {self.entry.remarks}",
                style="label_secondary"
            )
            remarks_label.pack(anchor="w", pady=(spacing["padding_xs"], 0))

        # Timestamps
        created_label = create_themed_label(
            self.details_content,
            text=f"📅 Created: {self.entry.created_at.strftime('%Y-%m-%d %H:%M')}",
            style="label_secondary"
        )
        created_label.pack(anchor="w")

        if self.entry.modified_at and self.entry.modified_at != self.entry.created_at:
            modified_label = create_themed_label(
                self.details_content,
                text=f"🔄 Modified: {self.entry.modified_at.strftime('%Y-%m-%d %H:%M')}",
                style="label_secondary"
            )
            modified_label.pack(anchor="w")

    def _get_security_indicators(self) -> List[Dict[str, str]]:
        """Get security indicator icons and tooltips"""
        indicators = []

        # Favorite indicator
        if self.entry.is_favorite:
            indicators.append({
                "icon": "⭐",
                "tooltip": "Favorite password entry"
            })

        # Age indicator (if entry is old)
        if self.entry.created_at:
            age_days = (datetime.now() - self.entry.created_at).days
            if age_days > 365:
                indicators.append({
                    "icon": "⚠️",
                    "tooltip": f"Old password ({age_days} days) - consider updating"
                })

        # Breach indicator (placeholder - would integrate with breach detection)
        # This would be populated based on breach detection results

        return indicators

    def _check_existing_view_permission(self):
        """Check if user already has valid view permission"""
        try:
            has_permission, permission_info = self.service_integrator.check_password_view_permission(
                self.session_id)

            if has_permission:
                self.view_permission_active = True
                self._update_view_state(True)
                self._start_countdown_display(permission_info)
                logger.debug(f"Existing view permission found for entry {self.entry.id}")

        except Exception as e:
            logger.error(f"Error checking existing view permission: {e}")

    def _toggle_password_view(self):
        """Toggle password visibility with authentication"""
        if self.is_password_visible:
            # Hide password
            self._hide_password()
        else:
            # Show authentication dialog
            self._show_view_authentication()

    def _show_view_authentication(self):
        """Show password view authentication dialog"""
        try:
            def on_auth_success(permission):
                """Handle successful authentication"""
                self.view_permission_active = True
                self._update_view_state(True)
                self._start_countdown_display(
                    permission.to_dict() if hasattr(
                        permission, 'to_dict') else permission)

                # Record password view in service integrator
                self.service_integrator.record_password_view(
                    self.session_id, self.user_id, self.entry.id, self.entry.website
                )

                logger.info(f"Password view authenticated for entry {self.entry.id}")

            def on_auth_failure(reason):
                """Handle authentication failure"""
                logger.warning(
                    f"Password view authentication failed for entry {
                        self.entry.id}: {reason}")
                messagebox.showwarning("Authentication Failed", f"Could not authenticate: {reason}")

            # Show authentication dialog
            dialog = PasswordViewAuthDialog(
                parent=self.main_window,
                service_integrator=self.service_integrator,
                user_id=self.user_id,
                session_id=self.session_id,
                on_success=on_auth_success,
                on_failure=on_auth_failure
            )

            dialog.show_dialog()

        except Exception as e:
            logger.error(f"Error showing view authentication dialog: {e}")
            messagebox.showerror("Authentication Error", f"An error occurred: {e}")

    def _update_view_state(self, show_password: bool):
        """Update UI based on view state"""
        self.is_password_visible = show_password

        if show_password:
            # Show password
            self.password_display_label.configure(text=self.entry.password or "No password")
            self.copy_password_btn.pack(side="left", padx=(10, 0))
            self.view_button.configure(text="🙈 Hide")

            # Show status area
            self.status_frame.pack(fill="x", pady=(5, 0))

        else:
            # Hide password
            self.password_display_label.configure(text="••••••••••••")
            self.copy_password_btn.pack_forget()
            self.view_button.configure(text="👁 View")

            # Hide status area
            self.status_frame.pack_forget()

    def _start_countdown_display(self, permission_info: Dict[str, Any]):
        """Start countdown display for view permission"""
        if self.countdown_running:
            return

        self.countdown_running = True
        self.countdown_thread = threading.Thread(
            target=self._countdown_worker,
            args=(permission_info,),
            daemon=True
        )
        self.countdown_thread.start()

    def _countdown_worker(self, permission_info: Dict[str, Any]):
        """Worker thread for countdown display"""
        while self.countdown_running and self.view_permission_active:
            try:
                # Check current permission status
                has_permission, current_info = self.service_integrator.check_password_view_permission(
                    self.session_id)

                if not has_permission:
                    # Permission expired
                    self.after(0, self._on_view_permission_expired)
                    break

                remaining_seconds = current_info.get('remaining_seconds', 0)

                if remaining_seconds <= 0:
                    # Permission expired
                    self.after(0, self._on_view_permission_expired)
                    break

                # Update countdown display on main thread
                self.after(0, lambda r=remaining_seconds: self._update_countdown_display(r))

                time.sleep(1)  # Update every second

            except Exception as e:
                logger.error(f"Error in countdown worker: {e}")
                break

        self.countdown_running = False

    def _update_countdown_display(self, remaining_seconds: int):
        """Update countdown display (called on main thread)"""
        if not self.view_permission_active:
            return

        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60

        self.countdown_label.configure(text=f"⏱ {minutes:02d}:{seconds:02d}")

        # Change color based on remaining time
        if remaining_seconds <= 30:
            self.countdown_label.configure(text_color="#e74c3c")  # Red
        elif remaining_seconds <= 120:
            self.countdown_label.configure(text_color="#f39c12")  # Orange
        else:
            self.countdown_label.configure(text_color="#27ae60")  # Green

    def _on_view_permission_expired(self):
        """Handle view permission expiration"""
        logger.info(f"View permission expired for entry {self.entry.id}")

        self.view_permission_active = False
        self.countdown_running = False

        # Update UI to hide password
        self._update_view_state(False)

        # Show notification
        self.main_window._show_temporary_message("Password viewing session expired", "warning")

    def _hide_password(self):
        """Manually hide password"""
        self.view_permission_active = False
        self.countdown_running = False
        self._update_view_state(False)

    def _copy_password_secure(self):
        """Copy password to clipboard with security logging"""
        if not self.is_password_visible or not self.entry.password:
            return

        try:
            # Copy to clipboard
            pyperclip.copy(self.entry.password)

            # Log the copy operation
            if hasattr(self.service_integrator, '_security_audit_logger'):
                self.service_integrator._security_audit_logger.log_event(
                    SecurityEventType.PASSWORD_VIEWED,
                    self.user_id, self.session_id,
                    target_entry_id=self.entry.id,
                    event_details={
                        'action': 'copy_password',
                        'website': self.entry.website
                    }
                )

            # Show success message
            self.main_window._show_temporary_message("Password copied to clipboard", "success")

            # Schedule clipboard clearing after 30 seconds
            self.after(30000, self._clear_clipboard_if_matches)

            logger.debug(f"Password copied to clipboard for entry {self.entry.id}")

        except Exception as e:
            logger.error(f"Error copying password: {e}")
            self.main_window._show_temporary_message("Failed to copy password", "error")

    def _clear_clipboard_if_matches(self):
        """Clear clipboard if it still contains the password"""
        try:
            current_clipboard = pyperclip.paste()
            if current_clipboard == self.entry.password:
                pyperclip.copy("")
                logger.debug("Clipboard cleared after timeout")
        except Exception as e:
            logger.debug(f"Error clearing clipboard: {e}")

    def _delete_password_with_confirmation(self):
        """Delete password with comprehensive confirmation workflow"""
        try:
            # Get deletion validation requirements
            allowed, message, requirements = self.service_integrator.validate_password_deletion(
                self.user_id, self.session_id, self.entry.id,
                self.entry.website, "user_initiated"
            )

            if not allowed:
                messagebox.showerror("Deletion Not Allowed", message)
                return

            # Show appropriate confirmation dialog based on requirements
            confirmation_type = requirements.get('confirmation_type', 'simple')

            if confirmation_type == 'simple':
                confirmed = self._show_simple_confirmation()
            elif confirmation_type == 'type_website':
                confirmed = self._show_type_website_confirmation()
            elif confirmation_type == 'master_password':
                confirmed = self._show_master_password_confirmation()
            elif confirmation_type == 'smart':
                confirmed = self._show_smart_confirmation(requirements)
            else:
                confirmed = False

            if confirmed:
                # Perform actual deletion
                self._perform_password_deletion()

        except Exception as e:
            logger.error(f"Error in password deletion workflow: {e}")
            messagebox.showerror("Deletion Error", f"An error occurred: {e}")

    def _show_simple_confirmation(self) -> bool:
        """Show simple yes/no confirmation"""
        return messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete the password for {self.entry.website}?\n\n"
            f"Username: {self.entry.username}\n"
            "This action cannot be undone."
        )

    def _show_type_website_confirmation(self) -> bool:
        """Show confirmation that requires typing website name"""
        from tkinter import simpledialog

        typed_website = simpledialog.askstring(
            "Confirm Deletion",
            "To confirm deletion, please type the website name:\n\n"
            f"Website: {self.entry.website}\n"
            f"Username: {self.entry.username}\n\n"
            "Type the website name to confirm:"
        )

        if typed_website and typed_website.lower().strip() == self.entry.website.lower().strip():
            return True
        elif typed_website:
            messagebox.showerror("Confirmation Failed", "Website name does not match.")

        return False

    def _show_master_password_confirmation(self) -> bool:
        """Show confirmation that requires master password"""
        from tkinter import simpledialog

        master_password = simpledialog.askstring(
            "Master Password Required",
            f"Deleting password for {self.entry.website} requires master password verification.\n\n"
            "Enter your master password:",
            show="*"
        )

        if master_password:
            # Validate with service integrator (placeholder)
            # In real implementation, this would verify the master password
            return len(master_password) > 0

        return False

    def _show_smart_confirmation(self, requirements: Dict[str, Any]) -> bool:
        """Show smart confirmation based on rules"""
        # Smart confirmation logic would analyze various factors
        # For now, default to simple confirmation
        return self._show_simple_confirmation()

    def _perform_password_deletion(self):
        """Perform the actual password deletion"""
        try:
            # Confirm with service integrator
            success, message = self.service_integrator.confirm_password_deletion(
                self.user_id, self.session_id, self.entry.id,
                self.entry.website, {'confirmed': True}
            )

            if success:
                # Delete from password manager
                self.main_window.password_manager.delete_password_entry(
                    self.session_id, self.entry.id
                )

                # Show success message
                self.main_window._show_temporary_message(
                    f"Password for {self.entry.website} deleted successfully", "success"
                )

                # Refresh the password list
                self.main_window._refresh_entries()

                logger.info(f"Password entry {self.entry.id} deleted successfully")

            else:
                messagebox.showerror("Deletion Failed", f"Could not delete password: {message}")

        except Exception as e:
            logger.error(f"Error performing password deletion: {e}")
            messagebox.showerror("Deletion Error", f"An error occurred: {e}")

    def _edit_password(self):
        """Edit password entry"""
        self.main_window._edit_password_entry(self.entry)

    def _toggle_favorite(self):
        """Toggle favorite status"""
        # This would integrate with the password manager to update favorite status
        # For now, just show a message
        action = "remove from" if self.entry.is_favorite else "add to"
        self.main_window._show_temporary_message(f"Would {action} favorites", "info")

    def _toggle_details(self):
        """Toggle details section visibility"""
        if hasattr(self, '_details_expanded') and self._details_expanded:
            self.details_content.pack_forget()
            self.expand_btn.configure(text="▼ Details")
            self._details_expanded = False
        else:
            self.details_content.pack(fill="x", pady=(5, 0))
            self.expand_btn.configure(text="▲ Hide Details")
            self._details_expanded = True


class EnhancedPasswordListFrame(PasswordListFrame):
    """
    Enhanced password list frame with integrated security features

    This frame extends the basic password list with enhanced password entry
    widgets that provide secure viewing and deletion capabilities.
    """

    def __init__(self, parent, main_window, service_integrator: PasswordManagerServiceIntegrator,
                 user_id: int, session_id: str):
        """
        Initialize enhanced password list frame

        Args:
            parent: Parent widget
            main_window: Reference to main window
            service_integrator: Service integrator for authentication and logging
            user_id: Current user ID
            session_id: Current session ID
        """
        self.service_integrator = service_integrator
        self.user_id = user_id
        self.session_id = session_id

        super().__init__(parent, main_window)

    def update_entries(self, entries: List[PasswordEntry]):
        """
        Update displayed password entries with enhanced widgets

        Args:
            entries: List of password entries to display
        """
        # Clear existing widgets
        for widget in self.entry_widgets:
            widget.destroy()
        self.entry_widgets.clear()

        # Create enhanced entry widgets
        if entries:
            for entry in entries:
                entry_widget = EnhancedPasswordEntryWidget(
                    parent=self,
                    entry=entry,
                    main_window=self.main_window,
                    service_integrator=self.service_integrator,
                    user_id=self.user_id,
                    session_id=self.session_id
                )
                entry_widget.pack(fill="x", padx=10, pady=5)
                self.entry_widgets.append(entry_widget)
        else:
            # Show no entries message
            no_entries_label = create_themed_label(
                self,
                text="No password entries found. Click 'Add Password' to create your first entry.",
                style="label_secondary"
            )
            no_entries_label.pack(pady=20)
            self.entry_widgets.append(no_entries_label)

# ==========================================
# UTILITY FUNCTIONS
# ==========================================


def create_enhanced_password_list(
        parent,
        main_window,
        service_integrator: PasswordManagerServiceIntegrator,
        user_id: int,
        session_id: str) -> EnhancedPasswordListFrame:
    """
    Factory function to create enhanced password list frame

    Args:
        parent: Parent widget
        main_window: Reference to main window
        service_integrator: Service integrator for authentication
        user_id: Current user ID
        session_id: Current session ID

    Returns:
        EnhancedPasswordListFrame: Enhanced password list frame
    """
    return EnhancedPasswordListFrame(parent, main_window, service_integrator, user_id, session_id)


# Example usage and testing
if __name__ == "__main__":
    # This section would only run if the file is executed directly (for testing)
    import os
    import sys

    # Add parent directories to path for imports
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    print("Enhanced Password List Component Test")
    print("This component requires integration with the main application")
    print("and ServiceIntegrator for full functionality.")
