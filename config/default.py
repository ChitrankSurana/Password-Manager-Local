#!/usr/bin/env python3
"""
Default Configuration Settings
Personal Password Manager - Base Configuration

This file contains all default configuration values for the password manager.
These settings can be overridden by environment-specific configs or .env file.

DO NOT store secrets or sensitive values here - use .env file instead.
"""

import os
from pathlib import Path


class DefaultConfig:
    """
    Default configuration for Personal Password Manager

    All settings have sensible defaults that work out of the box.
    Override in environment-specific configs or .env file as needed.
    """

    # =========================================================================
    # APPLICATION SETTINGS
    # =========================================================================

    # Application metadata
    APP_NAME = "Personal Password Manager"
    APP_VERSION = "2.2.0"
    APP_AUTHOR = "Password Manager Team"

    # Application mode: 'development', 'production', 'testing'
    APP_ENV = os.getenv("APP_ENV", "production")

    # Enable debug mode (verbose logging, detailed errors)
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

    # =========================================================================
    # DIRECTORY PATHS
    # =========================================================================

    # Base directory (project root)
    BASE_DIR = Path(__file__).parent.parent.absolute()

    # Data directory (databases, user data)
    DATA_DIR = BASE_DIR / "data"

    # Backup directory
    BACKUP_DIR = BASE_DIR / "backups"

    # Logs directory
    LOG_DIR = BASE_DIR / "logs"

    # Temp directory
    TEMP_DIR = BASE_DIR / "temp"

    # Documentation directory
    DOCS_DIR = BASE_DIR / "Documentation"

    # Ensure directories exist
    for directory in [DATA_DIR, BACKUP_DIR, LOG_DIR, TEMP_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # DATABASE SETTINGS
    # =========================================================================

    # Database file path
    DB_PATH = str(DATA_DIR / "password_manager.db")

    # Database connection timeout (seconds)
    DB_TIMEOUT = int(os.getenv("DB_TIMEOUT", "30"))

    # Database schema version
    DB_SCHEMA_VERSION = 3

    # Enable foreign key constraints
    DB_FOREIGN_KEYS = True

    # Enable database WAL mode (better concurrency)
    DB_WAL_MODE = True

    # Database backup settings
    DB_BACKUP_ENABLED = os.getenv("DB_BACKUP_ENABLED", "True").lower() in ("true", "1", "yes")
    DB_BACKUP_ON_STARTUP = False
    DB_BACKUP_RETENTION_DAYS = int(os.getenv("DB_BACKUP_RETENTION_DAYS", "30"))
    DB_MAX_BACKUPS = int(os.getenv("DB_MAX_BACKUPS", "10"))

    # =========================================================================
    # SECURITY SETTINGS
    # =========================================================================

    # Encryption settings
    ENCRYPTION_ALGORITHM = "AES-256-CBC"
    PBKDF2_ITERATIONS = int(os.getenv("PBKDF2_ITERATIONS", "100000"))
    PBKDF2_ALGORITHM = "sha256"
    SALT_LENGTH = 32  # bytes
    IV_LENGTH = 16  # bytes for AES

    # Password hashing (for user accounts)
    BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))

    # Session management
    SESSION_TIMEOUT_HOURS = int(os.getenv("SESSION_TIMEOUT_HOURS", "8"))
    SESSION_TOKEN_LENGTH = 32  # bytes
    SESSION_CLEANUP_INTERVAL = 3600  # seconds (1 hour)

    # Authentication settings
    MAX_FAILED_ATTEMPTS = int(os.getenv("MAX_FAILED_ATTEMPTS", "5"))
    LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "30"))

    # Master password caching
    MASTER_PASSWORD_CACHE_ENABLED = os.getenv("MASTER_PASSWORD_CACHE_ENABLED", "True").lower() in (
        "true",
        "1",
        "yes",
    )
    MASTER_PASSWORD_CACHE_TIMEOUT = int(
        os.getenv("MASTER_PASSWORD_CACHE_TIMEOUT", "300")
    )  # seconds (5 minutes)

    # Security audit logging
    AUDIT_LOG_ENABLED = os.getenv("AUDIT_LOG_ENABLED", "True").lower() in ("true", "1", "yes")
    AUDIT_LOG_RETENTION_DAYS = int(os.getenv("AUDIT_LOG_RETENTION_DAYS", "90"))

    # Password strength requirements
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_UPPERCASE = False
    REQUIRE_LOWERCASE = False
    REQUIRE_DIGITS = False
    REQUIRE_SPECIAL_CHARS = False

    # =========================================================================
    # LOGGING SETTINGS
    # =========================================================================

    # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Log file paths
    LOG_FILE_APP = str(LOG_DIR / "app.log")
    LOG_FILE_SECURITY = str(LOG_DIR / "security.log")
    LOG_FILE_ERROR = str(LOG_DIR / "error.log")
    LOG_FILE_AUDIT = str(LOG_DIR / "audit.log")

    # Log format
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    # Log rotation
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10 MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # Console logging
    LOG_TO_CONSOLE = os.getenv("LOG_TO_CONSOLE", "True").lower() in ("true", "1", "yes")
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "True").lower() in ("true", "1", "yes")

    # Sensitive data masking in logs
    MASK_PASSWORDS_IN_LOGS = True
    MASK_ENCRYPTION_KEYS_IN_LOGS = True

    # =========================================================================
    # GUI SETTINGS
    # =========================================================================

    # Window settings
    WINDOW_WIDTH = int(os.getenv("WINDOW_WIDTH", "1000"))
    WINDOW_HEIGHT = int(os.getenv("WINDOW_HEIGHT", "700"))
    WINDOW_MIN_WIDTH = 800
    WINDOW_MIN_HEIGHT = 600

    # Theme settings
    DEFAULT_THEME = os.getenv("DEFAULT_THEME", "dark")  # 'dark' or 'light'
    DEFAULT_COLOR_SCHEME = os.getenv("DEFAULT_COLOR_SCHEME", "blue")

    # Font settings
    DEFAULT_FONT_FAMILY = "Segoe UI"
    DEFAULT_FONT_SIZE = int(os.getenv("DEFAULT_FONT_SIZE", "12"))
    DEFAULT_FONT_SCALE = float(os.getenv("DEFAULT_FONT_SCALE", "1.0"))

    # UI behavior
    AUTO_CLEAR_CLIPBOARD = os.getenv("AUTO_CLEAR_CLIPBOARD", "True").lower() in ("true", "1", "yes")
    CLIPBOARD_CLEAR_TIMEOUT = int(os.getenv("CLIPBOARD_CLEAR_TIMEOUT", "30"))  # seconds

    SHOW_PASSWORD_BY_DEFAULT = False
    CONFIRM_ON_DELETE = True
    CONFIRM_ON_EXIT = False

    # Search settings
    SEARCH_DEBOUNCE_MS = 300  # milliseconds
    SEARCH_MIN_CHARS = 1

    # Pagination
    PASSWORDS_PER_PAGE = int(os.getenv("PASSWORDS_PER_PAGE", "50"))

    # =========================================================================
    # WEB INTERFACE SETTINGS (Flask)
    # =========================================================================

    # Flask settings
    FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG = DEBUG  # Inherit from DEBUG setting

    # Secret key for Flask sessions (MUST be set in .env for production)
    FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-CHANGE-IN-PRODUCTION")

    # Session settings
    FLASK_SESSION_TYPE = "filesystem"
    FLASK_SESSION_PERMANENT = False
    FLASK_PERMANENT_SESSION_LIFETIME = 28800  # 8 hours in seconds

    # CSRF protection
    FLASK_CSRF_ENABLED = os.getenv("FLASK_CSRF_ENABLED", "True").lower() in ("true", "1", "yes")

    # Rate limiting
    FLASK_RATE_LIMIT_ENABLED = os.getenv("FLASK_RATE_LIMIT_ENABLED", "True").lower() in (
        "true",
        "1",
        "yes",
    )
    FLASK_RATE_LIMIT_DEFAULT = os.getenv("FLASK_RATE_LIMIT_DEFAULT", "100 per hour")
    FLASK_RATE_LIMIT_LOGIN = os.getenv("FLASK_RATE_LIMIT_LOGIN", "5 per minute")

    # =========================================================================
    # PASSWORD GENERATOR SETTINGS
    # =========================================================================

    # Default password generation settings
    DEFAULT_PASSWORD_LENGTH = int(os.getenv("DEFAULT_PASSWORD_LENGTH", "16"))
    DEFAULT_PASSWORD_INCLUDE_UPPERCASE = True
    DEFAULT_PASSWORD_INCLUDE_LOWERCASE = True
    DEFAULT_PASSWORD_INCLUDE_DIGITS = True
    DEFAULT_PASSWORD_INCLUDE_SPECIAL = True

    # Character sets
    CHARSET_UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    CHARSET_LOWERCASE = "abcdefghijklmnopqrstuvwxyz"
    CHARSET_DIGITS = "0123456789"
    CHARSET_SPECIAL = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # Memorable password settings
    MEMORABLE_WORD_COUNT = 4
    MEMORABLE_SEPARATOR = "-"
    MEMORABLE_DICTIONARY_PATH = str(DATA_DIR / "wordlist.txt")

    # =========================================================================
    # IMPORT/EXPORT SETTINGS
    # =========================================================================

    # Supported import formats
    IMPORT_FORMATS = ["csv", "json", "chrome", "firefox", "edge"]

    # Export settings
    EXPORT_ENCRYPTION_ENABLED = True
    EXPORT_INCLUDE_TIMESTAMPS = True
    EXPORT_INCLUDE_METADATA = True

    # Browser import paths (Windows)
    CHROME_IMPORT_PATH = os.path.expanduser(
        "~/AppData/Local/Google/Chrome/User Data/Default/Login Data"
    )
    FIREFOX_IMPORT_PATH = os.path.expanduser("~/AppData/Roaming/Mozilla/Firefox/Profiles")
    EDGE_IMPORT_PATH = os.path.expanduser(
        "~/AppData/Local/Microsoft/Edge/User Data/Default/Login Data"
    )

    # =========================================================================
    # PERFORMANCE SETTINGS
    # =========================================================================

    # Caching
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "True").lower() in ("true", "1", "yes")
    CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # seconds (5 minutes)
    CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "1000"))  # items

    # Connection pooling
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_POOL_MAX_OVERFLOW = int(os.getenv("DB_POOL_MAX_OVERFLOW", "10"))

    # =========================================================================
    # FEATURE FLAGS
    # =========================================================================

    # Enable/disable features
    FEATURE_WEB_INTERFACE = os.getenv("FEATURE_WEB_INTERFACE", "True").lower() in (
        "true",
        "1",
        "yes",
    )
    FEATURE_PASSWORD_HEALTH = os.getenv("FEATURE_PASSWORD_HEALTH", "True").lower() in (
        "true",
        "1",
        "yes",
    )
    FEATURE_IMPORT_EXPORT = os.getenv("FEATURE_IMPORT_EXPORT", "True").lower() in (
        "true",
        "1",
        "yes",
    )
    FEATURE_BACKUP_RESTORE = os.getenv("FEATURE_BACKUP_RESTORE", "True").lower() in (
        "true",
        "1",
        "yes",
    )
    FEATURE_2FA = os.getenv("FEATURE_2FA", "False").lower() in (
        "true",
        "1",
        "yes",
    )  # Not yet implemented

    # =========================================================================
    # NOTIFICATION SETTINGS
    # =========================================================================

    # Desktop notifications
    NOTIFICATIONS_ENABLED = os.getenv("NOTIFICATIONS_ENABLED", "False").lower() in (
        "true",
        "1",
        "yes",
    )
    NOTIFY_ON_PASSWORD_COPIED = False
    NOTIFY_ON_WEAK_PASSWORD = True
    NOTIFY_ON_OLD_PASSWORD = True

    # =========================================================================
    # DEVELOPER SETTINGS
    # =========================================================================

    # Testing mode
    TESTING = os.getenv("TESTING", "False").lower() in ("true", "1", "yes")

    # SQL query logging
    LOG_SQL_QUERIES = DEBUG

    # Performance profiling
    ENABLE_PROFILING = False

    # Error reporting
    SEND_ERROR_REPORTS = False
    ERROR_REPORT_ENDPOINT = None

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    @classmethod
    def get_all_settings(cls) -> dict:
        """
        Get all configuration settings as a dictionary

        Returns:
            dict: All settings and their values
        """
        return {
            key: getattr(cls, key) for key in dir(cls) if not key.startswith("_") and key.isupper()
        }

    @classmethod
    def validate(cls) -> bool:
        """
        Validate configuration settings

        Returns:
            bool: True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        # Check required directories exist
        if not cls.DATA_DIR.exists():
            raise ValueError(f"Data directory does not exist: {cls.DATA_DIR}")

        # Validate security settings
        if cls.PBKDF2_ITERATIONS < 10000:
            raise ValueError("PBKDF2_ITERATIONS must be at least 10000 for security")

        if cls.BCRYPT_ROUNDS < 10:
            raise ValueError("BCRYPT_ROUNDS must be at least 10 for security")

        if cls.SESSION_TIMEOUT_HOURS < 1:
            raise ValueError("SESSION_TIMEOUT_HOURS must be at least 1")

        # Validate Flask secret key in production
        if (
            cls.APP_ENV == "production"
            and cls.FLASK_SECRET_KEY == "dev-secret-key-CHANGE-IN-PRODUCTION"
        ):
            raise ValueError("FLASK_SECRET_KEY must be changed in production! Set in .env file")

        # Validate paths
        if not cls.BASE_DIR.exists():
            raise ValueError(f"Base directory does not exist: {cls.BASE_DIR}")

        return True

    @classmethod
    def print_config(cls, hide_secrets: bool = True):
        """
        Print all configuration settings (for debugging)

        Args:
            hide_secrets: Whether to hide sensitive values
        """
        secret_keys = [
            "FLASK_SECRET_KEY",
            "DB_PATH",
            "SECRET",
            "PASSWORD",
            "KEY",
            "TOKEN",
        ]

        print(f"\n{'=' * 70}")
        print(f"{cls.APP_NAME} - Configuration Settings")
        print(f"{'=' * 70}\n")

        for key, value in sorted(cls.get_all_settings().items()):
            # Hide sensitive values
            if hide_secrets and any(secret in key for secret in secret_keys):
                display_value = "***HIDDEN***"
            else:
                display_value = value

            print(f"{key:40} = {display_value}")

        print(f"\n{'=' * 70}\n")
