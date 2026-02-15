"""
Personal Password Manager - Login Page
========================================

Handles user authentication (login) and account creation (register).
After a successful login, checks if AES-CBC to AES-GCM migration is
needed and shows a progress dialog if so.

Flow:
    1. User enters credentials
    2. On login success: store session in AppState
    3. Check needs_encryption_migration() via PasswordManagerCore
    4. If migration needed: show MigrationDialog with progress bar
    5. Navigate to /dashboard

Version: 3.0.0
"""

import flet as ft
from typing import Optional

from ..state import AppState


class LoginPage(ft.Container):
    """
    Login and registration page.

    Displays a centered card with username/password fields, a login button,
    and a toggle to switch to registration mode. Error messages are shown
    via a snack bar.

    Args:
        state: The shared AppState object
    """

    def __init__(self, state: AppState):
        self.state = state
        self._is_register_mode = False

        # --- Form fields ---
        self._username_field = ft.TextField(
            label="Username",
            prefix_icon=ft.Icons.PERSON,
            autofocus=True,
            on_submit=self._on_submit,
        )

        self._password_field = ft.TextField(
            label="Master Password",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            on_submit=self._on_submit,
        )

        self._confirm_password_field = ft.TextField(
            label="Confirm Password",
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            password=True,
            can_reveal_password=True,
            visible=False,
            on_submit=self._on_submit,
        )

        # --- Buttons ---
        self._submit_btn = ft.FilledButton(
            text="Login",
            icon=ft.Icons.LOGIN,
            on_click=self._on_submit,
            width=200,
        )

        self._toggle_btn = ft.TextButton(
            text="Don't have an account? Register",
            on_click=self._toggle_mode,
        )

        # --- Error display ---
        self._error_text = ft.Text(
            value="",
            color=ft.Colors.RED,
            size=13,
            visible=False,
        )

        # --- Loading indicator ---
        self._loading = ft.ProgressRing(visible=False, width=20, height=20)

        # --- Page title ---
        self._title = ft.Text(
            "Login",
            size=28,
            weight=ft.FontWeight.BOLD,
        )

        # --- Build the card layout ---
        card_content = ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.SHIELD, size=48),
                            ft.Text(
                                "Personal Password Manager",
                                size=22,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    padding=ft.padding.only(bottom=20),
                ),
                self._title,
                self._username_field,
                self._password_field,
                self._confirm_password_field,
                self._error_text,
                ft.Container(
                    content=ft.Row(
                        [self._submit_btn, self._loading],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    padding=ft.padding.only(top=10),
                ),
                ft.Container(
                    content=self._toggle_btn,
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(top=10),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            width=400,
        )

        super().__init__(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Card(
                            content=ft.Container(
                                content=card_content,
                                padding=ft.padding.all(40),
                            ),
                            elevation=4,
                        ),
                        alignment=ft.alignment.center,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            ),
            expand=True,
        )

    def _toggle_mode(self, e: ft.ControlEvent) -> None:
        """Toggle between login and register modes."""
        self._is_register_mode = not self._is_register_mode
        self._error_text.visible = False

        if self._is_register_mode:
            self._title.value = "Register"
            self._submit_btn.text = "Create Account"
            self._submit_btn.icon = ft.Icons.PERSON_ADD
            self._toggle_btn.text = "Already have an account? Login"
            self._confirm_password_field.visible = True
        else:
            self._title.value = "Login"
            self._submit_btn.text = "Login"
            self._submit_btn.icon = ft.Icons.LOGIN
            self._toggle_btn.text = "Don't have an account? Register"
            self._confirm_password_field.visible = False

        self.update()

    def _on_submit(self, e: ft.ControlEvent) -> None:
        """Handle form submission (login or register)."""
        username = self._username_field.value.strip()
        password = self._password_field.value

        # Basic validation
        if not username or not password:
            self._show_error("Username and password are required.")
            return

        if self._is_register_mode:
            self._handle_register(username, password)
        else:
            self._handle_login(username, password)

    def _handle_login(self, username: str, password: str) -> None:
        """Attempt to authenticate the user."""
        self._set_loading(True)
        self._error_text.visible = False

        try:
            # Authenticate via the core AuthenticationManager
            session_id = self.state.auth_manager.authenticate_user(
                username, password
            )

            if session_id:
                # Get user info for the session
                session_info = self.state.auth_manager.get_session_info(session_id)
                user_id = session_info.get("user_id") if session_info else None

                # Store session in app state
                self.state.login(
                    session_id=session_id,
                    username=username,
                    user_id=user_id,
                    master_password=password,
                )

                # Cache master password in PasswordManagerCore
                try:
                    self.state.password_manager._cache_master_password(
                        session_id, password
                    )
                except Exception:
                    pass  # Non-critical

                # Check if encryption migration is needed
                self._check_migration_and_navigate()
            else:
                self._show_error("Invalid username or password.")
        except Exception as ex:
            self._show_error(f"Login failed: {str(ex)}")
        finally:
            self._set_loading(False)

    def _handle_register(self, username: str, password: str) -> None:
        """Create a new user account."""
        confirm = self._confirm_password_field.value

        if password != confirm:
            self._show_error("Passwords do not match.")
            return

        self._set_loading(True)
        self._error_text.visible = False

        try:
            # Create the user account
            self.state.auth_manager.create_user_account(username, password)

            # Show success and switch to login mode
            self._is_register_mode = False
            self._toggle_mode(None)
            self._show_success("Account created! Please log in.")
        except Exception as ex:
            self._show_error(str(ex))
        finally:
            self._set_loading(False)

    def _check_migration_and_navigate(self) -> None:
        """
        Check if AES-CBC -> AES-GCM migration is needed.

        If migration is needed, show a progress dialog. Otherwise,
        navigate directly to the dashboard.
        """
        try:
            needs_migration = self.state.password_manager.needs_encryption_migration(
                self.state.session_id
            )
        except Exception:
            needs_migration = False

        if needs_migration:
            self._show_migration_dialog()
        else:
            # Clear master password from state (no longer needed)
            self.state.clear_master_password()
            if self.state.navigate:
                self.state.navigate("/dashboard")

    def _show_migration_dialog(self) -> None:
        """
        Show the AES-CBC -> AES-GCM migration progress dialog.

        Runs the migration in a background thread and updates the
        progress bar as entries are re-encrypted.
        """
        progress_bar = ft.ProgressBar(width=400, value=0)
        status_text = ft.Text("Upgrading encryption...", size=14)
        count_text = ft.Text("", size=12)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Encryption Upgrade"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "Your passwords are being upgraded from AES-CBC to "
                            "AES-256-GCM for stronger security. This is a one-time "
                            "operation.",
                            size=13,
                        ),
                        ft.Container(height=16),
                        progress_bar,
                        status_text,
                        count_text,
                    ],
                    spacing=8,
                    width=400,
                ),
                padding=ft.padding.all(10),
            ),
        )

        self.state.page.overlay.append(dialog)
        dialog.open = True
        self.state.page.update()

        def progress_callback(current: int, total: int) -> None:
            """Update progress bar from the migration thread."""
            if total > 0:
                progress_bar.value = current / total
            count_text.value = f"{current} / {total} entries"
            self.state.page.update()

        def run_migration() -> None:
            """Run the migration in a background thread."""
            try:
                self.state.password_manager.migrate_all_entries_to_gcm(
                    session_id=self.state.session_id,
                    master_password=self.state.master_password,
                    progress_callback=progress_callback,
                )
                status_text.value = "Upgrade complete!"
                progress_bar.value = 1.0
                self.state.page.update()

                # Brief pause so the user sees "complete"
                import time
                time.sleep(1)

                # Close dialog and navigate
                dialog.open = False
                self.state.page.update()
                self.state.clear_master_password()
                if self.state.navigate:
                    self.state.navigate("/dashboard")

            except Exception as ex:
                status_text.value = f"Migration failed: {ex}"
                status_text.color = ft.Colors.RED
                self.state.page.update()

        # Run migration in background thread to keep UI responsive
        import threading
        migration_thread = threading.Thread(target=run_migration, daemon=True)
        migration_thread.start()

    def _show_error(self, message: str) -> None:
        """Display an error message below the form fields."""
        self._error_text.value = message
        self._error_text.visible = True
        self._error_text.color = ft.Colors.RED
        self.update()

    def _show_success(self, message: str) -> None:
        """Display a success message below the form fields."""
        self._error_text.value = message
        self._error_text.visible = True
        self._error_text.color = ft.Colors.GREEN
        self.update()

    def _set_loading(self, loading: bool) -> None:
        """Show or hide the loading indicator."""
        self._loading.visible = loading
        self._submit_btn.disabled = loading
        self.update()
