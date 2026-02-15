"""
Personal Password Manager - Flet Application State
====================================================

Centralized state management for the Flet UI. This module holds the
authenticated session, core service references, and provides reactive
methods that pages call to trigger updates across the UI.

Design:
    AppState is created once in app.py after the page initializes. It is
    passed to every page constructor so they can:
    1. Access core services (auth_manager, password_manager, etc.)
    2. Read/write session data (session_id, username, user_id)
    3. Trigger navigation via the navigate() callback
    4. Request a full page refresh via refresh()

    This avoids global mutable state and makes testing easier — pages
    receive an AppState instance that can be mocked.

Thread Safety:
    Flet runs UI updates on a single thread, so AppState does not need
    locking for page.update() calls. Background operations (e.g., migration)
    should use page.run_thread() and call page.update() when done.

Version: 3.0.0
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

import flet as ft


@dataclass
class AppState:
    """
    Centralized application state passed to all pages.

    Attributes:
        page: The Flet page object (for navigation and updates)
        auth_manager: AuthenticationManager instance
        password_manager: PasswordManagerCore instance
        health_service: PasswordHealthService instance
        session_id: Active session token (None if not logged in)
        username: Logged-in username (None if not logged in)
        user_id: Logged-in user's database ID (None if not logged in)
        master_password: Cached master password (cleared after migration)
        navigate: Callback to switch the current page/route
        refresh: Callback to refresh the current page's data
        settings: User-specific settings dictionary
    """

    page: ft.Page

    # Core services — initialized in app.py, never None after startup
    auth_manager: Any = None
    password_manager: Any = None
    health_service: Any = None
    backup_manager: Any = None
    password_generator: Any = None
    strength_checker: Any = None

    # Session data — populated after successful login
    session_id: Optional[str] = None
    username: Optional[str] = None
    user_id: Optional[int] = None
    master_password: Optional[str] = None  # Cleared after encryption migration

    # Navigation callback: navigate("/dashboard"), navigate("/login"), etc.
    navigate: Optional[Callable[[str], None]] = None

    # Refresh callback: triggers data reload on the current page
    refresh: Optional[Callable[[], None]] = None

    # User preferences loaded from SettingsService
    settings: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_authenticated(self) -> bool:
        """Check if a user is currently logged in."""
        return self.session_id is not None

    def login(
        self,
        session_id: str,
        username: str,
        user_id: int,
        master_password: Optional[str] = None,
    ) -> None:
        """
        Store session data after successful authentication.

        Args:
            session_id: The session token from auth_manager
            username: The authenticated username
            user_id: The user's database ID
            master_password: Optional master password for migration
        """
        self.session_id = session_id
        self.username = username
        self.user_id = user_id
        self.master_password = master_password

    def logout(self) -> None:
        """
        Clear all session data on logout.

        Also invalidates the session in the auth_manager so the token
        cannot be reused.
        """
        if self.auth_manager and self.session_id:
            try:
                self.auth_manager.invalidate_session(self.session_id)
            except Exception:
                pass  # Best-effort invalidation

        self.session_id = None
        self.username = None
        self.user_id = None
        self.master_password = None
        self.settings = {}

    def clear_master_password(self) -> None:
        """
        Clear the cached master password from memory.

        Called after encryption migration is complete so the password
        doesn't linger in memory longer than necessary.
        """
        self.master_password = None
