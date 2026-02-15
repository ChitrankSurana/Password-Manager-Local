"""
Personal Password Manager - Flet Theme Configuration
=====================================================

Material Design 3 theme system for the Flet UI. Maps the existing color
schemes (blue, green, purple, red, orange) from the CustomTkinter/Flask
interfaces to Flet's native theme API.

The theme supports:
- Dark/light mode toggle via page.theme_mode
- Color scheme switching via color_scheme_seed
- Consistent typography and spacing
- Persistence of user preference via SettingsService

Usage:
    from flet_app.theme import apply_theme, THEME_COLORS

    apply_theme(page, color_scheme="blue", dark_mode=True)

Version: 3.0.0
"""

import flet as ft
from typing import Optional


# ---------------------------------------------------------------------------
# COLOR SCHEME MAPPING
# ---------------------------------------------------------------------------
# Map our existing color scheme names to Material Design 3 seed colors.
# Flet generates a full tonal palette from each seed color.
THEME_COLORS = {
    "blue": "#2196F3",     # Material Blue 500
    "green": "#4CAF50",    # Material Green 500
    "purple": "#9C27B0",   # Material Purple 500
    "red": "#F44336",      # Material Red 500
    "orange": "#FF9800",   # Material Orange 500
}

# Default scheme used when no user preference is set
DEFAULT_COLOR_SCHEME = "blue"
DEFAULT_DARK_MODE = True


def apply_theme(
    page: ft.Page,
    color_scheme: str = DEFAULT_COLOR_SCHEME,
    dark_mode: bool = DEFAULT_DARK_MODE,
    font_family: Optional[str] = None,
) -> None:
    """
    Apply a Material Design 3 theme to the Flet page.

    This replaces the CustomTkinter theme system. Flet natively supports
    Material Design 3, so we only need to set the seed color and mode.

    Args:
        page: The Flet page to theme
        color_scheme: One of "blue", "green", "purple", "red", "orange"
        dark_mode: True for dark mode, False for light mode
        font_family: Optional font family override (default: system font)
    """
    # Resolve seed color from our scheme map
    seed_color = THEME_COLORS.get(color_scheme, THEME_COLORS[DEFAULT_COLOR_SCHEME])

    # Set theme mode (dark vs. light)
    page.theme_mode = ft.ThemeMode.DARK if dark_mode else ft.ThemeMode.LIGHT

    # Build the theme with the seed color
    page.theme = ft.Theme(
        color_scheme_seed=seed_color,
        # Use Material Design 3 visual density for a comfortable layout
        visual_density=ft.VisualDensity.COMFORTABLE,
    )

    # Dark theme uses the same seed so palette tones are consistent
    page.dark_theme = ft.Theme(
        color_scheme_seed=seed_color,
        visual_density=ft.VisualDensity.COMFORTABLE,
    )

    # Apply font if specified
    if font_family:
        page.theme = ft.Theme(
            color_scheme_seed=seed_color,
            visual_density=ft.VisualDensity.COMFORTABLE,
            font_family=font_family,
        )
        page.dark_theme = ft.Theme(
            color_scheme_seed=seed_color,
            visual_density=ft.VisualDensity.COMFORTABLE,
            font_family=font_family,
        )

    page.update()


def get_available_schemes() -> list:
    """
    Get the list of available color scheme names.

    Returns:
        List of scheme name strings (e.g., ["blue", "green", ...])
    """
    return list(THEME_COLORS.keys())
