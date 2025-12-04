#!/usr/bin/env python3
"""
Personal Password Manager - Font Manager
========================================

This module provides global font size management and scaling for the entire
application, ensuring consistent typography and accessibility.

Key Features:
- User preference-based font scaling
- Percentage-based size calculations
- Consistent font family management
- Dynamic font size updates
- Preset font configurations

Author: Personal Password Manager
Version: 2.2.0
"""

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class FontConfig:
    """
    Font configuration with family and scaled sizes

    Attributes:
        family: Font family name
        size: Base font size
        weight: Font weight (e.g., "normal", "bold")
    """

    family: str
    size: int
    weight: str = "normal"

    def as_tuple(self) -> Tuple[str, int, str]:
        """Return font configuration as tuple for CustomTkinter"""
        if self.weight == "normal":
            return (self.family, self.size)
        return (self.family, self.size, self.weight)


class FontManager:
    """
    Global font manager for consistent typography

    This class manages font sizes across the entire application, providing
    scaled sizes based on user preferences and ensuring consistent typography.

    Font Size Presets:
    - small: 90% of base size
    - medium: 100% of base size (default)
    - large: 110% of base size
    - extra_large: 120% of base size

    Features:
    - Percentage-based scaling
    - Consistent font families
    - Dynamic size calculations
    - Category-based font management
    """

    # Base font sizes (medium/100%)
    BASE_SIZES = {
        "heading_large": 24,
        "heading": 18,
        "heading_small": 16,
        "body": 14,
        "body_small": 12,
        "caption": 11,
        "tiny": 10,
    }

    # Scale factors for each font size preference
    SCALE_FACTORS = {"small": 0.90, "medium": 1.00, "large": 1.10, "extra_large": 1.20}

    # Default font family
    DEFAULT_FONT_FAMILY = "Segoe UI"

    def __init__(self, font_size_preference: str = "medium"):
        """
        Initialize the font manager

        Args:
            font_size_preference: User's font size preference
                                 (small, medium, large, extra_large)
        """
        self.font_size_preference = font_size_preference
        self.scale_factor = self.SCALE_FACTORS.get(font_size_preference, 1.0)

    def set_font_size_preference(self, preference: str):
        """
        Update the font size preference

        Args:
            preference: New font size preference
        """
        if preference in self.SCALE_FACTORS:
            self.font_size_preference = preference
            self.scale_factor = self.SCALE_FACTORS[preference]

    def get_scale_factor(self) -> float:
        """Get the current scale factor"""
        return self.scale_factor

    def get_font_size_percentage(self) -> int:
        """Get the font size as a percentage"""
        return int(self.scale_factor * 100)

    def scale_size(self, base_size: int) -> int:
        """
        Scale a font size based on user preference

        Args:
            base_size: Base font size

        Returns:
            Scaled font size (rounded to nearest integer)
        """
        return round(base_size * self.scale_factor)

    def get_font(self, category: str, weight: str = "normal", family: str = None) -> FontConfig:
        """
        Get a scaled font configuration for a category

        Args:
            category: Font category (heading_large, heading, body, etc.)
            weight: Font weight ("normal", "bold")
            family: Font family (defaults to DEFAULT_FONT_FAMILY)

        Returns:
            FontConfig with scaled size
        """
        base_size = self.BASE_SIZES.get(category, self.BASE_SIZES["body"])
        scaled_size = self.scale_size(base_size)
        font_family = family or self.DEFAULT_FONT_FAMILY

        return FontConfig(font_family, scaled_size, weight)

    def get_all_fonts(self, family: str = None) -> Dict[str, FontConfig]:
        """
        Get all font configurations scaled for current preference

        Args:
            family: Font family to use (defaults to DEFAULT_FONT_FAMILY)

        Returns:
            Dictionary of font category -> FontConfig
        """
        fonts = {}
        font_family = family or self.DEFAULT_FONT_FAMILY

        for category, base_size in self.BASE_SIZES.items():
            scaled_size = self.scale_size(base_size)
            fonts[category] = FontConfig(font_family, scaled_size)

        return fonts

    def get_heading_large(self, bold: bool = True) -> FontConfig:
        """Get large heading font (24pt base)"""
        weight = "bold" if bold else "normal"
        return self.get_font("heading_large", weight)

    def get_heading(self, bold: bool = True) -> FontConfig:
        """Get standard heading font (18pt base)"""
        weight = "bold" if bold else "normal"
        return self.get_font("heading", weight)

    def get_heading_small(self, bold: bool = True) -> FontConfig:
        """Get small heading font (16pt base)"""
        weight = "bold" if bold else "normal"
        return self.get_font("heading_small", weight)

    def get_body(self, bold: bool = False) -> FontConfig:
        """Get body text font (14pt base)"""
        weight = "bold" if bold else "normal"
        return self.get_font("body", weight)

    def get_body_small(self, bold: bool = False) -> FontConfig:
        """Get small body text font (12pt base)"""
        weight = "bold" if bold else "normal"
        return self.get_font("body_small", weight)

    def get_caption(self) -> FontConfig:
        """Get caption font (11pt base)"""
        return self.get_font("caption")

    def get_tiny(self) -> FontConfig:
        """Get tiny font (10pt base)"""
        return self.get_font("tiny")

    def get_button_font(self, size: str = "medium") -> FontConfig:
        """
        Get button font

        Args:
            size: Button size (small, medium, large)

        Returns:
            Scaled FontConfig for button
        """
        size_map = {"small": "body_small", "medium": "body", "large": "heading_small"}
        category = size_map.get(size, "body")
        return self.get_font(category, "normal")

    def get_label_font(self, size: str = "body") -> FontConfig:
        """
        Get label font

        Args:
            size: Label size category

        Returns:
            Scaled FontConfig for label
        """
        return self.get_font(size, "normal")

    def get_input_font(self) -> FontConfig:
        """Get input field font"""
        return self.get_font("body", "normal")

    def get_monospace_font(self, size: str = "body") -> FontConfig:
        """
        Get monospace font (for passwords, code)

        Args:
            size: Font size category

        Returns:
            Scaled FontConfig with monospace family
        """
        return self.get_font(size, "normal", "Consolas")

    def __repr__(self) -> str:
        """String representation"""
        return f"FontManager(preference={self.font_size_preference}, scale={self.scale_factor})"


# Global font manager instance (will be initialized by app)
_global_font_manager: FontManager = None


def initialize_font_manager(font_size_preference: str = "medium") -> FontManager:
    """
    Initialize the global font manager

    Args:
        font_size_preference: User's font size preference

    Returns:
        Initialized FontManager instance
    """
    global _global_font_manager
    _global_font_manager = FontManager(font_size_preference)
    return _global_font_manager


def get_font_manager() -> FontManager:
    """
    Get the global font manager instance

    Returns:
        Global FontManager instance

    Raises:
        RuntimeError: If font manager not initialized
    """
    global _global_font_manager
    if _global_font_manager is None:
        # Initialize with default if not already initialized
        _global_font_manager = FontManager("medium")
    return _global_font_manager


def update_font_size_preference(preference: str):
    """
    Update the global font size preference

    Args:
        preference: New font size preference
    """
    font_manager = get_font_manager()
    font_manager.set_font_size_preference(preference)


# Export commonly used functions
__all__ = [
    "FontManager",
    "FontConfig",
    "initialize_font_manager",
    "get_font_manager",
    "update_font_size_preference",
]


if __name__ == "__main__":
    # Test the font manager
    print("Testing FontManager...")

    # Test different scales
    for preference in ["small", "medium", "large", "extra_large"]:
        fm = FontManager(preference)
        print(f"\n{preference.upper()} ({fm.get_font_size_percentage()}%):")
        print(f"  Heading Large: {fm.get_heading_large().size}pt")
        print(f"  Heading: {fm.get_heading().size}pt")
        print(f"  Body: {fm.get_body().size}pt")
        print(f"  Caption: {fm.get_caption().size}pt")

    print("\nFontManager test completed!")
