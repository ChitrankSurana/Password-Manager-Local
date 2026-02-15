"""
Personal Password Manager - Flet UI Application
=================================================

This package implements the unified UI for the Password Manager using the
Flet framework (Flutter-based Python UI). It replaces both the CustomTkinter
desktop GUI and the Flask web interface with a single codebase that runs
natively on desktop and optionally in a web browser.

Architecture:
    flet_app/
      app.py          - Main application entry point, routing, service init
      theme.py        - Material Design 3 theme configuration
      state.py        - Centralized app state (session, services, reactive data)
      pages/          - Full-page views (login, dashboard, settings, etc.)
      components/     - Reusable UI widgets (password card, search bar, etc.)

Design Principles:
    1. Pages call core services only — no direct DB or encryption access.
    2. All business logic lives in src/core/ (password_manager, auth, etc.).
    3. The state module provides reactive updates so pages stay in sync.
    4. Theme configuration mirrors the existing color schemes.

Version: 3.0.0
"""
