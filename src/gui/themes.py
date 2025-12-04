#!/usr/bin/env python3
"""
Personal Password Manager - Modern GUI Theme System
==================================================

This module provides comprehensive theming support for the password manager GUI,
featuring modern Windows 11-style design with dark mode support and customizable
color schemes. It uses CustomTkinter for modern UI components with proper theming.

Key Features:
- Windows 11-inspired design language
- Dark and light theme modes
- Customizable color palettes
- Consistent styling across all components
- Accessibility considerations
- Theme persistence and user preferences
- Dynamic theme switching
- Component-specific styling

Design Principles:
- Modern flat design with subtle depth
- Consistent spacing and typography
- High contrast for accessibility
- Smooth animations and transitions
- Professional color schemes
- Responsive layout considerations

Author: Personal Password Manager
Version: 2.2.0
"""

import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import customtkinter as ctk

from ..utils.font_manager import get_font_manager

# Configure logging for theme operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThemeMode(Enum):
    """Theme mode enumeration"""

    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"


class ColorScheme(Enum):
    """Available color schemes"""

    BLUE = "blue"
    GREEN = "green"
    PURPLE = "purple"
    RED = "red"
    ORANGE = "orange"
    CUSTOM = "custom"


class ThemeManager:
    """
    Comprehensive theme management system for the password manager

    This class manages all theming aspects including colors, fonts, spacing,
    and component styles. It provides consistent theming across the entire
    application with support for multiple color schemes and modes.

    Features:
    - Dynamic theme switching
    - Color scheme management
    - Font and typography settings
    - Component-specific styling
    - Theme persistence
    - Accessibility support
    """

    def __init__(self, theme_config_path: str = "data/theme_config.json"):
        """
        Initialize the theme manager

        Args:
            theme_config_path (str): Path to theme configuration file
        """
        self.config_path = Path(theme_config_path)
        self.current_mode = ThemeMode.DARK
        self.current_scheme = ColorScheme.BLUE
        self._callbacks: List[Callable] = []  # Theme change callbacks

        # Load theme configuration
        self.config = self._load_theme_config()

        # Set up CustomTkinter appearance
        self._setup_customtkinter()

        logger.info(
            f"Theme manager initialized: {
                self.current_mode.value} mode, {
                self.current_scheme.value} scheme")

    def _setup_customtkinter(self):
        """Configure CustomTkinter appearance settings"""
        # Set appearance mode
        ctk.set_appearance_mode(self.current_mode.value)

        # Set color theme based on scheme
        if self.current_scheme == ColorScheme.BLUE:
            ctk.set_default_color_theme("blue")
        elif self.current_scheme == ColorScheme.GREEN:
            ctk.set_default_color_theme("green")
        else:
            ctk.set_default_color_theme("blue")  # Default fallback

    def get_colors(self) -> Dict[str, str]:
        """
        Get current theme color palette

        Returns:
            Dict[str, str]: Color definitions for current theme
        """
        mode_key = self.current_mode.value
        scheme_key = self.current_scheme.value

        # Get base colors for current mode
        if mode_key == "dark":
            colors = self._get_dark_colors()
        else:
            colors = self._get_light_colors()

        # Apply color scheme modifications
        colors.update(self._get_scheme_colors(scheme_key))

        return colors

    def _get_dark_colors(self) -> Dict[str, str]:
        """Get dark theme color palette"""
        return {
            # Primary background colors
            "bg_primary": "#1a1a1a",  # Main background
            "bg_secondary": "#2d2d2d",  # Secondary background
            "bg_tertiary": "#3d3d3d",  # Tertiary background (cards, panels)
            "bg_quaternary": "#4d4d4d",  # Quaternary background (hover states)
            # Surface colors
            "surface": "#2d2d2d",  # Card/panel surfaces
            "surface_variant": "#3d3d3d",  # Variant surface
            "surface_hover": "#404040",  # Hover state
            "surface_pressed": "#353535",  # Pressed state
            # Text colors
            "text_primary": "#ffffff",  # Primary text
            "text_secondary": "#b0b0b0",  # Secondary text
            "text_tertiary": "#808080",  # Tertiary text (hints, labels)
            "text_disabled": "#606060",  # Disabled text
            # Border and outline colors
            "border": "#404040",  # Default borders
            "border_light": "#505050",  # Light borders
            "border_heavy": "#606060",  # Heavy borders
            "outline": "#606060",  # Focus outlines
            # State colors
            "success": "#4ade80",  # Success green
            "warning": "#fbbf24",  # Warning yellow
            "error": "#f87171",  # Error red
            "info": "#60a5fa",  # Info blue
            # Interactive colors (will be overridden by scheme)
            "primary": "#3b82f6",  # Primary brand color
            "primary_hover": "#2563eb",  # Primary hover
            "primary_pressed": "#1d4ed8",  # Primary pressed
            "secondary": "#6b7280",  # Secondary color
            "secondary_hover": "#4b5563",  # Secondary hover
            # Shadow and elevation
            "shadow": "rgba(0, 0, 0, 0.5)",  # Drop shadows
            "shadow_light": "rgba(0, 0, 0, 0.3)",  # Light shadows
        }

    def _get_light_colors(self) -> Dict[str, str]:
        """Get light theme color palette"""
        return {
            # Primary background colors
            "bg_primary": "#ffffff",  # Main background
            "bg_secondary": "#f8fafc",  # Secondary background
            "bg_tertiary": "#f1f5f9",  # Tertiary background (cards, panels)
            "bg_quaternary": "#e2e8f0",  # Quaternary background (hover states)
            # Surface colors
            "surface": "#ffffff",  # Card/panel surfaces
            "surface_variant": "#f8fafc",  # Variant surface
            "surface_hover": "#f1f5f9",  # Hover state
            "surface_pressed": "#e2e8f0",  # Pressed state
            # Text colors
            "text_primary": "#1e293b",  # Primary text
            "text_secondary": "#475569",  # Secondary text
            "text_tertiary": "#64748b",  # Tertiary text (hints, labels)
            "text_disabled": "#94a3b8",  # Disabled text
            # Border and outline colors
            "border": "#e2e8f0",  # Default borders
            "border_light": "#f1f5f9",  # Light borders
            "border_heavy": "#cbd5e1",  # Heavy borders
            "outline": "#3b82f6",  # Focus outlines
            # State colors
            "success": "#059669",  # Success green
            "warning": "#d97706",  # Warning yellow
            "error": "#dc2626",  # Error red
            "info": "#2563eb",  # Info blue
            # Interactive colors (will be overridden by scheme)
            "primary": "#3b82f6",  # Primary brand color
            "primary_hover": "#2563eb",  # Primary hover
            "primary_pressed": "#1d4ed8",  # Primary pressed
            "secondary": "#6b7280",  # Secondary color
            "secondary_hover": "#4b5563",  # Secondary hover
            # Shadow and elevation
            "shadow": "rgba(0, 0, 0, 0.1)",  # Drop shadows
            "shadow_light": "rgba(0, 0, 0, 0.05)",  # Light shadows
        }

    def _get_scheme_colors(self, scheme: str) -> Dict[str, str]:
        """Get color scheme-specific colors"""
        schemes = {
            "blue": {
                "primary": "#3b82f6",
                "primary_hover": "#2563eb",
                "primary_pressed": "#1d4ed8",
                "accent": "#60a5fa",
                "accent_hover": "#3b82f6",
            },
            "green": {
                "primary": "#059669",
                "primary_hover": "#047857",
                "primary_pressed": "#065f46",
                "accent": "#10b981",
                "accent_hover": "#059669",
            },
            "purple": {
                "primary": "#7c3aed",
                "primary_hover": "#6d28d9",
                "primary_pressed": "#5b21b6",
                "accent": "#8b5cf6",
                "accent_hover": "#7c3aed",
            },
            "red": {
                "primary": "#dc2626",
                "primary_hover": "#b91c1c",
                "primary_pressed": "#991b1b",
                "accent": "#ef4444",
                "accent_hover": "#dc2626",
            },
            "orange": {
                "primary": "#ea580c",
                "primary_hover": "#c2410c",
                "primary_pressed": "#9a3412",
                "accent": "#f97316",
                "accent_hover": "#ea580c",
            },
        }

        return schemes.get(scheme, schemes["blue"])

    def get_fonts(self) -> Dict[str, Tuple[str, int, str]]:
        """
        Get font definitions for the current theme with user-preference scaling

        Returns:
            Dict[str, Tuple[str, int, str]]: Font definitions (family, size, weight)
        """
        # Get the global font manager for scaled fonts
        font_mgr = get_font_manager()

        return {
            # Heading fonts
            "heading_large": font_mgr.get_heading_large().as_tuple(),  # Page titles
            "heading_medium": font_mgr.get_heading().as_tuple(),  # Section headers
            "heading_small": font_mgr.get_heading_small().as_tuple(),  # Subsection headers
            # Body fonts
            "body_large": font_mgr.get_body().as_tuple(),  # Large body text
            "body_medium": font_mgr.get_body_small().as_tuple(),  # Standard body text
            "body_small": font_mgr.get_caption().as_tuple(),  # Small body text
            # UI fonts
            "button": font_mgr.get_body_small().as_tuple(),  # Button text
            "label": font_mgr.get_caption().as_tuple(),  # Form labels
            "input": font_mgr.get_body_small().as_tuple(),  # Input fields
            "caption": font_mgr.get_tiny().as_tuple(),  # Captions, hints
            # Monospace fonts
            "code": font_mgr.get_monospace_font("caption").as_tuple(),  # Code, passwords
            "code_small": font_mgr.get_monospace_font("tiny").as_tuple(),  # Small code text
        }

    def get_spacing(self) -> Dict[str, int]:
        """
        Get spacing definitions for consistent layout

        Returns:
            Dict[str, int]: Spacing values in pixels
        """
        return {
            # Padding values
            "padding_xs": 4,
            "padding_sm": 8,
            "padding_md": 12,
            "padding_lg": 16,
            "padding_xl": 24,
            "padding_xxl": 32,
            # Margin values
            "margin_xs": 4,
            "margin_sm": 8,
            "margin_md": 12,
            "margin_lg": 16,
            "margin_xl": 24,
            "margin_xxl": 32,
            # Component spacing
            "component_gap": 8,  # Gap between related components
            "section_gap": 16,  # Gap between sections
            "page_margin": 24,  # Page margins
            # Border radius
            "radius_sm": 4,
            "radius_md": 6,
            "radius_lg": 8,
            "radius_xl": 12,
            # Border width
            "border_thin": 1,
            "border_medium": 2,
            "border_thick": 3,
        }

    def get_component_style(self, component: str) -> Dict[str, Any]:
        """
        Get styling for specific components

        Args:
            component (str): Component name

        Returns:
            Dict[str, Any]: Component styling configuration
        """
        colors = self.get_colors()
        fonts = self.get_fonts()
        spacing = self.get_spacing()

        styles = {
            "window": {
                "fg_color": colors["bg_primary"],
                "corner_radius": 0,
            },
            "frame": {
                "fg_color": colors["surface"],
                "border_color": colors["border"],
                "border_width": spacing["border_thin"],
                "corner_radius": spacing["radius_md"],
            },
            "button_primary": {
                "fg_color": colors["primary"],
                "hover_color": colors["primary_hover"],
                "text_color": "#ffffff",
                "font": fonts["button"],
                "corner_radius": spacing["radius_md"],
                "border_width": 0,
                "height": 36,
            },
            "button_secondary": {
                "fg_color": colors["surface"],
                "hover_color": colors["surface_hover"],
                "text_color": colors["text_primary"],
                "border_color": colors["border"],
                "border_width": spacing["border_thin"],
                "font": fonts["button"],
                "corner_radius": spacing["radius_md"],
                "height": 36,
            },
            "button_danger": {
                "fg_color": colors["error"],
                "hover_color": "#dc2626",
                "text_color": "#ffffff",
                "font": fonts["button"],
                "corner_radius": spacing["radius_md"],
                "border_width": 0,
                "height": 36,
            },
            "entry": {
                "fg_color": colors["surface"],
                "border_color": colors["border"],
                "text_color": colors["text_primary"],
                "placeholder_text_color": colors["text_tertiary"],
                "font": fonts["input"],
                "corner_radius": spacing["radius_md"],
                "border_width": spacing["border_thin"],
                "height": 36,
            },
            "entry_password": {
                "fg_color": colors["surface"],
                "border_color": colors["border"],
                "text_color": colors["text_primary"],
                "font": fonts["code"],  # Monospace for passwords
                "corner_radius": spacing["radius_md"],
                "border_width": spacing["border_thin"],
                "height": 36,
            },
            "textbox": {
                "fg_color": colors["surface"],
                "border_color": colors["border"],
                "text_color": colors["text_primary"],
                "font": fonts["body_medium"],
                "corner_radius": spacing["radius_md"],
                "border_width": spacing["border_thin"],
            },
            "label": {
                "text_color": colors["text_primary"],
                "font": fonts["label"],
                "anchor": "w",
            },
            "label_secondary": {
                "text_color": colors["text_secondary"],
                "font": fonts["caption"],
                "anchor": "w",
            },
            "checkbox": {
                "checkbox_width": 18,
                "checkbox_height": 18,
                "corner_radius": spacing["radius_sm"],
                "border_width": spacing["border_thin"],
                "text_color": colors["text_primary"],
                "font": fonts["body_medium"],
            },
            "switch": {
                "switch_width": 48,
                "switch_height": 24,
                "corner_radius": 12,
                "border_width": spacing["border_thin"],
                "text_color": colors["text_primary"],
                "font": fonts["body_medium"],
            },
            "progressbar": {
                "fg_color": colors["bg_tertiary"],
                "progress_color": colors["primary"],
                "corner_radius": spacing["radius_sm"],
                "height": 8,
            },
            "scrollbar": {
                "fg_color": colors["bg_secondary"],
                "button_color": colors["bg_quaternary"],
                "button_hover_color": colors["surface_hover"],
                "corner_radius": spacing["radius_sm"],
            },
            "tabview": {
                "fg_color": colors["surface"],
                "border_color": colors["border"],
                "segmented_button_fg_color": colors["bg_secondary"],
                "segmented_button_selected_color": colors["primary"],
                "segmented_button_selected_hover_color": colors["primary_hover"],
                "text_color": colors["text_primary"],
                "corner_radius": spacing["radius_md"],
            },
            "toplevel": {
                "fg_color": colors["bg_primary"],
                "corner_radius": spacing["radius_lg"],
            },
            "menu": {
                "fg_color": colors["surface"],
                "border_color": colors["border_heavy"],
                "text_color": colors["text_primary"],
                "font": fonts["body_medium"],
                "corner_radius": spacing["radius_md"],
                "border_width": spacing["border_thin"],
            },
            "tooltip": {
                "fg_color": colors["bg_quaternary"],
                "text_color": colors["text_primary"],
                "corner_radius": spacing["radius_sm"],
                "font": fonts["caption"],
            },
        }

        return styles.get(component, {})

    def apply_component_style(self, widget, component: str):
        """
        Apply styling to a widget component

        Args:
            widget: Widget to style
            component (str): Component type
        """
        try:
            style = self.get_component_style(component)

            # Apply each style property
            for property_name, value in style.items():
                if hasattr(widget, "configure"):
                    widget.configure(**{property_name: value})

        except Exception as e:
            logger.error(f"Failed to apply style to {component}: {e}")

    def register_theme_change_callback(self, callback: Callable):
        """
        Register a callback to be called when theme changes

        Args:
            callback: Function to call when theme changes (receives old_mode, new_mode)
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)
            logger.debug(f"Registered theme change callback: {callback.__name__}")

    def unregister_theme_change_callback(self, callback: Callable):
        """
        Unregister a theme change callback

        Args:
            callback: Function to remove from callbacks
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            logger.debug(f"Unregistered theme change callback: {callback.__name__}")

    def set_theme_mode(self, mode: ThemeMode):
        """
        Change the theme mode with proper error handling and notifications

        Args:
            mode (ThemeMode): New theme mode

        Returns:
            bool: True if theme change was successful, False otherwise
        """
        old_mode = self.current_mode

        # Don't do anything if mode is the same
        if old_mode == mode:
            logger.debug(f"Theme mode already set to: {mode.value}")
            return True

        try:
            # Update current mode
            self.current_mode = mode

            # Apply to CustomTkinter
            ctk.set_appearance_mode(mode.value)

            # Save configuration
            self._save_theme_config()

            logger.info(f"Theme mode changed: {old_mode.value} → {mode.value}")

            # Notify all registered callbacks
            for callback in self._callbacks:
                try:
                    callback(old_mode, mode)
                except Exception as e:
                    logger.error(f"Theme callback error in {callback.__name__}: {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to change theme mode: {e}")
            # Rollback on error
            self.current_mode = old_mode
            try:
                ctk.set_appearance_mode(old_mode.value)
            except Exception:
                pass
            return False

    def set_color_scheme(self, scheme: ColorScheme):
        """
        Change the color scheme with proper error handling

        Args:
            scheme (ColorScheme): New color scheme

        Returns:
            bool: True if color scheme change was successful, False otherwise
        """
        old_scheme = self.current_scheme

        # Don't do anything if scheme is the same
        if old_scheme == scheme:
            logger.debug(f"Color scheme already set to: {scheme.value}")
            return True

        try:
            # Update current scheme
            self.current_scheme = scheme

            # Apply to CustomTkinter
            self._setup_customtkinter()

            # Save configuration
            self._save_theme_config()

            logger.info(f"Color scheme changed: {old_scheme.value} → {scheme.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to change color scheme: {e}")
            # Rollback on error
            self.current_scheme = old_scheme
            try:
                self._setup_customtkinter()
            except Exception:
                pass
            return False

    def _load_theme_config(self) -> Dict[str, Any]:
        """Load theme configuration from file"""
        default_config = {
            "mode": self.current_mode.value,
            "scheme": self.current_scheme.value,
            "custom_colors": {},
            "font_scale": 1.0,
        }

        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                # Update current settings from config
                self.current_mode = ThemeMode(config.get("mode", "dark"))
                self.current_scheme = ColorScheme(config.get("scheme", "blue"))

                return config

            except Exception as e:
                logger.error(f"Failed to load theme config: {e}")

        return default_config

    def _save_theme_config(self):
        """Save theme configuration to file"""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            config = {
                "mode": self.current_mode.value,
                "scheme": self.current_scheme.value,
                "custom_colors": self.config.get("custom_colors", {}),
                "font_scale": self.config.get("font_scale", 1.0),
                "saved_at": str(datetime.now().isoformat()),
            }

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save theme config: {e}")

    def get_strength_color(self, strength_level: str) -> str:
        """
        Get color for password strength indication

        Args:
            strength_level (str): Strength level name

        Returns:
            str: Color code for the strength level
        """
        colors = self.get_colors()

        strength_colors = {
            "very_weak": colors["error"],
            "weak": "#ff6b35",
            "fair": colors["warning"],
            "good": "#a3d977",
            "strong": colors["success"],
            "very_strong": "#00c851",
        }

        return strength_colors.get(strength_level, colors["text_tertiary"])


# Global theme manager instance
_theme_manager = None


def setup_theme(config_path: str = "data/theme_config.json") -> ThemeManager:
    """
    Initialize the global theme manager

    Args:
        config_path (str): Path to theme configuration file

    Returns:
        ThemeManager: Configured theme manager instance
    """
    global _theme_manager

    if _theme_manager is None:
        _theme_manager = ThemeManager(config_path)

    return _theme_manager


def get_theme() -> ThemeManager:
    """
    Get the global theme manager instance

    Returns:
        ThemeManager: Current theme manager
    """
    global _theme_manager

    if _theme_manager is None:
        _theme_manager = setup_theme()

    return _theme_manager


def apply_window_theme(window):
    """
    Apply theme to a window

    Args:
        window: Window to theme
    """
    theme = get_theme()
    colors = theme.get_colors()

    try:
        # Apply window background
        if hasattr(window, "configure"):
            window.configure(fg_color=colors["bg_primary"])

        # Set window icon and properties
        if hasattr(window, "iconify") and hasattr(window, "deiconify"):
            # This is a toplevel window
            try:
                window.title("Personal Password Manager")
                window.geometry("1000x700")
                window.minsize(800, 600)

                # Center window on screen
                window.update_idletasks()
                width = window.winfo_width()
                height = window.winfo_height()
                x = (window.winfo_screenwidth() // 2) - (width // 2)
                y = (window.winfo_screenheight() // 2) - (height // 2)
                window.geometry(f"{width}x{height}+{x}+{y}")

            except Exception as e:
                logger.debug(f"Could not set window properties: {e}")

    except Exception as e:
        logger.error(f"Failed to apply window theme: {e}")


# Utility functions for common theming tasks


def create_themed_frame(parent, style: str = "frame") -> ctk.CTkFrame:
    """Create a themed frame"""
    theme = get_theme()
    frame = ctk.CTkFrame(parent)
    theme.apply_component_style(frame, style)
    return frame


def create_themed_button(
    parent, text: str, style: str = "button_primary", **kwargs
) -> ctk.CTkButton:
    """Create a themed button"""
    theme = get_theme()
    button = ctk.CTkButton(parent, text=text, **kwargs)
    theme.apply_component_style(button, style)
    return button


def create_themed_entry(parent, style: str = "entry", **kwargs) -> ctk.CTkEntry:
    """Create a themed entry field"""
    theme = get_theme()
    entry = ctk.CTkEntry(parent, **kwargs)
    theme.apply_component_style(entry, style)
    return entry


def create_themed_label(parent, text: str, style: str = "label", **kwargs) -> ctk.CTkLabel:
    """Create a themed label"""
    theme = get_theme()
    label = ctk.CTkLabel(parent, text=text, **kwargs)
    theme.apply_component_style(label, style)
    return label


if __name__ == "__main__":
    # Test the theme system
    print("Testing Personal Password Manager Theme System...")

    try:
        # Initialize theme
        theme = setup_theme()

        # Test color retrieval
        colors = theme.get_colors()
        print(f"✓ Retrieved {len(colors)} color definitions")

        # Test font retrieval
        fonts = theme.get_fonts()
        print(f"✓ Retrieved {len(fonts)} font definitions")

        # Test spacing
        spacing = theme.get_spacing()
        print(f"✓ Retrieved {len(spacing)} spacing definitions")

        # Test component styling
        button_style = theme.get_component_style("button_primary")
        print(f"✓ Retrieved button style with {len(button_style)} properties")

        # Test theme switching
        theme.set_theme_mode(ThemeMode.LIGHT)
        light_colors = theme.get_colors()
        print("✓ Theme mode switching works")

        theme.set_theme_mode(ThemeMode.DARK)

        # Test color scheme switching
        theme.set_color_scheme(ColorScheme.GREEN)
        green_colors = theme.get_colors()
        print("✓ Color scheme switching works")

        # Test strength colors
        weak_color = theme.get_strength_color("weak")
        strong_color = theme.get_strength_color("strong")
        print(f"✓ Strength colors: weak={weak_color}, strong={strong_color}")

        print("✓ All theme system tests passed!")

    except Exception as e:
        print(f"❌ Theme system test failed: {e}")
        import traceback

        traceback.print_exc()
