"""
Personal Password Manager - Add / Edit Password Page
=====================================================

Form page for creating a new password entry or editing an existing one.
When entry_id is provided, the page loads the existing entry and pre-fills
the form. Otherwise, an empty form is shown for creating a new entry.

Features:
- Website, username, password, and remarks text fields
- Real-time password strength indicator (via AdvancedPasswordStrengthChecker)
- Generate-password button that opens the generator inline
- Favorite toggle
- Save / Cancel buttons
- Validation: website and password are required; username is required for new

The page uses the NavRail sidebar for consistent navigation.

Version: 3.0.0
"""

import threading
from typing import Optional

import flet as ft

from ..components.confirm_dialog import show_snack_bar
from ..components.nav_rail import NavRail
from ..components.strength_indicator import StrengthIndicator
from ..state import AppState


class AddEditPage(ft.Container):
    """
    Add or edit a password entry.

    When entry_id is None, the page is in "add" mode. When entry_id is
    provided, the page loads the existing entry and switches to "edit" mode.

    Args:
        state: The shared AppState object
        entry_id: ID of the entry to edit (None = add new)
    """

    def __init__(self, state: AppState, entry_id: Optional[int] = None):
        self.state = state
        self._entry_id = entry_id
        self._is_edit_mode = entry_id is not None

        page_title = "Edit Password" if self._is_edit_mode else "Add Password"

        # --- Page header ---
        self._title = ft.Text(
            page_title,
            size=24,
            weight=ft.FontWeight.BOLD,
        )

        # --- Form fields ---
        self._website_field = ft.TextField(
            label="Website / Service",
            prefix_icon=ft.Icons.LANGUAGE,
            hint_text="e.g., github.com",
            autofocus=not self._is_edit_mode,
        )

        self._username_field = ft.TextField(
            label="Username / Email",
            prefix_icon=ft.Icons.PERSON,
            hint_text="e.g., john@example.com",
        )

        self._password_field = ft.TextField(
            label="Password",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            on_change=self._on_password_change,
            hint_text="Enter or generate a password",
        )

        # --- Strength indicator ---
        self._strength_indicator = StrengthIndicator()

        # --- Generate password button (inline) ---
        self._generate_btn = ft.OutlinedButton(
            text="Generate",
            icon=ft.Icons.AUTO_FIX_HIGH,
            on_click=self._on_generate_password,
        )

        # --- Remarks / notes ---
        self._remarks_field = ft.TextField(
            label="Notes / Remarks",
            prefix_icon=ft.Icons.NOTES,
            hint_text="Optional notes about this entry",
            multiline=True,
            min_lines=2,
            max_lines=4,
        )

        # --- Favorite toggle ---
        self._favorite_switch = ft.Switch(
            label="Favorite",
            value=False,
        )

        # --- Action buttons ---
        self._save_btn = ft.FilledButton(
            text="Save",
            icon=ft.Icons.SAVE,
            on_click=self._on_save,
            width=140,
        )

        self._cancel_btn = ft.OutlinedButton(
            text="Cancel",
            icon=ft.Icons.CLOSE,
            on_click=self._on_cancel,
            width=140,
        )

        # --- Loading state ---
        self._loading = ft.ProgressRing(visible=False, width=20, height=20)

        # --- Error text ---
        self._error_text = ft.Text(
            value="",
            color=ft.Colors.RED,
            size=13,
            visible=False,
        )

        # --- Master password field (needed for encryption) ---
        # Shown only when the cached master password is not available
        self._master_password_field = ft.TextField(
            label="Master Password (for encryption)",
            prefix_icon=ft.Icons.KEY,
            password=True,
            can_reveal_password=True,
            visible=False,  # Hidden unless needed
        )

        # --- Build the form layout ---
        form = ft.Column(
            [
                self._title,
                ft.Divider(height=1),
                self._website_field,
                self._username_field,
                # Password row with generate button
                ft.Row(
                    [
                        ft.Container(
                            content=self._password_field,
                            expand=True,
                        ),
                        self._generate_btn,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.END,
                    spacing=8,
                ),
                self._strength_indicator,
                self._remarks_field,
                self._favorite_switch,
                self._master_password_field,
                self._error_text,
                # Button row
                ft.Container(
                    content=ft.Row(
                        [self._save_btn, self._loading, self._cancel_btn],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=16,
                    ),
                    padding=ft.padding.only(top=16),
                ),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            width=500,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # --- Main content area ---
        content_area = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=form,
                        alignment=ft.alignment.top_center,
                        padding=ft.padding.all(24),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
        )

        # --- NavRail + content ---
        # Highlight the dashboard destination since add/edit is part of that flow
        nav_rail = NavRail(state=state, current_route="/dashboard")

        super().__init__(
            content=ft.Row(
                [
                    nav_rail,
                    ft.VerticalDivider(width=1),
                    content_area,
                ],
                expand=True,
            ),
            expand=True,
        )

        # If editing, load the existing entry in background
        if self._is_edit_mode:
            self._load_entry()

    # ------------------------------------------------------------------
    # Load existing entry for edit mode
    # ------------------------------------------------------------------

    def _load_entry(self) -> None:
        """Fetch the existing entry in a background thread."""
        self._loading.visible = True
        try:
            self.update()
        except Exception:
            pass

        thread = threading.Thread(target=self._fetch_entry_background, daemon=True)
        thread.start()

    def _fetch_entry_background(self) -> None:
        """Background thread: retrieve entry from PasswordManagerCore."""
        try:
            entry = self.state.password_manager.get_password_entry(
                session_id=self.state.session_id,
                entry_id=self._entry_id,
                decrypt_password=True,
            )
            self._populate_form(entry)
        except Exception as ex:
            self._show_error(f"Failed to load entry: {ex}")

    def _populate_form(self, entry) -> None:
        """Fill form fields with data from an existing entry."""
        self._website_field.value = getattr(entry, "website", "") or ""
        self._username_field.value = getattr(entry, "username", "") or ""
        self._password_field.value = getattr(entry, "password", "") or ""
        self._remarks_field.value = getattr(entry, "remarks", "") or ""
        self._favorite_switch.value = getattr(entry, "is_favorite", False)
        self._loading.visible = False

        # Trigger strength check for the loaded password
        if self._password_field.value:
            self._update_strength(self._password_field.value)

        try:
            self.update()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Real-time password strength
    # ------------------------------------------------------------------

    def _on_password_change(self, e: ft.ControlEvent) -> None:
        """Update strength indicator as the user types."""
        password = e.control.value
        if password:
            self._update_strength(password)
        else:
            self._strength_indicator.hide()

    def _update_strength(self, password: str) -> None:
        """
        Evaluate password strength and update the indicator.

        Uses AdvancedPasswordStrengthChecker.analyze_password_realtime()
        for fast feedback. The strength_level string maps directly to
        the StrengthIndicator levels.
        """
        if not self.state.strength_checker:
            return

        try:
            result = self.state.strength_checker.analyze_password_realtime(password)
            level = result.get("strength_level", "very_weak")
            self._strength_indicator.set_strength(level)
        except Exception:
            pass  # Non-critical — don't break the form

    # ------------------------------------------------------------------
    # Generate password inline
    # ------------------------------------------------------------------

    def _on_generate_password(self, e: ft.ControlEvent) -> None:
        """
        Generate a random password and insert it into the password field.

        Uses the PasswordGenerator with default settings (20 chars, all
        character types). For advanced generation, the user can visit the
        dedicated Generator page.
        """
        if not self.state.password_generator:
            show_snack_bar(self.state.page, "Password generator not available.")
            return

        try:
            # Generate with sensible defaults
            password = self.state.password_generator.generate_random(
                length=20,
                use_uppercase=True,
                use_lowercase=True,
                use_digits=True,
                use_symbols=True,
            )
            self._password_field.value = password
            self._update_strength(password)
            self.update()
        except Exception as ex:
            show_snack_bar(self.state.page, f"Generation failed: {ex}")

    # ------------------------------------------------------------------
    # Save entry
    # ------------------------------------------------------------------

    def _on_save(self, e: ft.ControlEvent) -> None:
        """Validate the form and save the entry."""
        website = self._website_field.value.strip() if self._website_field.value else ""
        username = self._username_field.value.strip() if self._username_field.value else ""
        password = self._password_field.value or ""
        remarks = self._remarks_field.value.strip() if self._remarks_field.value else ""
        is_favorite = self._favorite_switch.value

        # --- Validation ---
        if not website:
            self._show_error("Website / service name is required.")
            return
        if not password:
            self._show_error("Password is required.")
            return
        if not self._is_edit_mode and not username:
            self._show_error("Username is required for new entries.")
            return

        # Get master password for encryption
        master_password = self._master_password_field.value or None

        self._error_text.visible = False
        self._set_loading(True)

        # Run save in background thread
        thread = threading.Thread(
            target=self._save_background,
            args=(website, username, password, remarks, is_favorite, master_password),
            daemon=True,
        )
        thread.start()

    def _save_background(
        self,
        website: str,
        username: str,
        password: str,
        remarks: str,
        is_favorite: bool,
        master_password: Optional[str],
    ) -> None:
        """Background thread: create or update the entry via core."""
        try:
            if self._is_edit_mode:
                self.state.password_manager.update_password_entry(
                    session_id=self.state.session_id,
                    entry_id=self._entry_id,
                    website=website,
                    username=username,
                    password=password,
                    master_password=master_password,
                    remarks=remarks,
                    is_favorite=is_favorite,
                )
                self._on_save_success("Password updated.")
            else:
                self.state.password_manager.add_password_entry(
                    session_id=self.state.session_id,
                    website=website,
                    username=username,
                    password=password,
                    master_password=master_password,
                    remarks=remarks,
                    is_favorite=is_favorite,
                )
                self._on_save_success("Password saved.")

        except Exception as ex:
            error_msg = str(ex)
            # If the error is about master password, show the field
            if "master password" in error_msg.lower():
                self._master_password_field.visible = True
                self._show_error("Master password required. Please enter it below.")
            else:
                self._show_error(f"Save failed: {error_msg}")

            self._set_loading(False)

    def _on_save_success(self, message: str) -> None:
        """Navigate back to dashboard after successful save."""
        self._set_loading(False)
        try:
            show_snack_bar(self.state.page, message)
        except Exception:
            pass
        if self.state.navigate:
            self.state.navigate("/dashboard")

    # ------------------------------------------------------------------
    # Cancel
    # ------------------------------------------------------------------

    def _on_cancel(self, e: ft.ControlEvent) -> None:
        """Navigate back to the dashboard without saving."""
        if self.state.navigate:
            self.state.navigate("/dashboard")

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------

    def _show_error(self, message: str) -> None:
        """Display a validation or save error below the form."""
        self._error_text.value = message
        self._error_text.visible = True
        try:
            self.update()
        except Exception:
            pass

    def _set_loading(self, loading: bool) -> None:
        """Toggle the loading spinner and disable/enable the save button."""
        self._loading.visible = loading
        self._save_btn.disabled = loading
        try:
            self.update()
        except Exception:
            pass
