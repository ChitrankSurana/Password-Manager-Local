#!/usr/bin/env python3
"""
Personal Password Manager - Password Generator Dialog
====================================================

This module provides an interactive password generation dialog with real-time
customization options, strength analysis, and multiple generation methods.

Author: Personal Password Manager
Version: 2.0.0
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import pyperclip
import logging
from typing import Optional

from ..themes import get_theme, create_themed_button, create_themed_entry, create_themed_label
from ...utils.password_generator import PasswordGenerator, GenerationMethod, GenerationOptions

logger = logging.getLogger(__name__)

class PasswordGeneratorDialog(ctk.CTkToplevel):
    """Interactive password generation dialog"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.theme = get_theme()
        self.generator = PasswordGenerator()
        
        # Variables
        self.length_var = ctk.IntVar(value=16)
        self.include_lowercase_var = ctk.BooleanVar(value=True)
        self.include_uppercase_var = ctk.BooleanVar(value=True)
        self.include_digits_var = ctk.BooleanVar(value=True)
        self.include_symbols_var = ctk.BooleanVar(value=True)
        self.generated_password_var = ctk.StringVar()
        
        self._setup_dialog()
        self._create_ui()
        self._generate_password()  # Generate initial password
    
    def _setup_dialog(self):
        """Setup dialog properties"""
        self.title("Password Generator")
        self.geometry("500x600")
        self.resizable(False, False)
        
        if self.master:
            x = self.master.winfo_x() + (self.master.winfo_width() // 2) - 250
            y = self.master.winfo_y() + (self.master.winfo_height() // 2) - 300
            self.geometry(f"500x600+{x}+{y}")
        
        self.transient(self.master)
        self.grab_set()
    
    def _create_ui(self):
        """Create the user interface"""
        spacing = self.theme.get_spacing()
        
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=spacing["padding_lg"], pady=spacing["padding_lg"])
        
        # Title
        title_label = create_themed_label(main_frame, "Password Generator", "label")
        title_label.configure(font=self.theme.get_fonts()["heading_medium"])
        title_label.pack(pady=(0, spacing["section_gap"]))
        
        # Generated password display
        password_frame = ctk.CTkFrame(main_frame)
        password_frame.pack(fill="x", pady=(0, spacing["section_gap"]))
        
        self.password_entry = create_themed_entry(
            password_frame,
            textvariable=self.generated_password_var,
            style="entry_password",
            state="readonly"
        )
        self.password_entry.pack(fill="x", padx=spacing["padding_md"], pady=spacing["padding_md"])
        
        # Copy button
        copy_btn = create_themed_button(
            password_frame,
            text="📋 Copy",
            style="button_primary",
            command=self._copy_password
        )
        copy_btn.pack(pady=(0, spacing["padding_md"]))
        
        # Options
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="both", expand=True, pady=(0, spacing["section_gap"]))
        
        # Length slider
        length_label = create_themed_label(options_frame, f"Length: {self.length_var.get()}", "label")
        length_label.pack(anchor="w", padx=spacing["padding_md"], pady=(spacing["padding_md"], 0))
        
        self.length_slider = ctk.CTkSlider(
            options_frame,
            from_=8,
            to=64,
            number_of_steps=56,
            variable=self.length_var,
            command=self._on_length_change
        )
        self.length_slider.pack(fill="x", padx=spacing["padding_md"], pady=spacing["padding_sm"])
        
        # Character type checkboxes
        char_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        char_frame.pack(fill="x", padx=spacing["padding_md"], pady=spacing["padding_sm"])
        
        self.lowercase_cb = ctk.CTkCheckBox(char_frame, text="Lowercase (a-z)", variable=self.include_lowercase_var, command=self._generate_password)
        self.lowercase_cb.pack(anchor="w", pady=spacing["padding_xs"])
        
        self.uppercase_cb = ctk.CTkCheckBox(char_frame, text="Uppercase (A-Z)", variable=self.include_uppercase_var, command=self._generate_password)
        self.uppercase_cb.pack(anchor="w", pady=spacing["padding_xs"])
        
        self.digits_cb = ctk.CTkCheckBox(char_frame, text="Digits (0-9)", variable=self.include_digits_var, command=self._generate_password)
        self.digits_cb.pack(anchor="w", pady=spacing["padding_xs"])
        
        self.symbols_cb = ctk.CTkCheckBox(char_frame, text="Symbols (!@#$)", variable=self.include_symbols_var, command=self._generate_password)
        self.symbols_cb.pack(anchor="w", pady=spacing["padding_xs"])
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        generate_btn = create_themed_button(
            button_frame,
            text="🎲 Generate New",
            style="button_secondary",
            command=self._generate_password
        )
        generate_btn.pack(side="left")
        
        close_btn = create_themed_button(
            button_frame,
            text="Close",
            style="button_secondary",
            command=self.destroy
        )
        close_btn.pack(side="right")
    
    def _on_length_change(self, value):
        """Handle length slider change"""
        length = int(value)
        self.length_var.set(length)
        
        # Update label
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkFrame):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, ctk.CTkLabel) and "Length:" in str(grandchild.cget("text")):
                                grandchild.configure(text=f"Length: {length}")
        
        self._generate_password()
    
    def _generate_password(self):
        """Generate a new password with current options"""
        try:
            options = GenerationOptions(
                length=self.length_var.get(),
                include_lowercase=self.include_lowercase_var.get(),
                include_uppercase=self.include_uppercase_var.get(),
                include_digits=self.include_digits_var.get(),
                include_symbols=self.include_symbols_var.get()
            )
            
            result = self.generator.generate_password(options, GenerationMethod.RANDOM)
            self.generated_password_var.set(result.password)
            
        except Exception as e:
            logger.error(f"Password generation failed: {e}")
            messagebox.showerror("Error", f"Failed to generate password: {str(e)}")
    
    def _copy_password(self):
        """Copy generated password to clipboard"""
        try:
            password = self.generated_password_var.get()
            if password:
                pyperclip.copy(password)
                messagebox.showinfo("Success", "Password copied to clipboard!")
        except Exception as e:
            logger.error(f"Failed to copy password: {e}")
            messagebox.showerror("Error", "Failed to copy password to clipboard")