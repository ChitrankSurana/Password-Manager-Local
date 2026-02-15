"""
Personal Password Manager - Backup / Import / Export Page
==========================================================

Provides database backup/restore and password import/export functionality:

1. **Backup**: One-click database backup via BackupManager.create_database_backup()
2. **Restore**: Select a backup file and restore (with confirmation)
3. **Export Encrypted**: Export all passwords as encrypted JSON
4. **Export CSV**: Export as plaintext CSV (requires confirmation gate)
5. **Import CSV**: Import from browser CSV (Chrome/Firefox/Edge)

Flet's FilePicker is used for file selection dialogs in both desktop and web
modes. Destructive operations (restore, plaintext export) use confirmation
dialogs.

Version: 3.0.0
"""

import threading
from typing import Optional

import flet as ft

from ..components.confirm_dialog import show_confirm_dialog, show_snack_bar
from ..components.nav_rail import NavRail
from ..state import AppState


class BackupPage(ft.Container):
    """
    Backup, restore, import, and export page.

    Args:
        state: The shared AppState object
    """

    def __init__(self, state: AppState):
        self.state = state

        # --- File picker (hidden; used for import/restore file selection) ---
        self._file_picker = ft.FilePicker(on_result=self._on_file_picked)
        self._pending_action: Optional[str] = None  # "import" or "restore"

        # --- Master password field (needed for export/import encryption) ---
        self._master_pw_field = ft.TextField(
            label="Master Password",
            prefix_icon=ft.Icons.KEY,
            password=True,
            can_reveal_password=True,
            width=350,
            hint_text="Required for export and import operations",
        )

        # --- Loading & status ---
        self._loading = ft.ProgressRing(visible=False, width=24, height=24)
        self._status_text = ft.Text("", size=13, visible=False)

        # --- Backup section ---
        backup_section = ft.ExpansionTile(
            title=ft.Text("Database Backup", weight=ft.FontWeight.W_600),
            subtitle=ft.Text("Create a full database backup"),
            leading=ft.Icon(ft.Icons.BACKUP),
            initially_expanded=True,
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Creates a copy of the entire database file. "
                                "Backups are saved to the /backups directory.",
                                size=13,
                                opacity=0.7,
                            ),
                            ft.FilledButton(
                                text="Create Backup",
                                icon=ft.Icons.SAVE,
                                on_click=self._on_create_backup,
                                width=180,
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                ),
            ],
        )

        # --- Restore section ---
        restore_section = ft.ExpansionTile(
            title=ft.Text("Restore from Backup", weight=ft.FontWeight.W_600),
            subtitle=ft.Text("Restore the database from a .db backup file"),
            leading=ft.Icon(ft.Icons.RESTORE),
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Select a backup file to restore. This will REPLACE the "
                                "current database — make a backup first!",
                                size=13,
                                color=ft.Colors.ORANGE,
                            ),
                            ft.OutlinedButton(
                                text="Select Backup File",
                                icon=ft.Icons.FOLDER_OPEN,
                                on_click=self._on_restore_pick,
                                width=200,
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                ),
            ],
        )

        # --- Export section ---
        export_section = ft.ExpansionTile(
            title=ft.Text("Export Passwords", weight=ft.FontWeight.W_600),
            subtitle=ft.Text("Export encrypted JSON or plaintext CSV"),
            leading=ft.Icon(ft.Icons.FILE_DOWNLOAD),
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            self._master_pw_field,
                            ft.Row(
                                [
                                    ft.FilledButton(
                                        text="Export Encrypted (JSON)",
                                        icon=ft.Icons.ENHANCED_ENCRYPTION,
                                        on_click=self._on_export_encrypted,
                                        width=230,
                                    ),
                                    ft.OutlinedButton(
                                        text="Export Plain CSV",
                                        icon=ft.Icons.WARNING_AMBER,
                                        on_click=self._on_export_csv_click,
                                        width=200,
                                    ),
                                ],
                                spacing=8,
                                wrap=True,
                            ),
                            ft.Text(
                                "Plain CSV exports passwords in cleartext. "
                                "Use only for migration purposes.",
                                size=11,
                                color=ft.Colors.ORANGE,
                                opacity=0.8,
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                ),
            ],
        )

        # --- Import section ---
        # Browser type dropdown
        self._browser_dropdown = ft.Dropdown(
            label="Browser",
            value="chrome",
            width=180,
            options=[
                ft.dropdown.Option("chrome", "Chrome"),
                ft.dropdown.Option("firefox", "Firefox"),
                ft.dropdown.Option("edge", "Edge"),
            ],
        )

        import_section = ft.ExpansionTile(
            title=ft.Text("Import Passwords", weight=ft.FontWeight.W_600),
            subtitle=ft.Text("Import from browser CSV export"),
            leading=ft.Icon(ft.Icons.FILE_UPLOAD),
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Import passwords from a browser CSV export. "
                                "The master password field above is required.",
                                size=13,
                                opacity=0.7,
                            ),
                            ft.Row(
                                [
                                    self._browser_dropdown,
                                    ft.FilledButton(
                                        text="Select CSV File",
                                        icon=ft.Icons.UPLOAD_FILE,
                                        on_click=self._on_import_pick,
                                        width=180,
                                    ),
                                ],
                                spacing=8,
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                ),
            ],
        )

        # --- Build page ---
        content_area = ft.Column(
            [
                ft.Text("Backup & Import/Export", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=1),
                # Status row
                ft.Row(
                    [self._loading, self._status_text],
                    spacing=8,
                ),
                backup_section,
                restore_section,
                export_section,
                import_section,
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        nav_rail = NavRail(state=state, current_route="/backup")

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

        # Register the file picker with the page overlay so it can open dialogs
        state.page.overlay.append(self._file_picker)
        state.page.update()

    # ------------------------------------------------------------------
    # Backup
    # ------------------------------------------------------------------

    def _on_create_backup(self, e: ft.ControlEvent) -> None:
        """Create a database backup."""
        self._set_status("Creating backup...", loading=True)

        def run():
            try:
                path = self.state.backup_manager.create_database_backup()
                self._set_status(f"Backup saved: {path}", loading=False)
                show_snack_bar(self.state.page, "Backup created successfully.")
            except Exception as ex:
                self._set_status(f"Backup failed: {ex}", loading=False)

        threading.Thread(target=run, daemon=True).start()

    # ------------------------------------------------------------------
    # Restore
    # ------------------------------------------------------------------

    def _on_restore_pick(self, e: ft.ControlEvent) -> None:
        """Open file picker for restore."""
        self._pending_action = "restore"
        self._file_picker.pick_files(
            dialog_title="Select Backup File",
            allowed_extensions=["db"],
        )

    def _confirm_restore(self, path: str) -> None:
        """Show confirmation before restoring."""
        show_confirm_dialog(
            page=self.state.page,
            title="Restore Backup",
            message=(
                "This will REPLACE the current database with the backup. "
                "All current data will be lost. Are you sure?"
            ),
            on_confirm=lambda: self._do_restore(path),
            confirm_text="Restore",
            destructive=True,
        )

    def _do_restore(self, path: str) -> None:
        """Run the restore operation."""
        self._set_status("Restoring...", loading=True)

        def run():
            try:
                self.state.backup_manager.restore_database_backup(
                    path, confirm_restore=True,
                )
                self._set_status("Restore complete. Please restart the app.", loading=False)
                show_snack_bar(self.state.page, "Database restored. Please restart.")
            except Exception as ex:
                self._set_status(f"Restore failed: {ex}", loading=False)

        threading.Thread(target=run, daemon=True).start()

    # ------------------------------------------------------------------
    # Export encrypted
    # ------------------------------------------------------------------

    def _on_export_encrypted(self, e: ft.ControlEvent) -> None:
        """Export passwords as encrypted JSON."""
        master_pw = self._master_pw_field.value
        if not master_pw:
            show_snack_bar(self.state.page, "Master password is required for export.")
            return

        self._set_status("Exporting encrypted data...", loading=True)

        def run():
            try:
                path = self.state.backup_manager.export_encrypted_data(
                    user_id=self.state.user_id,
                    username=self.state.username,
                    master_password=master_pw,
                )
                self._set_status(f"Encrypted export saved: {path}", loading=False)
                show_snack_bar(self.state.page, "Encrypted export complete.")
            except Exception as ex:
                self._set_status(f"Export failed: {ex}", loading=False)

        threading.Thread(target=run, daemon=True).start()

    # ------------------------------------------------------------------
    # Export plain CSV (with confirmation gate)
    # ------------------------------------------------------------------

    def _on_export_csv_click(self, e: ft.ControlEvent) -> None:
        """Show warning dialog before plaintext export."""
        master_pw = self._master_pw_field.value
        if not master_pw:
            show_snack_bar(self.state.page, "Master password is required for export.")
            return

        show_confirm_dialog(
            page=self.state.page,
            title="Plaintext Export Warning",
            message=(
                "This will create a CSV file with ALL passwords in UNENCRYPTED "
                "cleartext. Anyone with access to this file can read your passwords. "
                "Proceed only if you understand the risk."
            ),
            on_confirm=lambda: self._do_export_csv(master_pw),
            confirm_text="Export Plaintext",
            destructive=True,
        )

    def _do_export_csv(self, master_pw: str) -> None:
        """Run the plaintext CSV export."""
        self._set_status("Exporting plaintext CSV...", loading=True)

        def run():
            try:
                from datetime import datetime as dt
                output_path = f"exports/passwords_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv"
                self.state.backup_manager.export_plain_csv(
                    user_id=self.state.user_id,
                    username=self.state.username,
                    master_password=master_pw,
                    output_path=output_path,
                    confirm_plaintext=True,
                )
                self._set_status(f"CSV exported: {output_path}", loading=False)
                show_snack_bar(self.state.page, "Plaintext CSV exported.")
            except Exception as ex:
                self._set_status(f"Export failed: {ex}", loading=False)

        threading.Thread(target=run, daemon=True).start()

    # ------------------------------------------------------------------
    # Import from browser CSV
    # ------------------------------------------------------------------

    def _on_import_pick(self, e: ft.ControlEvent) -> None:
        """Open file picker for CSV import."""
        self._pending_action = "import"
        self._file_picker.pick_files(
            dialog_title="Select Browser CSV File",
            allowed_extensions=["csv"],
        )

    def _do_import(self, csv_path: str) -> None:
        """Run the import operation."""
        master_pw = self._master_pw_field.value
        if not master_pw:
            show_snack_bar(self.state.page, "Master password is required for import.")
            return

        browser = self._browser_dropdown.value or "chrome"
        self._set_status(f"Importing from {browser} CSV...", loading=True)

        def run():
            try:
                result = self.state.backup_manager.import_browser_passwords(
                    user_id=self.state.user_id,
                    master_password=master_pw,
                    browser_type=browser,
                    csv_file_path=csv_path,
                )
                imported = result.get("imported", 0)
                skipped = result.get("skipped", 0)
                self._set_status(
                    f"Import complete: {imported} imported, {skipped} skipped.",
                    loading=False,
                )
                show_snack_bar(self.state.page, f"Imported {imported} passwords.")
            except Exception as ex:
                self._set_status(f"Import failed: {ex}", loading=False)

        threading.Thread(target=run, daemon=True).start()

    # ------------------------------------------------------------------
    # File picker callback (shared between import and restore)
    # ------------------------------------------------------------------

    def _on_file_picked(self, e: ft.FilePickerResultEvent) -> None:
        """Handle file picker result."""
        if not e.files or len(e.files) == 0:
            return  # User cancelled

        file_path = e.files[0].path
        if not file_path:
            return

        if self._pending_action == "restore":
            self._confirm_restore(file_path)
        elif self._pending_action == "import":
            self._do_import(file_path)

        self._pending_action = None

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    def _set_status(self, message: str, loading: bool = False) -> None:
        """Update the status text and loading indicator."""
        self._status_text.value = message
        self._status_text.visible = True
        self._loading.visible = loading
        try:
            self.update()
        except Exception:
            pass
