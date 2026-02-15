"""
Personal Password Manager - Password Generator Page
=====================================================

Dedicated page for generating passwords using multiple methods:
- Random: Cryptographically random characters with configurable character sets
- Memorable: Dictionary-based passphrases (word-separator-word)
- Pattern: Template-based generation (e.g., "Llll-dddd-Ssss")
- Pronounceable: Semi-random but pronounceable syllables

The user selects a method, adjusts settings, clicks Generate, and can copy
the result to clipboard. A strength indicator shows real-time feedback.

Version: 3.0.0
"""

import flet as ft
from typing import Optional

from ..components.nav_rail import NavRail
from ..components.strength_indicator import StrengthIndicator
from ..components.confirm_dialog import show_snack_bar
from ..state import AppState


class GeneratorPage(ft.Container):
    """
    Password generator with method selection and configuration controls.

    Layout:
        NavRail | Method selector tabs
               | Config controls (length slider, toggles, etc.)
               | [Generate] button
               | Result display + copy button + strength indicator

    Args:
        state: The shared AppState object
    """

    def __init__(self, state: AppState):
        self.state = state

        # --- Method selector ---
        self._method_dropdown = ft.Dropdown(
            label="Generation Method",
            value="random",
            width=250,
            options=[
                ft.dropdown.Option("random", "Random (Recommended)"),
                ft.dropdown.Option("memorable", "Memorable Passphrase"),
                ft.dropdown.Option("pattern", "Pattern-Based"),
                ft.dropdown.Option("pronounceable", "Pronounceable"),
            ],
            on_change=self._on_method_change,
        )

        # ---- Random method controls ----
        self._length_slider = ft.Slider(
            min=8,
            max=64,
            value=20,
            divisions=56,
            label="{value}",
            on_change=self._on_length_change,
            expand=True,
        )
        self._length_label = ft.Text("Length: 20", size=14)

        self._uppercase_switch = ft.Switch(label="Uppercase (A-Z)", value=True)
        self._lowercase_switch = ft.Switch(label="Lowercase (a-z)", value=True)
        self._digits_switch = ft.Switch(label="Digits (0-9)", value=True)
        self._symbols_switch = ft.Switch(label="Symbols (!@#$...)", value=True)
        self._exclude_similar_switch = ft.Switch(
            label="Exclude similar (0, O, l, 1)", value=True
        )

        # Container for random-method options
        self._random_options = ft.Column(
            [
                ft.Row(
                    [self._length_label, self._length_slider],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    [self._uppercase_switch, self._lowercase_switch],
                    wrap=True,
                ),
                ft.Row(
                    [self._digits_switch, self._symbols_switch],
                    wrap=True,
                ),
                self._exclude_similar_switch,
            ],
            spacing=8,
            visible=True,  # Visible by default (random is default method)
        )

        # ---- Memorable method controls ----
        self._word_count_slider = ft.Slider(
            min=3,
            max=8,
            value=4,
            divisions=5,
            label="{value}",
            on_change=self._on_word_count_change,
            expand=True,
        )
        self._word_count_label = ft.Text("Words: 4", size=14)

        self._separator_field = ft.TextField(
            label="Separator",
            value="-",
            width=80,
            text_align=ft.TextAlign.CENTER,
        )
        self._capitalize_switch = ft.Switch(label="Capitalize words", value=True)
        self._add_numbers_switch = ft.Switch(label="Add numbers", value=True)

        self._memorable_options = ft.Column(
            [
                ft.Row(
                    [self._word_count_label, self._word_count_slider],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    [self._separator_field, self._capitalize_switch, self._add_numbers_switch],
                    wrap=True,
                    spacing=12,
                ),
            ],
            spacing=8,
            visible=False,
        )

        # ---- Pattern method controls ----
        self._pattern_field = ft.TextField(
            label="Pattern Template",
            hint_text="L=upper, l=lower, d=digit, s=symbol (e.g., Llll-dddd-Ssss)",
            value="Llll-dddd-Ssss",
            width=400,
        )

        self._pattern_options = ft.Column(
            [
                self._pattern_field,
                ft.Text(
                    "L = uppercase, l = lowercase, d = digit, s = symbol, - = literal",
                    size=11,
                    opacity=0.6,
                ),
            ],
            spacing=4,
            visible=False,
        )

        # ---- Pronounceable has no extra options ----
        self._pronounceable_options = ft.Column(
            [
                ft.Text(
                    "Generates a semi-random pronounceable password using syllable patterns.",
                    size=13,
                    opacity=0.7,
                ),
            ],
            visible=False,
        )

        # --- Generate button ---
        self._generate_btn = ft.FilledButton(
            text="Generate Password",
            icon=ft.Icons.AUTO_FIX_HIGH,
            on_click=self._on_generate,
            width=220,
        )

        # --- Result display ---
        self._result_field = ft.TextField(
            label="Generated Password",
            read_only=True,
            text_size=16,
            width=400,
        )

        self._copy_btn = ft.IconButton(
            icon=ft.Icons.CONTENT_COPY,
            tooltip="Copy to clipboard",
            on_click=self._on_copy,
        )

        # --- Strength indicator ---
        self._strength_indicator = StrengthIndicator()

        # --- Build page layout ---
        content_area = ft.Column(
            [
                ft.Text("Password Generator", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=1),
                self._method_dropdown,
                ft.Container(height=8),
                # Method-specific option panels
                self._random_options,
                self._memorable_options,
                self._pattern_options,
                self._pronounceable_options,
                ft.Container(height=8),
                # Generate button (centered)
                ft.Container(
                    content=self._generate_btn,
                    alignment=ft.alignment.center,
                ),
                ft.Container(height=16),
                # Result row
                ft.Row(
                    [self._result_field, self._copy_btn],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                ),
                self._strength_indicator,
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            expand=True,
        )

        nav_rail = NavRail(state=state, current_route="/generator")

        super().__init__(
            content=ft.Row(
                [
                    nav_rail,
                    ft.VerticalDivider(width=1),
                    ft.Container(
                        content=content_area,
                        padding=ft.padding.all(24),
                        expand=True,
                    ),
                ],
                expand=True,
            ),
            expand=True,
        )

    # ------------------------------------------------------------------
    # Method switching
    # ------------------------------------------------------------------

    def _on_method_change(self, e: ft.ControlEvent) -> None:
        """Show/hide option panels based on selected method."""
        method = e.control.value
        self._random_options.visible = method == "random"
        self._memorable_options.visible = method == "memorable"
        self._pattern_options.visible = method == "pattern"
        self._pronounceable_options.visible = method == "pronounceable"
        self.update()

    # ------------------------------------------------------------------
    # Slider label updates
    # ------------------------------------------------------------------

    def _on_length_change(self, e: ft.ControlEvent) -> None:
        self._length_label.value = f"Length: {int(e.control.value)}"
        self.update()

    def _on_word_count_change(self, e: ft.ControlEvent) -> None:
        self._word_count_label.value = f"Words: {int(e.control.value)}"
        self.update()

    # ------------------------------------------------------------------
    # Generate
    # ------------------------------------------------------------------

    def _on_generate(self, e: ft.ControlEvent) -> None:
        """
        Generate a password using the selected method and display it.

        Builds a GenerationOptions object from the current UI state and
        calls PasswordGenerator.generate_password().
        """
        if not self.state.password_generator:
            show_snack_bar(self.state.page, "Generator not available.")
            return

        try:
            from utils.password_generator import GenerationMethod, GenerationOptions

            method_str = self._method_dropdown.value
            method = GenerationMethod(method_str)

            # Build options from UI controls
            options = GenerationOptions(
                length=int(self._length_slider.value),
                include_uppercase=self._uppercase_switch.value,
                include_lowercase=self._lowercase_switch.value,
                include_digits=self._digits_switch.value,
                include_symbols=self._symbols_switch.value,
                exclude_similar=self._exclude_similar_switch.value,
                word_count=int(self._word_count_slider.value),
                word_separator=self._separator_field.value or "-",
                capitalize_words=self._capitalize_switch.value,
                add_numbers=self._add_numbers_switch.value,
                pattern_template=self._pattern_field.value or "",
            )

            result = self.state.password_generator.generate_password(options, method)
            password = result.password

            # Display result
            self._result_field.value = password

            # Update strength indicator
            if self.state.strength_checker:
                analysis = self.state.strength_checker.analyze_password_realtime(password)
                level = analysis.get("strength_level", "very_weak")
                self._strength_indicator.set_strength(level)

            self.update()

        except Exception as ex:
            show_snack_bar(self.state.page, f"Generation failed: {ex}")

    # ------------------------------------------------------------------
    # Copy to clipboard
    # ------------------------------------------------------------------

    def _on_copy(self, e: ft.ControlEvent) -> None:
        """Copy the generated password to the system clipboard."""
        password = self._result_field.value
        if password:
            try:
                self.state.page.set_clipboard(password)
                show_snack_bar(self.state.page, "Password copied to clipboard.")
            except Exception:
                show_snack_bar(self.state.page, "Failed to copy.")
        else:
            show_snack_bar(self.state.page, "No password generated yet.")
