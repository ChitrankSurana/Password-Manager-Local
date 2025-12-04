#!/usr/bin/env python3
"""
Personal Password Manager - Export Dialog
==========================================

This module provides a GUI dialog for exporting passwords to various formats.

Author: Personal Password Manager
Version: 2.2.0
"""

from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk

from ..core.logging_config import get_logger
from .error_dialog import show_error, show_warning
from .themes import apply_window_theme, create_themed_button, create_themed_label, get_theme

logger = get_logger(__name__)


class ExportDialog(ctk.CTkToplevel):
    """
    Dialog for exporting passwords

    Allows users to export passwords to CSV, JSON, or encrypted ZIP formats
    with various configuration options.
    """

    def __init__(
        self, parent, password_manager, session_id: str, import_export_service, theme=None
    ):
        """
        Initialize export dialog

        Args:
            parent: Parent window
            password_manager: Password manager instance
            session_id: Current session ID
            import_export_service: Import/export service instance
            theme: Theme configuration
        """
        super().__init__(parent)

        self.parent_window = parent
        self.password_manager = password_manager
        self.session_id = session_id
        self.import_export_service = import_export_service
        self.theme = theme or get_theme()

        # State variables
        self.export_format = ctk.StringVar(value="csv")
        self.include_metadata = ctk.BooleanVar(value=True)
        self.pretty_print = ctk.BooleanVar(value=True)
        self.encrypt_zip = ctk.BooleanVar(value=False)
        self.output_path = ctk.StringVar()

        # Setup dialog
        self._setup_dialog()
        self._create_ui()

        logger.info("Export dialog initialized")

    def _setup_dialog(self) -> None:
        """Configure dialog properties"""
        self.title("Export Passwords")
        self.geometry("600x550")
        self.resizable(False, False)

        # Center on parent
        if self.parent_window:
            x = self.parent_window.winfo_x() + (self.parent_window.winfo_width() // 2) - 300
            y = self.parent_window.winfo_y() + (self.parent_window.winfo_height() // 2) - 275
            self.geometry(f"600x550+{x}+{y}")

        # Apply theme
        apply_window_theme(self)

        # Make modal
        self.transient(self.parent_window)
        self.grab_set()

        # Bind escape to close
        self.bind("<Escape>", lambda e: self.destroy())

    def _create_ui(self) -> None:
        """Create the user interface"""
        spacing = self.theme.get_spacing()
        colors = self.theme.get_colors()
        fonts = self.theme.get_fonts()

        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(
            fill="both", expand=True, padx=spacing["padding_xl"], pady=spacing["padding_xl"]
        )

        # Header
        header_label = create_themed_label(main_frame, text="📤 Export Passwords", style="label")
        header_label.configure(font=fonts["heading_medium"])
        header_label.pack(pady=(0, spacing["section_gap"]))

        # Description
        desc_label = create_themed_label(
            main_frame,
            text="Export your passwords to a file for backup or transfer.",
            style="label_secondary",
        )
        desc_label.pack(pady=(0, spacing["section_gap"]))

        # Format selection
        format_frame = ctk.CTkFrame(main_frame)
        format_frame.pack(fill="x", pady=(0, spacing["padding_md"]))

        format_title = create_themed_label(format_frame, text="Export Format", style="label")
        format_title.configure(font=fonts["heading_small"])
        format_title.pack(
            anchor="w",
            padx=spacing["padding_md"],
            pady=(spacing["padding_md"], spacing["padding_xs"]),
        )

        # Format radio buttons
        formats = [
            ("CSV (Spreadsheet)", "csv", "Compatible with Excel, Google Sheets"),
            ("JSON (Structured)", "json", "Full data with metadata"),
            ("Encrypted ZIP", "encrypted_zip", "Password-protected archive"),
        ]

        for label, value, desc in formats:
            radio_frame = ctk.CTkFrame(format_frame, fg_color="transparent")
            radio_frame.pack(fill="x", padx=spacing["padding_md"], pady=spacing["padding_xs"])

            radio = ctk.CTkRadioButton(
                radio_frame,
                text=label,
                variable=self.export_format,
                value=value,
                command=self._on_format_change,
            )
            self.theme.apply_component_style(radio, "radiobutton")
            radio.pack(side="left")

            desc_label = create_themed_label(
                radio_frame, text=f"  ({desc})", style="label_secondary"
            )
            desc_label.configure(font=fonts["body_small"])
            desc_label.pack(side="left")

        # Options frame
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", pady=(0, spacing["padding_md"]))

        options_title = create_themed_label(options_frame, text="Options", style="label")
        options_title.configure(font=fonts["heading_small"])
        options_title.pack(
            anchor="w",
            padx=spacing["padding_md"],
            pady=(spacing["padding_md"], spacing["padding_xs"]),
        )

        # Metadata checkbox
        self.metadata_check = ctk.CTkCheckBox(
            options_frame,
            text="Include timestamps (created_at, last_modified)",
            variable=self.include_metadata,
        )
        self.theme.apply_component_style(self.metadata_check, "checkbox")
        self.metadata_check.pack(anchor="w", padx=spacing["padding_md"], pady=spacing["padding_xs"])

        # Pretty print checkbox (JSON only)
        self.pretty_print_check = ctk.CTkCheckBox(
            options_frame,
            text="Pretty print JSON (formatted with indentation)",
            variable=self.pretty_print,
        )
        self.theme.apply_component_style(self.pretty_print_check, "checkbox")
        self.pretty_print_check.pack(
            anchor="w", padx=spacing["padding_md"], pady=spacing["padding_xs"]
        )

        # Output path
        output_frame = ctk.CTkFrame(main_frame)
        output_frame.pack(fill="x", pady=(0, spacing["padding_md"]))

        output_title = create_themed_label(output_frame, text="Output Location", style="label")
        output_title.configure(font=fonts["heading_small"])
        output_title.pack(
            anchor="w",
            padx=spacing["padding_md"],
            pady=(spacing["padding_md"], spacing["padding_xs"]),
        )

        path_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        path_frame.pack(fill="x", padx=spacing["padding_md"], pady=spacing["padding_sm"])

        self.path_entry = ctk.CTkEntry(
            path_frame,
            textvariable=self.output_path,
            placeholder_text="Select output file location...",
        )
        self.theme.apply_component_style(self.path_entry, "entry")
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, spacing["padding_xs"]))

        browse_btn = create_themed_button(
            path_frame,
            text="Browse...",
            style="button_secondary",
            command=self._browse_output_path,
            width=100,
        )
        browse_btn.pack(side="right")

        # Warning box
        self.warning_frame = ctk.CTkFrame(
            main_frame, fg_color=colors.get("warning_bg", colors["surface"])
        )
        self.warning_frame.pack(fill="x", pady=spacing["padding_md"])

        warning_label = create_themed_label(
            self.warning_frame,
            text="⚠️ Warning: Exported files contain your passwords in readable format.\n"
            "Store them securely and delete after use.",
            style="label_secondary",
        )
        warning_label.configure(font=fonts["body_small"])
        warning_label.pack(padx=spacing["padding_sm"], pady=spacing["padding_sm"])

        # Button frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(spacing["section_gap"], 0))

        cancel_btn = create_themed_button(
            button_frame, text="Cancel", style="button_secondary", command=self.destroy, width=120
        )
        cancel_btn.pack(side="right", padx=(spacing["padding_xs"], 0))

        self.export_btn = create_themed_button(
            button_frame,
            text="Export",
            style="button_primary",
            command=self._export_passwords,
            width=120,
        )
        self.export_btn.pack(side="right")

        # Initial format update
        self._on_format_change()

    def _on_format_change(self) -> None:
        """Handle format selection change"""
        format_val = self.export_format.get()

        # Show/hide pretty print option for JSON
        if format_val == "json":
            self.pretty_print_check.configure(state="normal")
        else:
            self.pretty_print_check.configure(state="disabled")

        # Update file extension hint in path
        if self.output_path.get():
            current_path = Path(self.output_path.get())
            if format_val == "csv":
                new_path = current_path.with_suffix(".csv")
            elif format_val == "json":
                new_path = current_path.with_suffix(".json")
            else:  # encrypted_zip
                new_path = current_path.with_suffix(".zip")
            self.output_path.set(str(new_path))

    def _browse_output_path(self) -> None:
        """Open file browser to select output location"""
        format_val = self.export_format.get()

        # Determine file type and extension
        if format_val == "csv":
            filetypes = [("CSV files", "*.csv"), ("All files", "*.*")]
            default_ext = ".csv"
        elif format_val == "json":
            filetypes = [("JSON files", "*.json"), ("All files", "*.*")]
            default_ext = ".json"
        else:  # encrypted_zip
            filetypes = [("ZIP archives", "*.zip"), ("All files", "*.*")]
            default_ext = ".zip"

        # Generate default filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"passwords_export_{timestamp}{default_ext}"

        # Show save dialog
        filepath = filedialog.asksaveasfilename(
            parent=self,
            title="Select Export Location",
            defaultextension=default_ext,
            filetypes=filetypes,
            initialfile=default_name,
        )

        if filepath:
            self.output_path.set(filepath)

    def _export_passwords(self) -> None:
        """Perform the export operation"""
        try:
            # Validate output path
            output_path = self.output_path.get().strip()
            if not output_path:
                show_warning(
                    "No Output Path", "Please select an output file location.", parent=self
                )
                return

            # Get user's passwords
            passwords = self.password_manager.get_all_passwords(self.session_id)

            if not passwords:
                show_warning("No Passwords", "You don't have any passwords to export.", parent=self)
                return

            # Get format
            format_val = self.export_format.get()

            # Get session info for user_id
            session = self.password_manager.auth_manager.get_session(self.session_id)
            if not session:
                show_error(
                    "Session Error", "Your session has expired. Please log in again.", parent=self
                )
                self.destroy()
                return

            user_id = session.user_id

            # Perform export based on format
            success = False

            if format_val == "csv":
                success = self.import_export_service.export_passwords_csv(
                    user_id=user_id,
                    passwords=passwords,
                    output_path=output_path,
                    include_metadata=self.include_metadata.get(),
                )

            elif format_val == "json":
                success = self.import_export_service.export_passwords_json(
                    user_id=user_id,
                    passwords=passwords,
                    output_path=output_path,
                    include_metadata=self.include_metadata.get(),
                    pretty_print=self.pretty_print.get(),
                )

            elif format_val == "encrypted_zip":
                # Ask for ZIP password
                zip_password = self._ask_zip_password()
                if not zip_password:
                    return  # User cancelled

                success = self.import_export_service.export_passwords_encrypted_zip(
                    user_id=user_id,
                    passwords=passwords,
                    output_path=output_path,
                    zip_password=zip_password,
                    format="json",
                )

            if success:
                messagebox.showinfo(
                    "Export Successful",
                    f"Successfully exported {len(passwords)} passwords to:\n{output_path}",
                    parent=self,
                )
                self.destroy()
            else:
                show_error(
                    "Export Failed", "Failed to export passwords. Please try again.", parent=self
                )

        except Exception as e:
            logger.error(f"Export failed: {e}")
            show_error(
                "Export Error",
                "An error occurred while exporting passwords.",
                details=str(e),
                parent=self,
            )

    def _ask_zip_password(self) -> Optional[str]:
        """Ask user for ZIP archive password"""
        dialog = ctk.CTkInputDialog(
            text="Enter password to protect ZIP archive:", title="ZIP Password"
        )
        password = dialog.get_input()

        if password:
            # Confirm password
            confirm_dialog = ctk.CTkInputDialog(
                text="Confirm ZIP password:", title="Confirm Password"
            )
            confirm = confirm_dialog.get_input()

            if password == confirm:
                return password
            else:
                show_warning(
                    "Password Mismatch", "Passwords do not match. Please try again.", parent=self
                )
                return None

        return None


if __name__ == "__main__":
    print("Export Dialog Module")
    print("=" * 50)
    print("✓ Module loaded successfully")
