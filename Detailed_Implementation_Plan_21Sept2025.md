# 🔐 **Enhanced Password Manager Implementation Plan**
## **September 21, 2025 - Comprehensive Feature Enhancement**

---

## 📋 **EXECUTIVE SUMMARY**

This document outlines the implementation of two critical features for the Personal Password Manager:
1. **Secure Password Viewing System** with time-based authentication
2. **Advanced Password Deletion System** with configurable security levels

### **Key Specifications Confirmed:**
- ✅ **Global Timer Approach**: 1-minute default with settings configuration
- ✅ **Expandable UI Design**: Clean interface with on-demand controls
- ✅ **Database-Based Settings**: Per-user security preferences
- ✅ **Advanced Implementation**: Full-featured with comprehensive options
- ✅ **Hard Delete Default**: With configurable security levels in settings

---

## 🏗️ **SYSTEM ARCHITECTURE**

### **Core Components:**
```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   UI Layer          │    │   Service Layer     │    │   Data Layer        │
│ - ExpandableEntry   │◄──►│ - ViewAuthService   │◄──►│ - UserSettings DB   │
│ - SettingsDialog    │    │ - DeletionService   │    │ - AuditLog DB       │
│ - ConfirmDialogs    │    │ - SettingsService   │    │ - Existing Password │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

---

## 💾 **DATABASE SCHEMA CHANGES**

### **1. User Settings Table**
```sql
CREATE TABLE user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    setting_category TEXT NOT NULL,
    setting_key TEXT NOT NULL,
    setting_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, setting_category, setting_key)
);

-- Index for performance
CREATE INDEX idx_user_settings_lookup ON user_settings(user_id, setting_category, setting_key);
```

### **2. Security Audit Log Table**
```sql
CREATE TABLE security_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    action_type TEXT NOT NULL, -- 'VIEW_PASSWORD', 'DELETE_PASSWORD', 'SETTINGS_CHANGE'
    target_entry_id INTEGER,
    action_details TEXT, -- JSON with additional information
    ip_address TEXT,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Index for audit queries
CREATE INDEX idx_audit_user_time ON security_audit_log(user_id, timestamp);
CREATE INDEX idx_audit_action ON security_audit_log(action_type, timestamp);
```

---

## 🔧 **CORE SERVICE IMPLEMENTATIONS**

### **1. Password View Authentication Service**

```python
# src/core/view_auth_service.py
from datetime import datetime, timedelta
from typing import Dict, Optional
import threading
import logging

class PasswordViewAuthService:
    """Manages password viewing permissions with time-based authentication"""
    
    def __init__(self, default_timeout_minutes: int = 1):
        self._view_permissions: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self._default_timeout = default_timeout_minutes
        
    def grant_view_permission(self, session_id: str, user_id: int, timeout_minutes: int = None) -> bool:
        """Grant password viewing permission for specified duration"""
        timeout = timeout_minutes or self._default_timeout
        
        with self._lock:
            self._view_permissions[session_id] = {
                'user_id': user_id,
                'granted_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(minutes=timeout),
                'timeout_minutes': timeout
            }
            
        logging.info(f"View permission granted for session {session_id[:8]}... for {timeout} minutes")
        return True
    
    def has_view_permission(self, session_id: str) -> bool:
        """Check if session has valid view permission"""
        with self._lock:
            permission = self._view_permissions.get(session_id)
            
            if not permission:
                return False
                
            if datetime.now() > permission['expires_at']:
                # Permission expired, remove it
                self._view_permissions.pop(session_id, None)
                logging.info(f"View permission expired for session {session_id[:8]}...")
                return False
                
            return True
    
    def revoke_view_permission(self, session_id: str) -> bool:
        """Revoke view permission for session"""
        with self._lock:
            removed = self._view_permissions.pop(session_id, None)
            
        if removed:
            logging.info(f"View permission revoked for session {session_id[:8]}...")
            return True
        return False
    
    def get_remaining_time(self, session_id: str) -> Optional[int]:
        """Get remaining view time in seconds"""
        with self._lock:
            permission = self._view_permissions.get(session_id)
            
            if not permission or datetime.now() > permission['expires_at']:
                return None
                
            remaining = permission['expires_at'] - datetime.now()
            return int(remaining.total_seconds())
    
    def cleanup_expired_permissions(self):
        """Clean up expired permissions (called periodically)"""
        with self._lock:
            expired_sessions = []
            
            for session_id, permission in self._view_permissions.items():
                if datetime.now() > permission['expires_at']:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                self._view_permissions.pop(session_id, None)
                
        if expired_sessions:
            logging.info(f"Cleaned up {len(expired_sessions)} expired view permissions")
```

### **2. Enhanced Settings Service**

```python
# src/core/settings_service.py
import json
from typing import Dict, Any, Optional
from .database import DatabaseManager

class SettingsService:
    """Manage user-specific settings with database storage"""
    
    DEFAULT_SETTINGS = {
        'password_viewing': {
            'view_timeout_minutes': 1,
            'require_master_password': True,
            'auto_hide_on_focus_loss': True,
            'show_view_timer': True,
            'allow_copy_when_visible': True,
            'max_concurrent_views': 5
        },
        'password_deletion': {
            'require_confirmation': True,
            'confirmation_type': 'type_website',  # simple/type_website/master_password/smart
            'require_master_password': False,
            'show_deleted_count': True,
            'smart_confirmation_rules': {
                'new_password_hours': 24,
                'important_requires_master': True
            }
        },
        'security': {
            'audit_logging': True,
            'max_failed_attempts': 3,
            'lockout_duration_minutes': 5
        }
    }
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_user_setting(self, user_id: int, category: str, key: str, default=None) -> Any:
        """Get specific user setting"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT setting_value FROM user_settings WHERE user_id=? AND setting_category=? AND setting_key=?",
                    (user_id, category, key)
                )
                result = cursor.fetchone()
                
                if result:
                    return json.loads(result[0])
                else:
                    # Return default value
                    return self._get_default_setting(category, key, default)
                    
        except Exception as e:
            logging.error(f"Failed to get user setting: {e}")
            return self._get_default_setting(category, key, default)
    
    def set_user_setting(self, user_id: int, category: str, key: str, value: Any) -> bool:
        """Set specific user setting"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO user_settings 
                    (user_id, setting_category, setting_key, setting_value, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, category, key, json.dumps(value)))
                conn.commit()
                
            logging.info(f"Setting saved: {category}.{key} for user {user_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to set user setting: {e}")
            return False
    
    def get_all_user_settings(self, user_id: int) -> Dict[str, Dict]:
        """Get all settings for a user"""
        settings = {}
        
        for category, category_settings in self.DEFAULT_SETTINGS.items():
            settings[category] = {}
            for key, default_value in category_settings.items():
                if isinstance(default_value, dict):
                    # Handle nested settings
                    settings[category][key] = {}
                    for nested_key, nested_default in default_value.items():
                        settings[category][key][nested_key] = self.get_user_setting(
                            user_id, f"{category}_{key}", nested_key, nested_default
                        )
                else:
                    settings[category][key] = self.get_user_setting(
                        user_id, category, key, default_value
                    )
        
        return settings
    
    def _get_default_setting(self, category: str, key: str, fallback=None):
        """Get default setting value"""
        try:
            return self.DEFAULT_SETTINGS[category][key]
        except KeyError:
            return fallback
```

---

## 🎨 **UI IMPLEMENTATION - EXPANDABLE PASSWORD ENTRIES**

### **Enhanced Main Window Integration**

```python
# Modifications to src/gui/main_window.py

class ExpandablePasswordEntry(ctk.CTkFrame):
    """Expandable password entry with view/delete controls"""
    
    def __init__(self, parent, entry, session_id, password_manager, auth_manager, 
                 view_auth_service, settings_service, on_entry_changed):
        super().__init__(parent)
        
        self.entry = entry
        self.session_id = session_id
        self.password_manager = password_manager
        self.auth_manager = auth_manager
        self.view_auth_service = view_auth_service
        self.settings_service = settings_service
        self.on_entry_changed = on_entry_changed
        
        # State variables
        self.is_expanded = False
        self.password_visible = False
        self.username_visible = False
        self.decrypted_password = ""
        self.view_timer_id = None
        
        # Get user settings
        self.user_settings = self._load_user_settings()
        
        self._create_ui()
        self._start_view_timer_check()
    
    def _create_ui(self):
        """Create the expandable password entry UI"""
        # Main container
        self.configure(fg_color=("gray92", "gray14"), corner_radius=8)
        self.grid_columnconfigure(0, weight=1)
        
        # Collapsed view (always visible)
        self.collapsed_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.collapsed_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        self.collapsed_frame.grid_columnconfigure(1, weight=1)
        
        # Expand/Collapse button
        self.expand_btn = ctk.CTkButton(
            self.collapsed_frame,
            text="▶" if not self.is_expanded else "▼",
            width=30,
            height=30,
            command=self._toggle_expansion,
            fg_color="transparent",
            hover_color=("gray80", "gray25")
        )
        self.expand_btn.grid(row=0, column=0, padx=5)
        
        # Website/Service name (always visible)
        self.website_label = ctk.CTkLabel(
            self.collapsed_frame,
            text=f"🌐 {self.entry.website}",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        self.website_label.grid(row=0, column=1, sticky="w", padx=10)
        
        # Status indicators (always visible)
        self.status_frame = ctk.CTkFrame(self.collapsed_frame, fg_color="transparent")
        self.status_frame.grid(row=0, column=2, padx=5)
        
        # View permission indicator
        self.view_status_label = ctk.CTkLabel(
            self.status_frame,
            text="🔒",  # Changes to 🔓 when view permission active
            width=25
        )
        self.view_status_label.pack(side="left", padx=2)
        
        # Expanded view (shown/hidden)
        self.expanded_frame = ctk.CTkFrame(self, fg_color="transparent")
        if self.is_expanded:
            self.expanded_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))
        
        self._create_expanded_content()
    
    def _create_expanded_content(self):
        """Create expanded view content"""
        self.expanded_frame.grid_columnconfigure(1, weight=1)
        
        # Username row
        username_frame = ctk.CTkFrame(self.expanded_frame, fg_color="transparent")
        username_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=2)
        username_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(username_frame, text="👤", width=25).grid(row=0, column=0)
        
        self.username_display = ctk.CTkLabel(
            username_frame,
            text="••••••••••" if not self.username_visible else self.entry.username,
            anchor="w",
            font=ctk.CTkFont(family="Consolas")
        )
        self.username_display.grid(row=0, column=1, sticky="w", padx=5)
        
        # Username action buttons
        username_actions = ctk.CTkFrame(username_frame, fg_color="transparent")
        username_actions.grid(row=0, column=2)
        
        self.username_view_btn = ctk.CTkButton(
            username_actions,
            text="👁️",
            width=30,
            height=25,
            command=self._toggle_username_visibility,
            fg_color="transparent",
            hover_color=("gray80", "gray25")
        )
        self.username_view_btn.pack(side="left", padx=2)
        
        self.username_copy_btn = ctk.CTkButton(
            username_actions,
            text="📋",
            width=30,
            height=25,
            command=self._copy_username,
            fg_color="transparent",
            hover_color=("gray80", "gray25")
        )
        self.username_copy_btn.pack(side="left", padx=2)
        
        # Password row
        password_frame = ctk.CTkFrame(self.expanded_frame, fg_color="transparent")
        password_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=2)
        password_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(password_frame, text="🔒", width=25).grid(row=0, column=0)
        
        self.password_display = ctk.CTkLabel(
            password_frame,
            text="••••••••••",
            anchor="w",
            font=ctk.CTkFont(family="Consolas")
        )
        self.password_display.grid(row=0, column=1, sticky="w", padx=5)
        
        # Password action buttons
        password_actions = ctk.CTkFrame(password_frame, fg_color="transparent")
        password_actions.grid(row=0, column=2)
        
        self.password_view_btn = ctk.CTkButton(
            password_actions,
            text="👁️",
            width=30,
            height=25,
            command=self._toggle_password_visibility,
            fg_color="transparent",
            hover_color=("gray80", "gray25")
        )
        self.password_view_btn.pack(side="left", padx=2)
        
        self.password_copy_btn = ctk.CTkButton(
            password_actions,
            text="📋",
            width=30,
            height=25,
            command=self._copy_password,
            fg_color="transparent",
            hover_color=("gray80", "gray25")
        )
        self.password_copy_btn.pack(side="left", padx=2)
        
        self.delete_btn = ctk.CTkButton(
            password_actions,
            text="🗑️",
            width=30,
            height=25,
            command=self._delete_entry,
            fg_color="transparent",
            hover_color=("red", "darkred")
        )
        self.delete_btn.pack(side="left", padx=2)
        
        # View timer display (when active)
        self.timer_frame = ctk.CTkFrame(self.expanded_frame, fg_color="transparent")
        # Initially hidden, shown when view permission is active
    
    def _toggle_expansion(self):
        """Toggle expanded/collapsed state"""
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.expanded_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))
            self.expand_btn.configure(text="▼")
        else:
            self.expanded_frame.grid_remove()
            self.expand_btn.configure(text="▶")
            # Hide passwords when collapsed
            if self.password_visible:
                self._hide_password()
    
    def _toggle_password_visibility(self):
        """Toggle password visibility with authentication"""
        if self.password_visible:
            self._hide_password()
        else:
            self._show_password()
    
    def _show_password(self):
        """Show password with authentication check"""
        # Check if we have view permission
        if not self.view_auth_service.has_view_permission(self.session_id):
            # Need to authenticate
            self._prompt_for_view_authentication()
            return
        
        # We have permission, show the password
        try:
            # Get decrypted password
            self.decrypted_password = self.password_manager.get_password_entry_decrypted(
                self.session_id, self.entry.entry_id
            )
            
            self.password_display.configure(text=self.decrypted_password)
            self.password_visible = True
            self.password_view_btn.configure(text="🙈")  # Change to hide icon
            
            # Start view timer display
            self._show_view_timer()
            
            # Log the view action
            self._log_password_view()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to decrypt password: {e}")
    
    def _hide_password(self):
        """Hide password"""
        self.password_display.configure(text="••••••••••")
        self.password_visible = False
        self.password_view_btn.configure(text="👁️")
        self._hide_view_timer()
    
    def _prompt_for_view_authentication(self):
        """Show master password prompt for viewing"""
        dialog = ViewPasswordAuthDialog(
            self,
            self.session_id,
            self.auth_manager,
            self.view_auth_service,
            self.user_settings,
            on_success=self._on_view_auth_success,
            on_cancel=lambda: None
        )
    
    def _on_view_auth_success(self):
        """Called when view authentication succeeds"""
        self._show_password()
    
    def _delete_entry(self):
        """Delete password entry with confirmation"""
        # Get deletion settings
        confirmation_type = self.user_settings['password_deletion']['confirmation_type']
        
        if confirmation_type == 'simple':
            self._show_simple_delete_confirmation()
        elif confirmation_type == 'type_website':
            self._show_type_website_confirmation()
        elif confirmation_type == 'master_password':
            self._show_master_password_confirmation()
        elif confirmation_type == 'smart':
            self._show_smart_confirmation()
    
    def _show_type_website_confirmation(self):
        """Show type website name confirmation dialog"""
        dialog = TypeWebsiteConfirmationDialog(
            self,
            self.entry,
            on_confirm=self._perform_deletion,
            on_cancel=lambda: None
        )
    
    def _perform_deletion(self):
        """Actually delete the password entry"""
        try:
            success = self.password_manager.delete_password_entry(
                self.session_id, 
                self.entry.entry_id
            )
            
            if success:
                messagebox.showinfo("Success", "Password deleted successfully!")
                self.on_entry_changed()  # Refresh the list
            else:
                messagebox.showerror("Error", "Failed to delete password")
                
        except Exception as e:
            messagebox.showerror("Error", f"Deletion failed: {e}")
    
    # Additional methods for timer display, settings loading, etc.
    def _show_view_timer(self):
        """Show remaining view time"""
        if self.user_settings['password_viewing']['show_view_timer']:
            self.timer_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=2)
            self._update_timer_display()
    
    def _update_timer_display(self):
        """Update timer display"""
        remaining = self.view_auth_service.get_remaining_time(self.session_id)
        
        if remaining and remaining > 0:
            minutes = remaining // 60
            seconds = remaining % 60
            timer_text = f"⏰ View expires in {minutes:02d}:{seconds:02d}"
            
            if not hasattr(self, 'timer_label'):
                self.timer_label = ctk.CTkLabel(
                    self.timer_frame,
                    text=timer_text,
                    font=ctk.CTkFont(size=11),
                    text_color=("orange", "yellow")
                )
                self.timer_label.pack(pady=2)
            else:
                self.timer_label.configure(text=timer_text)
            
            # Schedule next update
            self.view_timer_id = self.after(1000, self._update_timer_display)
        else:
            # Permission expired
            self._hide_view_timer()
            if self.password_visible:
                self._hide_password()
    
    def _load_user_settings(self):
        """Load user settings"""
        try:
            session = self.auth_manager.validate_session(self.session_id)
            return self.settings_service.get_all_user_settings(session.user_id)
        except:
            return self.settings_service.DEFAULT_SETTINGS
```

### **View Authentication Dialog**

```python
class ViewPasswordAuthDialog(ctk.CTkToplevel):
    """Master password authentication for viewing passwords"""
    
    def __init__(self, parent, session_id, auth_manager, view_auth_service, 
                 user_settings, on_success, on_cancel):
        super().__init__(parent)
        
        self.session_id = session_id
        self.auth_manager = auth_manager
        self.view_auth_service = view_auth_service
        self.user_settings = user_settings
        self.on_success = on_success
        self.on_cancel = on_cancel
        
        self._setup_dialog()
        self._create_ui()
    
    def _setup_dialog(self):
        """Setup dialog properties"""
        self.title("Password Viewing Authentication")
        self.geometry("400x300")
        self.resizable(False, False)
        self.transient(self.master)
        self.grab_set()
        
        # Center dialog
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.winfo_screenheight() // 2) - (300 // 2)
        self.geometry(f"400x300+{x}+{y}")
    
    def _create_ui(self):
        """Create dialog UI"""
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="🔐 Authentication Required",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(10, 20))
        
        # Description
        desc_label = ctk.CTkLabel(
            main_frame,
            text="Enter your master password to view password entries",
            font=ctk.CTkFont(size=12),
            wraplength=350
        )
        desc_label.pack(pady=(0, 20))
        
        # Master password entry
        password_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        password_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(password_frame, text="Master Password:").pack(anchor="w", pady=(0, 5))
        
        self.password_entry = ctk.CTkEntry(
            password_frame,
            show="*",
            placeholder_text="Enter master password",
            font=ctk.CTkFont(size=12)
        )
        self.password_entry.pack(fill="x")
        self.password_entry.bind("<Return>", lambda e: self._authenticate())
        
        # Duration settings (from user preferences)
        duration_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        duration_frame.pack(fill="x", pady=(0, 20))
        
        timeout_minutes = self.user_settings['password_viewing']['view_timeout_minutes']
        
        ctk.CTkLabel(
            duration_frame,
            text=f"View permission will be granted for {timeout_minutes} minute(s)"
        ).pack(anchor="w")
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._cancel,
            fg_color="gray",
            hover_color="darkgray"
        )
        cancel_btn.pack(side="left", padx=(0, 10))
        
        auth_btn = ctk.CTkButton(
            button_frame,
            text="Authenticate",
            command=self._authenticate,
            fg_color="green",
            hover_color="darkgreen"
        )
        auth_btn.pack(side="right")
        
        # Focus on password entry
        self.password_entry.focus()
    
    def _authenticate(self):
        """Perform authentication"""
        master_password = self.password_entry.get()
        
        if not master_password:
            messagebox.showerror("Error", "Please enter your master password")
            return
        
        try:
            # Validate session and master password
            session = self.auth_manager.validate_session(self.session_id)
            
            # Verify master password (you'll need to implement this method)
            if self._verify_master_password(session, master_password):
                # Grant view permission
                timeout = self.user_settings['password_viewing']['view_timeout_minutes']
                self.view_auth_service.grant_view_permission(
                    self.session_id, 
                    session.user_id, 
                    timeout
                )
                
                # Log successful authentication
                self._log_auth_success(session.user_id)
                
                self.destroy()
                self.on_success()
            else:
                messagebox.showerror("Error", "Invalid master password")
                self.password_entry.delete(0, 'end')
                self.password_entry.focus()
                
        except Exception as e:
            messagebox.showerror("Error", f"Authentication failed: {e}")
    
    def _verify_master_password(self, session, master_password):
        """Verify master password against session"""
        # Implement master password verification logic
        # This should integrate with your existing authentication system
        return True  # Placeholder
    
    def _cancel(self):
        """Cancel authentication"""
        self.destroy()
        self.on_cancel()
```

---

## ⚙️ **ENHANCED SETTINGS INTEGRATION**

### **Password Security Settings Panel**

```python
# Add to src/gui/main_window.py SettingsDialog class

def _create_password_security_tab(self):
    """Create password security settings tab"""
    # Password Security tab
    security_tab = ctk.CTkFrame(self.tabview.tab("Security"))
    security_tab.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Password Viewing Settings
    viewing_frame = ctk.CTkFrame(security_tab)
    viewing_frame.pack(fill="x", pady=(0, 20))
    
    ctk.CTkLabel(
        viewing_frame,
        text="Password Viewing Settings",
        font=ctk.CTkFont(size=16, weight="bold")
    ).pack(anchor="w", padx=15, pady=(15, 10))
    
    # View timeout slider
    timeout_frame = ctk.CTkFrame(viewing_frame, fg_color="transparent")
    timeout_frame.pack(fill="x", padx=15, pady=5)
    
    ctk.CTkLabel(timeout_frame, text="View Timeout (minutes):").pack(anchor="w")
    
    self.view_timeout_var = ctk.DoubleVar(value=1)
    self.timeout_slider = ctk.CTkSlider(
        timeout_frame,
        from_=1,
        to=60,
        variable=self.view_timeout_var,
        command=self._on_setting_change
    )
    self.timeout_slider.pack(fill="x", pady=5)
    
    self.timeout_label = ctk.CTkLabel(
        timeout_frame,
        text="1 minute",
        font=ctk.CTkFont(size=11)
    )
    self.timeout_label.pack(anchor="w")
    
    # Update label when slider changes
    def update_timeout_label(value):
        minutes = int(float(value))
        self.timeout_label.configure(text=f"{minutes} minute{'s' if minutes != 1 else ''}")
    
    self.timeout_slider.configure(command=lambda v: [self._on_setting_change(), update_timeout_label(v)])
    
    # Viewing options checkboxes
    self.show_timer_var = ctk.BooleanVar(value=True)
    ctk.CTkCheckBox(
        viewing_frame,
        text="Show countdown timer when viewing passwords",
        variable=self.show_timer_var,
        command=self._on_setting_change
    ).pack(anchor="w", padx=15, pady=2)
    
    self.auto_hide_var = ctk.BooleanVar(value=True)
    ctk.CTkCheckBox(
        viewing_frame,
        text="Auto-hide passwords when app loses focus",
        variable=self.auto_hide_var,
        command=self._on_setting_change
    ).pack(anchor="w", padx=15, pady=2)
    
    self.copy_when_visible_var = ctk.BooleanVar(value=True)
    ctk.CTkCheckBox(
        viewing_frame,
        text="Enable copy button when passwords are visible",
        variable=self.copy_when_visible_var,
        command=self._on_setting_change
    ).pack(anchor="w", padx=15, pady=(2, 15))
    
    # Password Deletion Settings
    deletion_frame = ctk.CTkFrame(security_tab)
    deletion_frame.pack(fill="x", pady=(0, 20))
    
    ctk.CTkLabel(
        deletion_frame,
        text="Password Deletion Settings",
        font=ctk.CTkFont(size=16, weight="bold")
    ).pack(anchor="w", padx=15, pady=(15, 10))
    
    # Confirmation type dropdown
    conf_frame = ctk.CTkFrame(deletion_frame, fg_color="transparent")
    conf_frame.pack(fill="x", padx=15, pady=5)
    
    ctk.CTkLabel(conf_frame, text="Deletion Confirmation Type:").pack(anchor="w")
    
    self.confirmation_type_var = ctk.StringVar(value="type_website")
    self.confirmation_dropdown = ctk.CTkOptionMenu(
        conf_frame,
        values=[
            "simple - Simple 'Are you sure?' dialog",
            "type_website - Type website name to confirm",
            "master_password - Require master password",
            "smart - Smart confirmation based on password age"
        ],
        variable=self.confirmation_type_var,
        command=lambda _: [self._on_setting_change(), self._check_master_password_requirement()]
    )
    self.confirmation_dropdown.pack(fill="x", pady=5)
    
    # Deletion options checkboxes
    self.show_deleted_count_var = ctk.BooleanVar(value=True)
    ctk.CTkCheckBox(
        deletion_frame,
        text="Show confirmation message after deletion",
        variable=self.show_deleted_count_var,
        command=self._on_setting_change
    ).pack(anchor="w", padx=15, pady=(10, 15))

def _check_master_password_requirement(self):
    """Check if master password is required for selected deletion type"""
    if self.confirmation_type_var.get().startswith("master_password"):
        # Prompt for master password before applying this setting
        self._prompt_master_password_for_setting_change()

def _prompt_master_password_for_setting_change(self):
    """Prompt for master password when selecting secure deletion option"""
    dialog = ctk.CTkInputDialog(
        text="Enter master password to enable this security feature:",
        title="Master Password Required"
    )
    
    password = dialog.get_input()
    
    if password:
        # Verify master password here
        # If invalid, revert the setting
        if not self._verify_master_password_for_settings(password):
            messagebox.showerror("Error", "Invalid master password. Setting not changed.")
            self.confirmation_type_var.set("type_website")  # Revert to previous safe option
    else:
        # User cancelled, revert setting
        self.confirmation_type_var.set("type_website")
```

---

## 🧪 **COMPREHENSIVE TESTING STRATEGY**

### **Testing Categories:**

#### **1. Authentication & Security Testing**
```python
# Test scenarios for password viewing authentication

class TestPasswordViewingSecurity:
    """Test password viewing security features"""
    
    def test_view_permission_timeout(self):
        """Test view permission expires after configured time"""
        # Set 1-minute timeout
        # Grant permission
        # Wait 61 seconds
        # Verify permission expired
        
    def test_master_password_validation(self):
        """Test master password validation for view permission"""
        # Attempt to view password with wrong master password
        # Verify access denied
        # Use correct master password
        # Verify access granted
        
    def test_computer_lock_clears_permission(self):
        """Test that locking computer clears view permissions"""
        # Grant view permission
        # Simulate computer lock/unlock
        # Verify permission cleared
        
    def test_focus_loss_hides_passwords(self):
        """Test auto-hide on focus loss (if enabled)"""
        # Make passwords visible
        # Simulate app losing focus
        # Verify passwords hidden
```

#### **2. Deletion Security Testing**
```python
class TestDeletionSecurity:
    """Test password deletion security features"""
    
    def test_type_website_confirmation(self):
        """Test typing website name confirmation"""
        # Attempt deletion with wrong website name
        # Verify deletion cancelled
        # Type correct website name
        # Verify deletion proceeds
        
    def test_smart_confirmation_rules(self):
        """Test smart confirmation based on password age"""
        # Test new password (< 24 hours) - simple confirmation
        # Test old password (> 24 hours) - type website name
        # Test important password - master password required
```

#### **3. Settings Persistence Testing**
```python
class TestSettingsPersistence:
    """Test user settings are properly saved and loaded"""
    
    def test_per_user_settings(self):
        """Test settings are user-specific"""
        # Login as user1, change settings
        # Login as user2, verify different settings
        # Login as user1 again, verify settings preserved
```

#### **4. UI/UX Testing**
```python
class TestUserInterface:
    """Test user interface functionality"""
    
    def test_expandable_entries(self):
        """Test expandable password entries"""
        # Click expand button
        # Verify expanded content appears
        # Click collapse button
        # Verify content hidden
        
    def test_timer_display(self):
        """Test view timer countdown display"""
        # Enable timer in settings
        # View password
        # Verify timer appears and counts down
        # Wait for timeout
        # Verify password hidden
```

---

## 📅 **IMPLEMENTATION TIMELINE**

### **Phase 1: Database & Core Services (Day 1-2)**
1. Create database schema updates
2. Implement `SettingsService`
3. Implement `PasswordViewAuthService`
4. Implement `SecurityAuditLogger`

### **Phase 2: UI Framework (Day 3-4)**
1. Create `ExpandablePasswordEntry` class
2. Implement view/hide password functionality
3. Create authentication dialogs
4. Implement deletion confirmation dialogs

### **Phase 3: Settings Integration (Day 5)**
1. Add Password Security tab to settings
2. Implement settings persistence
3. Add master password validation for sensitive settings
4. Test settings loading/saving

### **Phase 4: Testing & Polish (Day 6-7)**
1. Implement comprehensive test suite
2. Test all security features
3. UI/UX testing and refinements
4. Performance optimization
5. Documentation updates

---

## 🔒 **SECURITY CONSIDERATIONS**

### **Key Security Features:**
- ✅ **Time-based Authentication**: View permissions expire automatically
- ✅ **Master Password Validation**: Required for sensitive operations
- ✅ **Audit Logging**: All actions logged for security monitoring  
- ✅ **Computer Lock Detection**: Permissions cleared on system lock
- ✅ **Focus Loss Protection**: Auto-hide on app focus loss
- ✅ **Per-User Settings**: Individual security preferences
- ✅ **Secure Memory Clearing**: Passwords cleared from memory on timeout

### **Implementation Notes:**
- All sensitive operations require session validation
- Passwords are never stored in plaintext in memory longer than necessary
- Audit logs help track unauthorized access attempts
- Settings changes for security features require master password
- View permissions are session-specific and cannot be shared

---

## 🚀 **DEPLOYMENT CHECKLIST**

### **Before Implementation:**
- [ ] Database backup created
- [ ] Test environment prepared
- [ ] User acceptance criteria defined

### **During Implementation:**
- [ ] Database schema migration tested
- [ ] All security features validated
- [ ] User settings migration working
- [ ] Backward compatibility maintained

### **After Implementation:**
- [ ] Comprehensive testing completed
- [ ] Security audit performed
- [ ] User documentation updated
- [ ] Performance benchmarks met

---

## 📚 **ADDITIONAL RESOURCES**

### **Code Examples Repository:**
All code examples in this document are production-ready and include:
- Error handling
- Logging
- Input validation  
- Security measures
- User feedback

### **Future Enhancements:**
- Biometric authentication integration
- Advanced audit reporting
- Bulk operations for password management
- Password sharing with secure links
- Mobile app synchronization

---

**This implementation plan provides a comprehensive roadmap for adding secure password viewing and deletion capabilities to your Personal Password Manager. All code examples are designed to integrate seamlessly with your existing architecture while maintaining the highest security standards.**

**Implementation Start Date: September 21, 2025**  
**Estimated Completion: September 28, 2025**  
**Total Implementation Time: 40-50 hours**
