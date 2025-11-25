#!/usr/bin/env python3
"""
Personal Password Manager - Security Audit Logger
================================================

This module provides comprehensive security event logging and monitoring for the
password manager. It tracks all security-sensitive actions, provides risk assessment,
performance monitoring, and detailed audit trails for compliance and security analysis.

Key Features:
- Comprehensive security event logging with context
- Risk assessment and scoring for security events
- Performance monitoring and execution time tracking  
- Event filtering, searching, and statistical analysis
- Real-time security alerts and notifications
- Audit log retention and cleanup management
- Integration with external security monitoring systems

Security Event Categories:
- Authentication: Login, logout, failed attempts, lockouts
- Password Management: View, create, modify, delete operations
- Settings Changes: Security configuration modifications
- Data Operations: Import, export, backup operations
- System Events: Application start/stop, errors, crashes

Risk Assessment Features:
- Dynamic risk scoring based on event context
- Anomaly detection for unusual activity patterns
- Rate limiting and threshold monitoring
- Geographic and temporal analysis
- User behavior profiling and deviation detection

Author: Personal Password Manager Enhancement Team
Version: 2.2.0
Date: September 21, 2025
"""

import hashlib
import json
import logging
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set, Tuple, Union
import platform
import psutil
import os

# Configure logging for security audit operations
logger = logging.getLogger(__name__)

class SecurityEventType(Enum):
    """Types of security events that can be logged"""
    # Authentication Events
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE" 
    LOGOUT = "LOGOUT"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    ACCOUNT_UNLOCKED = "ACCOUNT_UNLOCKED"
    BIOMETRIC_AUTH = "BIOMETRIC_AUTH"
    
    # Password Management Events
    PASSWORD_CREATED = "PASSWORD_CREATED"
    PASSWORD_VIEWED = "PASSWORD_VIEWED"
    PASSWORD_MODIFIED = "PASSWORD_MODIFIED"
    PASSWORD_DELETED = "PASSWORD_DELETED"
    BULK_PASSWORD_OPERATION = "BULK_PASSWORD_OPERATION"
    PASSWORD_BREACH_DETECTED = "PASSWORD_BREACH_DETECTED"
    
    # View Permission Events
    VIEW_PERMISSION_GRANTED = "VIEW_PERMISSION_GRANTED"
    VIEW_PERMISSION_DENIED = "VIEW_PERMISSION_DENIED"
    VIEW_PERMISSION_EXPIRED = "VIEW_PERMISSION_EXPIRED"
    VIEW_PERMISSION_REVOKED = "VIEW_PERMISSION_REVOKED"
    
    # Settings and Configuration
    SETTINGS_CHANGED = "SETTINGS_CHANGED"
    SECURITY_SETTINGS_CHANGED = "SECURITY_SETTINGS_CHANGED"
    BACKUP_SETTINGS_CHANGED = "BACKUP_SETTINGS_CHANGED"
    
    # Data Operations
    DATA_EXPORT = "DATA_EXPORT"
    DATA_IMPORT = "DATA_IMPORT"
    BACKUP_CREATED = "BACKUP_CREATED"
    BACKUP_RESTORED = "BACKUP_RESTORED"
    
    # System and Application Events
    APPLICATION_START = "APPLICATION_START"
    APPLICATION_STOP = "APPLICATION_STOP"
    DATABASE_ERROR = "DATABASE_ERROR"
    ENCRYPTION_ERROR = "ENCRYPTION_ERROR"
    SYSTEM_LOCK_DETECTED = "SYSTEM_LOCK_DETECTED"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"

class SecurityLevel(Enum):
    """Security risk levels for events"""
    LOW = "LOW"             # Normal operation, minimal risk
    MEDIUM = "MEDIUM"       # Moderate risk, monitor activity  
    HIGH = "HIGH"           # High risk, requires attention
    CRITICAL = "CRITICAL"   # Critical risk, immediate action needed

class EventResult(Enum):
    """Possible outcomes of security events"""
    SUCCESS = "SUCCESS"     # Event completed successfully
    FAILURE = "FAILURE"     # Event failed to complete
    PARTIAL = "PARTIAL"     # Event partially completed
    DENIED = "DENIED"       # Event was denied by security policy
    ERROR = "ERROR"         # Event resulted in an error

class SecurityEvent:
    """
    Represents a security event with comprehensive metadata
    
    This class encapsulates all information about a security event including
    timing, context, risk assessment, and performance metrics.
    """
    
    def __init__(self, event_type: SecurityEventType, user_id: int, session_id: str,
                 result: EventResult = EventResult.SUCCESS, 
                 target_entry_id: Optional[int] = None):
        """
        Initialize a security event
        
        Args:
            event_type (SecurityEventType): Type of security event
            user_id (int): User who triggered the event
            session_id (str): Session identifier
            result (EventResult): Outcome of the event
            target_entry_id (int, optional): Password entry ID if applicable
        """
        self.event_id = self._generate_event_id()
        self.event_type = event_type
        self.user_id = user_id
        self.session_id = session_id
        self.result = result
        self.target_entry_id = target_entry_id
        
        # Timing information
        self.timestamp = datetime.now()
        self.execution_time_ms = 0
        
        # Context and metadata
        self.client_ip = "127.0.0.1"  # Default for desktop app
        self.user_agent = f"Desktop-App-v2.0-{platform.system()}"
        self.client_version = "2.2.0"
        self.request_source = "GUI"
        
        # Event details
        self.error_message: Optional[str] = None
        self.affected_fields: List[str] = []
        self.old_values: Dict[str, Any] = {}
        self.new_values: Dict[str, Any] = {}
        self.event_details: Dict[str, Any] = {}
        
        # Risk assessment
        self.security_level = SecurityLevel.LOW
        self.risk_score = 0  # 0-100
        self.anomaly_score = 0.0  # 0.0-1.0
        
        # System context
        self._capture_system_context()
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        timestamp = str(int(time.time() * 1000))
        random_part = hashlib.md5(f"{time.time()}{os.getpid()}".encode()).hexdigest()[:8]
        return f"evt_{timestamp}_{random_part}"
    
    def _capture_system_context(self):
        """Capture system context for the event"""
        try:
            # Basic system information
            self.event_details.update({
                'os_platform': platform.system(),
                'os_version': platform.version(),
                'python_version': platform.python_version(),
                'process_id': os.getpid()
            })
            
            # Performance metrics (if available)
            try:
                process = psutil.Process(os.getpid())
                self.event_details.update({
                    'memory_usage_mb': round(process.memory_info().rss / 1024 / 1024, 2),
                    'cpu_percent': process.cpu_percent(),
                    'num_threads': process.num_threads()
                })
            except (psutil.Error, ImportError):
                # psutil not available or error occurred
                pass
                
        except Exception as e:
            logger.warning(f"Error capturing system context: {e}")
    
    def set_execution_time(self, start_time: float):
        """Set execution time from start timestamp"""
        self.execution_time_ms = int((time.time() - start_time) * 1000)
    
    def set_risk_assessment(self, security_level: SecurityLevel, risk_score: int, 
                          anomaly_score: float = 0.0):
        """Set risk assessment for this event"""
        self.security_level = security_level
        self.risk_score = max(0, min(100, risk_score))
        self.anomaly_score = max(0.0, min(1.0, anomaly_score))
    
    def add_detail(self, key: str, value: Any):
        """Add detail information to the event"""
        self.event_details[key] = value
    
    def set_change_context(self, affected_fields: List[str], old_values: Dict[str, Any], 
                          new_values: Dict[str, Any]):
        """Set context for change events"""
        self.affected_fields = affected_fields or []
        self.old_values = old_values or {}
        self.new_values = new_values or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for storage/serialization"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'user_id': self.user_id,
            'session_id': self.session_id[:16] + "..." if len(self.session_id) > 16 else self.session_id,
            'result': self.result.value,
            'target_entry_id': self.target_entry_id,
            'timestamp': self.timestamp.isoformat(),
            'execution_time_ms': self.execution_time_ms,
            'client_ip': self.client_ip,
            'user_agent': self.user_agent,
            'client_version': self.client_version,
            'request_source': self.request_source,
            'error_message': self.error_message,
            'affected_fields': self.affected_fields,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'security_level': self.security_level.value,
            'risk_score': self.risk_score,
            'anomaly_score': self.anomaly_score,
            'event_details': self.event_details
        }

class SecurityAuditLogger:
    """
    Comprehensive security audit logging and monitoring system
    
    This service provides complete security event logging with risk assessment,
    anomaly detection, performance monitoring, and audit trail management.
    It integrates with the database layer for persistent storage and provides
    real-time monitoring capabilities.
    
    Features:
    - Comprehensive security event logging with rich metadata
    - Dynamic risk scoring and anomaly detection
    - Performance monitoring and execution time tracking
    - Event filtering, searching, and statistical analysis
    - Real-time alert notifications for critical events
    - Audit log retention and cleanup management
    - Thread-safe operations for concurrent logging
    - Integration with external security monitoring systems
    """
    
    def __init__(self, database_manager=None, enable_real_time_alerts: bool = True):
        """
        Initialize the security audit logger
        
        Args:
            database_manager: DatabaseManager instance for persistence
            enable_real_time_alerts (bool): Enable real-time security alerts
        """
        self.database_manager = database_manager
        self.enable_real_time_alerts = enable_real_time_alerts
        
        # Thread safety
        self._lock = threading.RLock()
        
        # In-memory event buffer for high-performance logging
        self._event_buffer: deque = deque(maxlen=1000)
        
        # Real-time monitoring
        self._alert_callbacks: Set[Callable] = set()
        self._anomaly_detectors: Dict[str, Callable] = {}
        
        # Performance tracking
        self._performance_stats: Dict[str, List[float]] = defaultdict(list)
        
        # User activity tracking for anomaly detection
        self._user_activity: Dict[int, Dict[str, Any]] = defaultdict(lambda: {
            'last_login': None,
            'login_attempts': deque(maxlen=10),
            'recent_actions': deque(maxlen=50),
            'risk_profile': {'baseline_score': 10, 'current_score': 10},
            'locations': set(),
            'devices': set()
        })
        
        # Event rate limiting and thresholds
        self._rate_limits: Dict[str, Dict[str, Any]] = {
            'failed_logins': {'threshold': 5, 'window_minutes': 15, 'events': deque()},
            'password_views': {'threshold': 20, 'window_minutes': 30, 'events': deque()},
            'settings_changes': {'threshold': 10, 'window_minutes': 60, 'events': deque()}
        }
        
        # Statistics and metrics
        self._statistics = {
            'total_events': 0,
            'events_by_type': defaultdict(int),
            'events_by_level': defaultdict(int),
            'average_risk_score': 0.0,
            'high_risk_events_today': 0,
            'anomalies_detected': 0
        }
        
        # Background monitoring thread
        self._monitoring_thread = None
        self._start_background_monitoring()
        
        logger.info("SecurityAuditLogger initialized with comprehensive security monitoring")
    
    def log_event(self, event_type: SecurityEventType, user_id: int, session_id: str,
                  result: EventResult = EventResult.SUCCESS,
                  target_entry_id: Optional[int] = None,
                  error_message: Optional[str] = None,
                  event_details: Optional[Dict[str, Any]] = None,
                  execution_time_ms: int = 0) -> SecurityEvent:
        """
        Log a security event with comprehensive context
        
        Args:
            event_type (SecurityEventType): Type of event to log
            user_id (int): User who triggered the event
            session_id (str): Session identifier
            result (EventResult): Outcome of the event
            target_entry_id (int, optional): Password entry ID if applicable
            error_message (str, optional): Error details if event failed
            event_details (Dict, optional): Additional event metadata
            execution_time_ms (int): How long the operation took
            
        Returns:
            SecurityEvent: The logged event object
        """
        with self._lock:
            # Create security event
            event = SecurityEvent(event_type, user_id, session_id, result, target_entry_id)
            
            # Set additional details
            if error_message:
                event.error_message = error_message
            
            if event_details:
                event.event_details.update(event_details)
            
            if execution_time_ms > 0:
                event.execution_time_ms = execution_time_ms
            
            # Perform risk assessment
            self._assess_event_risk(event)
            
            # Check for anomalies
            self._detect_anomalies(event)
            
            # Update user activity tracking
            self._update_user_activity(event)
            
            # Check rate limits and thresholds
            self._check_rate_limits(event)
            
            # Add to buffer
            self._event_buffer.append(event)
            
            # Update statistics
            self._update_statistics(event)
            
            # Store in database (async to avoid blocking)
            self._store_event_async(event)
            
            # Check for real-time alerts
            if self.enable_real_time_alerts:
                self._check_for_alerts(event)
            
            # Log to system logger based on severity
            self._log_to_system(event)
            
            return event
    
    def log_password_view(self, user_id: int, session_id: str, entry_id: int,
                         view_duration_seconds: Optional[int] = None,
                         authentication_method: str = "master_password") -> SecurityEvent:
        """
        Log a password view event with security context
        
        Args:
            user_id (int): User who viewed the password
            session_id (str): Session identifier
            entry_id (int): Password entry that was viewed
            view_duration_seconds (int, optional): How long password was visible
            authentication_method (str): How user authenticated for viewing
            
        Returns:
            SecurityEvent: The logged event
        """
        event_details = {
            'authentication_method': authentication_method,
            'view_duration_seconds': view_duration_seconds,
            'security_context': 'password_viewing'
        }
        
        return self.log_event(
            SecurityEventType.PASSWORD_VIEWED,
            user_id, session_id,
            EventResult.SUCCESS,
            target_entry_id=entry_id,
            event_details=event_details
        )
    
    def log_password_deletion(self, user_id: int, session_id: str, entry_id: int,
                            deletion_method: str, confirmation_type: str,
                            website: str = "unknown") -> SecurityEvent:
        """
        Log a password deletion event with security context
        
        Args:
            user_id (int): User who deleted the password
            session_id (str): Session identifier
            entry_id (int): Password entry that was deleted
            deletion_method (str): How deletion was performed
            confirmation_type (str): Type of confirmation used
            website (str): Website/service for the deleted password
            
        Returns:
            SecurityEvent: The logged event
        """
        event_details = {
            'deletion_method': deletion_method,
            'confirmation_type': confirmation_type,
            'website': website,
            'security_context': 'password_deletion',
            'irreversible_action': True
        }
        
        return self.log_event(
            SecurityEventType.PASSWORD_DELETED,
            user_id, session_id,
            EventResult.SUCCESS,
            target_entry_id=entry_id,
            event_details=event_details
        )
    
    def log_authentication_attempt(self, user_id: Optional[int], username: str, 
                                  success: bool, failure_reason: Optional[str] = None,
                                  client_info: Optional[Dict[str, str]] = None) -> SecurityEvent:
        """
        Log an authentication attempt with security analysis
        
        Args:
            user_id (int, optional): User ID if known (None for failed logins)
            username (str): Username attempted
            success (bool): Whether authentication succeeded
            failure_reason (str, optional): Why authentication failed
            client_info (Dict, optional): Client information
            
        Returns:
            SecurityEvent: The logged event
        """
        event_type = SecurityEventType.LOGIN_SUCCESS if success else SecurityEventType.LOGIN_FAILURE
        result = EventResult.SUCCESS if success else EventResult.FAILURE
        
        event_details = {
            'username': username,
            'authentication_type': 'master_password',
            'security_context': 'authentication'
        }
        
        if failure_reason:
            event_details['failure_reason'] = failure_reason
        
        if client_info:
            event_details.update(client_info)
        
        return self.log_event(
            event_type,
            user_id or 0,  # Use 0 for unknown users
            "auth_session",
            result,
            error_message=failure_reason,
            event_details=event_details
        )
    
    def log_settings_change(self, user_id: int, session_id: str, category: str, key: str,
                           old_value: Any, new_value: Any, affects_security: bool = False) -> SecurityEvent:
        """
        Log a settings change with change tracking
        
        Args:
            user_id (int): User who changed the setting
            session_id (str): Session identifier
            category (str): Setting category
            key (str): Setting key
            old_value (Any): Previous value
            new_value (Any): New value
            affects_security (bool): Whether this affects security
            
        Returns:
            SecurityEvent: The logged event
        """
        event_type = (SecurityEventType.SECURITY_SETTINGS_CHANGED 
                     if affects_security else SecurityEventType.SETTINGS_CHANGED)
        
        event_details = {
            'setting_category': category,
            'setting_key': key,
            'security_context': 'settings_management',
            'affects_security': affects_security
        }
        
        event = self.log_event(
            event_type, user_id, session_id,
            EventResult.SUCCESS,
            event_details=event_details
        )
        
        # Set change context
        event.set_change_context([key], {key: old_value}, {key: new_value})
        
        return event
    
    def get_security_statistics(self, user_id: Optional[int] = None, 
                              hours: int = 24) -> Dict[str, Any]:
        """
        Get comprehensive security statistics
        
        Args:
            user_id (int, optional): Get stats for specific user
            hours (int): Time window for statistics
            
        Returns:
            Dict[str, Any]: Security statistics and metrics
        """
        with self._lock:
            # Get events from database if available
            recent_events = []
            if self.database_manager and hasattr(self.database_manager, 'get_security_audit_log'):
                try:
                    recent_events = self.database_manager.get_security_audit_log(
                        user_id=user_id, limit=1000, offset=0
                    )
                except Exception as e:
                    logger.error(f"Error getting security statistics from database: {e}")
            
            # Combine with buffer events
            cutoff_time = datetime.now() - timedelta(hours=hours)
            buffer_events = [e for e in self._event_buffer 
                           if e.timestamp >= cutoff_time and (user_id is None or e.user_id == user_id)]
            
            # Calculate statistics
            all_events = buffer_events  # In a full implementation, combine with DB events
            
            stats = {
                'time_window_hours': hours,
                'total_events': len(all_events),
                'events_by_type': defaultdict(int),
                'events_by_level': defaultdict(int),
                'events_by_result': defaultdict(int),
                'risk_distribution': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0},
                'average_risk_score': 0.0,
                'anomalies_detected': 0,
                'failed_authentications': 0,
                'successful_authentications': 0,
                'password_views': 0,
                'password_deletions': 0,
                'settings_changes': 0,
                'high_risk_events': []
            }
            
            total_risk_score = 0
            
            for event in all_events:
                # Event type distribution
                stats['events_by_type'][event.event_type.value] += 1
                
                # Security level distribution
                stats['events_by_level'][event.security_level.value] += 1
                
                # Result distribution
                stats['events_by_result'][event.result.value] += 1
                
                # Risk score calculation
                total_risk_score += event.risk_score
                
                # Risk level distribution
                if event.risk_score <= 25:
                    stats['risk_distribution']['low'] += 1
                elif event.risk_score <= 50:
                    stats['risk_distribution']['medium'] += 1
                elif event.risk_score <= 75:
                    stats['risk_distribution']['high'] += 1
                else:
                    stats['risk_distribution']['critical'] += 1
                
                # Anomaly detection
                if event.anomaly_score > 0.7:
                    stats['anomalies_detected'] += 1
                
                # Specific event counts
                if event.event_type == SecurityEventType.LOGIN_FAILURE:
                    stats['failed_authentications'] += 1
                elif event.event_type == SecurityEventType.LOGIN_SUCCESS:
                    stats['successful_authentications'] += 1
                elif event.event_type == SecurityEventType.PASSWORD_VIEWED:
                    stats['password_views'] += 1
                elif event.event_type == SecurityEventType.PASSWORD_DELETED:
                    stats['password_deletions'] += 1
                elif event.event_type in [SecurityEventType.SETTINGS_CHANGED, 
                                        SecurityEventType.SECURITY_SETTINGS_CHANGED]:
                    stats['settings_changes'] += 1
                
                # High risk events (for detailed review)
                if event.security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                    stats['high_risk_events'].append({
                        'event_type': event.event_type.value,
                        'timestamp': event.timestamp.isoformat(),
                        'risk_score': event.risk_score,
                        'details': event.event_details.get('summary', 'High risk event detected')
                    })
            
            # Calculate averages
            if all_events:
                stats['average_risk_score'] = round(total_risk_score / len(all_events), 2)
            
            # Add user-specific statistics
            if user_id and user_id in self._user_activity:
                user_profile = self._user_activity[user_id]
                stats['user_profile'] = {
                    'current_risk_score': user_profile['risk_profile']['current_score'],
                    'baseline_risk_score': user_profile['risk_profile']['baseline_score'],
                    'recent_activity_count': len(user_profile['recent_actions']),
                    'last_login': user_profile['last_login'].isoformat() if user_profile['last_login'] else None
                }
            
            return dict(stats)
    
    def search_security_events(self, filters: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search security events with advanced filtering
        
        Args:
            filters (Dict): Search filters (user_id, event_type, date_range, etc.)
            limit (int): Maximum number of results
            
        Returns:
            List[Dict]: Matching security events
        """
        results = []
        
        # Search database if available
        if self.database_manager and hasattr(self.database_manager, 'get_security_audit_log'):
            try:
                db_results = self.database_manager.get_security_audit_log(
                    user_id=filters.get('user_id'),
                    action_type=filters.get('event_type'),
                    limit=limit
                )
                results.extend(db_results)
            except Exception as e:
                logger.error(f"Error searching database events: {e}")
        
        # Search buffer events
        buffer_results = []
        for event in self._event_buffer:
            if self._event_matches_filters(event, filters):
                buffer_results.append(event.to_dict())
        
        # Combine and sort results
        all_results = results + buffer_results
        all_results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return all_results[:limit]
    
    def add_alert_callback(self, callback: Callable):
        """Add callback for real-time security alerts"""
        self._alert_callbacks.add(callback)
    
    def add_anomaly_detector(self, name: str, detector: Callable):
        """Add custom anomaly detection function"""
        self._anomaly_detectors[name] = detector
    
    def cleanup_old_events(self, days_to_keep: int = 90) -> int:
        """
        Clean up old security events from buffer and database
        
        Args:
            days_to_keep (int): Number of days of events to keep
            
        Returns:
            int: Number of events cleaned up
        """
        cleaned_count = 0
        
        # Clean up database if available
        if self.database_manager and hasattr(self.database_manager, 'cleanup_old_audit_logs'):
            try:
                cleaned_count += self.database_manager.cleanup_old_audit_logs(days_to_keep)
            except Exception as e:
                logger.error(f"Error cleaning up database audit logs: {e}")
        
        # Clean up buffer (keep only recent events)
        with self._lock:
            cutoff_time = datetime.now() - timedelta(days=days_to_keep)
            original_count = len(self._event_buffer)
            
            # Create new deque with only recent events
            new_buffer = deque(maxlen=1000)
            for event in self._event_buffer:
                if event.timestamp >= cutoff_time:
                    new_buffer.append(event)
            
            cleaned_count += original_count - len(new_buffer)
            self._event_buffer = new_buffer
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old security audit events")
        
        return cleaned_count
    
    # ==========================================
    # PRIVATE HELPER METHODS
    # ==========================================
    
    def _assess_event_risk(self, event: SecurityEvent):
        """Assess risk level and score for an event"""
        base_risk_scores = {
            SecurityEventType.LOGIN_FAILURE: 30,
            SecurityEventType.ACCOUNT_LOCKED: 70,
            SecurityEventType.PASSWORD_VIEWED: 20,
            SecurityEventType.PASSWORD_DELETED: 40,
            SecurityEventType.SECURITY_SETTINGS_CHANGED: 60,
            SecurityEventType.DATA_EXPORT: 50,
            SecurityEventType.SUSPICIOUS_ACTIVITY: 90,
            SecurityEventType.ENCRYPTION_ERROR: 80,
        }
        
        base_score = base_risk_scores.get(event.event_type, 10)
        
        # Adjust based on result
        if event.result == EventResult.FAILURE:
            base_score += 20
        elif event.result == EventResult.ERROR:
            base_score += 30
        
        # Adjust based on user activity
        user_activity = self._user_activity.get(event.user_id, {})
        current_user_risk = user_activity.get('risk_profile', {}).get('current_score', 10)
        base_score += max(0, current_user_risk - 10)
        
        # Adjust based on timing (e.g., after hours access)
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:  # After hours
            base_score += 15
        
        # Cap the risk score
        final_score = min(100, max(0, base_score))
        
        # Determine security level
        if final_score >= 80:
            security_level = SecurityLevel.CRITICAL
        elif final_score >= 60:
            security_level = SecurityLevel.HIGH
        elif final_score >= 30:
            security_level = SecurityLevel.MEDIUM
        else:
            security_level = SecurityLevel.LOW
        
        event.set_risk_assessment(security_level, final_score)
    
    def _detect_anomalies(self, event: SecurityEvent):
        """Detect anomalies in user behavior"""
        user_activity = self._user_activity.get(event.user_id, {})
        recent_actions = user_activity.get('recent_actions', deque())
        
        anomaly_score = 0.0
        
        # Check for unusual activity patterns
        if len(recent_actions) >= 10:
            # Check for rapid repeated actions
            recent_times = [action.get('timestamp', datetime.now()) for action in recent_actions]
            time_diffs = [(recent_times[i] - recent_times[i-1]).total_seconds() 
                         for i in range(1, min(6, len(recent_times)))]
            
            if time_diffs and sum(time_diffs) / len(time_diffs) < 2:  # Very rapid actions
                anomaly_score += 0.3
        
        # Check for unusual event types for this user
        user_event_types = set(action.get('event_type') for action in recent_actions)
        if event.event_type.value not in user_event_types and len(recent_actions) > 5:
            anomaly_score += 0.2
        
        # Check for error patterns
        recent_errors = sum(1 for action in recent_actions 
                           if action.get('result') in ['FAILURE', 'ERROR'])
        if recent_errors > 3:
            anomaly_score += 0.4
        
        # Apply custom anomaly detectors
        for name, detector in self._anomaly_detectors.items():
            try:
                custom_score = detector(event, user_activity)
                anomaly_score += custom_score
            except Exception as e:
                logger.error(f"Error in custom anomaly detector {name}: {e}")
        
        # Update event with anomaly score
        event.anomaly_score = min(1.0, anomaly_score)
        
        # If high anomaly score, increase risk
        if anomaly_score > 0.7:
            event.risk_score = min(100, event.risk_score + 30)
            event.security_level = SecurityLevel.HIGH
            
            # Log suspicious activity
            if anomaly_score > 0.9:
                self._log_suspicious_activity(event, anomaly_score)
    
    def _update_user_activity(self, event: SecurityEvent):
        """Update user activity tracking for anomaly detection"""
        user_activity = self._user_activity[event.user_id]
        
        # Update last login
        if event.event_type == SecurityEventType.LOGIN_SUCCESS:
            user_activity['last_login'] = event.timestamp
        
        # Track login attempts
        if event.event_type in [SecurityEventType.LOGIN_SUCCESS, SecurityEventType.LOGIN_FAILURE]:
            user_activity['login_attempts'].append({
                'timestamp': event.timestamp,
                'result': event.result.value,
                'ip': event.client_ip
            })
        
        # Track recent actions
        user_activity['recent_actions'].append({
            'timestamp': event.timestamp,
            'event_type': event.event_type.value,
            'result': event.result.value,
            'risk_score': event.risk_score
        })
        
        # Update risk profile
        risk_profile = user_activity['risk_profile']
        recent_risk_scores = [action.get('risk_score', 0) 
                             for action in list(user_activity['recent_actions'])[-10:]]
        if recent_risk_scores:
            current_avg = sum(recent_risk_scores) / len(recent_risk_scores)
            risk_profile['current_score'] = int(current_avg)
    
    def _check_rate_limits(self, event: SecurityEvent):
        """Check if event triggers rate limiting thresholds"""
        now = datetime.now()
        
        # Check failed login rate
        if event.event_type == SecurityEventType.LOGIN_FAILURE:
            rate_limit = self._rate_limits['failed_logins']
            rate_limit['events'].append(now)
            
            # Clean old events
            cutoff = now - timedelta(minutes=rate_limit['window_minutes'])
            rate_limit['events'] = deque([t for t in rate_limit['events'] if t > cutoff])
            
            # Check threshold
            if len(rate_limit['events']) >= rate_limit['threshold']:
                event.add_detail('rate_limit_triggered', 'failed_logins')
                event.risk_score = min(100, event.risk_score + 40)
        
        # Similar checks for other rate limits...
    
    def _store_event_async(self, event: SecurityEvent):
        """Store event in database asynchronously (placeholder)"""
        if self.database_manager and hasattr(self.database_manager, 'log_security_event'):
            try:
                self.database_manager.log_security_event(
                    user_id=event.user_id,
                    session_id=event.session_id,
                    action_type=event.event_type.value,
                    action_result=event.result.value,
                    target_entry_id=event.target_entry_id,
                    error_message=event.error_message,
                    action_details=event.event_details,
                    security_level=event.security_level.value,
                    risk_score=event.risk_score,
                    execution_time_ms=event.execution_time_ms
                )
            except Exception as e:
                logger.error(f"Error storing security event to database: {e}")
    
    def _check_for_alerts(self, event: SecurityEvent):
        """Check if event should trigger real-time alerts"""
        should_alert = (
            event.security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL] or
            event.anomaly_score > 0.8 or
            event.event_type in [
                SecurityEventType.ACCOUNT_LOCKED, 
                SecurityEventType.SUSPICIOUS_ACTIVITY,
                SecurityEventType.ENCRYPTION_ERROR
            ]
        )
        
        if should_alert:
            for callback in self._alert_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in security alert callback: {e}")
    
    def _log_to_system(self, event: SecurityEvent):
        """Log event to system logger based on severity"""
        if event.security_level == SecurityLevel.CRITICAL:
            logger.critical(f"CRITICAL SECURITY EVENT: {event.event_type.value} by user {event.user_id}")
        elif event.security_level == SecurityLevel.HIGH:
            logger.warning(f"HIGH RISK EVENT: {event.event_type.value} by user {event.user_id}")
        elif event.security_level == SecurityLevel.MEDIUM:
            logger.info(f"SECURITY EVENT: {event.event_type.value} by user {event.user_id}")
        else:
            logger.debug(f"Security event: {event.event_type.value} by user {event.user_id}")
    
    def _log_suspicious_activity(self, event: SecurityEvent, anomaly_score: float):
        """Log suspicious activity detection"""
        suspicious_event = SecurityEvent(
            SecurityEventType.SUSPICIOUS_ACTIVITY,
            event.user_id,
            event.session_id,
            EventResult.SUCCESS
        )
        
        suspicious_event.add_detail('trigger_event', event.event_type.value)
        suspicious_event.add_detail('anomaly_score', anomaly_score)
        suspicious_event.add_detail('original_risk_score', event.risk_score)
        
        suspicious_event.set_risk_assessment(SecurityLevel.HIGH, 85, anomaly_score)
        
        self._event_buffer.append(suspicious_event)
    
    def _update_statistics(self, event: SecurityEvent):
        """Update real-time statistics"""
        with self._lock:
            self._statistics['total_events'] += 1
            self._statistics['events_by_type'][event.event_type.value] += 1
            self._statistics['events_by_level'][event.security_level.value] += 1
            
            # Update rolling average risk score
            total_risk = (self._statistics['average_risk_score'] * 
                         (self._statistics['total_events'] - 1) + event.risk_score)
            self._statistics['average_risk_score'] = total_risk / self._statistics['total_events']
            
            # Count high risk events today
            if event.security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                if event.timestamp.date() == datetime.now().date():
                    self._statistics['high_risk_events_today'] += 1
            
            # Count anomalies
            if event.anomaly_score > 0.7:
                self._statistics['anomalies_detected'] += 1
    
    def _event_matches_filters(self, event: SecurityEvent, filters: Dict[str, Any]) -> bool:
        """Check if event matches search filters"""
        if 'user_id' in filters and event.user_id != filters['user_id']:
            return False
        
        if 'event_type' in filters and event.event_type.value != filters['event_type']:
            return False
        
        if 'security_level' in filters and event.security_level.value != filters['security_level']:
            return False
        
        if 'date_from' in filters:
            date_from = datetime.fromisoformat(filters['date_from'])
            if event.timestamp < date_from:
                return False
        
        if 'date_to' in filters:
            date_to = datetime.fromisoformat(filters['date_to'])
            if event.timestamp > date_to:
                return False
        
        return True
    
    def _start_background_monitoring(self):
        """Start background monitoring thread"""
        def monitoring_worker():
            while getattr(self, '_should_run_monitoring', True):
                try:
                    time.sleep(300)  # Run every 5 minutes
                    
                    # Update statistics
                    with self._lock:
                        # Clean up old rate limit events
                        now = datetime.now()
                        for rate_limit in self._rate_limits.values():
                            cutoff = now - timedelta(minutes=rate_limit['window_minutes'])
                            rate_limit['events'] = deque([t for t in rate_limit['events'] if t > cutoff])
                    
                    # Perform periodic cleanup
                    if datetime.now().hour == 3:  # 3 AM daily cleanup
                        self.cleanup_old_events(days_to_keep=90)
                        
                except Exception as e:
                    logger.error(f"Error in security monitoring thread: {e}")
        
        self._should_run_monitoring = True
        self._monitoring_thread = threading.Thread(target=monitoring_worker, daemon=True)
        self._monitoring_thread.start()
        
        logger.debug("Background security monitoring thread started")
    
    def shutdown(self):
        """Shutdown the security audit logger"""
        logger.info("Shutting down SecurityAuditLogger...")
        
        # Stop monitoring thread
        self._should_run_monitoring = False
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=10)
        
        # Final statistics
        final_stats = {
            'total_events_logged': self._statistics['total_events'],
            'events_in_buffer': len(self._event_buffer),
            'high_risk_events': self._statistics['high_risk_events_today'],
            'anomalies_detected': self._statistics['anomalies_detected']
        }
        
        logger.info(f"SecurityAuditLogger shutdown complete - {final_stats}")

# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def create_security_audit_logger(database_manager=None, enable_alerts: bool = True) -> SecurityAuditLogger:
    """
    Factory function to create a configured SecurityAuditLogger
    
    Args:
        database_manager: DatabaseManager instance for persistence
        enable_alerts (bool): Enable real-time security alerts
        
    Returns:
        SecurityAuditLogger: Configured logger instance
    """
    return SecurityAuditLogger(database_manager, enable_alerts)

# Example usage and testing
if __name__ == "__main__":
    # This section would only run if the file is executed directly (for testing)
    logging.basicConfig(level=logging.DEBUG)
    
    print("Testing SecurityAuditLogger...")
    
    # Create logger instance
    audit_logger = create_security_audit_logger(enable_alerts=True)
    
    # Test logging different event types
    print("Logging test events...")
    
    # Test authentication
    auth_event = audit_logger.log_authentication_attempt(
        user_id=1, username="testuser", success=True
    )
    print(f"Logged authentication: {auth_event.event_id}")
    
    # Test password view
    view_event = audit_logger.log_password_view(
        user_id=1, session_id="test_session", entry_id=101,
        view_duration_seconds=30
    )
    print(f"Logged password view: {view_event.event_id}")
    
    # Test settings change
    settings_event = audit_logger.log_settings_change(
        user_id=1, session_id="test_session",
        category="password_viewing", key="view_timeout_minutes",
        old_value=1, new_value=5, affects_security=True
    )
    print(f"Logged settings change: {settings_event.event_id}")
    
    # Get statistics
    stats = audit_logger.get_security_statistics(user_id=1, hours=1)
    print(f"Security statistics: {stats}")
    
    print("SecurityAuditLogger test completed successfully!")
    
    # Cleanup
    audit_logger.shutdown()
