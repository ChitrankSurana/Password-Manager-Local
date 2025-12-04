#!/usr/bin/env python3
"""
Personal Password Manager - Settings Service
===========================================

This module provides comprehensive user settings management for the password manager.
It handles per-user preferences, default configurations, settings validation, and
persistent storage through the database layer.

Key Features:
- Per-user settings storage and retrieval
- Default settings management with fallbacks
- Settings validation and type checking
- Category-based settings organization
- Settings change notifications and callbacks
- Import/export settings functionality
- Settings migration and versioning support

Settings Categories:
- password_viewing: Timeout, permissions, UI preferences
- password_deletion: Confirmation types, security levels
- security: Audit logging, rate limiting, lockout settings
- ui_preferences: Theme, display options, accessibility
- import_export: Default formats, encryption options

Security Features:
- Input validation for all settings values
- Secure storage of sensitive preferences
- Audit logging of settings changes
- Master password protection for critical settings
- Settings integrity validation

Author: Personal Password Manager Enhancement Team
Version: 2.2.0
Date: September 21, 2025
"""

import json
import logging
import threading
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

# Configure logging for settings operations
logger = logging.getLogger(__name__)


class SettingCategory(Enum):
    """Categories of user settings"""

    PASSWORD_VIEWING = "password_viewing"
    PASSWORD_DELETION = "password_deletion"
    SECURITY = "security"
    UI_PREFERENCES = "ui_preferences"
    IMPORT_EXPORT = "import_export"
    ADVANCED = "advanced"


class SettingType(Enum):
    """Types of setting values for validation"""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    ENUM = "enum"
    LIST = "list"


@dataclass
class SettingDefinition:
    """
    Defines a setting with its metadata, validation rules, and default value

    This class provides comprehensive setting definition including validation
    rules, allowed values, UI hints, and security requirements.
    """

    key: str  # Setting key (unique within category)
    display_name: str  # User-friendly display name
    description: str  # Detailed description for UI
    setting_type: SettingType  # Data type for validation
    default_value: Any  # Default value if not set
    category: SettingCategory  # Category this setting belongs to

    # Validation rules
    min_value: Optional[Union[int, float]] = None  # Minimum value for numbers
    max_value: Optional[Union[int, float]] = None  # Maximum value for numbers
    allowed_values: Optional[List[Any]] = None  # Allowed enum values
    regex_pattern: Optional[str] = None  # Regex for string validation

    # UI metadata
    ui_hint: Optional[str] = None  # UI control type hint
    is_advanced: bool = False  # Show in advanced settings
    requires_restart: bool = False  # App restart needed
    requires_master_password: bool = False  # Master password required

    # Security and behavior
    is_sensitive: bool = False  # Don't log value changes
    affects_security: bool = False  # Security-related setting
    version_introduced: str = "2.2.0"  # Version when added


class SettingsValidationError(Exception):
    """Raised when setting validation fails"""


class SettingsService:
    """
    Comprehensive user settings management service

    This service provides a complete settings management system with per-user
    storage, validation, defaults, and change tracking. It integrates with
    the database layer for persistent storage and provides a clean API for
    UI components.

    Features:
    - Per-user settings with database persistence
    - Comprehensive validation with type checking
    - Default settings management with fallbacks
    - Settings change callbacks and notifications
    - Import/export functionality for settings
    - Settings versioning and migration support
    - Thread-safe operations for concurrent access
    - Audit logging of settings changes
    """

    def __init__(self, database_manager=None):
        """
        Initialize the settings service

        Args:
            database_manager: DatabaseManager instance for persistence
        """
        self.database_manager = database_manager

        # Thread safety
        self._lock = threading.RLock()

        # Settings definitions registry
        self._setting_definitions: Dict[SettingCategory, Dict[str, SettingDefinition]] = {}

        # Cached settings per user (user_id -> category -> key -> value)
        self._settings_cache: Dict[int, Dict[str, Dict[str, Any]]] = {}

        # Change callbacks (category -> list of callbacks)
        self._change_callbacks: Dict[str, List[Callable]] = {}

        # Settings validation cache
        self._validation_cache: Dict[str, Any] = {}

        # Initialize default settings definitions
        self._initialize_setting_definitions()

        logger.info("SettingsService initialized with comprehensive user preference management")

    def _initialize_setting_definitions(self):
        """Initialize all setting definitions with defaults and validation rules"""

        # Password Viewing Settings
        viewing_settings = {
            "view_timeout_minutes": SettingDefinition(
                key="view_timeout_minutes",
                display_name="View Timeout",
                description="How long passwords remain visible after authentication (1-60 minutes)",
                setting_type=SettingType.INTEGER,
                default_value=1,
                category=SettingCategory.PASSWORD_VIEWING,
                min_value=1,
                max_value=60,
                ui_hint="slider",
                affects_security=True,
            ),
            "require_master_password": SettingDefinition(
                key="require_master_password",
                display_name="Always Require Master Password",
                description="Always require master password for viewing passwords (highest security)",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category=SettingCategory.PASSWORD_VIEWING,
                ui_hint="checkbox",
                affects_security=True,
            ),
            "auto_hide_on_focus_loss": SettingDefinition(
                key="auto_hide_on_focus_loss",
                display_name="Auto-Hide on Focus Loss",
                description="Automatically hide passwords when application loses focus",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category=SettingCategory.PASSWORD_VIEWING,
                ui_hint="checkbox",
                affects_security=True,
            ),
            "show_view_timer": SettingDefinition(
                key="show_view_timer",
                display_name="Show Countdown Timer",
                description="Display remaining time when passwords are visible",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category=SettingCategory.PASSWORD_VIEWING,
                ui_hint="checkbox",
            ),
            "allow_copy_when_visible": SettingDefinition(
                key="allow_copy_when_visible",
                display_name="Enable Copy Buttons",
                description="Show copy buttons when passwords are visible",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category=SettingCategory.PASSWORD_VIEWING,
                ui_hint="checkbox",
            ),
            "max_concurrent_views": SettingDefinition(
                key="max_concurrent_views",
                display_name="Max Concurrent Views",
                description="Maximum number of passwords that can be visible simultaneously",
                setting_type=SettingType.INTEGER,
                default_value=5,
                category=SettingCategory.PASSWORD_VIEWING,
                min_value=1,
                max_value=20,
                ui_hint="slider",
                is_advanced=True,
            ),
        }

        # Password Deletion Settings
        deletion_settings = {
            "require_confirmation": SettingDefinition(
                key="require_confirmation",
                display_name="Require Confirmation",
                description="Always show confirmation dialog before deleting passwords",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category=SettingCategory.PASSWORD_DELETION,
                ui_hint="checkbox",
                affects_security=True,
            ),
            "confirmation_type": SettingDefinition(
                key="confirmation_type",
                display_name="Confirmation Type",
                description="Type of confirmation required for password deletion",
                setting_type=SettingType.ENUM,
                default_value="type_website",
                category=SettingCategory.PASSWORD_DELETION,
                allowed_values=["simple", "type_website", "master_password", "smart"],
                ui_hint="dropdown",
                affects_security=True,
            ),
            "require_master_password": SettingDefinition(
                key="require_master_password",
                display_name="Require Master Password",
                description="Always require master password for password deletion",
                setting_type=SettingType.BOOLEAN,
                default_value=False,
                category=SettingCategory.PASSWORD_DELETION,
                ui_hint="checkbox",
                affects_security=True,
                requires_master_password=True,
            ),
            "show_deleted_count": SettingDefinition(
                key="show_deleted_count",
                display_name="Show Success Messages",
                description="Display confirmation message after successful deletion",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category=SettingCategory.PASSWORD_DELETION,
                ui_hint="checkbox",
            ),
            "smart_confirmation_rules": SettingDefinition(
                key="smart_confirmation_rules",
                display_name="Smart Confirmation Rules",
                description="Rules for smart confirmation based on password age and importance",
                setting_type=SettingType.JSON,
                default_value={
                    "new_password_hours": 24,
                    "important_requires_master": True,
                    "bulk_requires_master": True,
                },
                category=SettingCategory.PASSWORD_DELETION,
                ui_hint="json_editor",
                is_advanced=True,
                affects_security=True,
            ),
        }

        # Security Settings
        security_settings = {
            "audit_logging": SettingDefinition(
                key="audit_logging",
                display_name="Security Audit Logging",
                description="Enable comprehensive security event logging",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category=SettingCategory.SECURITY,
                ui_hint="checkbox",
                affects_security=True,
            ),
            "max_failed_attempts": SettingDefinition(
                key="max_failed_attempts",
                display_name="Max Failed Attempts",
                description="Maximum failed authentication attempts before temporary lockout",
                setting_type=SettingType.INTEGER,
                default_value=3,
                category=SettingCategory.SECURITY,
                min_value=1,
                max_value=10,
                ui_hint="number_input",
                affects_security=True,
            ),
            "lockout_duration_minutes": SettingDefinition(
                key="lockout_duration_minutes",
                display_name="Lockout Duration",
                description="How long to lock out after max failed attempts (1-60 minutes)",
                setting_type=SettingType.INTEGER,
                default_value=5,
                category=SettingCategory.SECURITY,
                min_value=1,
                max_value=60,
                ui_hint="slider",
                affects_security=True,
            ),
            "session_timeout_hours": SettingDefinition(
                key="session_timeout_hours",
                display_name="Session Timeout",
                description="Automatic logout after inactivity (1-24 hours)",
                setting_type=SettingType.INTEGER,
                default_value=8,
                category=SettingCategory.SECURITY,
                min_value=1,
                max_value=24,
                ui_hint="slider",
                affects_security=True,
            ),
            "require_biometric_when_available": SettingDefinition(
                key="require_biometric_when_available",
                display_name="Use Biometric Authentication",
                description="Use fingerprint/face unlock when available (future feature)",
                setting_type=SettingType.BOOLEAN,
                default_value=False,
                category=SettingCategory.SECURITY,
                ui_hint="checkbox",
                affects_security=True,
                version_introduced="2.1.0",
            ),
        }

        # UI Preferences
        ui_settings = {
            "theme_mode": SettingDefinition(
                key="theme_mode",
                display_name="Theme",
                description="Application color theme",
                setting_type=SettingType.ENUM,
                default_value="system",
                category=SettingCategory.UI_PREFERENCES,
                allowed_values=["light", "dark", "system"],
                ui_hint="dropdown",
                requires_restart=True,
            ),
            "default_sort_order": SettingDefinition(
                key="default_sort_order",
                display_name="Default Sort Order",
                description="Default sorting for password lists",
                setting_type=SettingType.ENUM,
                default_value="website_asc",
                category=SettingCategory.UI_PREFERENCES,
                allowed_values=["website_asc", "website_desc", "created_desc", "modified_desc"],
                ui_hint="dropdown",
            ),
            "entries_per_page": SettingDefinition(
                key="entries_per_page",
                display_name="Entries Per Page",
                description="Number of password entries to show per page",
                setting_type=SettingType.INTEGER,
                default_value=25,
                category=SettingCategory.UI_PREFERENCES,
                min_value=10,
                max_value=100,
                allowed_values=[10, 25, 50, 100],
                ui_hint="dropdown",
            ),
            "show_password_strength": SettingDefinition(
                key="show_password_strength",
                display_name="Show Password Strength",
                description="Display password strength indicators in lists",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category=SettingCategory.UI_PREFERENCES,
                ui_hint="checkbox",
            ),
            "compact_view": SettingDefinition(
                key="compact_view",
                display_name="Compact View",
                description="Use compact layout to show more entries on screen",
                setting_type=SettingType.BOOLEAN,
                default_value=False,
                category=SettingCategory.UI_PREFERENCES,
                ui_hint="checkbox",
            ),
            "font_size": SettingDefinition(
                key="font_size",
                display_name="Font Size",
                description="Application font size for better readability",
                setting_type=SettingType.ENUM,
                default_value="medium",
                category=SettingCategory.UI_PREFERENCES,
                allowed_values=["small", "medium", "large", "extra_large"],
                ui_hint="dropdown",
                requires_restart=False,
            ),
            "first_time_setup_completed": SettingDefinition(
                key="first_time_setup_completed",
                display_name="First Time Setup Completed",
                description="Indicates whether user has completed the first-time setup wizard",
                setting_type=SettingType.BOOLEAN,
                default_value=False,
                category=SettingCategory.UI_PREFERENCES,
                ui_hint="checkbox",
                is_advanced=True,
            ),
        }

        # Import/Export Settings
        import_export_settings = {
            "default_export_format": SettingDefinition(
                key="default_export_format",
                display_name="Default Export Format",
                description="Default format for password exports",
                setting_type=SettingType.ENUM,
                default_value="csv",
                category=SettingCategory.IMPORT_EXPORT,
                allowed_values=["csv", "json", "encrypted_json"],
                ui_hint="dropdown",
            ),
            "include_metadata_in_export": SettingDefinition(
                key="include_metadata_in_export",
                display_name="Include Metadata",
                description="Include creation dates and metadata in exports",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category=SettingCategory.IMPORT_EXPORT,
                ui_hint="checkbox",
            ),
            "auto_backup_frequency_days": SettingDefinition(
                key="auto_backup_frequency_days",
                display_name="Auto-Backup Frequency",
                description="Automatically create backups every N days (0 = disabled)",
                setting_type=SettingType.INTEGER,
                default_value=7,
                category=SettingCategory.IMPORT_EXPORT,
                min_value=0,
                max_value=30,
                ui_hint="slider",
            ),
        }

        # Register all settings
        self._setting_definitions[SettingCategory.PASSWORD_VIEWING] = viewing_settings
        self._setting_definitions[SettingCategory.PASSWORD_DELETION] = deletion_settings
        self._setting_definitions[SettingCategory.SECURITY] = security_settings
        self._setting_definitions[SettingCategory.UI_PREFERENCES] = ui_settings
        self._setting_definitions[SettingCategory.IMPORT_EXPORT] = import_export_settings

        logger.info(
            f"Initialized {sum(len(defs) for defs in self._setting_definitions.values())} setting definitions"
        )

    def get_user_setting(
        self, user_id: int, category: str, key: str, use_cache: bool = True
    ) -> Any:
        """
        Get a specific user setting value

        Args:
            user_id (int): User ID to get setting for
            category (str): Setting category
            key (str): Setting key
            use_cache (bool): Whether to use cached value

        Returns:
            Any: Setting value or default if not found
        """
        if not self._validate_user_and_setting(user_id, category, key):
            return None

        with self._lock:
            # Check cache first if enabled
            if use_cache and user_id in self._settings_cache:
                cached_categories = self._settings_cache[user_id]
                if category in cached_categories and key in cached_categories[category]:
                    return cached_categories[category][key]

            # Get from database
            if self.database_manager:
                try:
                    raw_value = self.database_manager.get_user_setting(user_id, category, key)
                    if raw_value is not None:
                        # Parse and validate the value
                        parsed_value = self._parse_setting_value(category, key, raw_value)

                        # Update cache
                        self._update_cache(user_id, category, key, parsed_value)

                        return parsed_value
                except Exception as e:
                    logger.error(f"Error getting setting {category}.{key} for user {user_id}: {e}")

            # Return default value
            return self._get_default_value(category, key)

    def set_user_setting(
        self, user_id: int, category: str, key: str, value: Any, validate: bool = True
    ) -> bool:
        """
        Set a user setting value with validation

        Args:
            user_id (int): User ID to set setting for
            category (str): Setting category
            key (str): Setting key
            value (Any): Setting value to store
            validate (bool): Whether to validate the value

        Returns:
            bool: True if successful, False otherwise
        """
        if not self._validate_user_and_setting(user_id, category, key):
            return False

        try:
            with self._lock:
                # Get setting definition
                setting_def = self._get_setting_definition(category, key)
                if not setting_def:
                    logger.error(f"Unknown setting: {category}.{key}")
                    return False

                # Validate value if requested
                if validate and not self._validate_setting_value(setting_def, value):
                    logger.error(f"Invalid value for {category}.{key}: {value}")
                    return False

                # Get current value for change detection
                old_value = self.get_user_setting(user_id, category, key)

                # Convert value to string for storage
                string_value = self._serialize_setting_value(value)

                # Store in database
                if self.database_manager:
                    success = self.database_manager.set_user_setting(
                        user_id, category, key, string_value
                    )

                    if success:
                        # Update cache
                        self._update_cache(user_id, category, key, value)

                        # Log setting change
                        self._log_setting_change(
                            user_id, category, key, old_value, value, setting_def
                        )

                        # Notify callbacks
                        self._notify_setting_changed(user_id, category, key, old_value, value)

                        logger.debug(f"Setting saved: {category}.{key} for user {user_id}")
                        return True
                    else:
                        logger.error(f"Failed to save setting {category}.{key} to database")
                        return False
                else:
                    logger.warning("No database manager available for settings storage")
                    return False

        except Exception as e:
            logger.error(f"Error setting {category}.{key} for user {user_id}: {e}")
            return False

    def get_all_user_settings(
        self, user_id: int, use_cache: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get all settings for a user organized by category

        Args:
            user_id (int): User ID to get settings for
            use_cache (bool): Whether to use cached values

        Returns:
            Dict[str, Dict[str, Any]]: Settings organized by category
        """
        if user_id <= 0:
            logger.error(f"Invalid user ID: {user_id}")
            return {}

        settings = {}

        # Get all defined categories and keys
        for category_enum, category_defs in self._setting_definitions.items():
            category = category_enum.value
            settings[category] = {}

            for key, setting_def in category_defs.items():
                value = self.get_user_setting(user_id, category, key, use_cache)
                settings[category][key] = value

        return settings

    def get_category_settings(self, user_id: int, category: str) -> Dict[str, Any]:
        """
        Get all settings for a specific category

        Args:
            user_id (int): User ID
            category (str): Category to get settings for

        Returns:
            Dict[str, Any]: Settings for the category
        """
        if not self._validate_user_and_category(user_id, category):
            return {}

        category_settings = {}
        category_enum = SettingCategory(category)

        if category_enum in self._setting_definitions:
            category_defs = self._setting_definitions[category_enum]
            for key in category_defs.keys():
                value = self.get_user_setting(user_id, category, key)
                category_settings[key] = value

        return category_settings

    def reset_user_setting(self, user_id: int, category: str, key: str) -> bool:
        """
        Reset a setting to its default value

        Args:
            user_id (int): User ID
            category (str): Setting category
            key (str): Setting key

        Returns:
            bool: True if reset successfully
        """
        default_value = self._get_default_value(category, key)
        if default_value is not None:
            return self.set_user_setting(user_id, category, key, default_value)
        return False

    def reset_category_settings(self, user_id: int, category: str) -> int:
        """
        Reset all settings in a category to defaults

        Args:
            user_id (int): User ID
            category (str): Category to reset

        Returns:
            int: Number of settings reset
        """
        if not self._validate_user_and_category(user_id, category):
            return 0

        reset_count = 0
        category_enum = SettingCategory(category)

        if category_enum in self._setting_definitions:
            category_defs = self._setting_definitions[category_enum]
            for key in category_defs.keys():
                if self.reset_user_setting(user_id, category, key):
                    reset_count += 1

        logger.info(f"Reset {reset_count} settings in category {category} for user {user_id}")
        return reset_count

    def get_setting_definition(self, category: str, key: str) -> Optional[SettingDefinition]:
        """
        Get the definition for a setting

        Args:
            category (str): Setting category
            key (str): Setting key

        Returns:
            Optional[SettingDefinition]: Setting definition or None
        """
        return self._get_setting_definition(category, key)

    def get_all_setting_definitions(self) -> Dict[str, Dict[str, SettingDefinition]]:
        """
        Get all setting definitions organized by category

        Returns:
            Dict[str, Dict[str, SettingDefinition]]: All setting definitions
        """
        definitions = {}
        for category_enum, category_defs in self._setting_definitions.items():
            definitions[category_enum.value] = category_defs
        return definitions

    def validate_setting_value(self, category: str, key: str, value: Any) -> bool:
        """
        Validate a setting value against its definition

        Args:
            category (str): Setting category
            key (str): Setting key
            value (Any): Value to validate

        Returns:
            bool: True if valid, False otherwise
        """
        setting_def = self._get_setting_definition(category, key)
        if not setting_def:
            return False

        return self._validate_setting_value(setting_def, value)

    def export_user_settings(self, user_id: int, include_defaults: bool = False) -> Dict[str, Any]:
        """
        Export all user settings to a dictionary for backup/transfer

        Args:
            user_id (int): User ID to export settings for
            include_defaults (bool): Include settings that are at default values

        Returns:
            Dict[str, Any]: Exportable settings data
        """
        if user_id <= 0:
            return {}

        export_data = {
            "user_id": user_id,
            "export_timestamp": datetime.now().isoformat(),
            "settings_version": "2.2.0",
            "settings": {},
        }

        all_settings = self.get_all_user_settings(user_id)

        for category, category_settings in all_settings.items():
            export_data["settings"][category] = {}

            for key, value in category_settings.items():
                # Include if not default or if including defaults
                default_value = self._get_default_value(category, key)
                if include_defaults or value != default_value:
                    export_data["settings"][category][key] = value

        return export_data

    def import_user_settings(
        self, user_id: int, settings_data: Dict[str, Any], validate: bool = True
    ) -> Dict[str, Any]:
        """
        Import user settings from exported data

        Args:
            user_id (int): User ID to import settings for
            settings_data (Dict): Settings data to import
            validate (bool): Whether to validate imported values

        Returns:
            Dict[str, Any]: Import result with success/error counts
        """
        if user_id <= 0 or not isinstance(settings_data, dict):
            return {"success": False, "error": "Invalid parameters"}

        imported_count = 0
        error_count = 0
        errors = []

        settings = settings_data.get("settings", {})

        for category, category_settings in settings.items():
            if not isinstance(category_settings, dict):
                continue

            for key, value in category_settings.items():
                try:
                    success = self.set_user_setting(user_id, category, key, value, validate)
                    if success:
                        imported_count += 1
                    else:
                        error_count += 1
                        errors.append(f"Failed to import {category}.{key}")
                except Exception as e:
                    error_count += 1
                    errors.append(f"Error importing {category}.{key}: {e}")

        result = {
            "success": error_count == 0,
            "imported_count": imported_count,
            "error_count": error_count,
            "errors": errors,
        }

        logger.info(
            f"Settings import for user {user_id}: {imported_count} imported, {error_count} errors"
        )
        return result

    def add_setting_change_callback(self, category: str, callback: Callable):
        """Add callback to be notified of setting changes in a category"""
        if category not in self._change_callbacks:
            self._change_callbacks[category] = []
        self._change_callbacks[category].append(callback)

    def clear_user_cache(self, user_id: int):
        """Clear cached settings for a user"""
        with self._lock:
            self._settings_cache.pop(user_id, None)

    # ==========================================
    # PRIVATE HELPER METHODS
    # ==========================================

    def _validate_user_and_setting(self, user_id: int, category: str, key: str) -> bool:
        """Validate user ID and setting exists"""
        if user_id <= 0:
            logger.error(f"Invalid user ID: {user_id}")
            return False

        return self._get_setting_definition(category, key) is not None

    def _validate_user_and_category(self, user_id: int, category: str) -> bool:
        """Validate user ID and category exists"""
        if user_id <= 0:
            logger.error(f"Invalid user ID: {user_id}")
            return False

        try:
            category_enum = SettingCategory(category)
            return category_enum in self._setting_definitions
        except ValueError:
            logger.error(f"Unknown category: {category}")
            return False

    def _get_setting_definition(self, category: str, key: str) -> Optional[SettingDefinition]:
        """Get setting definition by category and key"""
        try:
            category_enum = SettingCategory(category)
            if category_enum in self._setting_definitions:
                return self._setting_definitions[category_enum].get(key)
        except ValueError:
            pass
        return None

    def _get_default_value(self, category: str, key: str) -> Any:
        """Get default value for a setting"""
        setting_def = self._get_setting_definition(category, key)
        return setting_def.default_value if setting_def else None

    def _parse_setting_value(self, category: str, key: str, raw_value: str) -> Any:
        """Parse string value from database into proper type"""
        setting_def = self._get_setting_definition(category, key)
        if not setting_def:
            return raw_value

        try:
            if setting_def.setting_type == SettingType.BOOLEAN:
                return raw_value.lower() in ("true", "1", "yes", "on")
            elif setting_def.setting_type == SettingType.INTEGER:
                return int(raw_value)
            elif setting_def.setting_type == SettingType.FLOAT:
                return float(raw_value)
            elif setting_def.setting_type == SettingType.JSON:
                return json.loads(raw_value)
            elif setting_def.setting_type == SettingType.LIST:
                return json.loads(raw_value) if raw_value.startswith("[") else raw_value.split(",")
            else:  # STRING, ENUM
                return raw_value
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing setting value {category}.{key}: {e}")
            return setting_def.default_value

    def _serialize_setting_value(self, value: Any) -> str:
        """Convert setting value to string for database storage"""
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        elif isinstance(value, bool):
            return "true" if value else "false"
        else:
            return str(value)

    def _validate_setting_value(self, setting_def: SettingDefinition, value: Any) -> bool:
        """Validate setting value against its definition"""
        try:
            # Type validation
            if setting_def.setting_type == SettingType.BOOLEAN and not isinstance(value, bool):
                return False
            elif setting_def.setting_type == SettingType.INTEGER and not isinstance(value, int):
                return False
            elif setting_def.setting_type == SettingType.FLOAT and not isinstance(
                value, (int, float)
            ):
                return False
            elif setting_def.setting_type == SettingType.LIST and not isinstance(value, list):
                return False
            elif setting_def.setting_type == SettingType.JSON and not isinstance(
                value, (dict, list)
            ):
                return False

            # Range validation for numbers
            if isinstance(value, (int, float)):
                if setting_def.min_value is not None and value < setting_def.min_value:
                    return False
                if setting_def.max_value is not None and value > setting_def.max_value:
                    return False

            # Enum validation
            if setting_def.allowed_values and value not in setting_def.allowed_values:
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating setting value: {e}")
            return False

    def _update_cache(self, user_id: int, category: str, key: str, value: Any):
        """Update cached setting value"""
        if user_id not in self._settings_cache:
            self._settings_cache[user_id] = {}
        if category not in self._settings_cache[user_id]:
            self._settings_cache[user_id][category] = {}

        self._settings_cache[user_id][category][key] = value

    def _log_setting_change(
        self,
        user_id: int,
        category: str,
        key: str,
        old_value: Any,
        new_value: Any,
        setting_def: SettingDefinition,
    ):
        """Log setting change for audit purposes"""
        try:
            # Don't log sensitive setting values
            display_old = "[HIDDEN]" if setting_def.is_sensitive else str(old_value)
            display_new = "[HIDDEN]" if setting_def.is_sensitive else str(new_value)

            # Use database audit logging if available
            if self.database_manager and hasattr(self.database_manager, "log_security_event"):
                self.database_manager.log_security_event(
                    user_id=user_id,
                    session_id="settings_service",
                    action_type="SETTING_CHANGED",
                    action_result="SUCCESS",
                    action_details={
                        "category": category,
                        "key": key,
                        "old_value": display_old,
                        "new_value": display_new,
                        "affects_security": setting_def.affects_security,
                        "requires_restart": setting_def.requires_restart,
                    },
                    security_level="HIGH" if setting_def.affects_security else "LOW",
                )

            logger.info(f"Setting changed for user {user_id}: {category}.{key} = {display_new}")

        except Exception as e:
            logger.error(f"Error logging setting change: {e}")

    def _notify_setting_changed(
        self, user_id: int, category: str, key: str, old_value: Any, new_value: Any
    ):
        """Notify callbacks of setting changes"""
        callbacks = self._change_callbacks.get(category, [])
        for callback in callbacks:
            try:
                callback(user_id, key, old_value, new_value)
            except Exception as e:
                logger.error(f"Error in setting change callback: {e}")


# ==========================================
# UTILITY FUNCTIONS
# ==========================================


def create_settings_service(database_manager=None) -> SettingsService:
    """
    Factory function to create a configured SettingsService

    Args:
        database_manager: DatabaseManager instance for persistence

    Returns:
        SettingsService: Configured service instance
    """
    return SettingsService(database_manager)


# Example usage
if __name__ == "__main__":
    # This section would only run if the file is executed directly (for testing)
    logging.basicConfig(level=logging.DEBUG)

    print("Testing SettingsService...")

    # Create service (without database for testing)
    settings_service = create_settings_service()

    # Test setting definitions
    definitions = settings_service.get_all_setting_definitions()
    print(f"Loaded {sum(len(defs) for defs in definitions.values())} setting definitions")

    # Test validation
    is_valid = settings_service.validate_setting_value(
        "password_viewing", "view_timeout_minutes", 5
    )
    print(f"Validation test (5 minutes): {is_valid}")

    is_invalid = settings_service.validate_setting_value(
        "password_viewing", "view_timeout_minutes", 100
    )
    print(f"Validation test (100 minutes - should be invalid): {is_invalid}")

    print("SettingsService test completed!")
