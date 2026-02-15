"""
Flet UI Pages
=============

Each page module defines a full-screen view that is swapped in/out by the
router in app.py. Pages receive the AppState object and interact with core
services through it — they never import database or encryption modules directly.

Pages:
    login_page        - Login, registration, and 2FA
    dashboard_page    - Password list with search, filters, and sorting
    add_edit_page     - Add or edit a password entry
    health_page       - Password health dashboard (scores, recommendations)
    settings_page     - User preferences and security settings
    generator_page    - Password generator with multiple methods
    backup_page       - Backup, restore, import, and export
    migration_dialog  - AES-CBC to AES-GCM migration progress dialog
"""
