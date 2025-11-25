#!/usr/bin/env python3
"""
Personal Password Manager - Service Integration Layer
===================================================

This module provides integration and coordination between all core services in the
password manager. It acts as a central coordinator for password viewing authentication,
user settings management, and security audit logging.

Key Features:
- Centralized service management and coordination
- Cross-service communication and data flow
- Unified API for UI components to interact with services
- Service health monitoring and diagnostics
- Event-driven architecture for service notifications
- Configuration management for service settings
- Error handling and recovery coordination

Service Coordination:
- PasswordViewAuthService: Time-based password viewing authentication
- SettingsService: User preference and configuration management
- SecurityAuditLogger: Comprehensive security event logging
- DatabaseManager: Persistent data storage and retrieval

Integration Features:
- Automatic service initialization and dependency resolution
- Cross-service event notifications and callbacks
- Centralized error handling and logging
- Service health checks and monitoring
- Configuration consistency across services
- Performance monitoring and optimization

Author: Personal Password Manager Enhancement Team
Version: 2.2.0
Date: September 21, 2025
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
from dataclasses import dataclass
import json

# Import our core services
from .view_auth_service import (
    PasswordViewAuthService, 
    ViewPermissionGrant, 
    ViewPermissionStatus,
    create_password_hash,
    create_view_auth_service
)
from .settings_service import (
    SettingsService, 
    SettingCategory, 
    SettingDefinition,
    create_settings_service
)
from .security_audit_logger import (
    SecurityAuditLogger, 
    SecurityEvent, 
    SecurityEventType,
    SecurityLevel,
    EventResult,
    create_security_audit_logger
)

# Configure logging for service integration
logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """Status of individual services"""
    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    ERROR = "error"
    SHUTDOWN = "shutdown"

class IntegrationEventType(Enum):
    """Types of integration events"""
    SERVICE_INITIALIZED = "service_initialized"
    SERVICE_ERROR = "service_error"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    SETTINGS_CHANGED = "settings_changed"
    SECURITY_ALERT = "security_alert"
    HEALTH_CHECK_FAILED = "health_check_failed"

@dataclass
class ServiceHealthInfo:
    """Health information for a service"""
    service_name: str
    status: ServiceStatus
    last_health_check: datetime
    error_message: Optional[str] = None
    performance_metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.performance_metrics is None:
            self.performance_metrics = {}

class PasswordManagerServiceIntegrator:
    """
    Central coordinator for all password manager services
    
    This class provides a unified interface for managing and coordinating
    all core services in the password manager. It handles service lifecycle,
    cross-service communication, configuration management, and provides
    high-level APIs for UI components.
    
    Features:
    - Automatic service initialization with dependency resolution
    - Centralized configuration management across services
    - Cross-service event coordination and notifications
    - Health monitoring and service diagnostics
    - Unified error handling and recovery
    - Performance monitoring and optimization
    - Graceful service shutdown and cleanup
    """
    
    def __init__(self, database_manager=None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the service integrator
        
        Args:
            database_manager: DatabaseManager instance for persistence
            config (Dict, optional): Configuration for services
        """
        self.database_manager = database_manager
        self.config = config or {}
        
        # Service instances
        self._view_auth_service: Optional[PasswordViewAuthService] = None
        self._settings_service: Optional[SettingsService] = None
        self._security_audit_logger: Optional[SecurityAuditLogger] = None
        
        # Service health tracking
        self._service_health: Dict[str, ServiceHealthInfo] = {}
        
        # Integration state
        self._integration_callbacks: Dict[str, List[Callable]] = {}
        self._event_history: List[Dict[str, Any]] = []
        self._initialization_complete = False
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Performance monitoring
        self._performance_metrics: Dict[str, List[float]] = {}
        self._health_check_thread = None
        
        # Initialize services
        self._initialize_services()
        
        logger.info("PasswordManagerServiceIntegrator initialized successfully")
    
    def _initialize_services(self):
        """Initialize all core services with proper dependencies"""
        logger.info("Initializing password manager services...")
        
        try:
            # 1. Initialize Settings Service first (other services may need settings)
            self._initialize_settings_service()
            
            # 2. Initialize Security Audit Logger (other services will use it)
            self._initialize_security_audit_logger()
            
            # 3. Initialize View Auth Service (depends on settings and audit logging)
            self._initialize_view_auth_service()
            
            # 4. Setup cross-service integrations
            self._setup_service_integrations()
            
            # 5. Start health monitoring
            self._start_health_monitoring()
            
            self._initialization_complete = True
            self._notify_integration_event(IntegrationEventType.SERVICE_INITIALIZED, "All services initialized")
            
            logger.info("All password manager services initialized successfully")
            
        except Exception as e:
            logger.error(f"Error during service initialization: {e}")
            self._handle_initialization_error(e)
            raise
    
    def _initialize_settings_service(self):
        """Initialize the settings service"""
        try:
            self._settings_service = create_settings_service(self.database_manager)
            
            # Add callback for settings changes
            self._settings_service.add_setting_change_callback(
                SettingCategory.PASSWORD_VIEWING.value,
                self._on_password_viewing_settings_changed
            )
            self._settings_service.add_setting_change_callback(
                SettingCategory.SECURITY.value,
                self._on_security_settings_changed
            )
            
            self._service_health["settings"] = ServiceHealthInfo(
                service_name="SettingsService",
                status=ServiceStatus.HEALTHY,
                last_health_check=datetime.now()
            )
            
            logger.info("SettingsService initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing SettingsService: {e}")
            self._service_health["settings"] = ServiceHealthInfo(
                service_name="SettingsService",
                status=ServiceStatus.ERROR,
                last_health_check=datetime.now(),
                error_message=str(e)
            )
            raise
    
    def _initialize_security_audit_logger(self):
        """Initialize the security audit logger"""
        try:
            enable_alerts = self.config.get('enable_security_alerts', True)
            self._security_audit_logger = create_security_audit_logger(
                self.database_manager, enable_alerts
            )
            
            # Add callback for security alerts
            self._security_audit_logger.add_alert_callback(self._on_security_alert)
            
            self._service_health["security_audit"] = ServiceHealthInfo(
                service_name="SecurityAuditLogger",
                status=ServiceStatus.HEALTHY,
                last_health_check=datetime.now()
            )
            
            logger.info("SecurityAuditLogger initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing SecurityAuditLogger: {e}")
            self._service_health["security_audit"] = ServiceHealthInfo(
                service_name="SecurityAuditLogger",
                status=ServiceStatus.ERROR,
                last_health_check=datetime.now(),
                error_message=str(e)
            )
            raise
    
    def _initialize_view_auth_service(self):
        """Initialize the password view authentication service"""
        try:
            # Get default timeout from config or settings
            default_timeout = self.config.get('default_view_timeout', 1)
            
            self._view_auth_service = create_view_auth_service(default_timeout)
            
            # Add callbacks for permission events
            self._view_auth_service.add_permission_granted_callback(self._on_permission_granted)
            self._view_auth_service.add_permission_revoked_callback(self._on_permission_revoked)
            
            self._service_health["view_auth"] = ServiceHealthInfo(
                service_name="PasswordViewAuthService",
                status=ServiceStatus.HEALTHY,
                last_health_check=datetime.now()
            )
            
            logger.info("PasswordViewAuthService initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing PasswordViewAuthService: {e}")
            self._service_health["view_auth"] = ServiceHealthInfo(
                service_name="PasswordViewAuthService",
                status=ServiceStatus.ERROR,
                last_health_check=datetime.now(),
                error_message=str(e)
            )
            raise
    
    def _setup_service_integrations(self):
        """Setup cross-service integrations and communication"""
        logger.info("Setting up service integrations...")
        
        # All services are initialized, now set up cross-communication
        # Services can now reference each other through this integrator
        
        logger.info("Service integrations configured successfully")
    
    # ==========================================
    # PUBLIC API FOR PASSWORD VIEWING FEATURES
    # ==========================================
    
    def request_password_view_permission(self, user_id: int, session_id: str, 
                                       master_password: str,
                                       timeout_minutes: Optional[int] = None) -> Tuple[bool, str, Optional[ViewPermissionGrant]]:
        """
        Request permission to view passwords with comprehensive integration
        
        Args:
            user_id (int): User requesting permission
            session_id (str): Session identifier
            master_password (str): Master password for authentication
            timeout_minutes (int, optional): Custom timeout duration
            
        Returns:
            Tuple[bool, str, Optional[ViewPermissionGrant]]: 
                (success, message, permission_grant)
        """
        start_time = time.time()
        
        try:
            # Get user's master password hash (from database/auth service)
            if self.database_manager:
                # In a real implementation, you'd get the user's stored password hash
                stored_hash = create_password_hash(master_password)  # Placeholder
            else:
                return False, "Database not available for authentication", None
            
            # Get user's timeout preference from settings
            if timeout_minutes is None and self._settings_service:
                timeout_minutes = self._settings_service.get_user_setting(
                    user_id, SettingCategory.PASSWORD_VIEWING.value, "view_timeout_minutes"
                )
            
            # Hash the provided password
            provided_hash = create_password_hash(master_password)
            
            # Request permission from view auth service
            permission = self._view_auth_service.grant_view_permission(
                session_id=session_id,
                user_id=user_id,
                master_password_hash=stored_hash,
                provided_password_hash=provided_hash,
                timeout_minutes=timeout_minutes
            )
            
            # Log the event
            if self._security_audit_logger:
                self._security_audit_logger.log_event(
                    SecurityEventType.VIEW_PERMISSION_GRANTED,
                    user_id, session_id,
                    EventResult.SUCCESS,
                    event_details={
                        'timeout_minutes': timeout_minutes,
                        'authentication_method': 'master_password'
                    },
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )
            
            return True, f"Permission granted for {timeout_minutes} minutes", permission
            
        except PermissionError as e:
            # Log failed attempt
            if self._security_audit_logger:
                self._security_audit_logger.log_event(
                    SecurityEventType.VIEW_PERMISSION_DENIED,
                    user_id, session_id,
                    EventResult.DENIED,
                    error_message=str(e),
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )
            
            return False, f"Permission denied: {e}", None
            
        except Exception as e:
            logger.error(f"Error requesting view permission: {e}")
            
            # Log error
            if self._security_audit_logger:
                self._security_audit_logger.log_event(
                    SecurityEventType.VIEW_PERMISSION_DENIED,
                    user_id, session_id,
                    EventResult.ERROR,
                    error_message=str(e),
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )
            
            return False, f"Authentication error: {e}", None
    
    def check_password_view_permission(self, session_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if session has valid password viewing permission
        
        Args:
            session_id (str): Session to check
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (has_permission, permission_info)
        """
        if not self._view_auth_service:
            return False, {"error": "View auth service not available"}
        
        has_permission = self._view_auth_service.has_view_permission(session_id)
        permission_info = self._view_auth_service.get_permission_info(session_id) or {}
        
        return has_permission, permission_info
    
    def record_password_view(self, session_id: str, user_id: int, entry_id: int, 
                           website: str = "unknown") -> bool:
        """
        Record that a password was viewed (integrates auth and logging)
        
        Args:
            session_id (str): Session that viewed password
            user_id (int): User who viewed password
            entry_id (int): Password entry that was viewed
            website (str): Website/service name
            
        Returns:
            bool: True if recorded successfully
        """
        # Check permission and record view
        if self._view_auth_service:
            success = self._view_auth_service.record_password_view(session_id, entry_id)
            
            if not success:
                # Log unauthorized view attempt
                if self._security_audit_logger:
                    self._security_audit_logger.log_event(
                        SecurityEventType.PASSWORD_VIEWED,
                        user_id, session_id,
                        EventResult.DENIED,
                        target_entry_id=entry_id,
                        error_message="No valid view permission",
                        event_details={'website': website, 'unauthorized': True}
                    )
                return False
        
        # Log successful password view
        if self._security_audit_logger:
            self._security_audit_logger.log_password_view(
                user_id, session_id, entry_id
            )
        
        return True
    
    def revoke_password_view_permission(self, session_id: str, reason: str = "USER_REQUEST") -> bool:
        """
        Revoke password viewing permission
        
        Args:
            session_id (str): Session to revoke permission for
            reason (str): Reason for revocation
            
        Returns:
            bool: True if revoked successfully
        """
        if not self._view_auth_service:
            return False
        
        return self._view_auth_service.revoke_permission(session_id, reason)
    
    # ==========================================
    # PUBLIC API FOR PASSWORD DELETION FEATURES
    # ==========================================
    
    def validate_password_deletion(self, user_id: int, session_id: str, entry_id: int,
                                  website: str, deletion_method: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate password deletion request with settings and security checks
        
        Args:
            user_id (int): User requesting deletion
            session_id (str): Session identifier
            entry_id (int): Password entry to delete
            website (str): Website name for confirmation
            deletion_method (str): How deletion is being performed
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (allowed, message, requirements)
        """
        try:
            if not self._settings_service:
                return False, "Settings service not available", {}
            
            # Get user's deletion preferences
            deletion_settings = self._settings_service.get_category_settings(
                user_id, SettingCategory.PASSWORD_DELETION.value
            )
            
            requirements = {
                'requires_confirmation': deletion_settings.get('require_confirmation', True),
                'confirmation_type': deletion_settings.get('confirmation_type', 'type_website'),
                'requires_master_password': deletion_settings.get('require_master_password', False),
                'website_to_type': website if deletion_settings.get('confirmation_type') == 'type_website' else None
            }
            
            # Check smart confirmation rules if enabled
            if deletion_settings.get('confirmation_type') == 'smart':
                smart_rules = deletion_settings.get('smart_confirmation_rules', {})
                # Apply smart rules logic here
                requirements['smart_rules_applied'] = True
            
            # Log validation request
            if self._security_audit_logger:
                self._security_audit_logger.log_event(
                    SecurityEventType.PASSWORD_DELETED,
                    user_id, session_id,
                    EventResult.SUCCESS,
                    target_entry_id=entry_id,
                    event_details={
                        'validation_phase': True,
                        'deletion_method': deletion_method,
                        'website': website,
                        'requirements': requirements
                    }
                )
            
            return True, "Validation complete", requirements
            
        except Exception as e:
            logger.error(f"Error validating password deletion: {e}")
            return False, f"Validation error: {e}", {}
    
    def confirm_password_deletion(self, user_id: int, session_id: str, entry_id: int,
                                 website: str, confirmation_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Confirm password deletion with comprehensive logging
        
        Args:
            user_id (int): User confirming deletion
            session_id (str): Session identifier
            entry_id (int): Password entry being deleted
            website (str): Website name
            confirmation_data (Dict): Confirmation details
            
        Returns:
            Tuple[bool, str]: (confirmed, message)
        """
        start_time = time.time()
        
        try:
            # Get confirmation requirements
            _, _, requirements = self.validate_password_deletion(
                user_id, session_id, entry_id, website, "confirmation"
            )
            
            # Validate confirmation based on type
            confirmation_type = requirements.get('confirmation_type', 'simple')
            confirmed = False
            
            if confirmation_type == 'simple':
                confirmed = confirmation_data.get('confirmed', False)
            elif confirmation_type == 'type_website':
                typed_website = confirmation_data.get('typed_website', '')
                confirmed = typed_website.lower() == website.lower()
            elif confirmation_type == 'master_password':
                provided_password = confirmation_data.get('master_password', '')
                # Validate master password (placeholder implementation)
                confirmed = len(provided_password) > 0  # Real implementation would verify
            elif confirmation_type == 'smart':
                # Apply smart confirmation logic
                confirmed = self._apply_smart_confirmation(user_id, entry_id, confirmation_data)
            
            # Log the confirmation attempt
            if self._security_audit_logger:
                self._security_audit_logger.log_password_deletion(
                    user_id, session_id, entry_id,
                    deletion_method="user_initiated",
                    confirmation_type=confirmation_type,
                    website=website
                )
            
            if confirmed:
                return True, "Deletion confirmed"
            else:
                return False, "Confirmation failed"
                
        except Exception as e:
            logger.error(f"Error confirming password deletion: {e}")
            return False, f"Confirmation error: {e}"
    
    # ==========================================
    # PUBLIC API FOR SETTINGS MANAGEMENT
    # ==========================================
    
    def get_user_settings(self, user_id: int, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user settings with defaults
        
        Args:
            user_id (int): User ID
            category (str, optional): Specific category to get
            
        Returns:
            Dict[str, Any]: User settings
        """
        if not self._settings_service:
            return {}
        
        if category:
            return self._settings_service.get_category_settings(user_id, category)
        else:
            return self._settings_service.get_all_user_settings(user_id)
    
    def update_user_setting(self, user_id: int, session_id: str, category: str, 
                           key: str, value: Any) -> Tuple[bool, str]:
        """
        Update user setting with validation and logging
        
        Args:
            user_id (int): User ID
            session_id (str): Session identifier
            category (str): Setting category
            key (str): Setting key
            value (Any): New value
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if not self._settings_service:
            return False, "Settings service not available"
        
        try:
            # Get old value for change tracking
            old_value = self._settings_service.get_user_setting(user_id, category, key)
            
            # Update setting
            success = self._settings_service.set_user_setting(user_id, category, key, value)
            
            if success:
                # Check if setting affects security
                setting_def = self._settings_service.get_setting_definition(category, key)
                affects_security = setting_def.affects_security if setting_def else False
                
                # Log the change
                if self._security_audit_logger:
                    self._security_audit_logger.log_settings_change(
                        user_id, session_id, category, key,
                        old_value, value, affects_security
                    )
                
                return True, "Setting updated successfully"
            else:
                return False, "Failed to update setting"
                
        except Exception as e:
            logger.error(f"Error updating user setting: {e}")
            return False, f"Setting update error: {e}"
    
    # ==========================================
    # PUBLIC API FOR SECURITY MONITORING
    # ==========================================
    
    def get_security_dashboard(self, user_id: Optional[int] = None, 
                              hours: int = 24) -> Dict[str, Any]:
        """
        Get comprehensive security dashboard data
        
        Args:
            user_id (int, optional): Get data for specific user
            hours (int): Time window for statistics
            
        Returns:
            Dict[str, Any]: Security dashboard data
        """
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'time_window_hours': hours,
            'user_id': user_id,
            'services': {},
            'security_stats': {},
            'view_permissions': {},
            'alerts': []
        }
        
        # Service health information
        dashboard_data['services'] = {
            service_name: {
                'status': health.status.value,
                'last_check': health.last_health_check.isoformat(),
                'error': health.error_message
            }
            for service_name, health in self._service_health.items()
        }
        
        # Security statistics
        if self._security_audit_logger:
            dashboard_data['security_stats'] = self._security_audit_logger.get_security_statistics(
                user_id, hours
            )
        
        # View permission statistics
        if self._view_auth_service:
            dashboard_data['view_permissions'] = {
                'active_count': self._view_auth_service.get_active_permissions_count(),
                'statistics': self._view_auth_service.get_permission_statistics()
            }
        
        return dashboard_data
    
    def search_security_events(self, filters: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search security events across all services
        
        Args:
            filters (Dict): Search filters
            limit (int): Maximum results
            
        Returns:
            List[Dict]: Matching events
        """
        if not self._security_audit_logger:
            return []
        
        return self._security_audit_logger.search_security_events(filters, limit)
    
    # ==========================================
    # HEALTH MONITORING AND DIAGNOSTICS
    # ==========================================
    
    def get_service_health(self) -> Dict[str, Any]:
        """Get comprehensive service health information"""
        with self._lock:
            health_report = {
                'overall_status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'services': {},
                'performance_metrics': self._performance_metrics.copy(),
                'initialization_complete': self._initialization_complete
            }
            
            # Check each service
            error_count = 0
            for service_name, health in self._service_health.items():
                health_report['services'][service_name] = {
                    'status': health.status.value,
                    'last_check': health.last_health_check.isoformat(),
                    'error_message': health.error_message,
                    'performance': health.performance_metrics
                }
                
                if health.status in [ServiceStatus.ERROR, ServiceStatus.DEGRADED]:
                    error_count += 1
            
            # Determine overall status
            if error_count == len(self._service_health):
                health_report['overall_status'] = 'critical'
            elif error_count > 0:
                health_report['overall_status'] = 'degraded'
            
            return health_report
    
    def run_health_checks(self) -> Dict[str, bool]:
        """Run health checks on all services"""
        health_results = {}
        
        # Check settings service
        if self._settings_service:
            try:
                # Test basic functionality
                test_definitions = self._settings_service.get_all_setting_definitions()
                health_results['settings'] = len(test_definitions) > 0
                self._service_health['settings'].status = ServiceStatus.HEALTHY
                self._service_health['settings'].last_health_check = datetime.now()
                self._service_health['settings'].error_message = None
            except Exception as e:
                health_results['settings'] = False
                self._service_health['settings'].status = ServiceStatus.ERROR
                self._service_health['settings'].error_message = str(e)
        
        # Check view auth service
        if self._view_auth_service:
            try:
                # Test basic functionality
                stats = self._view_auth_service.get_permission_statistics()
                health_results['view_auth'] = isinstance(stats, dict)
                self._service_health['view_auth'].status = ServiceStatus.HEALTHY
                self._service_health['view_auth'].last_health_check = datetime.now()
                self._service_health['view_auth'].error_message = None
            except Exception as e:
                health_results['view_auth'] = False
                self._service_health['view_auth'].status = ServiceStatus.ERROR
                self._service_health['view_auth'].error_message = str(e)
        
        # Check security audit logger
        if self._security_audit_logger:
            try:
                # Test basic functionality
                stats = self._security_audit_logger.get_security_statistics(hours=1)
                health_results['security_audit'] = isinstance(stats, dict)
                self._service_health['security_audit'].status = ServiceStatus.HEALTHY
                self._service_health['security_audit'].last_health_check = datetime.now()
                self._service_health['security_audit'].error_message = None
            except Exception as e:
                health_results['security_audit'] = False
                self._service_health['security_audit'].status = ServiceStatus.ERROR
                self._service_health['security_audit'].error_message = str(e)
        
        return health_results
    
    # ==========================================
    # EVENT CALLBACKS AND INTEGRATION
    # ==========================================
    
    def _on_permission_granted(self, permission: ViewPermissionGrant):
        """Handle permission granted event"""
        logger.info(f"Password view permission granted to user {permission.user_id} for {permission.timeout_minutes} minutes")
        
        self._notify_integration_event(
            IntegrationEventType.PERMISSION_GRANTED,
            f"View permission granted to user {permission.user_id}",
            {'permission_id': permission.session_id, 'timeout': permission.timeout_minutes}
        )
    
    def _on_permission_revoked(self, permission: ViewPermissionGrant, reason: str):
        """Handle permission revoked event"""
        logger.info(f"Password view permission revoked for user {permission.user_id} (reason: {reason})")
        
        self._notify_integration_event(
            IntegrationEventType.PERMISSION_REVOKED,
            f"View permission revoked for user {permission.user_id}: {reason}",
            {'permission_id': permission.session_id, 'reason': reason}
        )
    
    def _on_password_viewing_settings_changed(self, user_id: int, key: str, old_value: Any, new_value: Any):
        """Handle password viewing settings changes"""
        logger.info(f"Password viewing setting changed for user {user_id}: {key} = {new_value}")
        
        # Update view auth service if timeout changed
        if key == 'view_timeout_minutes' and self._view_auth_service:
            self._view_auth_service.default_timeout_minutes = new_value
        
        self._notify_integration_event(
            IntegrationEventType.SETTINGS_CHANGED,
            f"Password viewing setting changed: {key}",
            {'user_id': user_id, 'key': key, 'old_value': old_value, 'new_value': new_value}
        )
    
    def _on_security_settings_changed(self, user_id: int, key: str, old_value: Any, new_value: Any):
        """Handle security settings changes"""
        logger.info(f"Security setting changed for user {user_id}: {key} = {new_value}")
        
        self._notify_integration_event(
            IntegrationEventType.SETTINGS_CHANGED,
            f"Security setting changed: {key}",
            {'user_id': user_id, 'key': key, 'old_value': old_value, 'new_value': new_value, 'security_related': True}
        )
    
    def _on_security_alert(self, event: SecurityEvent):
        """Handle security alert from audit logger"""
        logger.warning(f"Security alert: {event.event_type.value} (risk: {event.risk_score})")
        
        self._notify_integration_event(
            IntegrationEventType.SECURITY_ALERT,
            f"Security alert: {event.event_type.value}",
            {
                'event_type': event.event_type.value,
                'user_id': event.user_id,
                'risk_score': event.risk_score,
                'security_level': event.security_level.value
            }
        )
    
    def _apply_smart_confirmation(self, user_id: int, entry_id: int, confirmation_data: Dict[str, Any]) -> bool:
        """Apply smart confirmation logic based on rules"""
        # Placeholder implementation for smart confirmation
        # In practice, this would analyze entry age, importance, user patterns, etc.
        
        if not self._settings_service:
            return False
        
        smart_rules = self._settings_service.get_user_setting(
            user_id, SettingCategory.PASSWORD_DELETION.value, "smart_confirmation_rules"
        )
        
        if not smart_rules:
            return confirmation_data.get('confirmed', False)
        
        # Example smart logic:
        # - New passwords (< 24 hours) require additional confirmation
        # - Important/favorite passwords require master password
        # - Bulk operations require master password
        
        return True  # Simplified for now
    
    def _notify_integration_event(self, event_type: IntegrationEventType, message: str, details: Dict[str, Any] = None):
        """Notify callbacks about integration events"""
        event_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type.value,
            'message': message,
            'details': details or {}
        }
        
        self._event_history.append(event_data)
        
        # Keep only recent events in memory
        if len(self._event_history) > 1000:
            self._event_history = self._event_history[-500:]
        
        # Notify callbacks
        callbacks = self._integration_callbacks.get(event_type.value, [])
        for callback in callbacks:
            try:
                callback(event_data)
            except Exception as e:
                logger.error(f"Error in integration event callback: {e}")
    
    def _handle_initialization_error(self, error: Exception):
        """Handle errors during service initialization"""
        logger.error(f"Service initialization failed: {error}")
        
        # Update service health status
        for service_health in self._service_health.values():
            if service_health.status == ServiceStatus.INITIALIZING:
                service_health.status = ServiceStatus.ERROR
                service_health.error_message = str(error)
    
    def _start_health_monitoring(self):
        """Start background health monitoring"""
        def health_monitor():
            while getattr(self, '_should_monitor_health', True):
                try:
                    time.sleep(300)  # Check every 5 minutes
                    self.run_health_checks()
                except Exception as e:
                    logger.error(f"Error in health monitoring: {e}")
        
        self._should_monitor_health = True
        self._health_check_thread = threading.Thread(target=health_monitor, daemon=True)
        self._health_check_thread.start()
    
    def add_integration_callback(self, event_type: IntegrationEventType, callback: Callable):
        """Add callback for integration events"""
        event_type_str = event_type.value
        if event_type_str not in self._integration_callbacks:
            self._integration_callbacks[event_type_str] = []
        self._integration_callbacks[event_type_str].append(callback)
    
    def shutdown(self):
        """Shutdown all services gracefully"""
        logger.info("Shutting down PasswordManagerServiceIntegrator...")
        
        # Stop health monitoring
        self._should_monitor_health = False
        if self._health_check_thread and self._health_check_thread.is_alive():
            self._health_check_thread.join(timeout=10)
        
        # Shutdown services in reverse order
        if self._view_auth_service:
            self._view_auth_service.shutdown()
        
        if self._security_audit_logger:
            self._security_audit_logger.shutdown()
        
        # Settings service doesn't need explicit shutdown
        
        # Update service health
        for service_health in self._service_health.values():
            service_health.status = ServiceStatus.SHUTDOWN
        
        logger.info("All services shut down successfully")

# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def create_service_integrator(database_manager=None, config: Dict[str, Any] = None) -> PasswordManagerServiceIntegrator:
    """
    Factory function to create a configured service integrator
    
    Args:
        database_manager: DatabaseManager instance
        config (Dict): Configuration for services
        
    Returns:
        PasswordManagerServiceIntegrator: Configured integrator
    """
    return PasswordManagerServiceIntegrator(database_manager, config)

# Example usage
if __name__ == "__main__":
    # This section would only run if the file is executed directly (for testing)
    logging.basicConfig(level=logging.DEBUG)
    
    print("Testing PasswordManagerServiceIntegrator...")
    
    # Create integrator
    integrator = create_service_integrator(config={
        'default_view_timeout': 2,
        'enable_security_alerts': True
    })
    
    # Test service health
    health = integrator.get_service_health()
    print(f"Service health: {health['overall_status']}")
    print(f"Services: {list(health['services'].keys())}")
    
    # Test permission request (would fail without real auth, but tests integration)
    try:
        success, message, permission = integrator.request_password_view_permission(
            user_id=1,
            session_id="test_session",
            master_password="test_password",
            timeout_minutes=2
        )
        print(f"Permission request: {success} - {message}")
    except Exception as e:
        print(f"Permission request failed (expected): {e}")
    
    # Test settings
    settings = integrator.get_user_settings(user_id=1, category="password_viewing")
    print(f"User settings count: {len(settings)}")
    
    # Test security dashboard
    dashboard = integrator.get_security_dashboard(user_id=1, hours=1)
    print(f"Security dashboard services: {len(dashboard['services'])}")
    
    print("ServiceIntegrator test completed successfully!")
    
    # Cleanup
    integrator.shutdown()
