#!/usr/bin/env python3
"""
Personal Password Manager - Type Definitions
============================================

This module defines type aliases and TypedDict classes used throughout
the password manager application for better type safety and code clarity.

Author: Personal Password Manager
Version: 2.2.0
"""

from datetime import datetime
from typing import Any, Dict, List, NewType, Optional, TypedDict

# ============================================================================
# Type Aliases
# ============================================================================

# Session and User Types
SessionId = NewType("SessionId", str)
UserId = NewType("UserId", int)
PasswordId = NewType("PasswordId", int)

# Security Types
PasswordHash = NewType("PasswordHash", str)
EncryptedData = NewType("EncryptedData", bytes)
Salt = NewType("Salt", bytes)
SecretKey = NewType("SecretKey", bytes)

# Database Types
DatabasePath = NewType("DatabasePath", str)
TableName = NewType("TableName", str)

# TOTP Types
TOTPSecret = NewType("TOTPSecret", str)
TOTPCode = NewType("TOTPCode", str)
BackupCode = NewType("BackupCode", str)

# ============================================================================
# TypedDict Classes - Database Records
# ============================================================================


class UserRecord(TypedDict):
    """Database record for users table"""

    user_id: int
    username: str
    password_hash: str
    salt: str
    created_at: str
    last_login: Optional[str]
    failed_attempts: int
    locked_until: Optional[str]
    totp_secret: Optional[str]
    totp_enabled: bool
    backup_codes: Optional[str]


class PasswordRecord(TypedDict):
    """Database record for passwords table"""

    id: int
    user_id: int
    website: str
    username: str
    encrypted_password: bytes
    remarks: str
    created_at: str
    last_modified: str


class AuditLogRecord(TypedDict):
    """Database record for audit_log table"""

    id: int
    user_id: int
    action: str
    timestamp: str
    ip_address: Optional[str]
    details: Optional[str]


class SecurityAuditLogRecord(TypedDict):
    """Database record for security_audit_log table"""

    id: int
    timestamp: str
    event_type: str
    severity: str
    message: str
    user_id: Optional[int]
    ip_address: Optional[str]
    details: Optional[str]


# ============================================================================
# TypedDict Classes - Application Data Structures
# ============================================================================


class PasswordEntry(TypedDict):
    """Decrypted password entry for application use"""

    id: int
    user_id: int
    website: str
    username: str
    password: str
    remarks: str
    created_at: datetime
    last_modified: datetime


class UserSession(TypedDict):
    """User session information"""

    session_id: str
    user_id: int
    username: str
    login_time: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    pending_2fa: bool


class TwoFAStatus(TypedDict):
    """Two-Factor Authentication status"""

    enabled: bool
    has_secret: bool
    has_backup_codes: bool
    backup_codes_count: int


class PasswordHealthStats(TypedDict):
    """Password health statistics"""

    total_passwords: int
    weak_passwords: int
    duplicate_passwords: int
    old_passwords: int
    security_score: float
    weak_password_ids: List[int]
    duplicate_groups: List[List[int]]
    old_password_ids: List[int]


class UserStatistics(TypedDict):
    """User account statistics"""

    total_passwords: int
    last_login: Optional[str]
    account_created: str
    failed_login_attempts: int
    total_logins: int


class BackupMetadata(TypedDict):
    """Backup file metadata"""

    backup_path: str
    timestamp: str
    file_size: int
    username: str
    version: str


class EncryptionInfo(TypedDict):
    """Encryption configuration information"""

    algorithm: str
    key_derivation: str
    iterations: int
    salt_length: int


# ============================================================================
# TypedDict Classes - Configuration
# ============================================================================


class DatabaseConfig(TypedDict):
    """Database configuration"""

    database_path: str
    timeout: int
    check_same_thread: bool
    isolation_level: Optional[str]


class SecurityConfig(TypedDict):
    """Security configuration"""

    session_timeout: int
    max_failed_attempts: int
    lockout_duration: int
    password_min_length: int
    require_special_chars: bool


class ThemeConfig(TypedDict):
    """Theme configuration"""

    mode: str
    color_scheme: str
    accent_color: str


# ============================================================================
# TypedDict Classes - API Responses
# ============================================================================


class ValidationResult(TypedDict):
    """Result of validation operation"""

    valid: bool
    message: str
    details: Optional[Dict[str, Any]]


class OperationResult(TypedDict):
    """Result of a database or business logic operation"""

    success: bool
    message: str
    data: Optional[Any]
    error_code: Optional[str]


class SearchResult(TypedDict):
    """Search operation result"""

    results: List[PasswordEntry]
    total_count: int
    page: int
    per_page: int


# ============================================================================
# Type Guards and Utility Types
# ============================================================================

# Optional types for nullable database fields
OptionalStr = Optional[str]
OptionalInt = Optional[int]
OptionalBytes = Optional[bytes]
OptionalDatetime = Optional[datetime]

# Common dictionary types
JsonDict = Dict[str, Any]
StrDict = Dict[str, str]
IntDict = Dict[str, int]

# Callback types
OnSuccessCallback = Optional[Any]  # Will be refined based on specific use cases
OnErrorCallback = Optional[Any]


# ============================================================================
# Exported Types
# ============================================================================

__all__ = [
    # Type Aliases
    "SessionId",
    "UserId",
    "PasswordId",
    "PasswordHash",
    "EncryptedData",
    "Salt",
    "SecretKey",
    "DatabasePath",
    "TableName",
    "TOTPSecret",
    "TOTPCode",
    "BackupCode",
    # Database Records
    "UserRecord",
    "PasswordRecord",
    "AuditLogRecord",
    "SecurityAuditLogRecord",
    # Application Data Structures
    "PasswordEntry",
    "UserSession",
    "TwoFAStatus",
    "PasswordHealthStats",
    "UserStatistics",
    "BackupMetadata",
    "EncryptionInfo",
    # Configuration
    "DatabaseConfig",
    "SecurityConfig",
    "ThemeConfig",
    # API Responses
    "ValidationResult",
    "OperationResult",
    "SearchResult",
    # Utility Types
    "OptionalStr",
    "OptionalInt",
    "OptionalBytes",
    "OptionalDatetime",
    "JsonDict",
    "StrDict",
    "IntDict",
    "OnSuccessCallback",
    "OnErrorCallback",
]
