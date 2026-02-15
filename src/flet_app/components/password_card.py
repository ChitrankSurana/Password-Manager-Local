"""
Password Card Component
========================

Displays a single password entry as a Material Design card. Used in the
dashboard list view. Shows website, username, and action buttons (copy,
edit, delete). The password itself is hidden by default and revealed
on demand.

Version: 3.0.0
"""

import flet as ft
from typing import Any, Callable, Optional


class PasswordCard(ft.Card):
    """
    Card widget displaying a single password entry.

    Args:
        entry: Password entry object/dict with website, username, password, etc.
        on_edit: Callback when the edit button is clicked (receives entry_id)
        on_delete: Callback when the delete button is clicked (receives entry_id)
        on_copy: Callback when the copy button is clicked (receives password string)
    """

    def __init__(
        self,
        entry: Any,
        on_edit: Optional[Callable[[int], None]] = None,
        on_delete: Optional[Callable[[int], None]] = None,
        on_copy: Optional[Callable[[str], None]] = None,
    ):
        self.entry = entry
        self._on_edit = on_edit
        self._on_delete = on_delete
        self._on_copy = on_copy
        self._password_visible = False

        # Extract entry data (supports both dict and object access)
        self._entry_id = self._get("id", self._get("entry_id", 0))
        self._website = self._get("website", "")
        self._username = self._get("username", "")
        self._password = self._get("password", "")
        self._remarks = self._get("remarks", "")

        # Build the password display field
        self._password_text = ft.Text(
            value="*" * 12,
            size=14,
            selectable=True,
        )

        # Toggle visibility button
        self._visibility_btn = ft.IconButton(
            icon=ft.Icons.VISIBILITY_OFF,
            tooltip="Show password",
            on_click=self._toggle_password,
            icon_size=18,
        )

        super().__init__(
            content=ft.Container(
                content=ft.Column(
                    [
                        # Top row: website name and action buttons
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.LANGUAGE, size=20),
                                ft.Text(
                                    self._website,
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    expand=True,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.CONTENT_COPY,
                                    tooltip="Copy password",
                                    on_click=self._copy_password,
                                    icon_size=18,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    tooltip="Edit",
                                    on_click=self._edit_entry,
                                    icon_size=18,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    tooltip="Delete",
                                    on_click=self._delete_entry,
                                    icon_size=18,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        # Username row
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.PERSON_OUTLINE, size=16),
                                ft.Text(self._username, size=14),
                            ],
                        ),
                        # Password row with toggle
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.LOCK_OUTLINE, size=16),
                                self._password_text,
                                self._visibility_btn,
                            ],
                        ),
                        # Remarks (if any)
                        *(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.NOTES, size=16),
                                        ft.Text(
                                            self._remarks,
                                            size=12,
                                            italic=True,
                                            opacity=0.7,
                                        ),
                                    ],
                                )
                            ]
                            if self._remarks
                            else []
                        ),
                    ],
                    spacing=8,
                ),
                padding=ft.padding.all(16),
            ),
            elevation=1,
        )

    def _get(self, key: str, default: Any = None) -> Any:
        """Get attribute from entry (supports dict and object)."""
        if isinstance(self.entry, dict):
            return self.entry.get(key, default)
        return getattr(self.entry, key, default)

    def _toggle_password(self, e: ft.ControlEvent) -> None:
        """Toggle password visibility between masked and plaintext."""
        self._password_visible = not self._password_visible
        if self._password_visible:
            self._password_text.value = self._password
            self._visibility_btn.icon = ft.Icons.VISIBILITY
            self._visibility_btn.tooltip = "Hide password"
        else:
            self._password_text.value = "*" * 12
            self._visibility_btn.icon = ft.Icons.VISIBILITY_OFF
            self._visibility_btn.tooltip = "Show password"
        self.update()

    def _copy_password(self, e: ft.ControlEvent) -> None:
        """Copy the password to clipboard."""
        if self._on_copy:
            self._on_copy(self._password)

    def _edit_entry(self, e: ft.ControlEvent) -> None:
        """Trigger the edit callback."""
        if self._on_edit:
            self._on_edit(self._entry_id)

    def _delete_entry(self, e: ft.ControlEvent) -> None:
        """Trigger the delete callback."""
        if self._on_delete:
            self._on_delete(self._entry_id)
