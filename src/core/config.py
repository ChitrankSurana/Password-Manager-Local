#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Loader
Personal Password Manager - Centralized Configuration Management

This module provides a centralized way to access configuration settings.
It loads environment variables from .env file and selects the appropriate
configuration based on APP_ENV environment variable.

Usage:
    from src.core.config import config

    # Access settings
    db_path = config.DB_PATH
    debug = config.DEBUG
    iterations = config.PBKDF2_ITERATIONS

Environment Selection:
    Set APP_ENV environment variable to select configuration:
    - APP_ENV=development  → DevelopmentConfig
    - APP_ENV=production   → ProductionConfig
    - APP_ENV=testing      → TestingConfig
    - (default)            → ProductionConfig (safe default)

.env File:
    Create a .env file in project root to override settings:
    APP_ENV=development
    DEBUG=True
    DB_TIMEOUT=60
    FLASK_SECRET_KEY=your-secret-key-here
"""

import os
import sys
from pathlib import Path
from typing import Type

from config.default import DefaultConfig
from config.development import DevelopmentConfig
from config.production import ProductionConfig

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    try:
        import codecs

        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")
    except Exception:
        pass  # Fallback if encoding setup fails

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    # Look for .env file in project root
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        print(f"✓ Loaded environment variables from: {env_path}")
    else:
        print(f"ℹ No .env file found at {env_path}. Using defaults.")

except ImportError:
    print(
        "⚠ python-dotenv not installed. "
        "Install with: pip install python-dotenv\n"
        "  Using environment variables and defaults only."
    )

# Import configuration classes


class TestingConfig(DefaultConfig):
    """
    Testing configuration for pytest

    Used during automated testing.
    """

    APP_ENV = "testing"
    TESTING = True
    DEBUG = True

    # Use in-memory database for tests
    DB_PATH = ":memory:"

    # Fast encryption for tests (minimum safe values)
    PBKDF2_ITERATIONS = 10000  # Minimum safe value
    BCRYPT_ROUNDS = 4  # Fast for tests

    # Disable logging during tests
    LOG_TO_CONSOLE = False
    LOG_TO_FILE = False

    # Disable caching in tests
    CACHE_ENABLED = False

    # Short timeouts for tests
    SESSION_TIMEOUT_HOURS = 1
    MASTER_PASSWORD_CACHE_TIMEOUT = 60

    @classmethod
    def validate(cls) -> bool:
        """Skip validation for testing (allows lower security values)"""
        # Don't run strict validation in testing mode
        return True


# Configuration mapping
config_map = {
    "development": DevelopmentConfig,
    "dev": DevelopmentConfig,
    "production": ProductionConfig,
    "prod": ProductionConfig,
    "testing": TestingConfig,
    "test": TestingConfig,
}


def get_config(env: str = None) -> Type[DefaultConfig]:
    """
    Get configuration class based on environment

    Args:
        env: Environment name ('development', 'production', 'testing')
             If None, reads from APP_ENV environment variable

    Returns:
        Configuration class (DevelopmentConfig, ProductionConfig, etc.)

    Raises:
        ValueError: If environment name is invalid
    """
    if env is None:
        env = os.getenv("APP_ENV", "production")

    env = env.lower()

    if env not in config_map:
        raise ValueError(
            f"Invalid environment: {env}. " f"Valid options: {', '.join(config_map.keys())}"
        )

    config_class = config_map[env]

    # Validate configuration
    try:
        config_class.validate()
    except ValueError as e:
        print(f"\n❌ Configuration Validation Error: {e}\n")
        raise

    return config_class


# Global configuration object
# This is the main export - import as:
#   from src.core.config import config
try:
    config = get_config()
    print(f"✓ Loaded {config.__name__} configuration")

    # Print summary in debug mode
    if config.DEBUG:
        print("\nConfiguration Summary:")
        print(f"  Environment: {config.APP_ENV}")
        print(f"  Debug Mode: {config.DEBUG}")
        print(f"  Database: {config.DB_PATH}")
        print(f"  Log Level: {config.LOG_LEVEL}")
        print(f"  Flask Port: {config.FLASK_PORT}")
        print(f"  PBKDF2 Iterations: {config.PBKDF2_ITERATIONS}")

except Exception as e:
    print(f"\n❌ Failed to load configuration: {e}")
    print("Falling back to DefaultConfig")
    config = DefaultConfig


# Helper functions
def reload_config(env: str = None):
    """
    Reload configuration (useful for testing)

    Args:
        env: Environment name to load

    Returns:
        New configuration class
    """
    global config
    config = get_config(env)
    return config


def print_config(hide_secrets: bool = True):
    """
    Print current configuration settings

    Args:
        hide_secrets: Whether to hide sensitive values
    """
    config.print_config(hide_secrets=hide_secrets)


def validate_config() -> bool:
    """
    Validate current configuration

    Returns:
        bool: True if valid

    Raises:
        ValueError: If configuration is invalid
    """
    return config.validate()


# Export for easy importing
__all__ = [
    "config",
    "get_config",
    "reload_config",
    "print_config",
    "validate_config",
    "DefaultConfig",
    "DevelopmentConfig",
    "ProductionConfig",
    "TestingConfig",
]


if __name__ == "__main__":
    """
    Test configuration loading

    Usage: python -m src.core.config
    """
    print("\n" + "=" * 70)
    print("Configuration System Test")
    print("=" * 70 + "\n")

    # Test all environments
    for env_name in ["development", "production", "testing"]:
        print(f"\nTesting {env_name} configuration:")
        print("-" * 40)

        try:
            test_config = get_config(env_name)
            print(f"✓ {test_config.__name__} loaded successfully")
            print(f"  APP_ENV: {test_config.APP_ENV}")
            print(f"  DEBUG: {test_config.DEBUG}")
            print(f"  DB_PATH: {test_config.DB_PATH}")
            print(f"  LOG_LEVEL: {test_config.LOG_LEVEL}")
            print(f"  PBKDF2_ITERATIONS: {test_config.PBKDF2_ITERATIONS}")

            # Validate
            test_config.validate()
            print("✓ Configuration is valid")

        except Exception as e:
            print(f"✗ Error: {e}")

    # Print current config
    print("\n\nCurrent Active Configuration:")
    print("=" * 70)
    print_config(hide_secrets=True)

    print("\n✓ Configuration system test complete!\n")
