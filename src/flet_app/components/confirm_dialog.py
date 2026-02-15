"""
Confirmation Dialog Component
==============================

Reusable confirmation dialog for destructive actions (delete, logout,
replace imports, etc.). Provides a consistent UX across all pages.

Usage:
    show_confirm_dialog(
        page=page,
        title="Delete Password",
        message="Are you sure you want to delete this entry?",
        on_confirm=lambda: delete_entry(entry_id),
    )

Version: 3.0.0
"""

import flet as ft
from typing import Callable, Optional


def show_confirm_dialog(
    page: ft.Page,
    title: str,
    message: str,
    on_confirm: Callable[[], None],
    on_cancel: Optional[Callable[[], None]] = None,
    confirm_text: str = "Confirm",
    cancel_text: str = "Cancel",
    destructive: bool = False,
) -> None:
    """
    Show a modal confirmation dialog.

    The dialog blocks interaction with the rest of the app until the
    user confirms or cancels.

    Args:
        page: The Flet page to show the dialog on
        title: Dialog title text
        message: Description/warning text
        on_confirm: Callback when the user confirms
        on_cancel: Optional callback when the user cancels
        confirm_text: Text for the confirm button (default: "Confirm")
        cancel_text: Text for the cancel button (default: "Cancel")
        destructive: If True, the confirm button is colored red to
                     indicate a destructive action
    """

    def _handle_confirm(e: ft.ControlEvent) -> None:
        dialog.open = False
        page.update()
        on_confirm()

    def _handle_cancel(e: ft.ControlEvent) -> None:
        dialog.open = False
        page.update()
        if on_cancel:
            on_cancel()

    # Build the confirm button with optional destructive styling
    confirm_button = ft.TextButton(
        text=confirm_text,
        on_click=_handle_confirm,
        style=ft.ButtonStyle(
            color=ft.Colors.RED if destructive else None,
        ),
    )

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title),
        content=ft.Text(message),
        actions=[
            ft.TextButton(text=cancel_text, on_click=_handle_cancel),
            confirm_button,
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()


def show_snack_bar(
    page: ft.Page,
    message: str,
    action_text: Optional[str] = None,
    on_action: Optional[Callable[[], None]] = None,
    duration_ms: int = 3000,
) -> None:
    """
    Show a temporary snack bar message at the bottom of the page.

    Args:
        page: The Flet page
        message: Message text to display
        action_text: Optional action button text (e.g., "Undo")
        on_action: Callback for the action button
        duration_ms: How long to show the snack bar (milliseconds)
    """
    action = None
    if action_text and on_action:
        action = ft.SnackBarAction(text=action_text, on_click=lambda e: on_action())

    snack = ft.SnackBar(
        content=ft.Text(message),
        action=action,
        duration=duration_ms,
    )

    page.overlay.append(snack)
    snack.open = True
    page.update()
