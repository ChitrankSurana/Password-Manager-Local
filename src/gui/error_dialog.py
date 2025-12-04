#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User-Friendly Error Dialogs
Personal Password Manager - Professional Error Display

This module provides professional error dialogs for the GUI with:
- User-friendly messages
- Technical details (expandable)
- Error recovery suggestions
- Copy to clipboard functionality
- Different severity levels

Usage:
    from src.gui.error_dialog import show_error, show_warning, show_critical_error

    # Simple error
    show_error("Failed to save password", "The password could not be saved.")

    # With details and suggestions
    show_error(
        "Database Error",
        "Failed to connect to database",
        details="Connection timeout after 30 seconds",
        suggestions=["Check if database file exists", "Verify file permissions"]
    )
"""

import traceback
from tkinter import messagebox
from typing import List, Optional

import customtkinter as ctk

try:
    from .themes import get_theme
except ImportError:
    get_theme = None


class ErrorDialog(ctk.CTkToplevel):
    """
    Professional error dialog with expandable details

    Features:
    - User-friendly message
    - Expandable technical details
    - Error recovery suggestions
    - Copy to clipboard
    - Appropriate icons
    """

    def __init__(
        self,
        parent,
        title: str,
        message: str,
        details: Optional[str] = None,
        suggestions: Optional[List[str]] = None,
        severity: str = "error",
        **kwargs,
    ):
        """
        Initialize error dialog

        Args:
            parent: Parent window
            title: Dialog title
            message: User-friendly error message
            details: Technical details (optional)
            suggestions: List of suggestions for recovery (optional)
            severity: 'error', 'warning', or 'critical'
        """
        super().__init__(parent, **kwargs)

        self.title(title)
        self.message = message
        self.details = details
        self.suggestions = suggestions or []
        self.severity = severity

        # Window configuration
        self.geometry("500x300")
        self.resizable(False, False)

        # Modal dialog
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 300) // 2
        self.geometry(f"+{x}+{y}")

        # Build UI
        self._build_ui()

    def _build_ui(self):
        """Build the dialog UI"""
        # Colors based on severity
        colors = {
            "error": ("#f87171", "#dc2626"),  # Red
            "warning": ("#fbbf24", "#d97706"),  # Yellow
            "critical": ("#991b1b", "#7f1d1d"),  # Dark red
        }

        accent_color, dark_accent = colors.get(self.severity, colors["error"])

        # Header with icon
        header_frame = ctk.CTkFrame(self, fg_color=accent_color, corner_radius=0)
        header_frame.pack(fill="x", pady=0)

        # Icon and title
        icon_label = ctk.CTkLabel(
            header_frame,
            text=self._get_icon(),
            font=("Segoe UI", 32),
            text_color="white",
        )
        icon_label.pack(side="left", padx=20, pady=15)

        title_label = ctk.CTkLabel(
            header_frame,
            text=self.winfo_toplevel().title(),
            font=("Segoe UI", 16, "bold"),
            text_color="white",
        )
        title_label.pack(side="left", pady=15)

        # Main content area
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Message
        message_label = ctk.CTkLabel(
            content_frame,
            text=self.message,
            font=("Segoe UI", 12),
            wraplength=450,
            justify="left",
        )
        message_label.pack(anchor="w", pady=(0, 10))

        # Suggestions (if any)
        if self.suggestions:
            suggestions_label = ctk.CTkLabel(
                content_frame,
                text="Suggested actions:",
                font=("Segoe UI", 11, "bold"),
            )
            suggestions_label.pack(anchor="w", pady=(10, 5))

            for suggestion in self.suggestions:
                suggestion_label = ctk.CTkLabel(
                    content_frame,
                    text=f"• {suggestion}",
                    font=("Segoe UI", 10),
                    wraplength=430,
                    justify="left",
                )
                suggestion_label.pack(anchor="w", padx=(10, 0))

        # Details section (expandable)
        if self.details:
            self.details_visible = False

            # Show/Hide details button
            self.details_button = ctk.CTkButton(
                content_frame,
                text="▼ Show Technical Details",
                command=self._toggle_details,
                fg_color="transparent",
                hover_color=("gray70", "gray30"),
                text_color=accent_color,
                anchor="w",
            )
            self.details_button.pack(anchor="w", pady=(15, 5))

            # Details text (hidden by default)
            self.details_frame = ctk.CTkFrame(content_frame)

            details_text = ctk.CTkTextbox(
                self.details_frame, height=100, wrap="word", font=("Consolas", 9)
            )
            details_text.insert("1.0", self.details)
            details_text.configure(state="disabled")
            details_text.pack(fill="both", expand=True, padx=5, pady=5)

            # Copy button
            copy_button = ctk.CTkButton(
                self.details_frame,
                text="Copy to Clipboard",
                command=self._copy_details,
                height=25,
            )
            copy_button.pack(pady=(0, 5))

        # Button area
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 15))

        # OK button
        ok_button = ctk.CTkButton(
            button_frame,
            text="OK",
            command=self.destroy,
            width=100,
            fg_color=accent_color,
            hover_color=dark_accent,
        )
        ok_button.pack(side="right")

        # Focus OK button
        ok_button.focus_set()

        # Bind Enter key
        self.bind("<Return>", lambda e: self.destroy())
        self.bind("<Escape>", lambda e: self.destroy())

    def _get_icon(self) -> str:
        """Get icon based on severity"""
        icons = {"error": "⚠️", "warning": "⚡", "critical": "🛑"}
        return icons.get(self.severity, "⚠️")

    def _toggle_details(self):
        """Toggle details visibility"""
        if self.details_visible:
            self.details_frame.pack_forget()
            self.details_button.configure(text="▼ Show Technical Details")
            self.geometry("500x300")
        else:
            self.details_frame.pack(fill="both", expand=True, padx=10, pady=5)
            self.details_button.configure(text="▲ Hide Technical Details")
            self.geometry("500x500")

        self.details_visible = not self.details_visible

    def _copy_details(self):
        """Copy details to clipboard"""
        try:
            import pyperclip

            error_report = """Error Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 70}
Title: {self.winfo_toplevel().title()}
Message: {self.message}

Technical Details:
{self.details}

Suggestions:
{chr(10).join(f'• {s}' for s in self.suggestions)}
"""
            pyperclip.copy(error_report)
            messagebox.showinfo("Copied", "Error details copied to clipboard")

        except Exception as e:
            messagebox.showerror("Copy Failed", f"Failed to copy: {e}")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def show_error(
    title: str,
    message: str,
    details: Optional[str] = None,
    suggestions: Optional[List[str]] = None,
    parent=None,
):
    """
    Show error dialog

    Args:
        title: Dialog title
        message: User-friendly message
        details: Technical details (optional)
        suggestions: Recovery suggestions (optional)
        parent: Parent window (optional)
    """
    try:
        dialog = ErrorDialog(
            parent or _get_root(),
            title=title,
            message=message,
            details=details,
            suggestions=suggestions,
            severity="error",
        )
        dialog.wait_window()
    except Exception:
        # Fallback to simple messagebox
        messagebox.showerror(title, message)


def show_warning(
    title: str,
    message: str,
    details: Optional[str] = None,
    suggestions: Optional[List[str]] = None,
    parent=None,
):
    """Show warning dialog"""
    try:
        dialog = ErrorDialog(
            parent or _get_root(),
            title=title,
            message=message,
            details=details,
            suggestions=suggestions,
            severity="warning",
        )
        dialog.wait_window()
    except Exception:
        messagebox.showwarning(title, message)


def show_critical_error(
    title: str,
    message: str,
    details: Optional[str] = None,
    suggestions: Optional[List[str]] = None,
    parent=None,
):
    """Show critical error dialog"""
    try:
        dialog = ErrorDialog(
            parent or _get_root(),
            title=title,
            message=message,
            details=details,
            suggestions=suggestions,
            severity="critical",
        )
        dialog.wait_window()
    except Exception:
        messagebox.showerror(title, message)


def show_exception_dialog(exception: Exception, title: str = "Error Occurred", parent=None):
    """
    Show dialog for an exception

    Args:
        exception: Exception instance
        title: Dialog title
        parent: Parent window
    """
    from ..core.exceptions import get_exception_info

    # Get exception info
    error_info = get_exception_info(exception)

    # Get traceback
    tb = traceback.format_exc()

    # Show dialog
    show_error(
        title=title,
        message=error_info["user_message"],
        details=f"{error_info['message']}\n\n{tb}",
        suggestions=_get_recovery_suggestions(exception),
        parent=parent,
    )


def _get_recovery_suggestions(exception: Exception) -> List[str]:
    """Get recovery suggestions based on exception type"""
    from ..core.exceptions import DatabaseException, SecurityException, ValidationException

    if isinstance(exception, DatabaseException):
        return [
            "Check if the database file exists",
            "Verify file permissions",
            "Restore from backup if corrupted",
        ]
    elif isinstance(exception, SecurityException):
        return [
            "Verify your credentials are correct",
            "Check if your account is locked",
            "Try logging out and back in",
        ]
    elif isinstance(exception, ValidationException):
        return [
            "Check your input for errors",
            "Ensure all required fields are filled",
            "Follow the format requirements",
        ]
    else:
        return ["Try the operation again", "Contact support if the problem persists"]


def _get_root():
    """Get root window (fallback)"""
    try:
        import tkinter as tk

        for widget in tk._default_root.winfo_children():
            if isinstance(widget, (ctk.CTk, tk.Tk)):
                return widget
        return None
    except Exception:
        return None


# Export public API
__all__ = [
    "ErrorDialog",
    "show_error",
    "show_warning",
    "show_critical_error",
    "show_exception_dialog",
]
