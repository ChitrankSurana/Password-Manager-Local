#!/usr/bin/env python3
"""
Personal Password Manager - Backup Manager Dialog
=================================================

This module provides comprehensive backup and restore functionality with export/import
capabilities for the password manager, featuring a modern interface for data management.

Author: Personal Password Manager
Version: 2.2.0
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import threading
import logging
from datetime import datetime
from pathlib import Path
import os
import shutil

from ..themes import get_theme, create_themed_button, create_themed_label
from ...utils.import_export import BackupManager, BackupError, ExportError, ImportError

logger = logging.getLogger(__name__)

class BackupManagerDialog(ctk.CTkToplevel):
    """Comprehensive backup and restore management dialog"""

    def __init__(self, parent, session_id, password_manager, auth_manager):
        super().__init__(parent)

        self.session_id = session_id
        self.password_manager = password_manager
        self.auth_manager = auth_manager
        self.theme = get_theme()
        self.backup_manager = BackupManager()

        # Validate session and get user info
        try:
            session = self.auth_manager.validate_session(session_id)
            self.user_id = session.user_id
            self.username = session.username
        except Exception as e:
            messagebox.showerror("Session Error", f"Invalid session: {e}")
            self.destroy()
            return

        # UI state
        self.is_loading = False

        self._setup_dialog()
        self._create_ui()
        self._load_backup_list()
    
    def _setup_dialog(self):
        """Setup dialog properties"""
        self.title("Backup & Export Manager")
        self.geometry("600x500")
        self.resizable(True, True)
        
        if self.master:
            x = self.master.winfo_x() + (self.master.winfo_width() // 2) - 300
            y = self.master.winfo_y() + (self.master.winfo_height() // 2) - 250
            self.geometry(f"600x500+{x}+{y}")
        
        self.transient(self.master)
        self.grab_set()
    
    def _create_ui(self):
        """Create the comprehensive user interface"""
        spacing = self.theme.get_spacing()
        
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=spacing["padding_lg"], pady=spacing["padding_lg"])
        
        # Title
        title_label = create_themed_label(main_frame, "Backup & Export Manager", "label")
        title_label.configure(font=self.theme.get_fonts()["heading_medium"])
        title_label.pack(pady=(0, spacing["section_gap"]))
        
        # Create tabview for different operations
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True, pady=(0, spacing["section_gap"]))
        
        # Backup tab
        self.tabview.add("Database Backup")
        self._create_backup_tab()
        
        # Export tab
        self.tabview.add("Export Data")
        self._create_export_tab()
        
        # Import tab
        self.tabview.add("Import Data")
        self._create_import_tab()
        
        # Status area
        self._create_status_area(main_frame)
        
        # Close button
        close_btn = create_themed_button(
            main_frame,
            text="Close",
            style="button_secondary",
            command=self.destroy
        )
        close_btn.pack()
    
    def _create_backup_tab(self):
        """Create database backup tab"""
        backup_tab = self.tabview.tab("Database Backup")
        spacing = self.theme.get_spacing()
        
        # Backup creation section
        create_frame = ctk.CTkFrame(backup_tab)
        create_frame.pack(fill="x", padx=spacing["padding_md"], pady=spacing["padding_md"])
        
        create_label = create_themed_label(create_frame, "Create Database Backup", "label")
        create_label.configure(font=self.theme.get_fonts()["body_large"])
        create_label.pack(padx=spacing["padding_md"], pady=(spacing["padding_md"], spacing["padding_sm"]))
        
        desc_label = create_themed_label(
            create_frame,
            "Creates a complete backup of your password database.",
            "label_secondary"
        )
        desc_label.pack(padx=spacing["padding_md"], pady=(0, spacing["padding_sm"]))
        
        create_btn = create_themed_button(
            create_frame,
            text="📁 Create New Backup",
            style="button_primary",
            command=self._create_backup
        )
        create_btn.pack(pady=(0, spacing["padding_md"]))
        
        # Backup list section
        list_frame = ctk.CTkFrame(backup_tab)
        list_frame.pack(fill="both", expand=True, padx=spacing["padding_md"], pady=(0, spacing["padding_md"]))
        
        list_label = create_themed_label(list_frame, "Available Backups", "label")
        list_label.configure(font=self.theme.get_fonts()["body_large"])
        list_label.pack(padx=spacing["padding_md"], pady=(spacing["padding_md"], spacing["padding_sm"]))
        
        # Backup list
        self.backup_listbox = tk.Listbox(
            list_frame,
            height=8,
            selectmode=tk.SINGLE,
            font=self.theme.get_fonts()["body_medium"]
        )
        self.backup_listbox.pack(fill="both", expand=True, padx=spacing["padding_md"], pady=(0, spacing["padding_sm"]))
        
        # Backup actions
        backup_actions = ctk.CTkFrame(list_frame, fg_color="transparent")
        backup_actions.pack(fill="x", padx=spacing["padding_md"], pady=(0, spacing["padding_md"]))
        
        refresh_btn = create_themed_button(
            backup_actions,
            text="🔄 Refresh",
            style="button_secondary",
            command=self._load_backup_list
        )
        refresh_btn.pack(side="left")
        
        restore_btn = create_themed_button(
            backup_actions,
            text="📥 Restore",
            style="button_secondary",
            command=self._restore_backup
        )
        restore_btn.pack(side="left", padx=(spacing["padding_sm"], 0))
        
        delete_btn = create_themed_button(
            backup_actions,
            text="🗑️ Delete",
            style="button_danger",
            command=self._delete_backup
        )
        delete_btn.pack(side="right")
    
    def _create_export_tab(self):
        """Create data export tab"""
        export_tab = self.tabview.tab("Export Data")
        spacing = self.theme.get_spacing()
        
        # Export options
        options_frame = ctk.CTkFrame(export_tab)
        options_frame.pack(fill="x", padx=spacing["padding_md"], pady=spacing["padding_md"])
        
        options_label = create_themed_label(options_frame, "Export Options", "label")
        options_label.configure(font=self.theme.get_fonts()["body_large"])
        options_label.pack(padx=spacing["padding_md"], pady=(spacing["padding_md"], spacing["padding_sm"]))
        
        # Format selection
        format_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        format_frame.pack(fill="x", padx=spacing["padding_md"], pady=spacing["padding_sm"])
        
        format_label = create_themed_label(format_frame, "Export Format:", "label")
        format_label.pack(anchor="w")
        
        self.export_format_var = ctk.StringVar(value="json")
        
        json_radio = ctk.CTkRadioButton(format_frame, text="JSON (Recommended)", 
                                       variable=self.export_format_var, value="json")
        json_radio.pack(anchor="w", pady=(spacing["padding_xs"], 0))
        
        csv_radio = ctk.CTkRadioButton(format_frame, text="CSV (Compatible)", 
                                      variable=self.export_format_var, value="csv")
        csv_radio.pack(anchor="w", pady=(spacing["padding_xs"], 0))
        
        xml_radio = ctk.CTkRadioButton(format_frame, text="XML (Structured)", 
                                      variable=self.export_format_var, value="xml")
        xml_radio.pack(anchor="w", pady=(spacing["padding_xs"], 0))
        
        # Export actions
        export_actions = ctk.CTkFrame(export_tab)
        export_actions.pack(fill="x", padx=spacing["padding_md"], pady=(0, spacing["padding_md"]))
        
        export_desc = create_themed_label(
            export_actions,
            "Exports your password data in encrypted format for backup or transfer.",
            "label_secondary"
        )
        export_desc.pack(padx=spacing["padding_md"], pady=(spacing["padding_md"], spacing["padding_sm"]))
        
        export_btn = create_themed_button(
            export_actions,
            text="📤 Export Encrypted Data",
            style="button_primary",
            command=self._export_data
        )
        export_btn.pack(pady=(0, spacing["padding_md"]))

        # Plain CSV export section (for Excel)
        plain_export_frame = ctk.CTkFrame(export_tab)
        plain_export_frame.pack(fill="x", padx=spacing["padding_md"], pady=(0, spacing["padding_md"]))

        plain_export_label = create_themed_label(
            plain_export_frame,
            "Export Plain CSV (for Excel)",
            "label"
        )
        plain_export_label.configure(font=self.theme.get_fonts()["body_large"])
        plain_export_label.pack(padx=spacing["padding_md"], pady=(spacing["padding_md"], spacing["padding_sm"]))

        plain_export_warning = create_themed_label(
            plain_export_frame,
            "⚠️ WARNING: Creates UNENCRYPTED CSV file. Passwords are visible in plain text!",
            "label_secondary"
        )
        plain_export_warning.configure(text_color=self.theme.get_colors()["warning"])
        plain_export_warning.pack(padx=spacing["padding_md"], pady=(0, spacing["padding_sm"]))

        plain_export_desc = create_themed_label(
            plain_export_frame,
            "Use this only for temporary use in Excel. Delete the file after use.",
            "label_secondary"
        )
        plain_export_desc.pack(padx=spacing["padding_md"], pady=(0, spacing["padding_sm"]))

        plain_export_btn = create_themed_button(
            plain_export_frame,
            text="📊 Export Plain CSV for Excel",
            style="button_secondary",
            command=self._export_plain_csv
        )
        plain_export_btn.pack(pady=(0, spacing["padding_md"]))
    
    def _create_import_tab(self):
        """Create data import tab"""
        import_tab = self.tabview.tab("Import Data")
        spacing = self.theme.get_spacing()
        
        # Import from export
        export_import_frame = ctk.CTkFrame(import_tab)
        export_import_frame.pack(fill="x", padx=spacing["padding_md"], pady=spacing["padding_md"])
        
        export_import_label = create_themed_label(export_import_frame, "Import from Export", "label")
        export_import_label.configure(font=self.theme.get_fonts()["body_large"])
        export_import_label.pack(padx=spacing["padding_md"], pady=(spacing["padding_md"], spacing["padding_sm"]))
        
        export_import_desc = create_themed_label(
            export_import_frame,
            "Import data from encrypted export files created by this application.",
            "label_secondary"
        )
        export_import_desc.pack(padx=spacing["padding_md"], pady=(0, spacing["padding_sm"]))
        
        import_export_btn = create_themed_button(
            export_import_frame,
            text="📥 Import Export File",
            style="button_primary",
            command=self._import_export_file
        )
        import_export_btn.pack(pady=(0, spacing["padding_md"]))
        
        # Import from browsers
        browser_import_frame = ctk.CTkFrame(import_tab)
        browser_import_frame.pack(fill="x", padx=spacing["padding_md"], pady=(0, spacing["padding_md"]))
        
        browser_import_label = create_themed_label(browser_import_frame, "Import from Browser", "label")
        browser_import_label.configure(font=self.theme.get_fonts()["body_large"])
        browser_import_label.pack(padx=spacing["padding_md"], pady=(spacing["padding_md"], spacing["padding_sm"]))
        
        browser_import_desc = create_themed_label(
            browser_import_frame,
            "Import passwords from browser CSV exports (Chrome, Firefox, Edge).",
            "label_secondary"
        )
        browser_import_desc.pack(padx=spacing["padding_md"], pady=(0, spacing["padding_sm"]))
        
        # Browser selection
        browser_frame = ctk.CTkFrame(browser_import_frame, fg_color="transparent")
        browser_frame.pack(fill="x", padx=spacing["padding_md"], pady=spacing["padding_sm"])

        self.browser_type_var = ctk.StringVar(value="chrome")

        chrome_radio = ctk.CTkRadioButton(browser_frame, text="Chrome",
                                         variable=self.browser_type_var, value="chrome")
        chrome_radio.pack(side="left")

        firefox_radio = ctk.CTkRadioButton(browser_frame, text="Firefox",
                                          variable=self.browser_type_var, value="firefox")
        firefox_radio.pack(side="left", padx=(spacing["padding_md"], 0))

        edge_radio = ctk.CTkRadioButton(browser_frame, text="Edge",
                                       variable=self.browser_type_var, value="edge")
        edge_radio.pack(side="left", padx=(spacing["padding_md"], 0))

        # File selection section
        file_selection_frame = ctk.CTkFrame(browser_import_frame, fg_color="transparent")
        file_selection_frame.pack(fill="x", padx=spacing["padding_md"], pady=spacing["padding_sm"])

        # Selected file label
        self.browser_csv_file_label = create_themed_label(
            file_selection_frame,
            "No file selected",
            "label_secondary"
        )
        self.browser_csv_file_label.pack(anchor="w", pady=(0, spacing["padding_xs"]))

        # Buttons frame
        buttons_frame = ctk.CTkFrame(file_selection_frame, fg_color="transparent")
        buttons_frame.pack(fill="x")

        # Browse button
        browse_btn = create_themed_button(
            buttons_frame,
            text="📂 Browse CSV File",
            style="button_secondary",
            command=self._browse_csv_file
        )
        browse_btn.pack(side="left", padx=(0, spacing["padding_sm"]))

        # Import button (disabled by default)
        self.import_csv_btn = create_themed_button(
            buttons_frame,
            text="📥 Start Import",
            style="button_primary",
            command=self._import_browser_passwords
        )
        self.import_csv_btn.configure(state="disabled")
        self.import_csv_btn.pack(side="left")

        # Store selected file path
        self.selected_csv_file = None

        # Add spacing at bottom
        spacer = ctk.CTkFrame(browser_import_frame, fg_color="transparent", height=spacing["padding_md"])
        spacer.pack()
    
    def _create_status_area(self, parent):
        """Create status area for progress and messages"""
        spacing = self.theme.get_spacing()
        
        self.status_frame = ctk.CTkFrame(parent)
        self.status_frame.pack(fill="x", pady=(0, spacing["section_gap"]))
        
        # Progress bar (hidden by default)
        self.progress_bar = ctk.CTkProgressBar(self.status_frame)
        # Don't pack by default
        
        # Status message
        self.status_label = create_themed_label(self.status_frame, "Ready", "label_secondary")
        self.status_label.pack(padx=spacing["padding_md"], pady=spacing["padding_sm"])
    
    def _load_backup_list(self):
        """Load and display available backups"""
        try:
            backups = self.backup_manager.get_backup_list()
            
            # Clear listbox
            self.backup_listbox.delete(0, tk.END)
            
            # Add backups to listbox
            for backup in backups:
                size_mb = backup['size'] / (1024 * 1024)
                created_date = datetime.fromisoformat(backup['created_at']).strftime('%Y-%m-%d %H:%M')
                display_text = f"{backup['filename']} ({size_mb:.1f} MB) - {created_date}"
                self.backup_listbox.insert(tk.END, display_text)
                
            self._show_status(f"Found {len(backups)} backup(s)")
            
        except Exception as e:
            logger.error(f"Failed to load backup list: {e}")
            self._show_error(f"Failed to load backups: {str(e)}")
    
    def _create_backup(self):
        """Create database backup"""
        if self.is_loading:
            return
        
        self._start_loading("Creating backup...")
        
        # Run in background thread
        threading.Thread(target=self._create_backup_background, daemon=True).start()
    
    def _create_backup_background(self):
        """Create backup in background thread"""
        try:
            backup_path = self.backup_manager.create_database_backup()
            self.after(0, self._on_backup_created, backup_path)
        except Exception as e:
            self.after(0, self._on_backup_error, str(e))
    
    def _on_backup_created(self, backup_path: str):
        """Handle successful backup creation"""
        self._stop_loading()
        self._show_success(f"Backup created successfully")
        self._load_backup_list()
        messagebox.showinfo("Success", f"Database backup created:\n{backup_path}")
    
    def _on_backup_error(self, error_message: str):
        """Handle backup creation error"""
        self._stop_loading()
        self._show_error(f"Backup failed: {error_message}")
        messagebox.showerror("Backup Error", f"Failed to create backup:\n{error_message}")
    
    def _restore_backup(self):
        """Restore selected backup"""
        selection = self.backup_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a backup to restore.")
            return
        
        # Get backup info
        backups = self.backup_manager.get_backup_list()
        if selection[0] >= len(backups):
            return
        
        backup_info = backups[selection[0]]
        backup_path = backup_info['path']
        
        # Confirm restore
        result = messagebox.askyesno(
            "Confirm Restore",
            f"This will replace your current database with the backup:\n\n"
            f"Backup: {backup_info['filename']}\n"
            f"Created: {backup_info['created_at']}\n\n"
            f"Your current data will be backed up before restore.\n"
            f"Are you sure you want to continue?"
        )
        
        if result:
            try:
                self.backup_manager.restore_database_backup(backup_path, confirm_restore=True)
                messagebox.showinfo("Success", "Database restored successfully.\nPlease restart the application.")
            except Exception as e:
                logger.error(f"Restore failed: {e}")
                messagebox.showerror("Restore Error", f"Failed to restore backup:\n{str(e)}")
    
    def _delete_backup(self):
        """Delete selected backup"""
        selection = self.backup_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a backup to delete.")
            return
        
        backups = self.backup_manager.get_backup_list()
        if selection[0] >= len(backups):
            return
        
        backup_info = backups[selection[0]]
        
        # Confirm deletion
        result = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete this backup?\n\n"
            f"{backup_info['filename']}\n"
            f"Created: {backup_info['created_at']}\n\n"
            f"This action cannot be undone."
        )
        
        if result:
            try:
                os.remove(backup_info['path'])
                # Remove metadata file if exists
                metadata_path = Path(backup_info['path']).with_suffix('.meta.json')
                if metadata_path.exists():
                    os.remove(metadata_path)
                
                self._load_backup_list()
                messagebox.showinfo("Success", "Backup deleted successfully.")
            except Exception as e:
                logger.error(f"Delete failed: {e}")
                messagebox.showerror("Delete Error", f"Failed to delete backup:\n{str(e)}")
    
    def _export_data(self):
        """Export encrypted data"""
        # Get master password
        master_password = simpledialog.askstring(
            "Master Password",
            "Enter your master password to encrypt the export:",
            show='*'
        )

        if not master_password:
            return

        # Choose export location with auto-generated filename
        export_format = self.export_format_var.get()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = filedialog.asksaveasfilename(
            defaultextension=f".{export_format}.encrypted",
            filetypes=[
                (f"Encrypted {export_format.upper()} files", f"*.{export_format}.encrypted"),
                ("All encrypted files", "*.encrypted"),
                ("All files", "*.*")
            ],
            initialfile=f"{self.username}_passwords_{timestamp}.{export_format}.encrypted",
            title="Save Export As"
        )
        
        if not filename:
            return
        
        self._start_loading("Exporting data...")
        
        # Run export in background
        threading.Thread(
            target=self._export_data_background,
            args=(master_password, export_format, filename),
            daemon=True
        ).start()
    
    def _export_data_background(self, master_password: str, export_format: str, filename: str):
        """Export data in background thread"""
        try:
            # Use the temporary filename from the export process
            temp_export = self.backup_manager.export_encrypted_data(
                self.user_id, self.username, master_password, export_format
            )

            # Move to desired location
            shutil.move(temp_export, filename)

            self.after(0, self._on_export_completed, filename)
        except Exception as e:
            self.after(0, self._on_export_error, str(e))
    
    def _on_export_completed(self, filename: str):
        """Handle successful export"""
        self._stop_loading()
        self._show_success("Export completed successfully")
        messagebox.showinfo("Export Complete", f"Data exported to:\n{filename}")
    
    def _on_export_error(self, error_message: str):
        """Handle export error"""
        self._stop_loading()
        self._show_error(f"Export failed: {error_message}")
        messagebox.showerror("Export Error", f"Failed to export data:\n{error_message}")

    def _export_plain_csv(self):
        """Export plain CSV for Excel"""
        # Show security warning
        proceed = messagebox.askokcancel(
            "Security Warning",
            "⚠️ WARNING: This will create an UNENCRYPTED CSV file!\n\n"
            "Your passwords will be visible in plain text.\n\n"
            "Only use this feature if:\n"
            "• You need to open the file in Excel temporarily\n"
            "• You're on a secure, private computer\n"
            "• You will delete the file immediately after use\n\n"
            "Do you want to continue?",
            icon='warning'
        )

        if not proceed:
            return

        # Get master password
        master_password = simpledialog.askstring(
            "Master Password",
            "Enter your master password to decrypt the passwords:",
            show='*'
        )

        if not master_password:
            return

        # Choose save location with auto-generated filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ],
            initialfile=f"{self.username}_passwords_{timestamp}.csv",
            title="Save Plain CSV As"
        )

        if not filename:
            return

        self._start_loading("Exporting plain CSV...")

        # Run export in background
        threading.Thread(
            target=self._export_plain_csv_background,
            args=(master_password, filename),
            daemon=True
        ).start()

    def _export_plain_csv_background(self, master_password: str, filename: str):
        """Export plain CSV in background thread"""
        try:
            # Export plain CSV
            self.backup_manager.export_plain_csv(
                self.user_id, self.username, master_password, filename
            )

            self.after(0, self._on_plain_csv_exported, filename)
        except Exception as e:
            self.after(0, self._on_export_error, str(e))

    def _on_plain_csv_exported(self, filename: str):
        """Handle successful plain CSV export"""
        self._stop_loading()
        self._show_success("Plain CSV exported successfully")
        messagebox.showinfo(
            "Export Complete",
            f"Plain CSV exported to:\n{filename}\n\n"
            "⚠️ REMINDER: This file is UNENCRYPTED!\n"
            "Delete it immediately after use."
        )
    
    def _import_export_file(self):
        """Import from encrypted export file"""
        # Select import file
        filename = filedialog.askopenfilename(
            filetypes=[
                ("Encrypted files", "*.encrypted"),
                ("All files", "*.*")
            ],
            title="Select Export File to Import"
        )
        
        if not filename:
            return
        
        # Get master password
        master_password = simpledialog.askstring(
            "Master Password",
            "Enter the master password used to encrypt this export:",
            show='*'
        )
        
        if not master_password:
            return

        # Show import mode selection dialog
        import_mode = self._show_import_mode_dialog()

        if import_mode is None:
            return  # User cancelled

        self._start_loading("Importing data...")

        # Run import in background
        threading.Thread(
            target=self._import_data_background,
            args=(filename, master_password, import_mode),
            daemon=True
        ).start()

    def _show_import_mode_dialog(self):
        """Show dialog to select import mode with 3 options"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Choose Import Mode")
        dialog.geometry("500x350")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 250
        y = self.winfo_y() + (self.winfo_height() // 2) - 175
        dialog.geometry(f"500x350+{x}+{y}")

        selected_mode = [None]  # Use list to allow modification in nested function

        # Title
        title_label = ctk.CTkLabel(
            dialog,
            text="Choose Import Mode",
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=(20, 10))

        # Description
        desc_label = ctk.CTkLabel(
            dialog,
            text="Select how you want to import the passwords:",
            font=("Arial", 12)
        )
        desc_label.pack(pady=(0, 20))

        # Option 1: Merge (skip duplicates)
        option1_frame = ctk.CTkFrame(dialog)
        option1_frame.pack(fill="x", padx=20, pady=5)

        option1_btn = ctk.CTkButton(
            option1_frame,
            text="✅ Merge (Skip Duplicates)",
            font=("Arial", 12, "bold"),
            fg_color="#2B7A0B",
            hover_color="#3D9B1A",
            height=50,
            command=lambda: [selected_mode.__setitem__(0, "merge"), dialog.destroy()]
        )
        option1_btn.pack(fill="x", padx=10, pady=10)

        option1_desc = ctk.CTkLabel(
            option1_frame,
            text="Keeps existing passwords, adds new ones. Skips duplicates.\nSafe - No data loss. Recommended.",
            font=("Arial", 10),
            text_color="gray"
        )
        option1_desc.pack(padx=10, pady=(0, 10))

        # Option 2: Add all as new
        option2_frame = ctk.CTkFrame(dialog)
        option2_frame.pack(fill="x", padx=20, pady=5)

        option2_btn = ctk.CTkButton(
            option2_frame,
            text="➕ Add All (Allow Duplicates)",
            font=("Arial", 12, "bold"),
            fg_color="#1F538D",
            hover_color="#2E6BA8",
            height=50,
            command=lambda: [selected_mode.__setitem__(0, "add_all"), dialog.destroy()]
        )
        option2_btn.pack(fill="x", padx=10, pady=10)

        option2_desc = ctk.CTkLabel(
            option2_frame,
            text="Adds all passwords as new entries, even if duplicates exist.\nUse when you want to keep multiple copies.",
            font=("Arial", 10),
            text_color="gray"
        )
        option2_desc.pack(padx=10, pady=(0, 10))

        # Option 3: Replace all
        option3_frame = ctk.CTkFrame(dialog)
        option3_frame.pack(fill="x", padx=20, pady=5)

        option3_btn = ctk.CTkButton(
            option3_frame,
            text="🔄 Replace All",
            font=("Arial", 12, "bold"),
            fg_color="#8B0000",
            hover_color="#A52A2A",
            height=50,
            command=lambda: [selected_mode.__setitem__(0, "replace"), dialog.destroy()]
        )
        option3_btn.pack(fill="x", padx=10, pady=10)

        option3_desc = ctk.CTkLabel(
            option3_frame,
            text="⚠️ DELETES all existing passwords first, then imports.\nDangerous - Use with caution!",
            font=("Arial", 10),
            text_color="#FF6B6B"
        )
        option3_desc.pack(padx=10, pady=(0, 10))

        # Cancel button
        cancel_btn = ctk.CTkButton(
            dialog,
            text="Cancel",
            fg_color="gray",
            command=dialog.destroy,
            width=100
        )
        cancel_btn.pack(pady=10)

        # Wait for dialog to close
        self.wait_window(dialog)

        return selected_mode[0]

    def _import_data_background(self, filename: str, master_password: str, import_mode: str):
        """Import data in background thread"""
        try:
            results = self.backup_manager.import_encrypted_data(
                self.user_id, master_password, filename, import_mode
            )
            self.after(0, self._on_import_completed, results)
        except Exception as e:
            self.after(0, self._on_import_error, str(e))
    
    def _on_import_completed(self, results: dict):
        """Handle successful import"""
        self._stop_loading()
        self._show_success("Import completed successfully")

        message = (
            f"Import completed!\n\n"
            f"Imported: {results['imported_count']} entries\n"
            f"Skipped: {results['skipped_count']} entries\n"
            f"Errors: {results['error_count']} entries\n"
            f"Total processed: {results['total_processed']} entries"
        )

        messagebox.showinfo("Import Complete", message)

        # Reset the CSV import UI
        self._reset_csv_import_ui()

    def _reset_csv_import_ui(self):
        """Reset the CSV import UI after completion"""
        try:
            self.selected_csv_file = None
            self.browser_csv_file_label.configure(
                text="No file selected",
                text_color=self.theme.get_colors()["text_secondary"]
            )
            self.import_csv_btn.configure(state="disabled")
        except:
            # Ignore if UI elements don't exist (for encrypted file imports)
            pass
    
    def _on_import_error(self, error_message: str):
        """Handle import error"""
        self._stop_loading()
        self._show_error(f"Import failed: {error_message}")
        messagebox.showerror("Import Error", f"Failed to import data:\n{error_message}")

        # Reset the CSV import UI
        self._reset_csv_import_ui()
    
    def _browse_csv_file(self):
        """Browse for CSV file to import"""
        filename = filedialog.askopenfilename(
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ],
            title="Select Browser Password Export CSV"
        )

        if filename:
            # Store the selected file
            self.selected_csv_file = filename

            # Update the label to show the selected file
            from pathlib import Path
            file_display = Path(filename).name
            if len(file_display) > 50:
                file_display = file_display[:47] + "..."

            self.browser_csv_file_label.configure(
                text=f"📄 Selected: {file_display}",
                text_color=self.theme.get_colors()["text_primary"]
            )

            # Enable the import button
            self.import_csv_btn.configure(state="normal")
        else:
            # User cancelled
            self.selected_csv_file = None
            self.browser_csv_file_label.configure(
                text="No file selected",
                text_color=self.theme.get_colors()["text_secondary"]
            )
            self.import_csv_btn.configure(state="disabled")

    def _import_browser_passwords(self):
        """Import passwords from browser CSV using mapping dialog"""
        # Check if file is selected
        if not self.selected_csv_file:
            messagebox.showwarning("No File Selected", "Please select a CSV file first.")
            return

        # Import CSVImportDialog here to avoid circular imports
        from ..main_window import CSVImportDialog

        try:
            # Open CSV import dialog with column mapping and selection
            CSVImportDialog(
                parent=self,
                session_id=self.session_id,
                password_manager=self.password_manager,
                csv_file_path=self.selected_csv_file,
                on_success=self._on_browser_import_success,
                auth_manager=self.auth_manager,
                username=self.username
            )
        except Exception as e:
            logger.error(f"Failed to open CSV import dialog: {e}")
            messagebox.showerror("Import Error", f"Failed to open import dialog:\n{str(e)}", parent=self)

    def _on_browser_import_success(self):
        """Handle successful browser import"""
        # Reset the CSV import UI
        self._reset_csv_import_ui()
        self._show_success("Browser passwords imported successfully")
        logger.info("Browser CSV import completed successfully")
    
    def _import_browser_background(self, filename: str, master_password: str, browser_type: str):
        """Import browser passwords in background thread"""
        try:
            results = self.backup_manager.import_browser_passwords(
                self.user_id, master_password, browser_type, filename
            )
            self.after(0, self._on_import_completed, results)
        except Exception as e:
            self.after(0, self._on_import_error, str(e))
    
    def _start_loading(self, message: str):
        """Start loading state"""
        self.is_loading = True
        self.progress_bar.pack(fill="x", padx=self.theme.get_spacing()["padding_md"], 
                              pady=(0, self.theme.get_spacing()["padding_sm"]))
        self.progress_bar.set(0)
        self.progress_bar.start()
        self._show_status(message)
    
    def _stop_loading(self):
        """Stop loading state"""
        self.is_loading = False
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
    
    def _show_status(self, message: str):
        """Show status message"""
        colors = self.theme.get_colors()
        self.status_label.configure(text=message, text_color=colors["text_secondary"])
    
    def _show_success(self, message: str):
        """Show success message"""
        colors = self.theme.get_colors()
        self.status_label.configure(text=message, text_color=colors["success"])
    
    def _show_error(self, message: str):
        """Show error message"""
        colors = self.theme.get_colors()
        self.status_label.configure(text=message, text_color=colors["error"])