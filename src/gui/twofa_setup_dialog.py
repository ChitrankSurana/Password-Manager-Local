#!/usr/bin/env python3
"""
Personal Password Manager - Two-Factor Authentication Setup Dialog
==================================================================

This module provides a comprehensive GUI dialog for setting up two-factor
authentication (2FA) for users. It guides users through QR code scanning,
verification, and backup code management.

Key Features:
- Step-by-step wizard interface
- QR code generation and display
- TOTP code verification
- Backup code generation and display
- Download backup codes to file
- Copy codes to clipboard

Author: Personal Password Manager
Version: 2.2.0
"""

import tkinter as tk
from tkinter import filedialog
from typing import Callable, Optional

import customtkinter as ctk

from ..core.database import DatabaseManager
from ..core.logging_config import get_logger
from ..core.totp_service import TOTPService
from .error_dialog import show_error, show_warning
from .themes import get_theme

logger = get_logger(__name__)


class TwoFASetupDialog(ctk.CTkToplevel):
    """
    Two-Factor Authentication Setup Dialog

    Provides a multi-step wizard for setting up 2FA including:
    - QR code display for authenticator app scanning
    - Verification of TOTP code
    - Backup code generation and display
    - Secure storage of 2FA credentials
    """

    def __init__(
        self,
        parent,
        user_id: int,
        username: str,
        db_manager: DatabaseManager,
        on_complete: Optional[Callable] = None,
        theme=None,
    ):
        super().__init__(parent)

        self.user_id = user_id
        self.username = username
        self.db_manager = db_manager
        self.on_complete = on_complete
        self.theme = theme or get_theme()
        self.totp_service = TOTPService()

        # 2FA data
        self.totp_secret = None
        self.backup_codes = []
        self.qr_image = None

        # Current step
        self.current_step = 1

        # Setup window
        self.title("Enable Two-Factor Authentication")
        self.geometry("600x700")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center window
        self._center_window()

        # Create UI
        self._create_ui()

        # Start with step 1
        self._show_step_1()

    def _center_window(self):
        """Center the window on screen"""
        self.update_idletasks()
        width = 600
        height = 700
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _create_ui(self):
        """Create the main UI structure"""
        colors = self.theme.get_colors()

        # Header
        header_frame = ctk.CTkFrame(self, fg_color=colors["surface"])
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        self.header_label = ctk.CTkLabel(
            header_frame, text="🔐 Enable Two-Factor Authentication", font=("Segoe UI", 20, "bold")
        )
        self.header_label.pack(pady=15)

        # Step indicator
        self.step_label = ctk.CTkLabel(header_frame, text="Step 1 of 3", font=("Segoe UI", 12))
        self.step_label.pack(pady=(0, 15))

        # Content area (will be dynamically populated)
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Buttons frame
        self.buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.pack(fill="x", padx=20, pady=(0, 20))

    def _clear_content(self):
        """Clear the content area"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _show_step_1(self):
        """Step 1: QR Code Display"""
        self.current_step = 1
        self.step_label.configure(text="Step 1 of 3: Scan QR Code")
        self._clear_content()

        colors = self.theme.get_colors()

        # Generate TOTP secret
        try:
            self.totp_secret = self.totp_service.generate_secret()
            logger.info(f"Generated TOTP secret for user {self.username}")
        except Exception as e:
            logger.error(f"Failed to generate TOTP secret: {e}")
            show_error(
                title="Setup Error",
                message="Failed to generate authentication secret",
                details=str(e),
                parent=self,
            )
            self.destroy()
            return

        # Instructions
        instructions = ctk.CTkLabel(
            self.content_frame,
            text="Scan this QR code with your authenticator app\n"
            "(Google Authenticator, Authy, Microsoft Authenticator, etc.)",
            font=("Segoe UI", 12),
            wraplength=500,
        )
        instructions.pack(pady=(20, 10))

        # QR Code
        try:
            pil_image = self.totp_service.generate_qr_code(
                self.totp_secret, self.username, size=300
            )

            # Convert PIL image to CTkImage
            self.qr_image = ctk.CTkImage(
                light_image=pil_image, dark_image=pil_image, size=(300, 300)
            )

            qr_label = ctk.CTkLabel(self.content_frame, image=self.qr_image, text="")
            qr_label.pack(pady=20)

        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            show_error(
                title="QR Code Error",
                message="Failed to generate QR code",
                details=str(e),
                parent=self,
            )

        # Manual entry option
        manual_frame = ctk.CTkFrame(self.content_frame, fg_color=colors["surface"])
        manual_frame.pack(fill="x", pady=20, padx=40)

        manual_label = ctk.CTkLabel(
            manual_frame, text="Can't scan? Enter this key manually:", font=("Segoe UI", 11)
        )
        manual_label.pack(pady=(10, 5))

        key_frame = ctk.CTkFrame(manual_frame, fg_color="transparent")
        key_frame.pack(pady=(0, 10))

        key_entry = ctk.CTkEntry(key_frame, width=350, font=("Courier", 12, "bold"))
        key_entry.insert(0, self.totp_secret)
        key_entry.configure(state="readonly")
        key_entry.pack(side="left", padx=(0, 5))

        copy_btn = ctk.CTkButton(
            key_frame,
            text="Copy",
            width=60,
            command=lambda: self._copy_to_clipboard(self.totp_secret),
        )
        copy_btn.pack(side="left")

        # Buttons
        self._update_buttons(
            next_text="Next: Verify Code", next_command=self._show_step_2, show_back=False
        )

    def _show_step_2(self):
        """Step 2: Verify TOTP Code"""
        self.current_step = 2
        self.step_label.configure(text="Step 2 of 3: Verify Code")
        self._clear_content()

        # Instructions
        instructions = ctk.CTkLabel(
            self.content_frame,
            text="Enter the 6-digit code from your authenticator app\n"
            "to verify the setup is working correctly",
            font=("Segoe UI", 12),
            wraplength=500,
        )
        instructions.pack(pady=(40, 30))

        # Code entry
        code_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        code_frame.pack(pady=20)

        code_label = ctk.CTkLabel(code_frame, text="Verification Code:", font=("Segoe UI", 12))
        code_label.pack(pady=(0, 10))

        self.code_entry = ctk.CTkEntry(
            code_frame,
            width=200,
            font=("Courier", 24, "bold"),
            justify="center",
            placeholder_text="000000",
        )
        self.code_entry.pack(pady=10)
        self.code_entry.focus()

        # Bind Enter key
        self.code_entry.bind("<Return>", lambda e: self._verify_code())

        # Status label
        self.verify_status_label = ctk.CTkLabel(code_frame, text="", font=("Segoe UI", 11))
        self.verify_status_label.pack(pady=10)

        # Hint
        hint = ctk.CTkLabel(
            self.content_frame,
            text="Tip: Codes change every 30 seconds",
            font=("Segoe UI", 10),
            text_color=self.theme.get_colors()["text_secondary"],
        )
        hint.pack(pady=20)

        # Buttons
        self._update_buttons(
            next_text="Verify",
            next_command=self._verify_code,
            show_back=True,
            back_command=self._show_step_1,
        )

    def _verify_code(self):
        """Verify the TOTP code"""
        code = self.code_entry.get().strip()

        if not code:
            self.verify_status_label.configure(
                text="Please enter a code", text_color=self.theme.get_colors().get("error", "red")
            )
            return

        if len(code) != 6 or not code.isdigit():
            self.verify_status_label.configure(
                text="Code must be 6 digits", text_color=self.theme.get_colors().get("error", "red")
            )
            return

        # Verify code
        is_valid = self.totp_service.verify_totp_code(
            self.totp_secret, code, user_id=self.user_id, username=self.username
        )

        if is_valid:
            self.verify_status_label.configure(
                text="✓ Code verified!", text_color=self.theme.get_colors().get("success", "green")
            )
            # Proceed to step 3 after short delay
            self.after(1000, self._show_step_3)
        else:
            self.verify_status_label.configure(
                text="✗ Invalid code. Please try again.",
                text_color=self.theme.get_colors().get("error", "red"),
            )
            self.code_entry.delete(0, tk.END)
            self.code_entry.focus()

    def _show_step_3(self):
        """Step 3: Backup Codes"""
        self.current_step = 3
        self.step_label.configure(text="Step 3 of 3: Save Backup Codes")
        self._clear_content()

        colors = self.theme.get_colors()

        # Generate backup codes
        try:
            self.backup_codes = self.totp_service.generate_backup_codes()
            logger.info(f"Generated {len(self.backup_codes)} backup codes")
        except Exception as e:
            logger.error(f"Failed to generate backup codes: {e}")
            show_error(
                title="Backup Codes Error",
                message="Failed to generate backup codes",
                details=str(e),
                parent=self,
            )
            return

        # Warning
        warning_frame = ctk.CTkFrame(
            self.content_frame, fg_color=colors.get("warning_bg", colors["surface"])
        )
        warning_frame.pack(fill="x", pady=(20, 10), padx=20)

        warning_icon = ctk.CTkLabel(warning_frame, text="⚠️", font=("Segoe UI", 24))
        warning_icon.pack(pady=(10, 5))

        warning_text = ctk.CTkLabel(
            warning_frame,
            text="Save these backup codes in a safe place!\n"
            "You can use them to access your account if you lose your phone.\n"
            "Each code can only be used once.",
            font=("Segoe UI", 11, "bold"),
            text_color=colors.get("warning", "orange"),
            wraplength=500,
        )
        warning_text.pack(pady=(0, 10))

        # Backup codes display
        codes_frame = ctk.CTkFrame(self.content_frame, fg_color=colors["surface"])
        codes_frame.pack(fill="both", expand=True, padx=20, pady=10)

        codes_label = ctk.CTkLabel(codes_frame, text="Backup Codes:", font=("Segoe UI", 12, "bold"))
        codes_label.pack(pady=(10, 5))

        # Scrollable codes area
        codes_text = ctk.CTkTextbox(codes_frame, width=400, height=200, font=("Courier", 12))
        codes_text.pack(padx=20, pady=(0, 10))

        # Insert codes
        for i, code in enumerate(self.backup_codes, 1):
            codes_text.insert(tk.END, f"{i:2d}. {code}\n")

        codes_text.configure(state="disabled")

        # Action buttons
        action_frame = ctk.CTkFrame(codes_frame, fg_color="transparent")
        action_frame.pack(pady=10)

        download_btn = ctk.CTkButton(
            action_frame, text="💾 Download Codes", command=self._download_backup_codes, width=150
        )
        download_btn.pack(side="left", padx=5)

        copy_btn = ctk.CTkButton(
            action_frame, text="📋 Copy to Clipboard", command=self._copy_backup_codes, width=150
        )
        copy_btn.pack(side="left", padx=5)

        # Confirmation checkbox
        self.confirm_var = tk.BooleanVar(value=False)
        confirm_check = ctk.CTkCheckBox(
            self.content_frame,
            text="I have saved my backup codes in a safe place",
            variable=self.confirm_var,
            command=self._update_enable_button,
            font=("Segoe UI", 11, "bold"),
        )
        confirm_check.pack(pady=20)

        # Buttons
        self._update_buttons(
            next_text="Enable 2FA",
            next_command=self._complete_setup,
            show_back=True,
            back_command=self._show_step_2,
            next_enabled=False,  # Disabled until checkbox checked
        )

    def _update_enable_button(self):
        """Update the Enable button state based on checkbox"""
        # Find and update the next button
        for widget in self.buttons_frame.winfo_children():
            if isinstance(widget, ctk.CTkButton) and "Enable" in widget.cget("text"):
                if self.confirm_var.get():
                    widget.configure(state="normal")
                else:
                    widget.configure(state="disabled")

    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard"""
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            logger.info("Copied to clipboard")
        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}")

    def _copy_backup_codes(self):
        """Copy backup codes to clipboard"""
        codes_text = "\n".join(f"{i}. {code}" for i, code in enumerate(self.backup_codes, 1))
        codes_text = "Password Manager - Backup Codes\n" + "=" * 40 + "\n" + codes_text
        self._copy_to_clipboard(codes_text)

        show_warning(
            title="Copied",
            message="Backup codes copied to clipboard",
            suggestions=["Paste them into a secure location"],
            parent=self,
        )

    def _download_backup_codes(self):
        """Download backup codes to a text file"""
        try:
            # Ask where to save
            filename = filedialog.asksaveasfilename(
                parent=self,
                title="Save Backup Codes",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=f"password_manager_backup_codes_{self.username}.txt",
            )

            if filename:
                # Write codes to file
                with open(filename, "w") as f:
                    f.write("Password Manager - Two-Factor Authentication Backup Codes\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(f"Username: {self.username}\n")
                    f.write(f"Generated: {ctk.CTkLabel._get_appearance_mode()}\n\n")
                    f.write("IMPORTANT: Keep these codes in a safe place!\n")
                    f.write("Each code can only be used once.\n\n")
                    f.write("Backup Codes:\n")
                    f.write("-" * 60 + "\n\n")

                    for i, code in enumerate(self.backup_codes, 1):
                        f.write(f"{i:2d}. {code}\n")

                logger.info(f"Backup codes saved to {filename}")
                show_warning(
                    title="Saved",
                    message=f"Backup codes saved to:\n{filename}",
                    suggestions=["Store this file in a secure location"],
                    parent=self,
                )

        except Exception as e:
            logger.error(f"Failed to save backup codes: {e}")
            show_error(
                title="Save Failed",
                message="Failed to save backup codes",
                details=str(e),
                parent=self,
            )

    def _complete_setup(self):
        """Complete the 2FA setup"""
        try:
            # Prepare backup codes for storage (hashed)
            backup_codes_json = self.totp_service.prepare_backup_codes_for_storage(
                self.backup_codes
            )

            # Enable 2FA in database
            self.db_manager.enable_2fa(self.user_id, self.totp_secret, backup_codes_json)

            logger.info(f"2FA enabled successfully for user {self.username}")

            # Show success message
            show_warning(
                title="2FA Enabled",
                message="Two-Factor Authentication has been enabled successfully!",
                suggestions=[
                    "You will need your authenticator app to login",
                    "Keep your backup codes safe",
                ],
                parent=self,
            )

            # Call completion callback
            if self.on_complete:
                self.on_complete()

            # Close dialog
            self.destroy()

        except Exception as e:
            logger.error(f"Failed to enable 2FA: {e}")
            show_error(
                title="Setup Failed",
                message="Failed to enable Two-Factor Authentication",
                details=str(e),
                suggestions=["Try again", "Check your database connection"],
                parent=self,
            )

    def _update_buttons(
        self,
        next_text: str,
        next_command: Callable,
        show_back: bool = False,
        back_command: Optional[Callable] = None,
        next_enabled: bool = True,
    ):
        """Update button configuration"""
        # Clear existing buttons
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()

        # Back button
        if show_back:
            back_btn = ctk.CTkButton(
                self.buttons_frame, text="← Back", command=back_command, width=120
            )
            back_btn.pack(side="left", padx=5)

        # Cancel button
        cancel_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Cancel",
            command=self._cancel_setup,
            width=120,
            fg_color="gray",
        )
        cancel_btn.pack(side="left", padx=5)

        # Next/Complete button
        next_btn = ctk.CTkButton(
            self.buttons_frame, text=next_text, command=next_command, width=150
        )
        next_btn.pack(side="right", padx=5)

        if not next_enabled:
            next_btn.configure(state="disabled")

    def _cancel_setup(self):
        """Cancel the 2FA setup"""
        from tkinter import messagebox

        result = messagebox.askyesno(
            "Cancel Setup", "Are you sure you want to cancel 2FA setup?", parent=self
        )
        if result:
            logger.info("2FA setup cancelled by user")
            self.destroy()


if __name__ == "__main__":
    print("2FA Setup Dialog module loaded successfully")
