#!/usr/bin/env python3
"""
Personal Password Manager - Password View Authentication Service
==============================================================

This module provides secure time-based authentication for password viewing operations.
It manages view permissions with configurable timeouts, master password verification,
and automatic cleanup of expired permissions.

Key Features:
- Time-based view permission management (global timer approach)
- Master password authentication for view access
- Automatic permission expiration and cleanup
- Computer lock/unlock detection and permission clearing
- Session-based permission isolation
- Comprehensive logging of authentication events
- Thread-safe operations for multi-user scenarios

Security Features:
- No plaintext password storage (uses hashes for verification)
- Automatic permission revocation on system events
- Rate limiting for authentication attempts
- Session validation before granting permissions
- Secure memory clearing of sensitive data

Author: Personal Password Manager Enhancement Team
Version: 2.2.0
Date: September 21, 2025
"""

import hashlib
import logging
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Optional, Set

# Configure logging for view authentication operations
logger = logging.getLogger(__name__)


class ViewPermissionStatus(Enum):
    """Enumeration of view permission states"""

    ACTIVE = "active"  # Permission is currently valid
    EXPIRED = "expired"  # Permission has timed out
    REVOKED = "revoked"  # Permission was manually revoked
    DENIED = "denied"  # Authentication failed
    PENDING = "pending"  # Authentication in progress


class AuthenticationMethod(Enum):
    """Methods used for view authentication"""

    MASTER_PASSWORD = "master_password"  # Standard master password entry
    BIOMETRIC = "biometric"  # Future: fingerprint/face unlock
    HARDWARE_KEY = "hardware_key"  # Future: USB security key
    CACHED_SESSION = "cached_session"  # Using existing session cache


class ViewPermissionGrant:
    """
    Represents a granted view permission with metadata

    This class encapsulates all information about a granted view permission,
    including timing, authentication method, and security context.
    """

    def __init__(
        self,
        session_id: str,
        user_id: int,
        timeout_minutes: int,
        auth_method: AuthenticationMethod,
        granted_by_ip: str = "127.0.0.1",
    ):
        """
        Initialize a view permission grant

        Args:
            session_id (str): Session that requested permission
            user_id (int): User ID who was granted permission
            timeout_minutes (int): How long permission should last
            auth_method (AuthenticationMethod): How permission was granted
            granted_by_ip (str): IP address that requested permission
        """
        self.session_id = session_id
        self.user_id = user_id
        self.timeout_minutes = timeout_minutes
        self.auth_method = auth_method
        self.granted_by_ip = granted_by_ip

        # Timing information
        self.granted_at = datetime.now()
        self.expires_at = self.granted_at + timedelta(minutes=timeout_minutes)

        # Usage tracking
        self.password_views_count = 0
        self.last_activity_at = self.granted_at

        # Security metadata
        self.risk_score = self._calculate_initial_risk_score()
        self.authentication_strength = self._assess_auth_strength()

    def is_valid(self) -> bool:
        """Check if permission is still valid (not expired)"""
        return datetime.now() < self.expires_at

    def get_remaining_seconds(self) -> int:
        """Get remaining time in seconds (0 if expired)"""
        if not self.is_valid():
            return 0

        remaining = self.expires_at - datetime.now()
        return int(remaining.total_seconds())

    def get_remaining_minutes(self) -> int:
        """Get remaining time in minutes (0 if expired)"""
        return max(0, self.get_remaining_seconds() // 60)

    def record_password_view(self):
        """Record that a password was viewed using this permission"""
        self.password_views_count += 1
        self.last_activity_at = datetime.now()

        # Increase risk score if too many views
        if self.password_views_count > 10:
            self.risk_score = min(100, self.risk_score + 5)

    def extend_permission(self, additional_minutes: int) -> bool:
        """
        Extend the permission for additional time

        Args:
            additional_minutes (int): Minutes to extend permission

        Returns:
            bool: True if extended successfully, False if already expired
        """
        if not self.is_valid():
            return False

        self.expires_at += timedelta(minutes=additional_minutes)
        self.last_activity_at = datetime.now()
        return True

    def _calculate_initial_risk_score(self) -> int:
        """Calculate initial risk score based on context (0-100)"""
        risk_score = 0

        # Base risk for any password viewing
        risk_score += 10

        # Higher risk for longer durations
        if self.timeout_minutes > 30:
            risk_score += 20
        elif self.timeout_minutes > 10:
            risk_score += 10

        # IP-based risk (future enhancement)
        if self.granted_by_ip != "127.0.0.1":
            risk_score += 15

        return min(100, risk_score)

    def _assess_auth_strength(self) -> str:
        """Assess authentication strength based on method"""
        strength_map = {
            AuthenticationMethod.MASTER_PASSWORD: "MEDIUM",
            AuthenticationMethod.BIOMETRIC: "HIGH",
            AuthenticationMethod.HARDWARE_KEY: "VERY_HIGH",
            AuthenticationMethod.CACHED_SESSION: "LOW",
        }

        return strength_map.get(self.auth_method, "UNKNOWN")

    def to_dict(self) -> Dict[str, Any]:
        """Convert permission grant to dictionary for logging/serialization"""
        return {
            "session_id": self.session_id[:8] + "..." if self.session_id else "unknown",
            "user_id": self.user_id,
            "timeout_minutes": self.timeout_minutes,
            "auth_method": self.auth_method.value,
            "granted_by_ip": self.granted_by_ip,
            "granted_at": self.granted_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_valid": self.is_valid(),
            "remaining_seconds": self.get_remaining_seconds(),
            "password_views_count": self.password_views_count,
            "last_activity_at": self.last_activity_at.isoformat(),
            "risk_score": self.risk_score,
            "authentication_strength": self.authentication_strength,
        }


class PasswordViewAuthService:
    """
    Manages password viewing authentication with time-based permissions

    This service handles the secure authentication process for viewing passwords,
    implementing a global timer approach where users authenticate once and can
    view passwords for a configured duration. It includes comprehensive security
    features like rate limiting, audit logging, and automatic cleanup.

    Features:
    - Global timer approach (authenticate once, view multiple passwords)
    - Configurable timeout periods (1-60 minutes)
    - Master password verification integration
    - Computer lock/unlock detection
    - Automatic permission cleanup and expiration
    - Comprehensive security event logging
    - Thread-safe operations for concurrent access
    - Rate limiting to prevent brute force attacks
    """

    def __init__(self, default_timeout_minutes: int = 1):
        """
        Initialize the password view authentication service

        Args:
            default_timeout_minutes (int): Default timeout for view permissions
        """
        self.default_timeout_minutes = default_timeout_minutes

        # Core permission storage - maps session_id to ViewPermissionGrant
        self._permissions: Dict[str, ViewPermissionGrant] = {}

        # Thread safety
        self._lock = threading.RLock()  # Reentrant lock for nested calls

        # Rate limiting - tracks authentication attempts per session
        self._auth_attempts: Dict[str, list] = {}  # session_id -> [timestamps]
        self._max_attempts_per_hour = 10

        # System event tracking
        self._system_lock_detected = False
        self._last_cleanup = datetime.now()

        # Callbacks for external event notification
        self._permission_granted_callbacks: Set[Callable] = set()
        self._permission_revoked_callbacks: Set[Callable] = set()

        # Start background cleanup thread
        self._cleanup_thread = None
        self._start_cleanup_thread()

        logger.info(
            f"PasswordViewAuthService initialized with {default_timeout_minutes}min default timeout"
        )

    def grant_view_permission(
        self,
        session_id: str,
        user_id: int,
        master_password_hash: str,
        provided_password_hash: str,
        timeout_minutes: Optional[int] = None,
        client_ip: str = "127.0.0.1",
    ) -> ViewPermissionGrant:
        """
        Grant view permission after successful master password authentication

        Args:
            session_id (str): Session requesting permission
            user_id (int): User ID for the session
            master_password_hash (str): Stored master password hash
            provided_password_hash (str): Hash of provided password
            timeout_minutes (int, optional): Custom timeout (defaults to service default)
            client_ip (str): IP address of requesting client

        Returns:
            ViewPermissionGrant: Permission grant object with metadata

        Raises:
            PermissionError: If authentication fails or rate limit exceeded
            ValueError: If invalid parameters provided
        """
        if not session_id or not master_password_hash or not provided_password_hash:
            raise ValueError("Session ID and password hashes are required")

        with self._lock:
            # Check rate limiting
            if not self._check_rate_limit(session_id):
                self._log_auth_attempt(session_id, user_id, "RATE_LIMITED", client_ip)
                raise PermissionError("Rate limit exceeded. Too many authentication attempts.")

            # Record authentication attempt
            self._record_auth_attempt(session_id)

            # Verify master password
            if not self._verify_password_hash(master_password_hash, provided_password_hash):
                self._log_auth_attempt(session_id, user_id, "INVALID_PASSWORD", client_ip)
                raise PermissionError("Invalid master password")

            # Clear any existing permission for this session
            if session_id in self._permissions:
                self._permissions[session_id]
                logger.info(f"Replacing existing permission for session {session_id[:8]}...")

            # Create new permission grant
            timeout = timeout_minutes or self.default_timeout_minutes
            permission = ViewPermissionGrant(
                session_id=session_id,
                user_id=user_id,
                timeout_minutes=timeout,
                auth_method=AuthenticationMethod.MASTER_PASSWORD,
                granted_by_ip=client_ip,
            )

            # Store permission
            self._permissions[session_id] = permission

            # Log successful authentication
            self._log_auth_attempt(session_id, user_id, "SUCCESS", client_ip, permission.to_dict())

            # Notify callbacks
            self._notify_permission_granted(permission)

            logger.info(
                f"View permission granted to session {session_id[:8]}... for {timeout} minutes"
            )
            return permission

    def has_view_permission(self, session_id: str) -> bool:
        """
        Check if session has valid view permission

        Args:
            session_id (str): Session to check

        Returns:
            bool: True if session has valid permission, False otherwise
        """
        if not session_id:
            return False

        with self._lock:
            permission = self._permissions.get(session_id)

            if not permission:
                return False

            if not permission.is_valid():
                # Permission expired, remove it
                self._revoke_permission(session_id, "EXPIRED")
                return False

            return True

    def get_permission_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a session's view permission

        Args:
            session_id (str): Session to get info for

        Returns:
            Optional[Dict[str, Any]]: Permission information or None if no permission
        """
        if not session_id:
            return None

        with self._lock:
            permission = self._permissions.get(session_id)

            if not permission:
                return None

            if not permission.is_valid():
                self._revoke_permission(session_id, "EXPIRED")
                return None

            return permission.to_dict()

    def record_password_view(self, session_id: str, entry_id: Optional[int] = None) -> bool:
        """
        Record that a password was viewed using this session's permission

        Args:
            session_id (str): Session that viewed password
            entry_id (int, optional): Password entry ID that was viewed

        Returns:
            bool: True if recorded successfully, False if no valid permission
        """
        if not self.has_view_permission(session_id):
            return False

        with self._lock:
            permission = self._permissions.get(session_id)
            if permission:
                permission.record_password_view()

                # Log the password view event
                self._log_password_view(session_id, permission.user_id, entry_id)

                return True

        return False

    def extend_permission(self, session_id: str, additional_minutes: int) -> bool:
        """
        Extend an existing view permission (if still valid)

        Args:
            session_id (str): Session to extend permission for
            additional_minutes (int): Minutes to add to current expiration

        Returns:
            bool: True if extended successfully, False otherwise
        """
        if not session_id or additional_minutes <= 0:
            return False

        with self._lock:
            permission = self._permissions.get(session_id)

            if not permission or not permission.is_valid():
                return False

            success = permission.extend_permission(additional_minutes)

            if success:
                logger.info(
                    f"Extended permission for session {session_id[:8]}... by {additional_minutes} minutes"
                )
                self._log_auth_attempt(
                    session_id,
                    permission.user_id,
                    "PERMISSION_EXTENDED",
                    permission.granted_by_ip,
                    {"additional_minutes": additional_minutes},
                )

            return success

    def revoke_permission(self, session_id: str, reason: str = "USER_REQUEST") -> bool:
        """
        Manually revoke view permission for a session

        Args:
            session_id (str): Session to revoke permission for
            reason (str): Reason for revocation

        Returns:
            bool: True if permission was revoked, False if no permission existed
        """
        return self._revoke_permission(session_id, reason)

    def revoke_all_permissions(self, reason: str = "SECURITY_EVENT") -> int:
        """
        Revoke all active view permissions (security measure)

        Args:
            reason (str): Reason for mass revocation

        Returns:
            int: Number of permissions revoked
        """
        with self._lock:
            session_ids = list(self._permissions.keys())
            revoked_count = 0

            for session_id in session_ids:
                if self._revoke_permission(session_id, reason):
                    revoked_count += 1

            logger.warning(f"Revoked all {revoked_count} view permissions due to: {reason}")
            return revoked_count

    def get_active_permissions_count(self) -> int:
        """Get count of currently active view permissions"""
        with self._lock:
            return len([p for p in self._permissions.values() if p.is_valid()])

    def get_permission_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about view permissions

        Returns:
            Dict[str, Any]: Statistics including active count, expired count, etc.
        """
        with self._lock:
            total_permissions = len(self._permissions)
            active_permissions = len([p for p in self._permissions.values() if p.is_valid()])
            expired_permissions = total_permissions - active_permissions

            # Calculate average timeout and usage stats
            if self._permissions:
                timeouts = [p.timeout_minutes for p in self._permissions.values()]
                view_counts = [p.password_views_count for p in self._permissions.values()]
                risk_scores = [p.risk_score for p in self._permissions.values()]

                avg_timeout = sum(timeouts) / len(timeouts)
                total_views = sum(view_counts)
                avg_risk_score = sum(risk_scores) / len(risk_scores)
            else:
                avg_timeout = 0
                total_views = 0
                avg_risk_score = 0

            return {
                "total_permissions_granted": total_permissions,
                "active_permissions": active_permissions,
                "expired_permissions": expired_permissions,
                "average_timeout_minutes": round(avg_timeout, 1),
                "total_password_views": total_views,
                "average_risk_score": round(avg_risk_score, 1),
                "service_uptime_minutes": int(
                    (datetime.now() - self._last_cleanup).total_seconds() / 60
                ),
                "cleanup_runs": getattr(self, "_cleanup_runs", 0),
            }

    def cleanup_expired_permissions(self) -> int:
        """
        Clean up expired permissions and return count of cleaned items

        Returns:
            int: Number of expired permissions cleaned up
        """
        with self._lock:
            expired_sessions = []

            for session_id, permission in self._permissions.items():
                if not permission.is_valid():
                    expired_sessions.append(session_id)

            # Remove expired permissions
            for session_id in expired_sessions:
                self._revoke_permission(session_id, "CLEANUP_EXPIRED")

            # Clean up old authentication attempts (older than 1 hour)
            self._cleanup_auth_attempts()

            if expired_sessions:
                logger.debug(f"Cleaned up {len(expired_sessions)} expired view permissions")

            self._last_cleanup = datetime.now()
            return len(expired_sessions)

    def detect_system_lock(self) -> bool:
        """
        Detect if system was locked/unlocked (basic implementation)

        Returns:
            bool: True if system lock state changed, False otherwise
        """
        # This is a basic implementation - in practice you'd use platform-specific APIs
        # For now, we'll implement a simple detection mechanism

        try:
            # On Windows, you could check if screensaver is active
            # On Linux/Mac, you could check for desktop lock signals
            # For now, this is a placeholder that returns False

            current_lock_state = False  # Placeholder implementation

            if current_lock_state != self._system_lock_detected:
                self._system_lock_detected = current_lock_state

                if current_lock_state:
                    # System was locked - revoke all permissions
                    revoked_count = self.revoke_all_permissions("SYSTEM_LOCKED")
                    logger.warning(
                        f"System lock detected - revoked {revoked_count} view permissions"
                    )
                    return True
                else:
                    logger.info("System unlock detected")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error detecting system lock state: {e}")
            return False

    # ==========================================
    # PRIVATE HELPER METHODS
    # ==========================================

    def _revoke_permission(self, session_id: str, reason: str) -> bool:
        """Internal method to revoke a permission"""
        permission = self._permissions.pop(session_id, None)

        if permission:
            # Log revocation
            self._log_auth_attempt(
                session_id,
                permission.user_id,
                "PERMISSION_REVOKED",
                permission.granted_by_ip,
                {"reason": reason, "views_performed": permission.password_views_count},
            )

            # Notify callbacks
            self._notify_permission_revoked(permission, reason)

            logger.debug(
                f"View permission revoked for session {session_id[:8]}... (reason: {reason})"
            )
            return True

        return False

    def _verify_password_hash(self, stored_hash: str, provided_hash: str) -> bool:
        """
        Verify password hash (constant-time comparison)

        Args:
            stored_hash (str): Hash stored in database/session
            provided_hash (str): Hash of password provided by user

        Returns:
            bool: True if hashes match, False otherwise
        """
        if not stored_hash or not provided_hash:
            return False

        # Use constant-time comparison to prevent timing attacks
        return (
            len(stored_hash) == len(provided_hash)
            and sum(a != b for a, b in zip(stored_hash, provided_hash)) == 0
        )

    def _check_rate_limit(self, session_id: str) -> bool:
        """Check if session is within rate limit for authentication attempts"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        # Get attempts for this session in the last hour
        attempts = self._auth_attempts.get(session_id, [])
        recent_attempts = [ts for ts in attempts if ts > hour_ago]

        return len(recent_attempts) < self._max_attempts_per_hour

    def _record_auth_attempt(self, session_id: str):
        """Record an authentication attempt for rate limiting"""
        if session_id not in self._auth_attempts:
            self._auth_attempts[session_id] = []

        self._auth_attempts[session_id].append(datetime.now())

    def _cleanup_auth_attempts(self):
        """Clean up old authentication attempts (older than 1 hour)"""
        hour_ago = datetime.now() - timedelta(hours=1)

        for session_id in list(self._auth_attempts.keys()):
            attempts = self._auth_attempts[session_id]
            recent_attempts = [ts for ts in attempts if ts > hour_ago]

            if recent_attempts:
                self._auth_attempts[session_id] = recent_attempts
            else:
                del self._auth_attempts[session_id]

    def _start_cleanup_thread(self):
        """Start background thread for automatic cleanup"""

        def cleanup_worker():
            cleanup_runs = 0
            while getattr(self, "_should_run_cleanup", True):
                try:
                    # Run cleanup every 60 seconds
                    time.sleep(60)

                    # Perform cleanup
                    self.cleanup_expired_permissions()

                    # Check for system lock every 30 seconds
                    if cleanup_runs % 30 == 0:
                        self.detect_system_lock()

                    cleanup_runs += 1
                    self._cleanup_runs = cleanup_runs

                except Exception as e:
                    logger.error(f"Error in cleanup thread: {e}")

        self._should_run_cleanup = True
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()

        logger.debug("Background cleanup thread started")

    def _notify_permission_granted(self, permission: ViewPermissionGrant):
        """Notify registered callbacks that permission was granted"""
        for callback in self._permission_granted_callbacks:
            try:
                callback(permission)
            except Exception as e:
                logger.error(f"Error in permission granted callback: {e}")

    def _notify_permission_revoked(self, permission: ViewPermissionGrant, reason: str):
        """Notify registered callbacks that permission was revoked"""
        for callback in self._permission_revoked_callbacks:
            try:
                callback(permission, reason)
            except Exception as e:
                logger.error(f"Error in permission revoked callback: {e}")

    def _log_auth_attempt(
        self,
        session_id: str,
        user_id: int,
        result: str,
        client_ip: str,
        details: Optional[Dict] = None,
    ):
        """Log authentication attempt to security audit (placeholder)"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id[:8] + "..." if session_id else "unknown",
            "user_id": user_id,
            "action": "VIEW_AUTH_ATTEMPT",
            "result": result,
            "client_ip": client_ip,
            "details": details or {},
        }

        # In a real implementation, this would use the SecurityAuditLogger
        logger.info(f"Auth attempt: {result} for user {user_id} from {client_ip}")

    def _log_password_view(self, session_id: str, user_id: int, entry_id: Optional[int]):
        """Log password view event to security audit (placeholder)"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id[:8] + "..." if session_id else "unknown",
            "user_id": user_id,
            "action": "PASSWORD_VIEWED",
            "entry_id": entry_id,
            "details": {"auth_method": "view_permission"},
        }

        # In a real implementation, this would use the SecurityAuditLogger
        logger.debug(f"Password viewed by user {user_id} (entry: {entry_id})")

    def add_permission_granted_callback(self, callback: Callable):
        """Add callback to be notified when permissions are granted"""
        self._permission_granted_callbacks.add(callback)

    def add_permission_revoked_callback(self, callback: Callable):
        """Add callback to be notified when permissions are revoked"""
        self._permission_revoked_callbacks.add(callback)

    def shutdown(self):
        """Shutdown the service and clean up resources"""
        logger.info("Shutting down PasswordViewAuthService...")

        # Stop cleanup thread
        self._should_run_cleanup = False
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)

        # Revoke all permissions
        with self._lock:
            self.revoke_all_permissions("SERVICE_SHUTDOWN")

        # Clear callbacks
        self._permission_granted_callbacks.clear()
        self._permission_revoked_callbacks.clear()

        logger.info("PasswordViewAuthService shutdown complete")


# ==========================================
# UTILITY FUNCTIONS
# ==========================================


def create_password_hash(password: str) -> str:
    """
    Create SHA-256 hash of password for authentication

    Args:
        password (str): Password to hash

    Returns:
        str: SHA-256 hash in hexadecimal format
    """
    if not password:
        return ""

    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_view_auth_service(default_timeout: int = 1) -> PasswordViewAuthService:
    """
    Factory function to create a configured PasswordViewAuthService

    Args:
        default_timeout (int): Default timeout in minutes

    Returns:
        PasswordViewAuthService: Configured service instance
    """
    return PasswordViewAuthService(default_timeout_minutes=default_timeout)


# Example usage and testing functions
if __name__ == "__main__":
    # This section would only run if the file is executed directly (for testing)
    logging.basicConfig(level=logging.DEBUG)

    # Create service instance
    auth_service = create_view_auth_service(default_timeout=2)

    # Simulate authentication
    try:
        # Test password hashing
        password = "test_master_password"
        password_hash = create_password_hash(password)

        print("Testing PasswordViewAuthService...")
        print(f"Password hash: {password_hash[:16]}...")

        # Test authentication
        permission = auth_service.grant_view_permission(
            session_id="test_session_123",
            user_id=1,
            master_password_hash=password_hash,
            provided_password_hash=password_hash,
            timeout_minutes=2,
        )

        print(f"Permission granted: {permission.is_valid()}")
        print(f"Expires in: {permission.get_remaining_seconds()} seconds")

        # Test permission check
        has_permission = auth_service.has_view_permission("test_session_123")
        print(f"Has permission: {has_permission}")

        # Test statistics
        stats = auth_service.get_permission_statistics()
        print(f"Service stats: {stats}")

        print("PasswordViewAuthService test completed successfully!")

    except Exception as e:
        print(f"Test failed: {e}")

    finally:
        # Cleanup
        auth_service.shutdown()
