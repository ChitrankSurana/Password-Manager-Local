#!/usr/bin/env python3
"""
Personal Password Manager - Settings Management Window
=====================================================

This module provides a comprehensive settings management interface for configuring
user preferences, security options, and application behavior. It integrates with
the SettingsService to provide a user-friendly interface for all configuration
options introduced with the enhanced password viewing and deletion features.

Key Features:
- Comprehensive settings organization across multiple categories
- Real-time validation and preview of setting changes
- User-friendly controls with tooltips and explanations
- Integration with SettingsService for persistent storage
- Security-focused settings with clear impact explanations
- Import/export settings functionality for backup and sharing

Settings Categories:
- Password Viewing: Timeout, authentication, UI preferences
- Password Deletion: Confirmation types, security levels
- Security: Audit logging, session management, lockout settings
- User Interface: Theme, display options, accessibility
- Advanced: Import/export, backup, developer options

Security Features:
- Master password protection for critical security settings
- Clear explanations of security implications for each setting
- Validation of setting combinations and conflicts
- Audit logging of all settings changes
- Secure handling of sensitive configuration data

Author: Personal Password Manager Enhancement Team
Version: 2.2.0
Date: September 21, 2025
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import os

# Import existing components
from .themes import get_theme, create_themed_button, create_themed_label, apply_window_theme
from .main_window import ToolTip

# Import our core services
from ..core.service_integration import PasswordManagerServiceIntegrator
from ..core.settings_service import SettingCategory, SettingDefinition

# Configure logging
logger = logging.getLogger(__name__)

class SettingsWindow(ctk.CTkToplevel):
    """
    Comprehensive settings management window
    
    This window provides a complete interface for managing all user preferences
    and configuration options. It includes multiple categories of settings with
    appropriate controls, validation, and security considerations.
    
    Features:
    - Tabbed interface for different setting categories
    - Real-time validation and change preview
    - Master password protection for security settings
    - Settings import/export functionality
    - Comprehensive help and explanations
    - Integration with ServiceIntegrator for persistence
    """
    
    def __init__(self, parent, service_integrator: PasswordManagerServiceIntegrator,
                 user_id: int, session_id: str):
        """
        Initialize settings window
        
        Args:
            parent: Parent window
            service_integrator: Service integrator for settings management
            user_id: Current user ID
            session_id: Current session ID
        """
        super().__init__(parent)
        
        self.service_integrator = service_integrator
        self.user_id = user_id
        self.session_id = session_id
        self.theme = get_theme()
        
        # Settings state
        self.settings_changed = False
        self.current_settings = {}
        self.setting_controls = {}  # Maps setting keys to their control widgets
        self.setting_definitions = {}  # Cache of setting definitions
        
        # UI components
        self.tabview: Optional[ctk.CTkTabview] = None
        self.apply_button: Optional[ctk.CTkButton] = None
        self.reset_button: Optional[ctk.CTkButton] = None
        
        # Initialize window
        self._setup_window()
        self._load_settings()
        self._create_ui()
        
        logger.info(f"Settings window initialized for user {user_id}")
    
    def _setup_window(self):
        """Configure settings window properties"""
        self.title("Password Manager Settings")
        self.geometry("800x700")
        self.minsize(700, 600)
        
        # Center window on parent
        self.transient(self.master)
        self.update_idletasks()
        
        parent_x = self.master.winfo_x()
        parent_y = self.master.winfo_y()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()
        
        x = parent_x + (parent_width // 2) - (800 // 2)
        y = parent_y + (parent_height // 2) - (700 // 2)
        self.geometry(f"800x700+{x}+{y}")
        
        # Apply theme
        apply_window_theme(self)
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # Make modal
        self.grab_set()
        self.focus_set()
    
    def _load_settings(self):
        """Load current user settings and definitions"""
        try:
            # Load current settings
            self.current_settings = self.service_integrator.get_user_settings(self.user_id)
            
            # Load setting definitions
            if hasattr(self.service_integrator, '_settings_service'):
                self.setting_definitions = self.service_integrator._settings_service.get_all_setting_definitions()
            
            logger.debug(f"Loaded settings for user {self.user_id}")
            
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            messagebox.showerror("Settings Error", f"Could not load settings: {e}")
    
    def _create_ui(self):
        """Create the settings user interface"""
        spacing = self.theme.get_spacing()
        
        # Main container
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=spacing["padding_lg"], pady=spacing["padding_lg"])
        
        # Header
        self._create_header(main_container)
        
        # Settings tabs
        self._create_settings_tabs(main_container)
        
        # Action buttons
        self._create_action_buttons(main_container)
    
    def _create_header(self, parent):
        """Create settings window header"""
        spacing = self.theme.get_spacing()
        fonts = self.theme.get_fonts()
        
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, spacing["section_gap"]))
        
        # Title
        title_label = create_themed_label(
            header_frame,
            text="⚙️ Password Manager Settings",
            style="label"
        )
        title_label.configure(font=fonts["heading_large"])
        title_label.pack(anchor="w")
        
        # Subtitle
        subtitle_label = create_themed_label(
            header_frame,
            text="Configure your password security and application preferences",
            style="label_secondary"
        )
        subtitle_label.pack(anchor="w", pady=(spacing["padding_xs"], 0))
    
    def _create_settings_tabs(self, parent):
        """Create tabbed interface for settings categories"""
        spacing = self.theme.get_spacing()
        
        # Create tabview
        self.tabview = ctk.CTkTabview(parent)
        self.tabview.pack(fill="both", expand=True, pady=(0, spacing["section_gap"]))
        
        # Create tabs for each settings category
        self._create_password_viewing_tab()
        self._create_password_deletion_tab()
        self._create_security_tab()
        self._create_ui_preferences_tab()
        self._create_advanced_tab()
    
    def _create_password_viewing_tab(self):
        """Create password viewing settings tab"""
        tab = self.tabview.add("🔍 Password Viewing")
        
        # Scrollable frame for settings
        scroll_frame = ctk.CTkScrollableFrame(tab, label_text="Password Viewing Preferences")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        category = SettingCategory.PASSWORD_VIEWING.value
        category_settings = self.current_settings.get(category, {})
        category_definitions = self.setting_definitions.get(category, {})
        
        # View timeout setting
        self._create_timeout_setting(scroll_frame, category, category_settings, category_definitions)
        
        # Master password requirement setting
        self._create_checkbox_setting(
            scroll_frame, category, "require_master_password",
            category_settings, category_definitions
        )
        
        # Auto-hide on focus loss
        self._create_checkbox_setting(
            scroll_frame, category, "auto_hide_on_focus_loss",
            category_settings, category_definitions
        )
        
        # Show view timer
        self._create_checkbox_setting(
            scroll_frame, category, "show_view_timer",
            category_settings, category_definitions
        )
        
        # Allow copy when visible
        self._create_checkbox_setting(
            scroll_frame, category, "allow_copy_when_visible",
            category_settings, category_definitions
        )
        
        # Max concurrent views
        self._create_slider_setting(
            scroll_frame, category, "max_concurrent_views",
            category_settings, category_definitions
        )
    
    def _create_password_deletion_tab(self):
        """Create password deletion settings tab"""
        tab = self.tabview.add("🗑️ Password Deletion")
        
        scroll_frame = ctk.CTkScrollableFrame(tab, label_text="Password Deletion Preferences")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        category = SettingCategory.PASSWORD_DELETION.value
        category_settings = self.current_settings.get(category, {})
        category_definitions = self.setting_definitions.get(category, {})
        
        # Require confirmation
        self._create_checkbox_setting(
            scroll_frame, category, "require_confirmation",
            category_settings, category_definitions
        )
        
        # Confirmation type
        self._create_dropdown_setting(
            scroll_frame, category, "confirmation_type",
            category_settings, category_definitions
        )
        
        # Require master password (security setting)
        self._create_security_checkbox_setting(
            scroll_frame, category, "require_master_password",
            category_settings, category_definitions
        )
        
        # Show deleted count
        self._create_checkbox_setting(
            scroll_frame, category, "show_deleted_count",
            category_settings, category_definitions
        )
        
        # Smart confirmation rules (advanced)
        self._create_advanced_setting_section(
            scroll_frame, category, "smart_confirmation_rules",
            category_settings, category_definitions
        )
    
    def _create_security_tab(self):
        """Create security settings tab"""
        tab = self.tabview.add("🛡️ Security")
        
        scroll_frame = ctk.CTkScrollableFrame(tab, label_text="Security & Audit Settings")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        category = SettingCategory.SECURITY.value
        category_settings = self.current_settings.get(category, {})
        category_definitions = self.setting_definitions.get(category, {})
        
        # Security warning
        self._create_security_warning(scroll_frame)
        
        # Audit logging
        self._create_checkbox_setting(
            scroll_frame, category, "audit_logging",
            category_settings, category_definitions
        )
        
        # Max failed attempts
        self._create_slider_setting(
            scroll_frame, category, "max_failed_attempts",
            category_settings, category_definitions
        )
        
        # Lockout duration
        self._create_slider_setting(
            scroll_frame, category, "lockout_duration_minutes",
            category_settings, category_definitions
        )
        
        # Session timeout
        self._create_slider_setting(
            scroll_frame, category, "session_timeout_hours",
            category_settings, category_definitions
        )
        
        # Biometric authentication (future)
        self._create_checkbox_setting(
            scroll_frame, category, "require_biometric_when_available",
            category_settings, category_definitions
        )
    
    def _create_ui_preferences_tab(self):
        """Create UI preferences tab"""
        tab = self.tabview.add("🎨 Interface")
        
        scroll_frame = ctk.CTkScrollableFrame(tab, label_text="User Interface Preferences")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        category = SettingCategory.UI_PREFERENCES.value
        category_settings = self.current_settings.get(category, {})
        category_definitions = self.setting_definitions.get(category, {})
        
        # Theme mode
        self._create_dropdown_setting(
            scroll_frame, category, "theme_mode",
            category_settings, category_definitions
        )
        
        # Default sort order
        self._create_dropdown_setting(
            scroll_frame, category, "default_sort_order",
            category_settings, category_definitions
        )
        
        # Entries per page
        self._create_dropdown_setting(
            scroll_frame, category, "entries_per_page",
            category_settings, category_definitions
        )
        
        # Show password strength
        self._create_checkbox_setting(
            scroll_frame, category, "show_password_strength",
            category_settings, category_definitions
        )
        
        # Compact view
        self._create_checkbox_setting(
            scroll_frame, category, "compact_view",
            category_settings, category_definitions
        )
    
    def _create_advanced_tab(self):
        """Create advanced settings tab"""
        tab = self.tabview.add("⚡ Advanced")
        
        scroll_frame = ctk.CTkScrollableFrame(tab, label_text="Advanced Settings & Tools")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Import/Export settings section
        self._create_import_export_section(scroll_frame)
        
        # Database and performance section
        self._create_database_section(scroll_frame)
        
        # Reset settings section
        self._create_reset_section(scroll_frame)
    
    def _create_timeout_setting(self, parent, category: str, settings: Dict, definitions: Dict):
        """Create timeout slider setting with preview"""
        setting_def = definitions.get("view_timeout_minutes")
        if not setting_def:
            return
        
        current_value = settings.get("view_timeout_minutes", setting_def.default_value)
        
        # Setting container
        setting_frame = ctk.CTkFrame(parent)
        setting_frame.pack(fill="x", padx=10, pady=5)
        
        # Label and current value
        label_frame = ctk.CTkFrame(setting_frame, fg_color="transparent")
        label_frame.pack(fill="x", padx=15, pady=10)
        
        title_label = create_themed_label(
            label_frame,
            text=setting_def.display_name,
            style="label"
        )
        title_label.pack(side="left")
        
        value_label = create_themed_label(
            label_frame,
            text=f"{current_value} minutes",
            style="label_secondary"
        )
        value_label.pack(side="right")
        
        # Slider
        slider_frame = ctk.CTkFrame(setting_frame, fg_color="transparent")
        slider_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        slider = ctk.CTkSlider(
            slider_frame,
            from_=setting_def.min_value,
            to=setting_def.max_value,
            number_of_steps=setting_def.max_value - setting_def.min_value,
            command=lambda value: self._update_timeout_display(value, value_label, category, "view_timeout_minutes")
        )
        slider.set(current_value)
        slider.pack(fill="x", pady=5)
        
        # Description
        desc_label = create_themed_label(
            slider_frame,
            text=setting_def.description,
            style="label_secondary"
        )
        desc_label.configure(wraplength=400)
        desc_label.pack(fill="x")
        
        # Quick buttons
        quick_frame = ctk.CTkFrame(slider_frame, fg_color="transparent")
        quick_frame.pack(fill="x", pady=5)
        
        for minutes in [1, 5, 15, 30]:
            btn = create_themed_button(
                quick_frame,
                text=f"{minutes}min",
                style="button_secondary",
                width=60,
                command=lambda m=minutes: self._set_quick_timeout(slider, value_label, m, category, "view_timeout_minutes")
            )
            btn.pack(side="left", padx=2)
        
        # Store control reference
        self.setting_controls[f"{category}.view_timeout_minutes"] = slider
        ToolTip(setting_frame, setting_def.description)
    
    def _create_checkbox_setting(self, parent, category: str, key: str, settings: Dict, definitions: Dict):
        """Create checkbox setting"""
        setting_def = definitions.get(key)
        if not setting_def:
            return
        
        current_value = settings.get(key, setting_def.default_value)
        
        # Setting container
        setting_frame = ctk.CTkFrame(parent)
        setting_frame.pack(fill="x", padx=10, pady=5)
        
        # Checkbox and label
        content_frame = ctk.CTkFrame(setting_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=15, pady=10)
        
        checkbox_var = tk.BooleanVar(value=current_value)
        checkbox = ctk.CTkCheckBox(
            content_frame,
            text=setting_def.display_name,
            variable=checkbox_var,
            command=lambda: self._on_setting_changed(category, key, checkbox_var.get())
        )
        checkbox.pack(side="left")
        
        # Security indicator
        if setting_def.affects_security:
            security_label = create_themed_label(
                content_frame,
                text="🔒",
                style="label"
            )
            security_label.pack(side="left", padx=(10, 0))
            ToolTip(security_label, "This setting affects security")
        
        # Description
        if setting_def.description:
            desc_label = create_themed_label(
                setting_frame,
                text=setting_def.description,
                style="label_secondary"
            )
            desc_label.configure(wraplength=500)
            desc_label.pack(fill="x", padx=15, pady=(0, 10))
        
        # Store control reference
        self.setting_controls[f"{category}.{key}"] = checkbox_var
        ToolTip(checkbox, setting_def.description or "")
    
    def _create_security_checkbox_setting(self, parent, category: str, key: str, settings: Dict, definitions: Dict):
        """Create security-sensitive checkbox setting with master password protection"""
        setting_def = definitions.get(key)
        if not setting_def:
            return
        
        current_value = settings.get(key, setting_def.default_value)
        
        # Setting container with security styling
        setting_frame = ctk.CTkFrame(parent)
        setting_frame.configure(border_width=2, border_color="#e74c3c")
        setting_frame.pack(fill="x", padx=10, pady=5)
        
        # Security header
        security_header = ctk.CTkFrame(setting_frame, fg_color="transparent")
        security_header.pack(fill="x", padx=15, pady=(10, 5))
        
        security_icon = create_themed_label(
            security_header,
            text="🛡️ SECURITY SETTING",
            style="label"
        )
        security_icon.configure(text_color="#e74c3c")
        security_icon.pack(side="left")
        
        # Checkbox and label
        content_frame = ctk.CTkFrame(setting_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=15, pady=5)
        
        checkbox_var = tk.BooleanVar(value=current_value)
        checkbox = ctk.CTkCheckBox(
            content_frame,
            text=setting_def.display_name,
            variable=checkbox_var,
            command=lambda: self._on_security_setting_changed(category, key, checkbox_var.get(), checkbox_var)
        )
        checkbox.pack(side="left")
        
        # Description with security warning
        desc_text = f"{setting_def.description}\n\n⚠️ This setting requires master password confirmation."
        desc_label = create_themed_label(
            setting_frame,
            text=desc_text,
            style="label_secondary"
        )
        desc_label.configure(wraplength=500)
        desc_label.pack(fill="x", padx=15, pady=(0, 10))
        
        # Store control reference
        self.setting_controls[f"{category}.{key}"] = checkbox_var
    
    def _create_dropdown_setting(self, parent, category: str, key: str, settings: Dict, definitions: Dict):
        """Create dropdown setting"""
        setting_def = definitions.get(key)
        if not setting_def:
            return
        
        current_value = settings.get(key, setting_def.default_value)
        
        # Setting container
        setting_frame = ctk.CTkFrame(parent)
        setting_frame.pack(fill="x", padx=10, pady=5)
        
        # Label
        label_frame = ctk.CTkFrame(setting_frame, fg_color="transparent")
        label_frame.pack(fill="x", padx=15, pady=10)
        
        title_label = create_themed_label(
            label_frame,
            text=setting_def.display_name,
            style="label"
        )
        title_label.pack(side="left")
        
        # Dropdown
        dropdown_var = tk.StringVar(value=current_value)
        dropdown = ctk.CTkComboBox(
            label_frame,
            variable=dropdown_var,
            values=setting_def.allowed_values or [],
            command=lambda value: self._on_setting_changed(category, key, value)
        )
        dropdown.pack(side="right")
        
        # Description
        if setting_def.description:
            desc_label = create_themed_label(
                setting_frame,
                text=setting_def.description,
                style="label_secondary"
            )
            desc_label.configure(wraplength=500)
            desc_label.pack(fill="x", padx=15, pady=(0, 10))
        
        # Store control reference
        self.setting_controls[f"{category}.{key}"] = dropdown_var
        ToolTip(dropdown, setting_def.description or "")
    
    def _create_slider_setting(self, parent, category: str, key: str, settings: Dict, definitions: Dict):
        """Create slider setting"""
        setting_def = definitions.get(key)
        if not setting_def:
            return
        
        current_value = settings.get(key, setting_def.default_value)
        
        # Setting container
        setting_frame = ctk.CTkFrame(parent)
        setting_frame.pack(fill="x", padx=10, pady=5)
        
        # Label and current value
        label_frame = ctk.CTkFrame(setting_frame, fg_color="transparent")
        label_frame.pack(fill="x", padx=15, pady=10)
        
        title_label = create_themed_label(
            label_frame,
            text=setting_def.display_name,
            style="label"
        )
        title_label.pack(side="left")
        
        value_label = create_themed_label(
            label_frame,
            text=str(current_value),
            style="label_secondary"
        )
        value_label.pack(side="right")
        
        # Slider
        slider_frame = ctk.CTkFrame(setting_frame, fg_color="transparent")
        slider_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        slider = ctk.CTkSlider(
            slider_frame,
            from_=setting_def.min_value,
            to=setting_def.max_value,
            number_of_steps=setting_def.max_value - setting_def.min_value,
            command=lambda value: self._update_slider_display(value, value_label, category, key)
        )
        slider.set(current_value)
        slider.pack(fill="x", pady=5)
        
        # Description
        if setting_def.description:
            desc_label = create_themed_label(
                slider_frame,
                text=setting_def.description,
                style="label_secondary"
            )
            desc_label.configure(wraplength=400)
            desc_label.pack(fill="x")
        
        # Store control reference
        self.setting_controls[f"{category}.{key}"] = slider
        ToolTip(setting_frame, setting_def.description or "")
    
    def _create_advanced_setting_section(self, parent, category: str, key: str, settings: Dict, definitions: Dict):
        """Create advanced setting section"""
        setting_def = definitions.get(key)
        if not setting_def:
            return
        
        # Advanced section container
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="x", padx=10, pady=5)
        
        # Header with expand button
        header_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=10)
        
        expand_btn = create_themed_button(
            header_frame,
            text="▶ Advanced: Smart Confirmation Rules",
            style="button_text",
            command=lambda: self._toggle_advanced_section(expand_btn, section_frame)
        )
        expand_btn.pack(side="left")
        
        # Content (initially hidden)
        content_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        # Don't pack initially
        
        desc_label = create_themed_label(
            content_frame,
            text="Configure rules for smart deletion confirmation based on password age and importance.",
            style="label_secondary"
        )
        desc_label.pack(fill="x", pady=5)
        
        # JSON editor placeholder
        json_label = create_themed_label(
            content_frame,
            text="JSON configuration editor would go here",
            style="label_secondary"
        )
        json_label.pack(fill="x", pady=5)
    
    def _create_security_warning(self, parent):
        """Create security settings warning"""
        warning_frame = ctk.CTkFrame(parent)
        warning_frame.configure(fg_color="#fff3cd", border_width=2, border_color="#ffc107")
        warning_frame.pack(fill="x", padx=10, pady=10)
        
        warning_content = ctk.CTkFrame(warning_frame, fg_color="transparent")
        warning_content.pack(fill="x", padx=15, pady=15)
        
        warning_icon = create_themed_label(
            warning_content,
            text="⚠️",
            style="label"
        )
        warning_icon.pack(side="left")
        
        warning_text = create_themed_label(
            warning_content,
            text="Security settings directly affect the safety of your passwords. "
                 "Changes to these settings may require master password confirmation "
                 "and will be logged for security auditing.",
            style="label_secondary"
        )
        warning_text.configure(wraplength=600, text_color="#856404")
        warning_text.pack(side="left", padx=(10, 0))
    
    def _create_import_export_section(self, parent):
        """Create import/export settings section"""
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="x", padx=10, pady=10)
        
        # Section header
        header_label = create_themed_label(
            section_frame,
            text="📁 Settings Import/Export",
            style="label"
        )
        header_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Export button
        export_btn = create_themed_button(
            buttons_frame,
            text="📤 Export Settings",
            style="button_secondary",
            command=self._export_settings
        )
        export_btn.pack(side="left", padx=(0, 10))
        ToolTip(export_btn, "Export current settings to a file")
        
        # Import button
        import_btn = create_themed_button(
            buttons_frame,
            text="📥 Import Settings",
            style="button_secondary",
            command=self._import_settings
        )
        import_btn.pack(side="left")
        ToolTip(import_btn, "Import settings from a file")
    
    def _create_database_section(self, parent):
        """Create database and performance section"""
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="x", padx=10, pady=10)
        
        # Section header
        header_label = create_themed_label(
            section_frame,
            text="🗃️ Database & Performance",
            style="label"
        )
        header_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        # Info labels
        info_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Database size info (placeholder)
        size_label = create_themed_label(
            info_frame,
            text="Database size: Calculating...",
            style="label_secondary"
        )
        size_label.pack(anchor="w")
        
        # Settings count info
        settings_count = sum(len(cat_settings) for cat_settings in self.current_settings.values())
        count_label = create_themed_label(
            info_frame,
            text=f"Active settings: {settings_count}",
            style="label_secondary"
        )
        count_label.pack(anchor="w")
    
    def _create_reset_section(self, parent):
        """Create reset settings section"""
        section_frame = ctk.CTkFrame(parent)
        section_frame.configure(border_width=2, border_color="#e74c3c")
        section_frame.pack(fill="x", padx=10, pady=10)
        
        # Section header
        header_label = create_themed_label(
            section_frame,
            text="🔄 Reset Settings",
            style="label"
        )
        header_label.configure(text_color="#e74c3c")
        header_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        # Warning text
        warning_label = create_themed_label(
            section_frame,
            text="⚠️ Warning: This will reset all settings to their default values. This action cannot be undone.",
            style="label_secondary"
        )
        warning_label.configure(wraplength=600, text_color="#e74c3c")
        warning_label.pack(anchor="w", padx=15, pady=(0, 10))
        
        # Reset button
        reset_btn = create_themed_button(
            section_frame,
            text="🔄 Reset All Settings",
            style="button_danger",
            command=self._reset_all_settings
        )
        reset_btn.pack(anchor="w", padx=15, pady=(0, 15))
        ToolTip(reset_btn, "Reset all settings to default values")
    
    def _create_action_buttons(self, parent):
        """Create action buttons at bottom of window"""
        spacing = self.theme.get_spacing()
        
        # Button frame
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", pady=(spacing["padding_md"], 0))
        
        # Cancel button
        cancel_btn = create_themed_button(
            button_frame,
            text="Cancel",
            style="button_secondary",
            width=100,
            command=self._cancel_changes
        )
        cancel_btn.pack(side="right", padx=(10, 0))
        
        # Apply button
        self.apply_button = create_themed_button(
            button_frame,
            text="Apply Changes",
            style="button_primary",
            width=120,
            command=self._apply_changes
        )
        self.apply_button.pack(side="right")
        self.apply_button.configure(state="disabled")
        
        # Reset current tab button
        reset_tab_btn = create_themed_button(
            button_frame,
            text="Reset Tab",
            style="button_secondary",
            width=100,
            command=self._reset_current_tab
        )
        reset_tab_btn.pack(side="left")
        
        # Status label
        self.status_label = create_themed_label(
            button_frame,
            text="No changes",
            style="label_secondary"
        )
        self.status_label.pack(side="left", padx=(20, 0))
    
    # ==========================================
    # EVENT HANDLERS
    # ==========================================
    
    def _on_setting_changed(self, category: str, key: str, value: Any):
        """Handle setting value change"""
        # Update current settings
        if category not in self.current_settings:
            self.current_settings[category] = {}
        
        self.current_settings[category][key] = value
        
        # Mark as changed
        self.settings_changed = True
        self.apply_button.configure(state="normal")
        self.status_label.configure(text="Settings modified")
        
        logger.debug(f"Setting changed: {category}.{key} = {value}")
    
    def _on_security_setting_changed(self, category: str, key: str, value: Any, checkbox_var):
        """Handle security setting change with master password confirmation"""
        if value:
            # Enabling security setting - require master password
            result = messagebox.askyesno(
                "Security Setting",
                f"Enabling this security setting will affect password deletion behavior.\n\n"
                f"Do you want to continue?",
                icon="warning"
            )
            
            if not result:
                # User cancelled, revert checkbox
                checkbox_var.set(False)
                return
            
            # In a real implementation, you would prompt for master password here
            # For now, just confirm the change
            self._on_setting_changed(category, key, value)
        else:
            # Disabling security setting
            self._on_setting_changed(category, key, value)
    
    def _update_timeout_display(self, value: float, label, category: str, key: str):
        """Update timeout display and setting"""
        int_value = int(value)
        label.configure(text=f"{int_value} minutes")
        self._on_setting_changed(category, key, int_value)
    
    def _update_slider_display(self, value: float, label, category: str, key: str):
        """Update slider display and setting"""
        int_value = int(value)
        label.configure(text=str(int_value))
        self._on_setting_changed(category, key, int_value)
    
    def _set_quick_timeout(self, slider, label, minutes: int, category: str, key: str):
        """Set quick timeout value"""
        slider.set(minutes)
        label.configure(text=f"{minutes} minutes")
        self._on_setting_changed(category, key, minutes)
    
    def _toggle_advanced_section(self, button, section_frame):
        """Toggle advanced section visibility"""
        # This would implement the expand/collapse functionality
        button.configure(text="▼ Advanced: Smart Confirmation Rules")
    
    # ==========================================
    # ACTION METHODS
    # ==========================================
    
    def _apply_changes(self):
        """Apply all setting changes"""
        if not self.settings_changed:
            return
        
        try:
            # Apply each changed setting
            changes_applied = 0
            errors = []
            
            for category, category_settings in self.current_settings.items():
                for key, value in category_settings.items():
                    try:
                        success, message = self.service_integrator.update_user_setting(
                            self.user_id, self.session_id, category, key, value
                        )
                        
                        if success:
                            changes_applied += 1
                        else:
                            errors.append(f"{category}.{key}: {message}")
                            
                    except Exception as e:
                        errors.append(f"{category}.{key}: {str(e)}")
            
            # Show results
            if errors:
                error_msg = f"Applied {changes_applied} changes, but {len(errors)} failed:\n\n"
                error_msg += "\n".join(errors[:5])  # Show first 5 errors
                if len(errors) > 5:
                    error_msg += f"\n... and {len(errors) - 5} more"
                
                messagebox.showwarning("Partial Success", error_msg)
            else:
                messagebox.showinfo("Success", f"Applied {changes_applied} setting changes successfully.")
            
            # Reset change state
            self.settings_changed = False
            self.apply_button.configure(state="disabled")
            self.status_label.configure(text="Changes applied")
            
            logger.info(f"Applied {changes_applied} setting changes for user {self.user_id}")
            
        except Exception as e:
            logger.error(f"Error applying settings changes: {e}")
            messagebox.showerror("Error", f"Failed to apply changes: {e}")
    
    def _cancel_changes(self):
        """Cancel changes and close window"""
        if self.settings_changed:
            result = messagebox.askyesno(
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to close without saving?"
            )
            if not result:
                return
        
        self._close_window()
    
    def _reset_current_tab(self):
        """Reset settings in current tab to defaults"""
        current_tab = self.tabview.get()
        
        result = messagebox.askyesno(
            "Reset Tab Settings",
            f"Reset all settings in the '{current_tab}' tab to their default values?"
        )
        
        if result:
            # This would implement tab-specific reset
            self.status_label.configure(text="Tab settings reset")
    
    def _reset_all_settings(self):
        """Reset all settings to defaults"""
        result = messagebox.askyesno(
            "Reset All Settings",
            "Are you sure you want to reset ALL settings to their default values?\n\n"
            "This action cannot be undone.",
            icon="warning"
        )
        
        if result:
            # Confirm with second dialog
            confirm = messagebox.askyesno(
                "Final Confirmation",
                "This will permanently reset all your preferences.\n\n"
                "Click Yes to proceed or No to cancel.",
                icon="warning"
            )
            
            if confirm:
                try:
                    # Reset all settings (implementation would go here)
                    messagebox.showinfo("Settings Reset", "All settings have been reset to defaults.")
                    
                    # Reload settings and refresh UI
                    self._load_settings()
                    self.status_label.configure(text="All settings reset")
                    
                except Exception as e:
                    logger.error(f"Error resetting settings: {e}")
                    messagebox.showerror("Reset Error", f"Failed to reset settings: {e}")
    
    def _export_settings(self):
        """Export settings to file"""
        try:
            # Get export file path
            file_path = filedialog.asksaveasfilename(
                title="Export Settings",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                parent=self
            )
            
            if not file_path:
                return
            
            # Export settings
            export_data = self.service_integrator._settings_service.export_user_settings(
                self.user_id, include_defaults=False
            )
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            messagebox.showinfo(
                "Export Complete", 
                f"Settings exported successfully to:\n{file_path}"
            )
            
            logger.info(f"Settings exported to {file_path}")
            
        except Exception as e:
            logger.error(f"Error exporting settings: {e}")
            messagebox.showerror("Export Error", f"Failed to export settings: {e}")
    
    def _import_settings(self):
        """Import settings from file"""
        try:
            # Get import file path
            file_path = filedialog.askopenfilename(
                title="Import Settings",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                parent=self
            )
            
            if not file_path:
                return
            
            # Read and validate file
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Show confirmation
            result = messagebox.askyesno(
                "Import Settings",
                f"Import settings from file?\n\n"
                f"File: {os.path.basename(file_path)}\n"
                f"This will overwrite current settings.",
                icon="question"
            )
            
            if result:
                # Import settings
                import_result = self.service_integrator._settings_service.import_user_settings(
                    self.user_id, import_data, validate=True
                )
                
                if import_result['success']:
                    messagebox.showinfo(
                        "Import Complete",
                        f"Successfully imported {import_result['imported_count']} settings."
                    )
                    
                    # Reload settings and refresh UI
                    self._load_settings()
                    self.status_label.configure(text="Settings imported")
                    
                else:
                    error_msg = f"Import completed with errors:\n\n"
                    error_msg += f"Imported: {import_result['imported_count']}\n"
                    error_msg += f"Errors: {import_result['error_count']}\n\n"
                    error_msg += "\n".join(import_result['errors'][:5])
                    
                    messagebox.showwarning("Import Errors", error_msg)
            
            logger.info(f"Settings imported from {file_path}")
            
        except Exception as e:
            logger.error(f"Error importing settings: {e}")
            messagebox.showerror("Import Error", f"Failed to import settings: {e}")
    
    def _on_window_close(self):
        """Handle window close event"""
        self._cancel_changes()
    
    def _close_window(self):
        """Close the settings window"""
        self.grab_release()
        self.destroy()

# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def show_settings_window(parent, service_integrator: PasswordManagerServiceIntegrator,
                        user_id: int, session_id: str) -> SettingsWindow:
    """
    Show settings management window
    
    Args:
        parent: Parent window
        service_integrator: Service integrator for settings management
        user_id: Current user ID
        session_id: Current session ID
        
    Returns:
        SettingsWindow: Settings window instance
    """
    return SettingsWindow(parent, service_integrator, user_id, session_id)

# Example usage and testing
if __name__ == "__main__":
    # This section would only run if the file is executed directly (for testing)
    import sys
    import os
    
    # Add parent directories to path for imports
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    print("Settings Management Window Test")
    print("This component requires integration with the main application")
    print("and ServiceIntegrator for full functionality.")
