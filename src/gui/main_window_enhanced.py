#!/usr/bin/env python3
"""
Personal Password Manager - Enhanced Main Window Integration
===========================================================

This module provides an enhanced main window that seamlessly integrates all
the new password viewing and deletion features while maintaining compatibility
with the existing application structure.

Key Features:
- Seamless integration with existing MainWindow architecture
- Enhanced password list with secure viewing and deletion
- Integrated settings management with comprehensive preferences
- Real-time service health monitoring and status display
- Automatic service initialization and cleanup
- Comprehensive error handling and fallback mechanisms

Integration Approach:
- Extends existing MainWindow class to maintain compatibility
- Replaces standard password list with EnhancedPasswordListFrame
- Integrates ServiceIntegrator for centralized service management
- Adds enhanced settings window with comprehensive preferences
- Provides fallback mechanisms for legacy operation

Author: Personal Password Manager Enhancement Team
Version: 2.0.0
Date: September 21, 2025
"""

import logging
import threading
from typing import Optional, Dict, Any
import customtkinter as ctk
from tkinter import messagebox

# Import existing components
from .main_window import MainWindow, PasswordListFrame
from .themes import get_theme, create_themed_button, create_themed_label

# Import enhanced components
from .enhanced_password_list import EnhancedPasswordListFrame
from .settings_window import show_settings_window
from .password_view_dialog import show_password_view_auth_dialog

# Import core services
from ..core.service_integration import PasswordManagerServiceIntegrator
from ..core.password_manager import PasswordEntry

# Configure logging
logger = logging.getLogger(__name__)

class EnhancedMainWindow(MainWindow):
    """
    Enhanced main window with integrated security features
    
    This class extends the existing MainWindow to add enhanced password
    viewing and deletion features while maintaining full compatibility
    with the existing application structure.
    
    Enhanced Features:
    - Time-based password viewing with authentication
    - Comprehensive deletion workflows with configurable confirmation
    - Advanced settings management with user preferences
    - Real-time service health monitoring
    - Security audit logging and event tracking
    - Automatic service cleanup and error recovery
    """
    
    def __init__(self, session_id: str, username: str, 
                 password_manager,
                 auth_manager,
                 service_integrator: Optional[PasswordManagerServiceIntegrator] = None,
                 user_id: int = 1,
                 parent=None):
        """
        Initialize enhanced main window
        
        Args:
            session_id: Valid session ID
            username: Authenticated username
            password_manager: Password management system
            auth_manager: Authentication manager
            service_integrator: Enhanced service integrator (optional)
            user_id: User ID for service integration
            parent: Parent window (optional)
        """
        # Store enhanced service references
        self.service_integrator = service_integrator
        self.enhanced_user_id = user_id
        self.enhanced_session_id = session_id
        self.services_available = service_integrator is not None
        
        # Service health monitoring
        self._service_health_timer = None
        self._service_health_status = "unknown"
        
        # Initialize base class
        super().__init__(session_id, username, password_manager, auth_manager, parent)
        
        # Apply enhanced features if services are available
        if self.services_available:
            self._integrate_enhanced_services()
            self._start_service_monitoring()
        
        logger.info(f"Enhanced main window initialized - Services available: {self.services_available}")
    
    def _integrate_enhanced_services(self):
        """Integrate enhanced services with the main window"""
        try:
            logger.info("Integrating enhanced services with main window")
            
            # Update window title to indicate enhanced version
            current_title = self.title()
            self.title(f"{current_title} - Enhanced v2.0")
            
            # Add service status indicator to status bar
            self._add_service_status_indicator()
            
            # Schedule service health check
            self.after(1000, self._update_service_health)
            
            logger.debug("Enhanced services integrated successfully")
            
        except Exception as e:
            logger.error(f"Error integrating enhanced services: {e}")
            self.services_available = False
    
    def _create_main_content(self, parent):
        """Override to create enhanced password list"""
        spacing = self.theme.get_spacing()
        
        # Main content frame
        content_frame = ctk.CTkFrame(parent, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        
        # Create enhanced or standard password list based on service availability
        if self.services_available:
            logger.debug("Creating enhanced password list with integrated services")
            try:
                from .enhanced_password_list import EnhancedPasswordListFrame
                
                self.password_list = EnhancedPasswordListFrame(
                    parent=content_frame,
                    main_window=self,
                    service_integrator=self.service_integrator,
                    user_id=self.enhanced_user_id,
                    session_id=self.enhanced_session_id
                )
                self.password_list.pack(fill="both", expand=True)
                
                logger.info("Enhanced password list created successfully")
                
            except Exception as e:
                logger.error(f"Failed to create enhanced password list: {e}")
                # Fallback to standard password list
                self._create_standard_password_list(content_frame)
        else:
            logger.debug("Creating standard password list (services not available)")
            self._create_standard_password_list(content_frame)
    
    def _create_standard_password_list(self, parent):
        """Create standard password list as fallback"""
        self.password_list = PasswordListFrame(parent, self)
        self.password_list.pack(fill="both", expand=True)
    
    def _add_service_status_indicator(self):
        """Add service status indicator to the UI"""
        try:
            # Find existing status bar and add service indicator
            if hasattr(self, 'status_label'):
                # Get parent of status label
                status_parent = self.status_label.master
                
                # Create service status frame
                service_frame = ctk.CTkFrame(status_parent, fg_color="transparent")
                service_frame.pack(side="right", padx=(10, 0))
                
                # Service status indicator
                self.service_status_label = create_themed_label(
                    service_frame,
                    text="🔧 Services: Checking...",
                    style="label_secondary"
                )
                self.service_status_label.pack(side="right")
                
                # Service health button
                self.service_health_btn = create_themed_button(
                    service_frame,
                    text="ℹ️",
                    style="button_secondary",
                    width=30,
                    command=self._show_service_health_dialog
                )
                self.service_health_btn.pack(side="right", padx=(5, 0))
                
                logger.debug("Service status indicator added")
                
        except Exception as e:
            logger.error(f"Error adding service status indicator: {e}")
    
    def _show_settings(self):
        """Override to show enhanced settings window"""
        if self.services_available:
            try:
                logger.debug("Showing enhanced settings window")
                show_settings_window(
                    parent=self,
                    service_integrator=self.service_integrator,
                    user_id=self.enhanced_user_id,
                    session_id=self.enhanced_session_id
                )
                return
                
            except Exception as e:
                logger.error(f"Error showing enhanced settings: {e}")
                # Fall through to standard settings
        
        # Fallback to standard settings
        logger.debug("Showing standard settings (fallback)")
        super()._show_settings()
    
    def _start_service_monitoring(self):
        """Start background service health monitoring"""
        if not self.services_available:
            return
        
        try:
            def monitor_services():
                """Background service monitoring worker"""
                while getattr(self, '_should_monitor_services', True):
                    try:
                        # Check service health every 30 seconds
                        threading.Event().wait(30)
                        
                        if hasattr(self, 'service_integrator') and self.service_integrator:
                            health = self.service_integrator.get_service_health()
                            self._service_health_status = health['overall_status']
                            
                            # Update UI on main thread
                            self.after(0, self._update_service_health_display, health)
                        
                    except Exception as e:
                        logger.error(f"Error in service monitoring: {e}")
                        break
            
            self._should_monitor_services = True
            monitor_thread = threading.Thread(target=monitor_services, daemon=True)
            monitor_thread.start()
            
            logger.debug("Service monitoring started")
            
        except Exception as e:
            logger.error(f"Error starting service monitoring: {e}")
    
    def _update_service_health(self):
        """Update service health status (called on main thread)"""
        if not self.services_available:
            return
        
        try:
            if self.service_integrator:
                health = self.service_integrator.get_service_health()
                self._update_service_health_display(health)
                
                # Schedule next health check
                self.after(60000, self._update_service_health)  # Check every minute
        
        except Exception as e:
            logger.error(f"Error updating service health: {e}")
    
    def _update_service_health_display(self, health_info: Dict[str, Any]):
        """Update service health display in the UI"""
        try:
            if not hasattr(self, 'service_status_label'):
                return
            
            status = health_info.get('overall_status', 'unknown')
            service_count = len(health_info.get('services', {}))
            
            # Set status text and color
            if status == 'healthy':
                status_text = f"🟢 Services: {service_count} healthy"
                color = "#27ae60"
            elif status == 'degraded':
                status_text = f"🟡 Services: {service_count} degraded"
                color = "#f39c12"
            elif status == 'critical':
                status_text = f"🔴 Services: {service_count} critical"
                color = "#e74c3c"
            else:
                status_text = f"⚪ Services: {service_count} unknown"
                color = "#95a5a6"
            
            self.service_status_label.configure(text=status_text, text_color=color)
            
        except Exception as e:
            logger.error(f"Error updating service health display: {e}")
    
    def _show_service_health_dialog(self):
        """Show detailed service health information"""
        if not self.services_available:
            messagebox.showinfo("Service Health", "Enhanced services are not available.")
            return
        
        try:
            health = self.service_integrator.get_service_health()
            
            # Create health report
            report_lines = [
                f"Overall Status: {health['overall_status'].upper()}",
                f"Last Check: {health['timestamp']}",
                "",
                "Service Details:"
            ]
            
            for service_name, service_info in health['services'].items():
                status = service_info['status']
                last_check = service_info['last_check']
                error = service_info.get('error_message', 'None')
                
                report_lines.append(f"  • {service_name}: {status}")
                if error != 'None':
                    report_lines.append(f"    Error: {error}")
            
            # Add performance metrics if available
            if 'performance_metrics' in health:
                report_lines.extend(["", "Performance Metrics:"])
                for metric, values in health['performance_metrics'].items():
                    if values:
                        avg_value = sum(values) / len(values)
                        report_lines.append(f"  • {metric}: {avg_value:.2f}ms avg")
            
            # Show in dialog
            messagebox.showinfo("Service Health Report", "\n".join(report_lines))
            
        except Exception as e:
            logger.error(f"Error showing service health dialog: {e}")
            messagebox.showerror("Health Check Error", f"Could not retrieve service health: {e}")
    
    def show_password_view_auth_dialog(self):
        """Show password view authentication dialog"""
        if not self.services_available:
            messagebox.showwarning("Feature Not Available", 
                "Enhanced password viewing requires service integration.")
            return None
        
        try:
            return show_password_view_auth_dialog(
                parent=self,
                service_integrator=self.service_integrator,
                user_id=self.enhanced_user_id,
                session_id=self.enhanced_session_id
            )
            
        except Exception as e:
            logger.error(f"Error showing password view auth dialog: {e}")
            messagebox.showerror("Authentication Error", f"Could not show authentication dialog: {e}")
            return None
    
    def get_security_dashboard_data(self, hours: int = 24):
        """Get security dashboard data for enhanced features"""
        if not self.services_available:
            return {}
        
        try:
            return self.service_integrator.get_security_dashboard(
                user_id=self.enhanced_user_id,
                hours=hours
            )
            
        except Exception as e:
            logger.error(f"Error getting security dashboard data: {e}")
            return {}
    
    def search_security_events(self, filters: Dict[str, Any] = None, limit: int = 100):
        """Search security events for enhanced features"""
        if not self.services_available:
            return []
        
        try:
            return self.service_integrator.search_security_events(
                filters or {}, limit
            )
            
        except Exception as e:
            logger.error(f"Error searching security events: {e}")
            return []
    
    def _on_entries_loaded(self, entries):
        """Override to handle enhanced entry loading"""
        # Call parent method
        super()._on_entries_loaded(entries)
        
        # Log entry loading if services available
        if self.services_available and self.service_integrator._security_audit_logger:
            try:
                from ..core.security_audit_logger import SecurityEventType, EventResult
                
                self.service_integrator._security_audit_logger.log_event(
                    SecurityEventType.APPLICATION_START,  # Use appropriate event type
                    self.enhanced_user_id,
                    self.enhanced_session_id,
                    EventResult.SUCCESS,
                    event_details={
                        'action': 'password_entries_loaded',
                        'entry_count': len(entries)
                    }
                )
                
            except Exception as e:
                logger.error(f"Error logging entry loading: {e}")
    
    def _show_temporary_message(self, message: str, msg_type: str = "info"):
        """Enhanced temporary message with service integration"""
        # Call parent method
        super()._show_temporary_message(message, msg_type)
        
        # Log message if it's an error or warning and services are available
        if self.services_available and msg_type in ['error', 'warning']:
            try:
                from ..core.security_audit_logger import SecurityEventType, EventResult
                
                event_type = SecurityEventType.APPLICATION_START  # Use appropriate type
                result = EventResult.ERROR if msg_type == 'error' else EventResult.SUCCESS
                
                self.service_integrator._security_audit_logger.log_event(
                    event_type,
                    self.enhanced_user_id,
                    self.enhanced_session_id,
                    result,
                    event_details={
                        'ui_message': message,
                        'message_type': msg_type
                    }
                )
                
            except Exception as e:
                logger.debug(f"Could not log UI message: {e}")
    
    def _on_window_close(self):
        """Enhanced window close with service cleanup"""
        logger.info("Enhanced main window closing - performing cleanup")
        
        # Stop service monitoring
        self._should_monitor_services = False
        
        # Cleanup services if available
        if self.services_available and self.service_integrator:
            try:
                # Log logout event
                from ..core.security_audit_logger import SecurityEventType, EventResult
                
                self.service_integrator._security_audit_logger.log_event(
                    SecurityEventType.LOGOUT,
                    self.enhanced_user_id,
                    self.enhanced_session_id,
                    EventResult.SUCCESS,
                    event_details={'logout_reason': 'window_close'}
                )
                
                # Note: Don't shutdown service integrator here as it may be shared
                # The main application should handle service shutdown
                
            except Exception as e:
                logger.error(f"Error during enhanced cleanup: {e}")
        
        # Call parent cleanup
        super()._on_window_close()

# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def create_enhanced_main_window(session_id: str, username: str, 
                               password_manager, auth_manager,
                               service_integrator: Optional[PasswordManagerServiceIntegrator] = None,
                               user_id: int = 1, parent=None) -> EnhancedMainWindow:
    """
    Factory function to create enhanced main window
    
    Args:
        session_id: Valid session ID
        username: Authenticated username
        password_manager: Password management system
        auth_manager: Authentication manager
        service_integrator: Enhanced service integrator (optional)
        user_id: User ID for service integration
        parent: Parent window (optional)
        
    Returns:
        EnhancedMainWindow: Enhanced main window instance
    """
    return EnhancedMainWindow(
        session_id=session_id,
        username=username,
        password_manager=password_manager,
        auth_manager=auth_manager,
        service_integrator=service_integrator,
        user_id=user_id,
        parent=parent
    )

def check_enhanced_features_available() -> bool:
    """
    Check if enhanced features are available
    
    Returns:
        bool: True if all enhanced components can be imported
    """
    try:
        from .enhanced_password_list import EnhancedPasswordListFrame
        from .settings_window import show_settings_window
        from .password_view_dialog import show_password_view_auth_dialog
        from ..core.service_integration import PasswordManagerServiceIntegrator
        
        return True
        
    except ImportError as e:
        logger.warning(f"Enhanced features not available: {e}")
        return False

# Example usage and testing
if __name__ == "__main__":
    # This section would only run if the file is executed directly (for testing)
    import sys
    import os
    
    # Add parent directories to path for imports
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    print("Enhanced Main Window Integration Test")
    print("This component requires full application context for testing.")
    print("Run main_enhanced.py to test the complete integration.")
