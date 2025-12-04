#!/usr/bin/env python3
"""
Development Configuration
Personal Password Manager - Development Environment Settings

This configuration is used during development.
It enables debug mode, verbose logging, and relaxed security for testing.
"""

import os

from .default import DefaultConfig


class DevelopmentConfig(DefaultConfig):
    """
    Development-specific configuration

    Overrides default settings for development environment.
    """

    # Application mode
    APP_ENV = "development"

    # Enable debug mode
    DEBUG = True

    # =========================================================================
    # DATABASE SETTINGS
    # =========================================================================

    # Use development database
    DB_PATH = str(DefaultConfig.DATA_DIR / "password_manager_dev.db")

    # More aggressive cleanup for testing
    SESSION_CLEANUP_INTERVAL = 60  # 1 minute

    # =========================================================================
    # SECURITY SETTINGS (Relaxed for development)
    # =========================================================================

    # Faster encryption (less secure, but faster for development)
    PBKDF2_ITERATIONS = 10000  # Minimum safe value

    # Faster password hashing
    BCRYPT_ROUNDS = 10  # Minimum safe value

    # Shorter session timeout for testing
    SESSION_TIMEOUT_HOURS = 24  # 24 hours for dev convenience

    # More lenient account lockout
    MAX_FAILED_ATTEMPTS = 10  # More attempts for dev
    LOCKOUT_DURATION_MINUTES = 5  # Shorter lockout

    # Longer master password cache for dev convenience
    MASTER_PASSWORD_CACHE_TIMEOUT = 600  # 10 minutes

    # =========================================================================
    # LOGGING SETTINGS
    # =========================================================================

    # Verbose logging for development
    LOG_LEVEL = "DEBUG"

    # Log to console by default
    LOG_TO_CONSOLE = True
    LOG_TO_FILE = True

    # Log SQL queries for debugging
    LOG_SQL_QUERIES = True

    # Development log files
    LOG_FILE_APP = str(DefaultConfig.LOG_DIR / "dev_app.log")
    LOG_FILE_SECURITY = str(DefaultConfig.LOG_DIR / "dev_security.log")
    LOG_FILE_ERROR = str(DefaultConfig.LOG_DIR / "dev_error.log")

    # =========================================================================
    # FLASK SETTINGS
    # =========================================================================

    # Flask debug mode
    FLASK_DEBUG = True

    # Development secret key (not secure, don't use in production!)
    FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-not-for-production")

    # Relaxed rate limiting
    FLASK_RATE_LIMIT_DEFAULT = "1000 per hour"
    FLASK_RATE_LIMIT_LOGIN = "50 per minute"

    # =========================================================================
    # PERFORMANCE SETTINGS
    # =========================================================================

    # Enable profiling in development
    ENABLE_PROFILING = True

    # Disable caching for development (see changes immediately)
    CACHE_ENABLED = False

    # =========================================================================
    # DEVELOPER SETTINGS
    # =========================================================================

    # Don't mask sensitive data in dev logs (easier debugging)
    MASK_PASSWORDS_IN_LOGS = False  # WARNING: Insecure!
    MASK_ENCRYPTION_KEYS_IN_LOGS = False  # WARNING: Insecure!

    # Auto-reload on file changes
    AUTO_RELOAD = True

    # Show detailed error pages
    SHOW_DETAILED_ERRORS = True

    # =========================================================================
    # BACKUP SETTINGS
    # =========================================================================

    # Fewer backups in development
    DB_MAX_BACKUPS = 3
    DB_BACKUP_RETENTION_DAYS = 7

    # =========================================================================
    # FEATURE FLAGS (Enable all for testing)
    # =========================================================================

    FEATURE_WEB_INTERFACE = True
    FEATURE_PASSWORD_HEALTH = True
    FEATURE_IMPORT_EXPORT = True
    FEATURE_BACKUP_RESTORE = True

    # =========================================================================
    # NOTIFICATIONS
    # =========================================================================

    # Disable notifications in development
    NOTIFICATIONS_ENABLED = False
