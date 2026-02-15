"""
Personal Password Manager - Settings Page
===========================================

User preferences and security settings. Organized into expandable sections:

1. **Appearance**: Color scheme picker and dark/light mode toggle.
   Changes are applied immediately via apply_theme().

2. **Security**: Change master password form with current + new + confirm
   fields. Calls AuthenticationManager.change_master_password().

3. **About**: Version info and links.

The page uses ExpansionTile so users can focus on one section at a time.

Version: 3.0.0
"""

import threading
import flet as ft

from ..components.confirm_dialog import show_snack_bar
from ..components.nav_rail import NavRail
from ..state import AppState
from ..theme import THEME_COLORS, apply_theme


class SettingsPage(ft.Container):
    """
    Settings page with appearance and security sections.

    Args:
        state: The shared AppState object
    """

    def __init__(self, state: AppState):
        self.state = state

        # ---- Appearance section ----

        # Color scheme radio buttons
        current_scheme = state.settings.get("color_scheme", "blue")
        self._scheme_group = ft.RadioGroup(
            value=current_scheme,
            on_change=self._on_scheme_change,
            content=ft.Row(
                [
                    ft.Radio(value=name, label=name.capitalize())
                    for name in THEME_COLORS
                ],
                wrap=True,
                spacing=16,
            ),
        )

        # Dark mode toggle
        is_dark = state.page.theme_mode == ft.ThemeMode.DARK
        self._dark_mode_switch = ft.Switch(
            label="Dark mode",
            value=is_dark,
            on_change=self._on_dark_mode_change,
        )

        appearance_section = ft.ExpansionTile(
            title=ft.Text("Appearance", weight=ft.FontWeight.W_600),
            subtitle=ft.Text("Theme color and dark/light mode"),
            leading=ft.Icon(ft.Icons.PALETTE),
            initially_expanded=True,
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Color Scheme", size=14, weight=ft.FontWeight.W_500),
                            self._scheme_group,
                            ft.Container(height=8),
                            self._dark_mode_switch,
                        ],
                        spacing=8,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                ),
            ],
        )

        # ---- Security section ----
        self._current_password_field = ft.TextField(
            label="Current Master Password",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            width=400,
        )
        self._new_password_field = ft.TextField(
            label="New Master Password",
            prefix_icon=ft.Icons.LOCK_RESET,
            password=True,
            can_reveal_password=True,
            width=400,
        )
        self._confirm_password_field = ft.TextField(
            label="Confirm New Password",
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            password=True,
            can_reveal_password=True,
            width=400,
        )

        self._change_pw_btn = ft.FilledButton(
            text="Change Password",
            icon=ft.Icons.SECURITY,
            on_click=self._on_change_password,
            width=200,
        )
        self._change_pw_loading = ft.ProgressRing(visible=False, width=20, height=20)
        self._change_pw_error = ft.Text(
            value="", color=ft.Colors.RED, size=13, visible=False,
        )

        security_section = ft.ExpansionTile(
            title=ft.Text("Security", weight=ft.FontWeight.W_600),
            subtitle=ft.Text("Change master password"),
            leading=ft.Icon(ft.Icons.SECURITY),
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Change your master password. All stored passwords "
                                "will be re-encrypted with the new key.",
                                size=13,
                                opacity=0.7,
                            ),
                            self._current_password_field,
                            self._new_password_field,
                            self._confirm_password_field,
                            self._change_pw_error,
                            ft.Row(
                                [self._change_pw_btn, self._change_pw_loading],
                                spacing=8,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                ),
            ],
        )

        # ---- About section ----
        about_section = ft.ExpansionTile(
            title=ft.Text("About", weight=ft.FontWeight.W_600),
            subtitle=ft.Text("Version and info"),
            leading=ft.Icon(ft.Icons.INFO_OUTLINE),
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Personal Password Manager", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text("Version 3.0.0", size=13, opacity=0.7),
                            ft.Text(
                                "A secure, local-first password manager with "
                                "AES-256-GCM encryption.",
                                size=13,
                                opacity=0.6,
                            ),
                        ],
                        spacing=4,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                ),
            ],
        )

        # ---- Build page ----
        content_area = ft.Column(
            [
                ft.Text("Settings", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=1),
                appearance_section,
                security_section,
                about_section,
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        nav_rail = NavRail(state=state, current_route="/settings")

        super().__init__(
            content=ft.Row(
                [
                    nav_rail,
                    ft.VerticalDivider(width=1),
                    ft.Container(
                        content=content_area,
                        padding=ft.padding.all(24),
                        expand=True,
                    ),
                ],
                expand=True,
            ),
            expand=True,
        )

    # ------------------------------------------------------------------
    # Appearance callbacks
    # ------------------------------------------------------------------

    def _on_scheme_change(self, e: ft.ControlEvent) -> None:
        """Apply the selected color scheme immediately."""
        scheme = e.control.value
        is_dark = self._dark_mode_switch.value
        apply_theme(self.state.page, color_scheme=scheme, dark_mode=is_dark)

        # Persist preference in app state
        self.state.settings["color_scheme"] = scheme

    def _on_dark_mode_change(self, e: ft.ControlEvent) -> None:
        """Toggle dark/light mode immediately."""
        is_dark = e.control.value
        scheme = self._scheme_group.value or "blue"
        apply_theme(self.state.page, color_scheme=scheme, dark_mode=is_dark)

        # Persist preference in app state
        self.state.settings["dark_mode"] = is_dark

    # ------------------------------------------------------------------
    # Change master password
    # ------------------------------------------------------------------

    def _on_change_password(self, e: ft.ControlEvent) -> None:
        """Validate inputs and change the master password."""
        current = self._current_password_field.value or ""
        new_pw = self._new_password_field.value or ""
        confirm = self._confirm_password_field.value or ""

        # Client-side validation
        if not current or not new_pw or not confirm:
            self._show_pw_error("All three fields are required.")
            return

        if new_pw != confirm:
            self._show_pw_error("New passwords do not match.")
            return

        if current == new_pw:
            self._show_pw_error("New password must be different from the current one.")
            return

        self._change_pw_error.visible = False
        self._change_pw_loading.visible = True
        self._change_pw_btn.disabled = True
        self.update()

        # Run in background so UI stays responsive during re-encryption
        thread = threading.Thread(
            target=self._change_password_background,
            args=(current, new_pw),
            daemon=True,
        )
        thread.start()

    def _change_password_background(self, current: str, new_pw: str) -> None:
        """Background: call auth_manager.change_master_password()."""
        try:
            self.state.auth_manager.change_master_password(
                session_id=self.state.session_id,
                current_password=current,
                new_password=new_pw,
            )
            # Success — clear fields and show confirmation
            self._current_password_field.value = ""
            self._new_password_field.value = ""
            self._confirm_password_field.value = ""
            self._change_pw_loading.visible = False
            self._change_pw_btn.disabled = False

            try:
                self.update()
            except Exception:
                pass

            show_snack_bar(self.state.page, "Master password changed successfully.")

        except Exception as ex:
            self._change_pw_loading.visible = False
            self._change_pw_btn.disabled = False
            self._show_pw_error(str(ex))

    def _show_pw_error(self, message: str) -> None:
        """Display an error below the change-password form."""
        self._change_pw_error.value = message
        self._change_pw_error.visible = True
        self._change_pw_loading.visible = False
        self._change_pw_btn.disabled = False
        try:
            self.update()
        except Exception:
            pass
