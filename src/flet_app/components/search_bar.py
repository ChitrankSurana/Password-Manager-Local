"""
Search Bar Component
=====================

Search input with debounce for filtering password entries. The debounce
prevents excessive filtering calls while the user is still typing — the
callback only fires after the user stops typing for DEBOUNCE_MS.

Usage:
    search = SearchBar(on_search=lambda query: print(query))
    # Callback fires 300ms after the user stops typing

Version: 3.0.0
"""

import flet as ft
from typing import Callable, Optional
import threading


# Default debounce delay in seconds
DEBOUNCE_SECONDS = 0.3


class SearchBar(ft.TextField):
    """
    Search text field with built-in debounce.

    Args:
        on_search: Callback receiving the search query string.
                   Called after DEBOUNCE_SECONDS of inactivity.
        hint_text: Placeholder text shown when the field is empty
    """

    def __init__(
        self,
        on_search: Optional[Callable[[str], None]] = None,
        hint_text: str = "Search passwords...",
    ):
        self._on_search = on_search
        self._debounce_timer: Optional[threading.Timer] = None

        super().__init__(
            hint_text=hint_text,
            prefix_icon=ft.Icons.SEARCH,
            suffix_icon=ft.Icons.CLEAR,
            on_change=self._on_change,
            on_submit=self._on_submit,
            border_radius=25,
            content_padding=ft.padding.symmetric(horizontal=16, vertical=8),
            expand=True,
        )

        # Wire up the clear button
        self.suffix = ft.IconButton(
            icon=ft.Icons.CLEAR,
            icon_size=16,
            on_click=self._clear,
            visible=False,
        )

    def _on_change(self, e: ft.ControlEvent) -> None:
        """Handle text change with debounce."""
        query = e.control.value.strip()

        # Show/hide clear button
        if self.suffix:
            self.suffix.visible = len(query) > 0
            self.suffix.update()

        # Cancel previous debounce timer
        if self._debounce_timer:
            self._debounce_timer.cancel()

        # Start new debounce timer
        if self._on_search:
            self._debounce_timer = threading.Timer(
                DEBOUNCE_SECONDS,
                self._fire_search,
                args=[query],
            )
            self._debounce_timer.start()

    def _on_submit(self, e: ft.ControlEvent) -> None:
        """Handle Enter key — fire search immediately."""
        if self._debounce_timer:
            self._debounce_timer.cancel()

        query = e.control.value.strip()
        if self._on_search:
            self._on_search(query)

    def _fire_search(self, query: str) -> None:
        """Fire the search callback (called from debounce timer thread)."""
        if self._on_search:
            self._on_search(query)

    def _clear(self, e: ft.ControlEvent) -> None:
        """Clear the search field and fire an empty search."""
        self.value = ""
        if self.suffix:
            self.suffix.visible = False
        self.update()

        if self._on_search:
            self._on_search("")
