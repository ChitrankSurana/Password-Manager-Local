"""
Personal Password Manager - Dashboard Page
============================================

Main authenticated page showing the user's password entries in a scrollable
list. Includes:
- Navigation rail (sidebar) for switching sections
- Search bar with debounce filtering
- Age-category dropdown filter (All / Fresh / Moderate / Old)
- Sort toggle (oldest-first or newest-first)
- Password cards with copy, edit, delete actions
- Floating action button to add new entries
- Entry count and welcome header

Data flow:
    1. On mount, calls PasswordManagerCore.search_password_entries() in a
       background thread so the UI stays responsive.
    2. Results pass through filter_entries_by_age() and sort_entries_by_age()
       before being rendered as PasswordCard widgets.
    3. Search bar fires a debounced callback that re-fetches entries with
       a SearchCriteria.website filter.
    4. Deleting an entry shows a confirmation dialog, then reloads.

Version: 3.0.0
"""

import threading
from typing import List, Optional

import flet as ft

from ..components.confirm_dialog import show_confirm_dialog, show_snack_bar
from ..components.nav_rail import NavRail
from ..components.password_card import PasswordCard
from ..components.search_bar import SearchBar
from ..state import AppState


class DashboardPage(ft.Container):
    """
    Password list dashboard with search, filtering, and sorting.

    Layout:
        ┌──────────┬──────────────────────────────────────────┐
        │          │  Welcome header + entry count             │
        │  NavRail │  Search bar + filter dropdowns            │
        │          │  Scrollable list of PasswordCards         │
        │          │                            [+ FAB]        │
        └──────────┴──────────────────────────────────────────┘

    Args:
        state: The shared AppState object
    """

    def __init__(self, state: AppState):
        self.state = state
        self._entries: List = []           # All entries from the last fetch
        self._filtered_entries: List = []  # After age filter + sort
        self._search_query: str = ""       # Current search text
        self._age_filter: str = "all"      # Age category filter
        self._sort_oldest_first: bool = True  # Sort direction

        # --- Header: welcome text and entry count ---
        self._welcome_text = ft.Text(
            f"Welcome, {state.username or 'User'}",
            size=22,
            weight=ft.FontWeight.BOLD,
        )
        self._entry_count = ft.Text(
            "Loading...",
            size=13,
            opacity=0.7,
        )

        # --- Search bar ---
        self._search_bar = SearchBar(on_search=self._on_search)

        # --- Age filter dropdown ---
        self._age_dropdown = ft.Dropdown(
            label="Age Filter",
            value="all",
            width=150,
            options=[
                ft.dropdown.Option("all", "All"),
                ft.dropdown.Option("fresh", "Fresh (< 90d)"),
                ft.dropdown.Option("moderate", "Moderate (90-180d)"),
                ft.dropdown.Option("old", "Old (> 180d)"),
            ],
            on_change=self._on_age_filter_change,
            dense=True,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=4),
        )

        # --- Sort toggle button ---
        self._sort_btn = ft.IconButton(
            icon=ft.Icons.ARROW_DOWNWARD,
            tooltip="Sort: Oldest first",
            on_click=self._on_sort_toggle,
        )

        # --- Password list (scrollable) ---
        self._password_list = ft.ListView(
            spacing=8,
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            expand=True,
        )

        # --- Loading indicator (shown while fetching) ---
        self._loading = ft.ProgressRing(visible=False, width=30, height=30)

        # --- Empty state message ---
        self._empty_state = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.LOCK_OPEN, size=64, opacity=0.3),
                    ft.Text(
                        "No passwords yet",
                        size=18,
                        weight=ft.FontWeight.W_500,
                        opacity=0.5,
                    ),
                    ft.Text(
                        "Click the + button to add your first password.",
                        size=13,
                        opacity=0.4,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.alignment.center,
            expand=True,
            visible=False,
        )

        # --- Floating action button for adding passwords ---
        fab = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            tooltip="Add password",
            on_click=self._on_add_click,
        )

        # --- Build the main content area (right of nav rail) ---
        content_area = ft.Column(
            [
                # Top header row
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Column(
                                [self._welcome_text, self._entry_count],
                                spacing=2,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=ft.padding.only(left=16, right=16, top=16, bottom=8),
                ),
                # Search and filter row
                ft.Container(
                    content=ft.Row(
                        [
                            self._search_bar,
                            self._age_dropdown,
                            self._sort_btn,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=4),
                ),
                # Loading indicator (centered)
                ft.Container(
                    content=self._loading,
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(top=20),
                ),
                # Password list or empty state
                ft.Stack(
                    [
                        self._password_list,
                        self._empty_state,
                    ],
                    expand=True,
                ),
            ],
            expand=True,
        )

        # --- Combine nav rail + content area ---
        nav_rail = NavRail(state=state, current_route="/dashboard")

        super().__init__(
            content=ft.Row(
                [
                    nav_rail,
                    ft.VerticalDivider(width=1),
                    # Content area with FAB overlay
                    ft.Stack(
                        [
                            content_area,
                            ft.Container(
                                content=fab,
                                alignment=ft.alignment.bottom_right,
                                padding=ft.padding.all(20),
                            ),
                        ],
                        expand=True,
                    ),
                ],
                expand=True,
            ),
            expand=True,
        )

        # Load entries on creation
        self._load_entries()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_entries(self) -> None:
        """
        Fetch password entries from core in a background thread.

        Uses search_password_entries() with an optional website filter
        when the user has typed a search query. Results are stored in
        self._entries and then filtered/sorted before display.
        """
        self._loading.visible = True
        self._password_list.controls.clear()
        self._empty_state.visible = False

        # Safe UI update — only call if the control is mounted
        try:
            self.update()
        except Exception:
            pass

        thread = threading.Thread(target=self._fetch_entries_background, daemon=True)
        thread.start()

    def _fetch_entries_background(self) -> None:
        """Background thread: fetch entries from PasswordManagerCore."""
        try:
            # Import SearchCriteria locally to avoid circular imports at module level
            from core.password_manager import SearchCriteria

            # Build search criteria
            criteria = SearchCriteria()
            if self._search_query:
                criteria.website = self._search_query

            entries = self.state.password_manager.search_password_entries(
                session_id=self.state.session_id,
                criteria=criteria,
                include_passwords=True,  # Need passwords for copy action
            )

            # Update UI on the Flet thread
            self._on_entries_loaded(entries)

        except Exception as ex:
            self._on_load_error(str(ex))

    def _on_entries_loaded(self, entries: list) -> None:
        """Process and display loaded entries (called from background thread)."""
        self._entries = entries

        # Apply age-based filtering and sorting via core methods
        self._apply_filters_and_display()

    def _on_load_error(self, message: str) -> None:
        """Handle entry loading failure."""
        self._loading.visible = False
        self._entry_count.value = "Failed to load passwords"

        try:
            self.update()
        except Exception:
            pass

        # Show error snack bar
        try:
            show_snack_bar(self.state.page, f"Error: {message}")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Filtering and display
    # ------------------------------------------------------------------

    def _apply_filters_and_display(self) -> None:
        """
        Apply the current age filter and sort order to self._entries,
        then rebuild the password card list.
        """
        from core.password_manager import PasswordManagerCore

        # 1. Filter by age category
        filtered = PasswordManagerCore.filter_entries_by_age(
            self._entries, self._age_filter
        )

        # 2. Sort by age
        sorted_entries = PasswordManagerCore.sort_entries_by_age(
            filtered, oldest_first=self._sort_oldest_first
        )

        self._filtered_entries = sorted_entries

        # Rebuild the list of PasswordCard widgets
        self._password_list.controls.clear()

        for entry in sorted_entries:
            card = PasswordCard(
                entry=entry,
                on_edit=self._on_edit_entry,
                on_delete=self._on_delete_entry,
                on_copy=self._on_copy_password,
            )
            self._password_list.controls.append(card)

        # Update counts and visibility
        total = len(self._entries)
        shown = len(sorted_entries)
        if total == shown:
            self._entry_count.value = f"{total} password{'s' if total != 1 else ''}"
        else:
            self._entry_count.value = (
                f"Showing {shown} of {total} password{'s' if total != 1 else ''}"
            )

        self._loading.visible = False
        self._empty_state.visible = shown == 0
        self._password_list.visible = shown > 0

        try:
            self.update()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Search callback (from SearchBar debounce)
    # ------------------------------------------------------------------

    def _on_search(self, query: str) -> None:
        """
        Called by SearchBar after the debounce delay.

        Updates the search query and re-fetches entries from the core.
        If the query is empty, all entries are returned.
        """
        self._search_query = query.strip()
        self._load_entries()

    # ------------------------------------------------------------------
    # Filter and sort callbacks
    # ------------------------------------------------------------------

    def _on_age_filter_change(self, e: ft.ControlEvent) -> None:
        """Handle age filter dropdown change."""
        self._age_filter = e.control.value
        # No need to re-fetch — just re-filter the existing entries
        self._apply_filters_and_display()

    def _on_sort_toggle(self, e: ft.ControlEvent) -> None:
        """Toggle sort direction between oldest-first and newest-first."""
        self._sort_oldest_first = not self._sort_oldest_first

        if self._sort_oldest_first:
            self._sort_btn.icon = ft.Icons.ARROW_DOWNWARD
            self._sort_btn.tooltip = "Sort: Oldest first"
        else:
            self._sort_btn.icon = ft.Icons.ARROW_UPWARD
            self._sort_btn.tooltip = "Sort: Newest first"

        # Re-sort without re-fetching
        self._apply_filters_and_display()

    # ------------------------------------------------------------------
    # Card action callbacks
    # ------------------------------------------------------------------

    def _on_add_click(self, e: ft.ControlEvent) -> None:
        """Navigate to the add-password page."""
        if self.state.navigate:
            self.state.navigate("/add")

    def _on_edit_entry(self, entry_id: int) -> None:
        """Navigate to the edit page for a specific entry."""
        if self.state.navigate:
            self.state.navigate(f"/edit/{entry_id}")

    def _on_delete_entry(self, entry_id: int) -> None:
        """
        Show a confirmation dialog before deleting a password entry.

        The actual deletion happens in _confirm_delete() after the user
        confirms.
        """
        show_confirm_dialog(
            page=self.state.page,
            title="Delete Password",
            message="Are you sure you want to delete this password entry? This action cannot be undone.",
            on_confirm=lambda: self._confirm_delete(entry_id),
            confirm_text="Delete",
            destructive=True,
        )

    def _confirm_delete(self, entry_id: int) -> None:
        """
        Delete an entry after user confirmation.

        Calls PasswordManagerCore.delete_password_entry() and reloads
        the list on success.
        """
        try:
            self.state.password_manager.delete_password_entry(
                session_id=self.state.session_id,
                entry_id=entry_id,
            )
            show_snack_bar(self.state.page, "Password deleted.")
            # Reload the list
            self._load_entries()
        except Exception as ex:
            show_snack_bar(self.state.page, f"Delete failed: {ex}")

    def _on_copy_password(self, password: str) -> None:
        """
        Copy a password to the system clipboard.

        Uses Flet's page.set_clipboard() API which works in both desktop
        and web modes.
        """
        if password:
            try:
                self.state.page.set_clipboard(password)
                show_snack_bar(self.state.page, "Password copied to clipboard.")
            except Exception:
                show_snack_bar(self.state.page, "Failed to copy password.")
