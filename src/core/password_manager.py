#!/usr/bin/env python3
"""
Personal Password Manager - Password Management Core
===================================================

This module provides the high-level password management functionality that integrates
all core systems (database, encryption, authentication) into a comprehensive API
for password operations. It handles secure password storage, retrieval, and management
with proper master password handling.

Key Features:
- Complete password CRUD operations with encryption
- Secure master password handling with optional caching
- Advanced search and filtering capabilities
- Bulk operations for import/export scenarios
- Data validation and duplicate detection
- Password organization and categorization
- Activity logging and audit trails
- Performance optimization for large datasets

Security Features:
- Master password validation before operations
- Secure temporary password caching with timeouts
- Input validation and sanitization
- Operation-level access control
- Audit logging for all password operations
- Memory clearing for sensitive data

Author: Personal Password Manager
Version: 1.0.0
"""

import logging
import threading
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import re

# Import our core modules
from .database import DatabaseManager, DatabaseError
from .encryption import PasswordEncryption, EncryptionError, DecryptionError
from .auth import AuthenticationManager, AuthenticationError, InvalidSessionError, SessionExpiredError

# Configure logging for password management operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PasswordManagerError(Exception):
    """Base exception for password manager operations"""
    pass

class MasterPasswordRequiredError(PasswordManagerError):
    """Raised when master password is required for an operation"""
    pass

class DuplicateEntryError(PasswordManagerError):
    """Raised when attempting to create duplicate password entries"""
    pass

class InvalidPasswordEntryError(PasswordManagerError):
    """Raised when password entry data is invalid"""
    pass

class PasswordCacheMode(Enum):
    """Enumeration of password caching modes"""
    NO_CACHE = "no_cache"           # Never cache master password
    TEMPORARY = "temporary"         # Cache for short periods
    SESSION = "session"             # Cache for entire session
    OPERATION = "operation"         # Cache for single operation chain

@dataclass
class PasswordEntry:
    """
    Represents a password entry with metadata
    
    This dataclass provides a structured representation of password entries
    with all necessary metadata for display and management purposes.
    """
    entry_id: int
    website: str
    username: str
    password: str = field(repr=False)  # Don't print password in logs
    remarks: str = ""
    created_at: datetime = None
    modified_at: datetime = None
    is_favorite: bool = False
    password_strength: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize computed fields"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.modified_at is None:
            self.modified_at = self.created_at

@dataclass
class SearchCriteria:
    """
    Represents search criteria for password entries
    """
    website: Optional[str] = None
    username: Optional[str] = None
    remarks: Optional[str] = None
    is_favorite: Optional[bool] = None
    tags: List[str] = field(default_factory=list)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: str = "website"
    sort_order: str = "asc"
    limit: Optional[int] = None

class PasswordManagerCore:
    """
    Core password management system that integrates all components
    
    This class provides a high-level API for password management operations,
    integrating the database, encryption, and authentication systems. It handles
    secure master password management and provides comprehensive password operations.
    
    Key Features:
    - Secure password operations with master password validation
    - Advanced search and filtering capabilities
    - Bulk operations for performance
    - Data validation and integrity checking
    - Activity logging and audit trails
    - Configurable master password caching
    
    Attributes:
        auth_manager (AuthenticationManager): Authentication system
        cache_mode (PasswordCacheMode): Master password caching strategy
        cache_timeout_minutes (int): Cache timeout for temporary mode
        _master_password_cache (Dict): Temporary password cache
        _cache_lock (threading.Lock): Thread synchronization for cache
    """
    
    def __init__(self, db_path: str = "data/password_manager.db",
                 cache_mode: PasswordCacheMode = PasswordCacheMode.TEMPORARY,
                 cache_timeout_minutes: int = 5,
                 auth_manager: AuthenticationManager = None):
        """
        Initialize the password manager core system
        
        Args:
            db_path (str): Path to the database file
            cache_mode (PasswordCacheMode): Master password caching strategy
            cache_timeout_minutes (int): Cache timeout for temporary mode
            auth_manager (AuthenticationManager): Existing auth manager to reuse
        """
        if auth_manager is not None:
            self.auth_manager = auth_manager
        else:
            self.auth_manager = AuthenticationManager(db_path)
        self.cache_mode = cache_mode
        self.cache_timeout_minutes = cache_timeout_minutes
        
        # Master password caching system
        self._master_password_cache: Dict[str, Dict] = {}
        self._cache_lock = threading.Lock()
        
        logger.info(f"Password manager initialized with cache mode: {cache_mode.value}")
    
    def add_password_entry(self, session_id: str, website: str, username: str,
                          password: str, master_password: str = None, remarks: str = "",
                          is_favorite: bool = False, tags: List[str] = None) -> int:
        """
        Add a new password entry with encryption
        
        Args:
            session_id (str): Valid session token
            website (str): Website or service name
            username (str): Username for the service
            password (str): Plain text password to encrypt and store
            master_password (str, optional): Master password for encryption (will use cached if not provided)
            remarks (str, optional): User notes about the entry
            is_favorite (bool, optional): Mark as favorite
            tags (List[str], optional): Tags for organization
            
        Returns:
            int: ID of the created password entry
            
        Raises:
            InvalidSessionError: If session is invalid
            MasterPasswordRequiredError: If master password is invalid
            DuplicateEntryError: If entry already exists
            InvalidPasswordEntryError: If entry data is invalid
        """
        try:
            # Validate session
            session = self.auth_manager.validate_session(session_id)
            
            # Validate input data
            self._validate_password_entry_data(website, username, password)
            
            # Get master password from cache if not provided
            if master_password is None:
                master_password = self._get_cached_master_password(session_id)
                if master_password is None:
                    raise MasterPasswordRequiredError("Master password required for encryption. Please provide master password.")
            
            # Verify master password
            if not self._verify_master_password(session_id, master_password):
                raise MasterPasswordRequiredError("Invalid master password")
            
            # Check for duplicate entries
            if self._check_duplicate_entry(session.user_id, website, username):
                raise DuplicateEntryError(f"Entry already exists for {website} - {username}")
            
            # Encrypt password
            encrypted_password = session.encryption_system.encrypt_password(password, master_password)
            
            # Add to database
            entry_id = self.auth_manager.db_manager.add_password_entry(
                user_id=session.user_id,
                website=website.strip(),
                username=username.strip(),
                encrypted_password=encrypted_password,
                remarks=remarks.strip()
            )
            
            # Update favorite status if needed
            if is_favorite:
                self.auth_manager.db_manager.update_password_entry(
                    entry_id, session.user_id, is_favorite=True
                )
            
            # Cache master password if enabled
            self._cache_master_password(session_id, master_password)
            
            logger.info(f"Password entry added: {website} - {username} (Entry ID: {entry_id})")
            return entry_id
            
        except (InvalidSessionError, SessionExpiredError, MasterPasswordRequiredError, 
                DuplicateEntryError, InvalidPasswordEntryError):
            raise
        except Exception as e:
            logger.error(f"Failed to add password entry: {e}")
            raise PasswordManagerError(f"Failed to add password entry: {e}")
    
    def get_password_entry(self, session_id: str, entry_id: int, 
                          master_password: str = None, decrypt_password: bool = True) -> PasswordEntry:
        """
        Retrieve a specific password entry with optional decryption
        
        Args:
            session_id (str): Valid session token
            entry_id (int): ID of the password entry to retrieve
            master_password (str, optional): Master password for decryption
            decrypt_password (bool): Whether to decrypt the password
            
        Returns:
            PasswordEntry: Password entry with decrypted password (if requested)
            
        Raises:
            InvalidSessionError: If session is invalid
            MasterPasswordRequiredError: If master password needed but not provided
            PasswordManagerError: If entry not found or decryption fails
        """
        try:
            # Validate session
            session = self.auth_manager.validate_session(session_id)
            
            # Get entry from database
            entries = self.auth_manager.db_manager.get_password_entries(session.user_id)
            target_entry = None
            
            for entry in entries:
                if entry['entry_id'] == entry_id:
                    target_entry = entry
                    break
            
            if not target_entry:
                raise PasswordManagerError("Password entry not found or access denied")
            
            # Prepare password field
            decrypted_password = ""
            if decrypt_password:
                # Check if master password is provided or cached
                mp = master_password or self._get_cached_master_password(session_id)
                
                if not mp:
                    raise MasterPasswordRequiredError("Master password required for password decryption")
                
                # Verify master password
                if not self._verify_master_password(session_id, mp):
                    raise MasterPasswordRequiredError("Invalid master password")
                
                # Decrypt password
                decrypted_password = session.encryption_system.decrypt_password(
                    target_entry['password_encrypted'], mp
                )
                
                # Cache master password if enabled
                self._cache_master_password(session_id, mp)
            
            # Create PasswordEntry object
            entry = PasswordEntry(
                entry_id=target_entry['entry_id'],
                website=target_entry['website'],
                username=target_entry['username'],
                password=decrypted_password,
                remarks=target_entry.get('remarks', ''),
                created_at=datetime.fromisoformat(target_entry['created_at']) if target_entry.get('created_at') else None,
                modified_at=datetime.fromisoformat(target_entry['modified_at']) if target_entry.get('modified_at') else None,
                is_favorite=bool(target_entry.get('is_favorite', False))
            )
            
            logger.debug(f"Retrieved password entry: {entry.website} - {entry.username}")
            return entry
            
        except (InvalidSessionError, SessionExpiredError, MasterPasswordRequiredError):
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve password entry {entry_id}: {e}")
            raise PasswordManagerError(f"Failed to retrieve password entry: {e}")
    
    def search_password_entries(self, session_id: str, criteria: SearchCriteria = None,
                               master_password: str = None, include_passwords: bool = False) -> List[PasswordEntry]:
        """
        Search password entries with advanced filtering
        
        Args:
            session_id (str): Valid session token
            criteria (SearchCriteria, optional): Search and filter criteria
            master_password (str, optional): Master password for password decryption
            include_passwords (bool): Whether to include decrypted passwords
            
        Returns:
            List[PasswordEntry]: List of matching password entries
            
        Raises:
            InvalidSessionError: If session is invalid
        """
        try:
            # Validate session
            session = self.auth_manager.validate_session(session_id)
            
            # Use default criteria if none provided
            if criteria is None:
                criteria = SearchCriteria()
            
            # Get all entries from database
            db_entries = self.auth_manager.db_manager.get_password_entries(
                session.user_id, 
                website=criteria.website
            )
            
            # Convert to PasswordEntry objects and apply filters
            password_entries = []
            
            for db_entry in db_entries:
                # Apply additional filters
                if criteria.username and criteria.username.lower() not in db_entry['username'].lower():
                    continue
                
                if criteria.remarks and criteria.remarks.lower() not in db_entry.get('remarks', '').lower():
                    continue
                
                if criteria.is_favorite is not None and bool(db_entry.get('is_favorite', False)) != criteria.is_favorite:
                    continue
                
                # Date filters
                if criteria.date_from or criteria.date_to:
                    created_at = datetime.fromisoformat(db_entry['created_at']) if db_entry.get('created_at') else datetime.min
                    
                    if criteria.date_from and created_at < criteria.date_from:
                        continue
                    
                    if criteria.date_to and created_at > criteria.date_to:
                        continue
                
                # Decrypt password if requested and master password available
                decrypted_password = ""
                if include_passwords:
                    mp = master_password or self._get_cached_master_password(session_id)
                    if mp and self._verify_master_password(session_id, mp):
                        try:
                            decrypted_password = session.encryption_system.decrypt_password(
                                db_entry['password_encrypted'], mp
                            )
                            # Cache master password if successful
                            self._cache_master_password(session_id, mp)
                        except (DecryptionError, EncryptionError):
                            logger.warning(f"Failed to decrypt password for entry {db_entry['entry_id']}")
                            decrypted_password = "[Decryption Failed]"
                
                # Create PasswordEntry object
                entry = PasswordEntry(
                    entry_id=db_entry['entry_id'],
                    website=db_entry['website'],
                    username=db_entry['username'],
                    password=decrypted_password,
                    remarks=db_entry.get('remarks', ''),
                    created_at=datetime.fromisoformat(db_entry['created_at']) if db_entry.get('created_at') else None,
                    modified_at=datetime.fromisoformat(db_entry['modified_at']) if db_entry.get('modified_at') else None,
                    is_favorite=bool(db_entry.get('is_favorite', False))
                )
                
                password_entries.append(entry)
            
            # Apply sorting
            password_entries = self._sort_entries(password_entries, criteria.sort_by, criteria.sort_order)
            
            # Apply limit
            if criteria.limit and criteria.limit > 0:
                password_entries = password_entries[:criteria.limit]
            
            logger.debug(f"Found {len(password_entries)} matching password entries")
            return password_entries
            
        except (InvalidSessionError, SessionExpiredError):
            raise
        except Exception as e:
            logger.error(f"Failed to search password entries: {e}")
            raise PasswordManagerError(f"Search failed: {e}")
    
    def update_password_entry(self, session_id: str, entry_id: int, website: str = None,
                             username: str = None, password: str = None, master_password: str = None,
                             remarks: str = None, is_favorite: bool = None) -> bool:
        """
        Update an existing password entry
        
        Args:
            session_id (str): Valid session token
            entry_id (int): ID of the entry to update
            website (str, optional): New website name
            username (str, optional): New username
            password (str, optional): New plain text password
            master_password (str, optional): Master password for encryption
            remarks (str, optional): New remarks
            is_favorite (bool, optional): New favorite status
            
        Returns:
            bool: True if update was successful
            
        Raises:
            InvalidSessionError: If session is invalid
            MasterPasswordRequiredError: If master password needed but not provided
            PasswordManagerError: If update fails
        """
        try:
            # Validate session
            session = self.auth_manager.validate_session(session_id)
            
            # Prepare update parameters
            update_params = {}
            
            if website is not None:
                update_params['website'] = website.strip()
            
            if username is not None:
                update_params['username'] = username.strip()
            
            if remarks is not None:
                update_params['remarks'] = remarks.strip()
            
            if is_favorite is not None:
                update_params['is_favorite'] = is_favorite
            
            # Handle password update (requires encryption)
            if password is not None:
                # Get master password
                mp = master_password or self._get_cached_master_password(session_id)
                
                if not mp:
                    raise MasterPasswordRequiredError("Master password required for password update")
                
                # Verify master password
                if not self._verify_master_password(session_id, mp):
                    raise MasterPasswordRequiredError("Invalid master password")
                
                # Encrypt new password
                encrypted_password = session.encryption_system.encrypt_password(password, mp)
                update_params['encrypted_password'] = encrypted_password
                
                # Cache master password if successful
                self._cache_master_password(session_id, mp)
            
            # Perform update
            success = self.auth_manager.db_manager.update_password_entry(
                entry_id, session.user_id, **update_params
            )
            
            if success:
                logger.info(f"Password entry updated: Entry ID {entry_id}")
            else:
                logger.warning(f"Password entry update failed: Entry ID {entry_id}")
            
            return success
            
        except (InvalidSessionError, SessionExpiredError, MasterPasswordRequiredError):
            raise
        except Exception as e:
            logger.error(f"Failed to update password entry {entry_id}: {e}")
            raise PasswordManagerError(f"Update failed: {e}")
    
    def delete_password_entry(self, session_id: str, entry_id: int) -> bool:
        """
        Delete a password entry
        
        Args:
            session_id (str): Valid session token
            entry_id (int): ID of the entry to delete
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            InvalidSessionError: If session is invalid
        """
        try:
            # Validate session
            session = self.auth_manager.validate_session(session_id)
            
            # Perform deletion
            success = self.auth_manager.db_manager.delete_password_entry(entry_id, session.user_id)
            
            if success:
                logger.info(f"Password entry deleted: Entry ID {entry_id}")
            else:
                logger.warning(f"Password entry deletion failed: Entry ID {entry_id}")
            
            return success
            
        except (InvalidSessionError, SessionExpiredError):
            raise
        except Exception as e:
            logger.error(f"Failed to delete password entry {entry_id}: {e}")
            raise PasswordManagerError(f"Deletion failed: {e}")
    
    def bulk_decrypt_passwords(self, session_id: str, entry_ids: List[int], 
                              master_password: str) -> Dict[int, str]:
        """
        Decrypt multiple passwords in a single operation for performance
        
        Args:
            session_id (str): Valid session token
            entry_ids (List[int]): List of entry IDs to decrypt
            master_password (str): Master password for decryption
            
        Returns:
            Dict[int, str]: Dictionary mapping entry IDs to decrypted passwords
            
        Raises:
            InvalidSessionError: If session is invalid
            MasterPasswordRequiredError: If master password is invalid
        """
        try:
            # Validate session
            session = self.auth_manager.validate_session(session_id)
            
            # Verify master password
            if not self._verify_master_password(session_id, master_password):
                raise MasterPasswordRequiredError("Invalid master password")
            
            # Get all entries for the user
            all_entries = self.auth_manager.db_manager.get_password_entries(session.user_id)
            
            # Filter requested entries and decrypt passwords
            decrypted_passwords = {}
            
            for entry in all_entries:
                if entry['entry_id'] in entry_ids:
                    try:
                        decrypted_password = session.encryption_system.decrypt_password(
                            entry['password_encrypted'], master_password
                        )
                        decrypted_passwords[entry['entry_id']] = decrypted_password
                    except (DecryptionError, EncryptionError) as e:
                        logger.error(f"Failed to decrypt entry {entry['entry_id']}: {e}")
                        decrypted_passwords[entry['entry_id']] = "[Decryption Failed]"
            
            # Cache master password after successful operations
            self._cache_master_password(session_id, master_password)
            
            logger.debug(f"Bulk decrypted {len(decrypted_passwords)} passwords")
            return decrypted_passwords
            
        except (InvalidSessionError, SessionExpiredError, MasterPasswordRequiredError):
            raise
        except Exception as e:
            logger.error(f"Bulk decryption failed: {e}")
            raise PasswordManagerError(f"Bulk decryption failed: {e}")
    
    def get_password_statistics(self, session_id: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics about user's password entries
        
        Args:
            session_id (str): Valid session token
            
        Returns:
            Dict[str, Any]: Statistics including counts, dates, and analysis
            
        Raises:
            InvalidSessionError: If session is invalid
        """
        try:
            # Validate session
            session = self.auth_manager.validate_session(session_id)
            
            # Get basic statistics from database
            db_stats = self.auth_manager.db_manager.get_user_statistics(session.user_id)
            
            # Get all entries for additional analysis
            entries = self.auth_manager.db_manager.get_password_entries(session.user_id)
            
            # Analyze entries
            website_counts = {}
            username_counts = {}
            recent_entries = []
            
            for entry in entries:
                # Count websites
                website = entry['website'].lower()
                website_counts[website] = website_counts.get(website, 0) + 1
                
                # Count usernames
                username = entry['username'].lower()
                username_counts[username] = username_counts.get(username, 0) + 1
                
                # Recent entries (last 30 days)
                created_at = datetime.fromisoformat(entry['created_at']) if entry.get('created_at') else datetime.min
                if (datetime.now() - created_at).days <= 30:
                    recent_entries.append(entry)
            
            # Compile comprehensive statistics
            statistics = {
                'total_entries': db_stats['total_entries'],
                'favorites': db_stats['favorites'],
                'unique_websites': db_stats['unique_websites'],
                'last_entry_date': db_stats['last_entry_date'],
                'recent_entries_30_days': len(recent_entries),
                'most_used_websites': sorted(website_counts.items(), key=lambda x: x[1], reverse=True)[:5],
                'most_used_usernames': sorted(username_counts.items(), key=lambda x: x[1], reverse=True)[:5],
                'duplicate_usernames': sum(1 for count in username_counts.values() if count > 1),
                'entries_per_website': {site: count for site, count in website_counts.items()}
            }
            
            logger.debug(f"Compiled statistics for user {session.username}")
            return statistics
            
        except (InvalidSessionError, SessionExpiredError):
            raise
        except Exception as e:
            logger.error(f"Failed to get password statistics: {e}")
            raise PasswordManagerError(f"Statistics retrieval failed: {e}")
    
    def change_master_password(self, session_id: str, current_password: str, 
                              new_password: str) -> bool:
        """
        Change master password and re-encrypt all password entries
        
        Args:
            session_id (str): Valid session token
            current_password (str): Current master password
            new_password (str): New master password
            
        Returns:
            bool: True if password change was successful
            
        Raises:
            InvalidSessionError: If session is invalid
            AuthenticationError: If current password is wrong or change fails
        """
        try:
            # Clear any cached master passwords first
            self._clear_master_password_cache(session_id)
            
            # Delegate to authentication manager (handles re-encryption)
            success = self.auth_manager.change_master_password(
                session_id, current_password, new_password
            )
            
            if success:
                logger.info("Master password changed successfully")
            
            return success
            
        except (InvalidSessionError, SessionExpiredError, AuthenticationError):
            raise
        except Exception as e:
            logger.error(f"Master password change failed: {e}")
            raise PasswordManagerError(f"Master password change failed: {e}")
    
    def _validate_password_entry_data(self, website: str, username: str, password: str):
        """
        Validate password entry input data
        
        Args:
            website (str): Website to validate
            username (str): Username to validate
            password (str): Password to validate
            
        Raises:
            InvalidPasswordEntryError: If any data is invalid
        """
        if not website or not website.strip():
            raise InvalidPasswordEntryError("Website cannot be empty")
        
        if not username or not username.strip():
            raise InvalidPasswordEntryError("Username cannot be empty")
        
        if not password:
            raise InvalidPasswordEntryError("Password cannot be empty")
        
        # Validate website format (basic check)
        if len(website.strip()) > 255:
            raise InvalidPasswordEntryError("Website name too long (max 255 characters)")
        
        # Validate username format
        if len(username.strip()) > 255:
            raise InvalidPasswordEntryError("Username too long (max 255 characters)")
        
        # Validate password length
        if len(password) > 1000:
            raise InvalidPasswordEntryError("Password too long (max 1000 characters)")
    
    def _check_duplicate_entry(self, user_id: int, website: str, username: str) -> bool:
        """
        Check if a password entry already exists for the same website/username combination
        
        Args:
            user_id (int): User ID to check for
            website (str): Website to check
            username (str): Username to check
            
        Returns:
            bool: True if duplicate exists, False otherwise
        """
        try:
            entries = self.auth_manager.db_manager.get_password_entries(user_id, website=website)
            
            for entry in entries:
                if (entry['website'].lower() == website.strip().lower() and 
                    entry['username'].lower() == username.strip().lower()):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking duplicate entry: {e}")
            return False
    
    def _verify_master_password(self, session_id: str, master_password: str) -> bool:
        """
        Verify master password by testing decryption of an existing entry
        
        Args:
            session_id (str): Session ID to get user context
            master_password (str): Master password to verify
            
        Returns:
            bool: True if master password is correct, False otherwise
        """
        try:
            # Get session to access user context
            session = self.auth_manager.validate_session(session_id)
            
            # Get any existing password entry to test decryption
            entries = self.auth_manager.db_manager.get_password_entries(session.user_id)
            
            if not entries:
                # No entries exist yet, so we can't verify the master password this way
                # We need to check against the user's account in a different way
                # For now, we'll attempt to authenticate the user again
                user_info = self.auth_manager.db_manager.authenticate_user(session.username, master_password)
                return user_info is not None
            
            # Try to decrypt the first password entry
            test_entry = entries[0]
            try:
                session.encryption_system.decrypt_password(
                    test_entry['password_encrypted'], master_password
                )
                return True
            except (DecryptionError, EncryptionError):
                return False
                
        except Exception as e:
            logger.error(f"Master password verification failed: {e}")
            return False
    
    def _cache_master_password(self, session_id: str, master_password: str):
        """
        Cache master password based on configured caching mode
        
        Args:
            session_id (str): Session ID for cache key
            master_password (str): Master password to cache
        """
        if self.cache_mode == PasswordCacheMode.NO_CACHE:
            return
        
        try:
            with self._cache_lock:
                # Store master password securely in memory for session duration
                # Note: This is stored in memory only and cleared when session ends
                cache_entry = {
                    'master_password': master_password,  # Store actual password for encryption operations
                    'password_hash': hashlib.sha256(master_password.encode('utf-8')).hexdigest(),  # Keep hash for verification
                    'cached_at': datetime.now(),
                    'session_id': session_id
                }
                
                if self.cache_mode == PasswordCacheMode.TEMPORARY:
                    cache_entry['expires_at'] = datetime.now() + timedelta(minutes=self.cache_timeout_minutes)
                elif self.cache_mode == PasswordCacheMode.SESSION:
                    # Cache until session expires (handled by session cleanup)
                    cache_entry['expires_at'] = datetime.now() + timedelta(hours=8)
                
                self._master_password_cache[session_id] = cache_entry
                
        except Exception as e:
            logger.error(f"Failed to cache master password: {e}")
    
    def _get_cached_master_password(self, session_id: str) -> Optional[str]:
        """
        Get cached master password if available and valid
        
        Args:
            session_id (str): Session ID to lookup
            
        Returns:
            Optional[str]: Cached master password or None
        """
        if self.cache_mode == PasswordCacheMode.NO_CACHE:
            return None
        
        try:
            with self._cache_lock:
                cache_entry = self._master_password_cache.get(session_id)
                
                if not cache_entry:
                    return None
                
                # Check expiration
                if 'expires_at' in cache_entry and datetime.now() > cache_entry['expires_at']:
                    # Remove expired entry
                    self._master_password_cache.pop(session_id, None)
                    return None
                
                # Return the cached master password (stored securely in memory)
                return cache_entry.get('master_password')
                
        except Exception as e:
            logger.error(f"Failed to get cached master password: {e}")
            return None
    
    def _clear_master_password_cache(self, session_id: str = None):
        """
        Clear master password cache for a session or all sessions
        
        Args:
            session_id (str, optional): Specific session to clear, or None for all
        """
        try:
            with self._cache_lock:
                if session_id:
                    cache_entry = self._master_password_cache.pop(session_id, None)
                    if cache_entry and 'master_password' in cache_entry:
                        # Securely clear the password from memory
                        cache_entry['master_password'] = '0' * len(cache_entry['master_password'])
                        del cache_entry['master_password']
                else:
                    # Clear all cached passwords securely
                    for entry in self._master_password_cache.values():
                        if 'master_password' in entry:
                            entry['master_password'] = '0' * len(entry['master_password'])
                            del entry['master_password']
                    self._master_password_cache.clear()
                    
        except Exception as e:
            logger.error(f"Failed to clear master password cache: {e}")
    
    def _sort_entries(self, entries: List[PasswordEntry], sort_by: str, sort_order: str) -> List[PasswordEntry]:
        """
        Sort password entries by specified criteria
        
        Args:
            entries (List[PasswordEntry]): Entries to sort
            sort_by (str): Field to sort by
            sort_order (str): "asc" or "desc"
            
        Returns:
            List[PasswordEntry]: Sorted entries
        """
        try:
            reverse = sort_order.lower() == "desc"
            
            if sort_by == "website":
                return sorted(entries, key=lambda e: e.website.lower(), reverse=reverse)
            elif sort_by == "username":
                return sorted(entries, key=lambda e: e.username.lower(), reverse=reverse)
            elif sort_by == "created_at":
                return sorted(entries, key=lambda e: e.created_at or datetime.min, reverse=reverse)
            elif sort_by == "modified_at":
                return sorted(entries, key=lambda e: e.modified_at or datetime.min, reverse=reverse)
            elif sort_by == "favorite":
                return sorted(entries, key=lambda e: (e.is_favorite, e.website.lower()), reverse=reverse)
            else:
                # Default to website sorting
                return sorted(entries, key=lambda e: e.website.lower(), reverse=reverse)
                
        except Exception as e:
            logger.error(f"Failed to sort entries: {e}")
            return entries
    
    def shutdown(self):
        """
        Shutdown the password manager and cleanup resources
        """
        try:
            # Clear password caches
            self._clear_master_password_cache()
            
            # Shutdown authentication manager
            self.auth_manager.shutdown()
            
            logger.info("Password manager core shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during password manager shutdown: {e}")

# Utility functions for external use

def create_password_manager(db_path: str = "data/password_manager.db",
                           cache_mode: PasswordCacheMode = PasswordCacheMode.TEMPORARY) -> PasswordManagerCore:
    """
    Factory function to create a password manager instance
    
    Args:
        db_path (str): Path to the database file
        cache_mode (PasswordCacheMode): Master password caching strategy
        
    Returns:
        PasswordManagerCore: Configured password manager
    """
    return PasswordManagerCore(db_path, cache_mode)

def validate_website_url(url: str) -> Dict[str, Any]:
    """
    Validate and normalize website URL for storage
    
    Args:
        url (str): Website URL to validate
        
    Returns:
        Dict[str, Any]: Validation results and normalized URL
    """
    if not url or not url.strip():
        return {
            'is_valid': False,
            'normalized_url': '',
            'issues': ['URL cannot be empty'],
            'suggestions': ['Enter a website URL']
        }
    
    url = url.strip()
    issues = []
    suggestions = []
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        if not url.startswith('www.') and '.' in url:
            url = 'https://' + url
        else:
            issues.append('Invalid URL format')
            suggestions.append('URLs should start with http:// or https://')
    
    # Basic URL validation
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    is_valid = bool(url_pattern.match(url))
    
    if not is_valid:
        issues.append('Invalid URL format')
        suggestions.append('Enter a valid website URL (e.g., https://example.com)')
    
    # Extract domain for display
    domain = url
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
    except:
        pass
    
    return {
        'is_valid': is_valid and len(issues) == 0,
        'normalized_url': url,
        'domain': domain,
        'issues': issues,
        'suggestions': suggestions
    }

if __name__ == "__main__":
    # Test code for password manager functionality
    print("Testing Personal Password Manager Core...")
    
    try:
        # Create password manager
        pm = PasswordManagerCore("test_pm.db", PasswordCacheMode.NO_CACHE)
        
        # Create test user
        user_id = pm.auth_manager.create_user_account("testuser", "testmaster123")
        print(f"✓ User created with ID: {user_id}")
        
        # Authenticate
        session_id = pm.auth_manager.authenticate_user("testuser", "testmaster123")
        print(f"✓ User authenticated, session: {session_id[:8]}...")
        
        # Add password entry
        entry_id = pm.add_password_entry(
            session_id=session_id,
            website="example.com",
            username="user@example.com",
            password="secretpassword123",
            master_password="testmaster123",
            remarks="Test password entry"
        )
        print(f"✓ Password entry added with ID: {entry_id}")
        
        # Search entries
        search_criteria = SearchCriteria(website="example")
        entries = pm.search_password_entries(
            session_id=session_id,
            criteria=search_criteria,
            master_password="testmaster123",
            include_passwords=True
        )
        print(f"✓ Found {len(entries)} matching entries")
        
        if entries:
            print(f"  Entry: {entries[0].website} - {entries[0].username}")
            print(f"  Password: {'*' * len(entries[0].password)}")  # Don't print actual password
        
        # Get statistics
        stats = pm.get_password_statistics(session_id)
        print(f"✓ Statistics: {stats['total_entries']} total entries")
        
        # Test URL validation
        url_validation = validate_website_url("example.com")
        print(f"✓ URL validation: {url_validation['normalized_url']}")
        
        # Cleanup
        pm.shutdown()
        
        print("✓ All password manager core tests passed!")
        
    except Exception as e:
        print(f"❌ Password manager core test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test database
        import os
        if os.path.exists("test_pm.db"):
            os.remove("test_pm.db")