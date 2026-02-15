"""
Navigation Rail Component
=========================

Persistent sidebar navigation for authenticated pages. Uses Flet's
NavigationRail widget to provide consistent navigation across the app.

The rail is shown on all authenticated pages and highlights the current
route. Clicking a destination calls state.navigate() to switch pages.

Version: 3.0.0
"""

import flet as ft
from typing import Optional

from ..state import AppState


# Map route paths to navigation rail indices.
# The order matches the destinations list below.
ROUTE_TO_INDEX = {
    "/dashboard": 0,
    "/generator": 1,
    "/health": 2,
    "/backup": 3,
    "/settings": 4,
}

# Reverse map: index -> route
INDEX_TO_ROUTE = {v: k for k, v in ROUTE_TO_INDEX.items()}


class NavRail(ft.NavigationRail):
    """
    Navigation rail sidebar for authenticated pages.

    Provides quick access to all main sections of the app. The logout
    action is handled via a trailing icon button, not a rail destination,
    since it's a destructive action that shouldn't be accidentally triggered.

    Args:
        state: The shared AppState object
        current_route: The route of the page displaying this rail
    """

    def __init__(self, state: AppState, current_route: str = "/dashboard"):
        self.state = state
        self._current_route = current_route

        # Determine which destination is selected based on current route
        selected_index = ROUTE_TO_INDEX.get(current_route, 0)

        super().__init__(
            selected_index=selected_index,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=80,
            min_extended_width=200,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.DASHBOARD_OUTLINED,
                    selected_icon=ft.Icons.DASHBOARD,
                    label="Dashboard",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.PASSWORD_OUTLINED,
                    selected_icon=ft.Icons.PASSWORD,
                    label="Generator",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.HEALTH_AND_SAFETY_OUTLINED,
                    selected_icon=ft.Icons.HEALTH_AND_SAFETY,
                    label="Health",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.BACKUP_OUTLINED,
                    selected_icon=ft.Icons.BACKUP,
                    label="Backup",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    selected_icon=ft.Icons.SETTINGS,
                    label="Settings",
                ),
            ],
            trailing=ft.Container(
                content=ft.Column(
                    [
                        ft.Divider(height=1),
                        ft.IconButton(
                            icon=ft.Icons.LOGOUT,
                            tooltip="Logout",
                            on_click=self._on_logout,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.only(top=20),
            ),
            on_change=self._on_destination_change,
        )

    def _on_destination_change(self, e: ft.ControlEvent) -> None:
        """Handle navigation rail destination selection."""
        index = e.control.selected_index
        route = INDEX_TO_ROUTE.get(index, "/dashboard")

        # Only navigate if the route is different from current
        if route != self._current_route and self.state.navigate:
            self.state.navigate(route)

    def _on_logout(self, e: ft.ControlEvent) -> None:
        """Handle logout button click."""
        self.state.logout()
        if self.state.navigate:
            self.state.navigate("/login")
