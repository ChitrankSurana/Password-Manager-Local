#!/usr/bin/env python3
"""
Production Configuration
Personal Password Manager - Production Environment Settings

This configuration is used in production.
It enforces strict security, proper logging, and optimal performance.
"""

import os

from .default import DefaultConfig


class ProductionConfig(DefaultConfig):
    """
    Production-specific configuration

    Overrides default settings for production environment.
    Enforces security best practices and performance optimizations.
    """

    # Application mode
    APP_ENV = "production"

    # Disable debug mode
    DEBUG = False

    # =========================================================================
    # SECURITY SETTINGS (Strict for production)
    # =========================================================================

    # Strong encryption
    PBKDF2_ITERATIONS = int(os.getenv("PBKDF2_ITERATIONS", "100000"))

    # Strong password hashing
    BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))

    # Strict session timeout
    SESSION_TIMEOUT_HOURS = int(os.getenv("SESSION_TIMEOUT_HOURS", "8"))

    # Strict account lockout
    MAX_FAILED_ATTEMPTS = int(os.getenv("MAX_FAILED_ATTEMPTS", "5"))
    LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "30"))

    # Shorter master password cache
    MASTER_PASSWORD_CACHE_TIMEOUT = int(os.getenv("MASTER_PASSWORD_CACHE_TIMEOUT", "300"))

    # Enable audit logging
    AUDIT_LOG_ENABLED = True
    AUDIT_LOG_RETENTION_DAYS = 90

    # =========================================================================
    # LOGGING SETTINGS
    # =========================================================================

    # Production log level
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Log to file in production
    LOG_TO_CONSOLE = os.getenv("LOG_TO_CONSOLE", "False").lower() in ("true", "1", "yes")
    LOG_TO_FILE = True

    # Don't log SQL queries in production
    LOG_SQL_QUERIES = False

    # Mask sensitive data in logs
    MASK_PASSWORDS_IN_LOGS = True
    MASK_ENCRYPTION_KEYS_IN_LOGS = True

    # Larger log files
    LOG_MAX_BYTES = 20971520  # 20 MB
    LOG_BACKUP_COUNT = 10

    # =========================================================================
    # FLASK SETTINGS
    # =========================================================================

    # Disable Flask debug in production
    FLASK_DEBUG = False

    # CRITICAL: Secret key MUST be set via environment variable
    # Validation happens in validate() method
    FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "NOT_SET")

    # Strict rate limiting
    FLASK_RATE_LIMIT_ENABLED = True
    FLASK_RATE_LIMIT_DEFAULT = os.getenv("FLASK_RATE_LIMIT_DEFAULT", "100 per hour")
    FLASK_RATE_LIMIT_LOGIN = os.getenv("FLASK_RATE_LIMIT_LOGIN", "5 per minute")

    # CSRF protection enabled
    FLASK_CSRF_ENABLED = True

    # =========================================================================
    # PERFORMANCE SETTINGS
    # =========================================================================

    # Enable caching for performance
    CACHE_ENABLED = True
    CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))
    CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "1000"))

    # Connection pooling
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_POOL_MAX_OVERFLOW = int(os.getenv("DB_POOL_MAX_OVERFLOW", "10"))

    # Disable profiling in production
    ENABLE_PROFILING = False

    # =========================================================================
    # BACKUP SETTINGS
    # =========================================================================

    # Regular backups in production
    DB_BACKUP_ENABLED = True
    DB_MAX_BACKUPS = int(os.getenv("DB_MAX_BACKUPS", "30"))
    DB_BACKUP_RETENTION_DAYS = int(os.getenv("DB_BACKUP_RETENTION_DAYS", "90"))

    # =========================================================================
    # DEVELOPER SETTINGS
    # =========================================================================

    # No detailed errors in production
    SHOW_DETAILED_ERRORS = False

    # No auto-reload in production
    AUTO_RELOAD = False

    # =========================================================================
    # VALIDATION
    # =========================================================================

    @classmethod
    def validate(cls) -> bool:
        """
        Validate production configuration

        Raises:
            ValueError: If production config is invalid or insecure
        """
        # Run base validation
        super().validate()

        # Validate FLASK_SECRET_KEY is set
        if not cls.FLASK_SECRET_KEY or cls.FLASK_SECRET_KEY == "NOT_SET":
            raise ValueError(
                "FLASK_SECRET_KEY must be set in production! "
                "Add FLASK_SECRET_KEY=<random-secret> to your .env file"
            )

        # Additional production-specific validations
        if cls.DEBUG:
            raise ValueError("DEBUG must be False in production!")

        if cls.FLASK_DEBUG:
            raise ValueError("FLASK_DEBUG must be False in production!")

        if not cls.MASK_PASSWORDS_IN_LOGS:
            raise ValueError("MASK_PASSWORDS_IN_LOGS must be True in production!")

        if cls.PBKDF2_ITERATIONS < 100000:
            raise ValueError("PBKDF2_ITERATIONS must be at least 100000 in production!")

        if cls.BCRYPT_ROUNDS < 12:
            raise ValueError("BCRYPT_ROUNDS must be at least 12 in production!")

        return True
