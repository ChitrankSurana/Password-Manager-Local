"""
Personal Password Manager - Flet Application Entry Point
=========================================================

Main entry point for the Flet-based UI. This module:
1. Initializes all core services (auth, password manager, health, etc.)
2. Sets up the page (window size, theme, title)
3. Implements client-side routing between pages
4. Checks for pending encryption migration after login

The same code runs as a native desktop window (default) or in a web
browser (when launched with --web flag). The mode is determined by
the caller in main.py, not here.

Routing:
    /login      -> LoginPage (unauthenticated)
    /dashboard  -> DashboardPage (authenticated, default after login)
    /add        -> AddEditPage (new entry)
    /edit/:id   -> AddEditPage (edit existing entry)
    /generator  -> GeneratorPage
    /health     -> HealthPage
    /backup     -> BackupPage
    /settings   -> SettingsPage

Version: 3.0.0
"""

import sys
from pathlib import Path

import flet as ft

# Ensure the src directory is on the Python path so core imports work
_src_dir = str(Path(__file__).parent.parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from core.auth import AuthenticationManager
from core.password_health_service import PasswordHealthService
from core.password_manager import PasswordManagerCore
from utils.import_export import BackupManager
from utils.password_generator import PasswordGenerator
from utils.strength_checker import AdvancedPasswordStrengthChecker

from .state import AppState
from .theme import apply_theme


def main(page: ft.Page) -> None:
    """
    Flet application entry point.

    This function is called by ft.app(target=main). It receives a Page
    object representing the application window (desktop) or browser tab (web).

    Args:
        page: The Flet Page object
    """
    # --- Window configuration ---
    page.title = "Personal Password Manager"
    page.window.width = 1000
    page.window.height = 700
    page.window.min_width = 800
    page.window.min_height = 600

    # --- Initialize core services ---
    # These are the same service objects used by the old GUI and Flask UIs.
    # Pages interact with them exclusively through AppState.
    auth_manager = AuthenticationManager()
    password_manager = PasswordManagerCore(auth_manager=auth_manager)
    health_service = PasswordHealthService()
    backup_manager = BackupManager()
    password_generator = PasswordGenerator()
    strength_checker = AdvancedPasswordStrengthChecker()

    # --- Build application state ---
    # AppState is a single object shared across all pages. It holds the
    # session, core service references, and navigation callbacks.
    state = AppState(
        page=page,
        auth_manager=auth_manager,
        password_manager=password_manager,
        health_service=health_service,
        backup_manager=backup_manager,
        password_generator=password_generator,
        strength_checker=strength_checker,
    )

    # --- Apply default theme ---
    apply_theme(page, color_scheme="blue", dark_mode=True)

    # --- Routing ---
    # Lazy imports to avoid circular dependencies and keep startup fast.
    # Each page module is loaded on first navigation to that route.
    _page_cache = {}

    def navigate(route: str) -> None:
        """
        Navigate to a route by swapping the page content.

        This is the primary navigation mechanism. Pages call
        state.navigate("/dashboard") to switch views. The function
        clears the current page controls and adds the new page's view.

        Args:
            route: The target route (e.g., "/login", "/dashboard")
        """
        page.controls.clear()

        # Guard: redirect to login if not authenticated (except for /login)
        if route != "/login" and not state.is_authenticated:
            route = "/login"

        if route == "/login":
            from .pages.login_page import LoginPage

            view = LoginPage(state)
        elif route == "/dashboard":
            from .pages.dashboard_page import DashboardPage

            view = DashboardPage(state)
        elif route == "/add":
            from .pages.add_edit_page import AddEditPage

            view = AddEditPage(state)
        elif route.startswith("/edit/"):
            from .pages.add_edit_page import AddEditPage

            # Extract the entry ID from the route
            entry_id = int(route.split("/edit/")[1])
            view = AddEditPage(state, entry_id=entry_id)
        elif route == "/generator":
            from .pages.generator_page import GeneratorPage

            view = GeneratorPage(state)
        elif route == "/health":
            from .pages.health_page import HealthPage

            view = HealthPage(state)
        elif route == "/backup":
            from .pages.backup_page import BackupPage

            view = BackupPage(state)
        elif route == "/settings":
            from .pages.settings_page import SettingsPage

            view = SettingsPage(state)
        else:
            # Unknown route — fall back to dashboard or login
            if state.is_authenticated:
                from .pages.dashboard_page import DashboardPage

                view = DashboardPage(state)
            else:
                from .pages.login_page import LoginPage

                view = LoginPage(state)

        page.controls.append(view)
        page.update()

    # Wire up the navigate callback in state
    state.navigate = navigate

    # --- Start on the login page ---
    navigate("/login")


def run_desktop() -> None:
    """Launch the application as a native desktop window."""
    ft.app(target=main)


def run_web(host: str = "127.0.0.1", port: int = 5000) -> None:
    """
    Launch the application in a web browser.

    Security note: The default host is 127.0.0.1 (localhost only).
    Binding to 0.0.0.0 exposes the application to all network interfaces
    and should only be done behind a reverse proxy with TLS.

    Args:
        host: Network interface to bind to
        port: Port number
    """
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        host=host,
        port=port,
    )
