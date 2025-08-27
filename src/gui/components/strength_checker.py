#!/usr/bin/env python3
"""
Personal Password Manager - Password Strength Indicator
=======================================================

This module provides visual password strength indication with real-time
analysis and improvement recommendations.

Author: Personal Password Manager
Version: 1.0.0
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional, Dict, Any

from ..themes import get_theme, create_themed_label
from ...utils.strength_checker import AdvancedPasswordStrengthChecker

class PasswordStrengthIndicator(ctk.CTkFrame):
    """Real-time password strength indicator widget"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.theme = get_theme()
        self.checker = AdvancedPasswordStrengthChecker(breach_check_enabled=False)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the strength indicator UI"""
        spacing = self.theme.get_spacing()
        
        # Configure frame
        colors = self.theme.get_colors()
        self.configure(fg_color=colors["surface"], corner_radius=spacing["radius_md"])
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self, height=8)
        self.progress_bar.pack(fill="x", padx=spacing["padding_md"], pady=(spacing["padding_md"], spacing["padding_sm"]))
        
        # Strength label
        self.strength_label = create_themed_label(self, "Enter password", "label_secondary")
        self.strength_label.pack(padx=spacing["padding_md"], pady=(0, spacing["padding_md"]))
    
    def update_strength(self, password: str):
        """Update strength indication for password"""
        if not password:
            self.progress_bar.set(0)
            self.strength_label.configure(text="Enter password")
            return
        
        try:
            # Get real-time analysis
            analysis = self.checker.analyze_password_realtime(password)
            
            # Update progress bar
            progress = analysis['progress'] / 100
            self.progress_bar.set(progress)
            
            # Update progress bar color based on strength
            strength_color = self.theme.get_strength_color(analysis['strength_level'])
            self.progress_bar.configure(progress_color=strength_color)
            
            # Update label
            strength_text = analysis['strength_level'].replace('_', ' ').title()
            score_text = f"{strength_text} ({analysis['strength_score']}/100)"
            self.strength_label.configure(text=score_text, text_color=strength_color)
            
        except Exception as e:
            self.strength_label.configure(text="Analysis error")