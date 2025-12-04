#!/usr/bin/env python3
"""
Personal Password Manager - Database Layer
==========================================

This module handles all database operations for the password manager including:
- SQLite database creation and management
- User account management with secure authentication
- Password storage and retrieval with encryption support
- Database schema management and migrations
- Data validation and sanitization
- Connection pooling and error handling

The database uses two main tables:
1. users - Stores user accounts with hashed passwords and security settings
2. passwords - Stores encrypted passwords with associated metadata

Security Features:
- Bcrypt password hashing for user accounts
- Account lockout after failed login attempts
- Foreign key constraints for data integrity
- Prepared statements to prevent SQL injection
- Automatic database backup on schema changes

Author: Personal Password Manager
Version: 2.2.0
"""

import json
import os
import secrets
import sqlite3
import stat
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import bcrypt

from .error_handlers import audit_action, handle_db_errors

# Import new error handling system
from .exceptions import AccountLockedError as NewAccountLockedError
from .exceptions import (
    DatabaseConnectionError,
    DatabaseException,
    DatabaseIntegrityError,
    RecordNotFoundError,
)
from .logging_config import get_logger, log_exception, log_security_event

# Get module logger using new logging system
logger = get_logger(__name__)

# Backwards compatibility aliases for old exception names
DatabaseError = DatabaseException
UserNotFoundError = RecordNotFoundError
UserAlreadyExistsError = DatabaseIntegrityError
AccountLockedError = NewAccountLockedError


class DatabaseManager:
    """
    Main database manager class for the Personal Password Manager

    This class handles all database operations including user management,
    password storage, and database maintenance. It uses SQLite as the backend
    database with proper security measures and error handling.

    Attributes:
        db_path (Path): Path to the SQLite database file
        connection_timeout (int): Database connection timeout in seconds
        max_failed_attempts (int): Maximum failed login attempts before lockout
        lockout_duration (int): Account lockout duration in minutes
        _lock (threading.Lock): Thread lock for database operations
    """

    # Database schema version for migrations
    SCHEMA_VERSION = 3  # Updated for entry_name field in passwords table

    # Security settings
    MAX_FAILED_ATTEMPTS = 5  # Lock account after 5 failed attempts
    LOCKOUT_DURATION_MINUTES = 30  # Lock for 30 minutes

    def __init__(self, db_path: str = "data/password_manager.db"):
        """
        Initialize the database manager

        Args:
            db_path (str): Path to the SQLite database file

        Raises:
            DatabaseError: If database initialization fails
        """
        self.db_path = Path(db_path)
        self.connection_timeout = 30  # 30 seconds timeout
        self.max_failed_attempts = self.MAX_FAILED_ATTEMPTS
        self.lockout_duration = self.LOCKOUT_DURATION_MINUTES

        # Thread lock for database operations
        self._lock = threading.Lock()

        # Ensure the database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize migration manager
        self._migration_manager = None

        # Initialize database schema with migration support
        try:
            self._initialize_database_with_migrations()
            logger.info(f"Database initialized successfully at {self.db_path}")

            # Enforce strict file permissions for security
            self._enforce_file_permissions()
        except Exception as e:
            log_exception(logger, e, "Failed to initialize database")
            raise DatabaseConnectionError(
                f"Database initialization failed: {e}",
                error_code="DB001",
                user_message="Could not initialize the database. Please check file permissions.",
            )

    def _enforce_file_permissions(self) -> None:
        """
        Enforce strict file permissions on the database file for security

        On Unix/Linux/Mac systems, sets permissions to 600 (read/write for owner only).
        On Windows systems, sets ACL to restrict access to the current user only.

        This is a critical security measure to prevent unauthorized access to the
        encrypted password database file.

        Note: This method logs errors but does not raise exceptions to maintain
        backward compatibility and avoid breaking existing deployments.
        """
        if not self.db_path.exists():
            # Database file doesn't exist yet, will be created on first connection
            return

        try:
            if os.name == "posix":  # Unix/Linux/Mac
                # Set permissions to 600 (rw-------)
                # Only the file owner can read and write
                os.chmod(self.db_path, stat.S_IRUSR | stat.S_IWUSR)
                logger.info("Database file permissions set to 600 (owner read/write only)")

            elif os.name == "nt":  # Windows
                # Set Windows ACL to restrict access to current user only
                try:
                    import ntsecuritycon as con
                    import win32security

                    # Get current user SID
                    user, domain, type = win32security.LookupAccountName("", os.getlogin())

                    # Create a security descriptor
                    sd = win32security.SECURITY_DESCRIPTOR()

                    # Create a DACL (Discretionary Access Control List)
                    dacl = win32security.ACL()

                    # Add ACE (Access Control Entry) for current user with full control
                    dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_ALL_ACCESS, user)

                    # Set the DACL
                    sd.SetSecurityDescriptorDacl(1, dacl, 0)

                    # Apply the security descriptor to the file
                    win32security.SetFileSecurity(
                        str(self.db_path), win32security.DACL_SECURITY_INFORMATION, sd
                    )

                    logger.info("Database file permissions set to current user only (Windows ACL)")

                except ImportError:
                    # pywin32 not available, try alternative method using icacls
                    logger.warning(
                        "pywin32 not available, attempting to use icacls for file permissions"
                    )
                    try:
                        import subprocess

                        # Remove all existing permissions
                        subprocess.run(
                            ["icacls", str(self.db_path), "/inheritance:r"],
                            check=True,
                            capture_output=True,
                        )

                        # Grant full control to current user only
                        current_user = os.getlogin()
                        subprocess.run(
                            ["icacls", str(self.db_path), "/grant", f"{current_user}:F"],
                            check=True,
                            capture_output=True,
                        )

                        logger.info(
                            "Database file permissions set using icacls (current user full control)"
                        )

                    except (subprocess.CalledProcessError, FileNotFoundError) as e:
                        logger.warning(f"Could not set Windows file permissions using icacls: {e}")
                        logger.warning("Database file permissions may not be optimal on Windows")

            else:
                logger.warning(f"Unknown operating system '{os.name}', cannot set file permissions")

        except PermissionError as e:
            logger.warning(f"Permission denied when setting database file permissions: {e}")
            logger.warning("Database file permissions may not be optimal")
        except Exception as e:
            logger.warning(f"Unexpected error setting database file permissions: {e}")
            logger.warning("Database file permissions may not be optimal")

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections

        Provides a database connection with proper error handling and cleanup.
        Uses a thread lock to ensure thread-safe operations.

        Yields:
            sqlite3.Connection: Database connection object

        Raises:
            DatabaseError: If connection fails
        """
        connection = None
        try:
            with self._lock:
                # Create connection with timeout and row factory
                connection = sqlite3.connect(
                    str(self.db_path), timeout=self.connection_timeout, check_same_thread=False
                )

                # Set row factory for dictionary-like access
                connection.row_factory = sqlite3.Row

                # Enable foreign key constraints
                connection.execute("PRAGMA foreign_keys = ON")

                # Enable WAL mode for better concurrency
                connection.execute("PRAGMA journal_mode = WAL")

                yield connection

        except sqlite3.Error as e:
            log_exception(logger, e, "Database connection error")
            if connection:
                connection.rollback()
            raise DatabaseConnectionError(
                f"Database connection failed: {e}",
                error_code="DB001",
                user_message="Could not connect to the database. Please try again.",
            )

        finally:
            if connection:
                connection.close()

    def _initialize_database_with_migrations(self):
        """
        Initialize database with migration support

        This method handles database initialization and applies any necessary
        migrations to bring the schema up to the current version. It includes
        automatic backup creation and safe migration handling.

        Raises:
            DatabaseError: If initialization or migration fails
        """
        try:
            # First, ensure basic schema exists (original tables)
            self._initialize_database()

            # Initialize migration manager (lazy loading to avoid circular import)
            if self._migration_manager is None:
                from .database_migrations import DatabaseMigrationManager

                self._migration_manager = DatabaseMigrationManager(str(self.db_path))

            # Check if migrations are needed
            if self._migration_manager.needs_migration():
                logger.info("Database migrations required, applying automatically...")

                # Apply migrations with automatic backup
                migration_success = self._migration_manager.apply_migrations()

                if not migration_success:
                    raise DatabaseException(
                        "Database migration failed - see logs for details",
                        error_code="DB003",
                        user_message="Database migration failed. Please restore from backup.",
                    )

                logger.info("Database migrations completed successfully")

                # Clean up old backups (keep last 30 days)
                self._migration_manager.cleanup_old_backups(keep_days=30)
            else:
                logger.info("Database schema is up to date")

        except Exception as e:
            log_exception(logger, e, "Database initialization with migrations failed")
            raise DatabaseException(
                f"Failed to initialize database with migrations: {e}",
                error_code="DB001",
                user_message="Could not initialize database. Please check permissions and disk space.",
            )

    def _initialize_database(self):
        """
        Initialize the database schema and create tables if they don't exist

        Creates the users and passwords tables with proper constraints and indexes.
        Also handles database migrations if schema version changes.

        Raises:
            DatabaseError: If schema creation fails
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Create users table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        salt TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP NULL,
                        failed_attempts INTEGER DEFAULT 0,
                        locked_until TIMESTAMP NULL,
                        is_active BOOLEAN DEFAULT 1
                    )
                """
                )

                # Create passwords table with foreign key constraint
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS passwords (
                        entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        entry_name TEXT DEFAULT NULL,
                        website TEXT NOT NULL,
                        username TEXT NOT NULL,
                        password_encrypted BLOB NOT NULL,
                        remarks TEXT DEFAULT '',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_favorite BOOLEAN DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                    )
                """
                )

                # Create indexes for better performance
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_passwords_user_website
                    ON passwords (user_id, website)
                """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_passwords_user_id
                    ON passwords (user_id)
                """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_users_username
                    ON users (username)
                """
                )

                # Create metadata table for schema versioning
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS database_metadata (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Set schema version
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO database_metadata (key, value, updated_at)
                    VALUES ('schema_version', ?, CURRENT_TIMESTAMP)
                """,
                    (str(self.SCHEMA_VERSION),),
                )

                # Create triggers for automatic timestamp updates
                cursor.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS update_password_modified_time
                    AFTER UPDATE ON passwords
                    BEGIN
                        UPDATE passwords SET modified_at = CURRENT_TIMESTAMP
                        WHERE entry_id = NEW.entry_id;
                    END
                """
                )

                conn.commit()
                logger.info("Database schema initialized successfully")

        except sqlite3.Error as e:
            log_exception(logger, e, "Schema initialization failed")
            raise DatabaseException(
                f"Failed to initialize database schema: {e}",
                error_code="DB001",
                user_message="Could not create database tables. Please check file permissions.",
            )

    @handle_db_errors("Failed to create user")
    @audit_action("CREATE_USER", lambda args, kwargs: None)  # No user_id yet
    def create_user(self, username: str, password: str) -> int:
        """
        Create a new user account with secure password hashing

        Args:
            username (str): Unique username for the account
            password (str): Plain text password to be hashed

        Returns:
            int: User ID of the created user

        Raises:
            UserAlreadyExistsError: If username already exists
            DatabaseError: If user creation fails
            ValueError: If username or password is invalid
        """
        # Validate input parameters
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")

        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        username = username.strip().lower()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Check if user already exists
                cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
                if cursor.fetchone():
                    raise DatabaseIntegrityError(
                        f"User '{username}' already exists", constraint="unique_username"
                    )

                # Generate salt and hash password
                salt = secrets.token_hex(32)  # 32 bytes = 64 hex characters
                password_hash = self._hash_password(password, salt)

                # Insert new user
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, salt, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (username, password_hash, salt),
                )

                user_id = cursor.lastrowid
                conn.commit()

                logger.info(f"User '{username}' created successfully with ID {user_id}")
                return user_id

        except DatabaseIntegrityError:
            raise
        except Exception as e:
            log_exception(logger, e, f"Failed to create user '{username}'")
            raise DatabaseException(
                f"User creation failed: {e}",
                error_code="DB001",
                user_message="Could not create user account. Please try again.",
            )

    def user_exists(self, username: str) -> bool:
        """
        Check if a user exists in the database

        Args:
            username (str): Username to check

        Returns:
            bool: True if user exists, False otherwise
        """
        if not username or not username.strip():
            return False

        username = username.strip().lower()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking if user exists '{username}': {e}")
            return False

    @handle_db_errors("Authentication failed")
    @audit_action("AUTHENTICATE_USER", lambda args, kwargs: None)  # Logged separately by security
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user with username and password

        This method handles account lockout after failed attempts and updates
        login timestamps on successful authentication.

        Args:
            username (str): Username to authenticate
            password (str): Plain text password to verify

        Returns:
            Optional[Dict[str, Any]]: User information if authentication succeeds, None otherwise

        Raises:
            AccountLockedError: If account is locked due to failed attempts
            DatabaseError: If authentication process fails
        """
        if not username or not password:
            return None

        username = username.strip().lower()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Get user information
                cursor.execute(
                    """
                    SELECT user_id, username, password_hash, salt, failed_attempts,
                           locked_until, is_active
                    FROM users
                    WHERE username = ?
                """,
                    (username,),
                )

                user_row = cursor.fetchone()
                if not user_row:
                    logger.warning(f"Authentication failed: User '{username}' not found")
                    return None

                user = dict(user_row)

                # Check if account is active
                if not user["is_active"]:
                    logger.warning(f"Authentication failed: Account '{username}' is deactivated")
                    return None

                # Check if account is locked
                if user["locked_until"]:
                    locked_until = datetime.fromisoformat(user["locked_until"])
                    if datetime.now() < locked_until:
                        remaining_time = locked_until - datetime.now()
                        raise NewAccountLockedError(
                            f"Account locked for {
                                remaining_time.seconds //
                                60} more minutes",
                            error_code="SEC005",
                            user_message=f"Your account is locked for {
                                remaining_time.seconds //
                                60} more minutes due to failed login attempts.",
                            lockout_duration=remaining_time.seconds //
                            60,
                        )
                    else:
                        # Unlock account if lockout period has passed
                        cursor.execute(
                            """
                            UPDATE users
                            SET locked_until = NULL, failed_attempts = 0
                            WHERE user_id = ?
                        """,
                            (user["user_id"],),
                        )

                # Verify password
                if self._verify_password(password, user["password_hash"], user["salt"]):
                    # Successful authentication - reset failed attempts and update last login
                    cursor.execute(
                        """
                        UPDATE users
                        SET failed_attempts = 0, locked_until = NULL, last_login = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """,
                        (user["user_id"],),
                    )

                    conn.commit()

                    logger.info(f"User '{username}' authenticated successfully")

                    # Return user information (without sensitive data)
                    return {
                        "user_id": user["user_id"],
                        "username": user["username"],
                        "last_login": user.get("last_login"),
                        "created_at": user.get("created_at"),
                    }

                else:
                    # Failed authentication - increment failed attempts
                    failed_attempts = user["failed_attempts"] + 1

                    if failed_attempts >= self.max_failed_attempts:
                        # Lock account
                        locked_until = datetime.now() + timedelta(minutes=self.lockout_duration)
                        cursor.execute(
                            """
                            UPDATE users
                            SET failed_attempts = ?, locked_until = ?
                            WHERE user_id = ?
                        """,
                            (failed_attempts, locked_until.isoformat(), user["user_id"]),
                        )

                        logger.warning(
                            f"Account '{username}' locked after {failed_attempts} failed attempts"
                        )

                    else:
                        cursor.execute(
                            """
                            UPDATE users
                            SET failed_attempts = ?
                            WHERE user_id = ?
                        """,
                            (failed_attempts, user["user_id"]),
                        )

                        logger.warning(
                            f"Authentication failed for '{username}' ({failed_attempts}/{self.max_failed_attempts} attempts)"
                        )

                    conn.commit()
                    return None

        except NewAccountLockedError:
            raise
        except Exception as e:
            log_exception(logger, e, f"Authentication error for user '{username}'")
            raise DatabaseException(
                f"Authentication failed: {e}",
                error_code="DB001",
                user_message="Authentication error. Please try again.",
            )

    @handle_db_errors("Failed to add password entry")
    @audit_action(
        "ADD_PASSWORD", lambda args, kwargs: args[1] if len(args) > 1 else kwargs.get("user_id")
    )
    def add_password_entry(
        self,
        user_id: int,
        website: str,
        username: str,
        encrypted_password: bytes,
        remarks: str = "",
        entry_name: str = None,
    ) -> int:
        """
        Add a new password entry for a user

        Args:
            user_id (int): ID of the user owning this password
            website (str): Website or service name
            username (str): Username for the service
            encrypted_password (bytes): AES-256 encrypted password
            remarks (str): Optional remarks/notes
            entry_name (str): Optional custom name/label for the entry

        Returns:
            int: Entry ID of the created password entry

        Raises:
            DatabaseError: If entry creation fails
            ValueError: If required parameters are invalid
        """
        # Validate input parameters
        if not website or not website.strip():
            raise ValueError("Website cannot be empty")

        if not username or not username.strip():
            raise ValueError("Username cannot be empty")

        if not encrypted_password:
            raise ValueError("Encrypted password cannot be empty")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Verify user exists
                cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
                if not cursor.fetchone():
                    raise ValueError(f"User ID {user_id} does not exist")

                # Prepare entry_name (strip if provided, otherwise NULL)
                prepared_entry_name = (
                    entry_name.strip() if entry_name and entry_name.strip() else None
                )

                # Insert password entry
                cursor.execute(
                    """
                    INSERT INTO passwords (user_id, entry_name, website, username, password_encrypted, remarks)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        user_id,
                        prepared_entry_name,
                        website.strip(),
                        username.strip(),
                        encrypted_password,
                        remarks.strip(),
                    ),
                )

                entry_id = cursor.lastrowid
                conn.commit()

                logger.info(
                    f"Password entry created for user {user_id}, website '{website}', entry ID {entry_id}")
                return entry_id

        except ValueError:
            raise
        except Exception as e:
            log_exception(logger, e, "Failed to add password entry")
            raise DatabaseException(
                f"Password entry creation failed: {e}",
                error_code="DB001",
                user_message="Could not save password entry. Please try again.",
            )

    @handle_db_errors("Failed to retrieve password entries")
    def get_password_entries(self, user_id: int, website: str = None) -> List[Dict[str, Any]]:
        """
        Retrieve password entries for a user, optionally filtered by website

        Args:
            user_id (int): ID of the user
            website (str, optional): Filter by website name (case-insensitive)

        Returns:
            List[Dict[str, Any]]: List of password entries

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                if website:
                    # Search for specific website or entry name (case-insensitive partial match)
                    cursor.execute(
                        """
                        SELECT entry_id, entry_name, website, username, password_encrypted, remarks,
                               created_at, modified_at, is_favorite
                        FROM passwords
                        WHERE user_id = ? AND (
                            LOWER(website) LIKE LOWER(?) OR
                            LOWER(entry_name) LIKE LOWER(?)
                        )
                        ORDER BY website, username
                    """,
                        (user_id, f"%{website.strip()}%", f"%{website.strip()}%"),
                    )
                else:
                    # Get all entries for user
                    cursor.execute(
                        """
                        SELECT entry_id, entry_name, website, username, password_encrypted, remarks,
                               created_at, modified_at, is_favorite
                        FROM passwords
                        WHERE user_id = ?
                        ORDER BY website, username
                    """,
                        (user_id,),
                    )

                entries = []
                for row in cursor.fetchall():
                    entry = dict(row)
                    entries.append(entry)

                logger.info(f"Retrieved {len(entries)} password entries for user {user_id}")
                return entries

        except Exception as e:
            log_exception(logger, e, "Failed to retrieve password entries")
            raise DatabaseException(
                f"Password entry retrieval failed: {e}",
                error_code="DB001",
                user_message="Could not load password entries. Please try again.",
            )

    def get_password_entries_advanced(
        self,
        user_id: int,
        website: str = None,
        username: str = None,
        remarks: str = None,
        is_favorite: bool = None,
        date_from: str = None,
        date_to: str = None,
        limit: int = None,
        offset: int = 0,
        order_by: str = "website",
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieve password entries with advanced SQL-based filtering and pagination

        This method performs all filtering at the database level for optimal performance,
        eliminating the N+1 query problem and reducing memory usage with large datasets.

        Args:
            user_id (int): ID of the user
            website (str, optional): Filter by website (case-insensitive partial match)
            username (str, optional): Filter by username (case-insensitive partial match)
            remarks (str, optional): Filter by remarks (case-insensitive partial match)
            is_favorite (bool, optional): Filter by favorite status
            date_from (str, optional): Filter by created date (ISO format: YYYY-MM-DD)
            date_to (str, optional): Filter by created date (ISO format: YYYY-MM-DD)
            limit (int, optional): Maximum number of entries to return (for pagination)
            offset (int): Number of entries to skip (for pagination)
            order_by (str): Column to sort by (default: "website")

        Returns:
            Tuple[List[Dict[str, Any]], int]: (List of password entries, Total count)

        Raises:
            DatabaseError: If retrieval fails
            ValueError: If parameters are invalid

        Example:
            # Get first page (100 entries) of passwords for google.com
            entries, total = db.get_password_entries_advanced(
                user_id=1,
                website="google.com",
                limit=100,
                offset=0
            )
        """
        # Validate order_by to prevent SQL injection
        valid_order_columns = ["website", "username", "created_at", "modified_at", "entry_name"]
        if order_by not in valid_order_columns:
            logger.warning(f"Invalid order_by column '{order_by}', defaulting to 'website'")
            order_by = "website"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Build WHERE clause dynamically based on provided filters
                where_conditions = ["user_id = ?"]
                query_params = [user_id]

                if website:
                    where_conditions.append(
                        "(LOWER(website) LIKE LOWER(?) OR LOWER(entry_name) LIKE LOWER(?))"
                    )
                    website_pattern = f"%{website.strip()}%"
                    query_params.extend([website_pattern, website_pattern])

                if username:
                    where_conditions.append("LOWER(username) LIKE LOWER(?)")
                    query_params.append(f"%{username.strip()}%")

                if remarks:
                    where_conditions.append("LOWER(remarks) LIKE LOWER(?)")
                    query_params.append(f"%{remarks.strip()}%")

                if is_favorite is not None:
                    where_conditions.append("is_favorite = ?")
                    query_params.append(1 if is_favorite else 0)

                if date_from:
                    where_conditions.append("created_at >= ?")
                    query_params.append(date_from)

                if date_to:
                    where_conditions.append("created_at <= ?")
                    query_params.append(date_to)

                where_clause = " AND ".join(where_conditions)

                # First, get total count (for pagination info)
                count_query = f"SELECT COUNT(*) as total FROM passwords WHERE {where_clause}"
                cursor.execute(count_query, query_params)
                total_count = cursor.fetchone()["total"]

                # Build main query with optional pagination
                main_query = """
                    SELECT entry_id, entry_name, website, username, password_encrypted, remarks,
                           created_at, modified_at, is_favorite
                    FROM passwords
                    WHERE {where_clause}
                    ORDER BY {order_by}, username
                """

                # Add pagination if limit is specified
                if limit is not None and limit > 0:
                    main_query += " LIMIT ? OFFSET ?"
                    query_params.extend([limit, offset])

                cursor.execute(main_query, query_params)

                entries = []
                for row in cursor.fetchall():
                    entry = dict(row)
                    entries.append(entry)

                logger.info(
                    f"Retrieved {len(entries)} of {total_count} password entries for user {user_id} "
                    f"(filters: website={website}, username={username}, favorites={is_favorite}, "
                    f"limit={limit}, offset={offset})"
                )

                return entries, total_count

        except sqlite3.Error as e:
            log_exception(logger, e, "Database error in advanced search")
            raise DatabaseException(
                f"Advanced search failed: {e}",
                error_code="DB001",
                user_message="Search failed. Please try again.",
            )
        except Exception as e:
            log_exception(logger, e, "Failed to retrieve password entries")
            raise DatabaseException(
                f"Password entry retrieval failed: {e}",
                error_code="DB001",
                user_message="Could not load password entries. Please try again.",
            )

    @handle_db_errors("Failed to update password entry")
    @audit_action(
        "UPDATE_PASSWORD", lambda args, kwargs: args[2] if len(args) > 2 else kwargs.get("user_id")
    )
    def update_password_entry(
        self,
        entry_id: int,
        user_id: int,
        website: str = None,
        username: str = None,
        encrypted_password: bytes = None,
        remarks: str = None,
        is_favorite: bool = None,
        entry_name: str = None,
    ) -> bool:
        """
        Update an existing password entry

        Args:
            entry_id (int): ID of the entry to update
            user_id (int): ID of the user (for security verification)
            website (str, optional): New website name
            username (str, optional): New username
            encrypted_password (bytes, optional): New encrypted password
            remarks (str, optional): New remarks
            is_favorite (bool, optional): Favorite status
            entry_name (str, optional): New custom name/label

        Returns:
            bool: True if update was successful, False if entry not found

        Raises:
            DatabaseError: If update fails
            ValueError: If user doesn't own the entry
        """
        if not any(
            [
                website,
                username,
                encrypted_password,
                remarks is not None,
                is_favorite is not None,
                entry_name is not None,
            ]
        ):
            return True  # No updates requested

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Verify entry exists and belongs to user
                cursor.execute(
                    """
                    SELECT user_id FROM passwords WHERE entry_id = ?
                """,
                    (entry_id,),
                )

                result = cursor.fetchone()
                if not result:
                    return False

                if result["user_id"] != user_id:
                    raise ValueError("User does not own this password entry")

                # Build dynamic update query
                update_fields = []
                update_values = []

                if entry_name is not None:
                    update_fields.append("entry_name = ?")
                    # Allow empty string to clear the name, otherwise strip
                    prepared_name = entry_name.strip() if entry_name.strip() else None
                    update_values.append(prepared_name)

                if website is not None:
                    update_fields.append("website = ?")
                    update_values.append(website.strip())

                if username is not None:
                    update_fields.append("username = ?")
                    update_values.append(username.strip())

                if encrypted_password is not None:
                    update_fields.append("password_encrypted = ?")
                    update_values.append(encrypted_password)

                if remarks is not None:
                    update_fields.append("remarks = ?")
                    update_values.append(remarks.strip())

                if is_favorite is not None:
                    update_fields.append("is_favorite = ?")
                    update_values.append(is_favorite)

                # Add entry_id to values for WHERE clause
                update_values.append(entry_id)

                # Execute update
                cursor.execute(
                    """
                    UPDATE passwords
                    SET {', '.join(update_fields)}
                    WHERE entry_id = ?
                """,
                    update_values,
                )

                conn.commit()

                logger.info(f"Password entry {entry_id} updated successfully")
                return True

        except ValueError:
            raise
        except Exception as e:
            log_exception(logger, e, f"Failed to update password entry {entry_id}")
            raise DatabaseException(
                f"Password entry update failed: {e}",
                error_code="DB001",
                user_message="Could not update password entry. Please try again.",
            )

    @handle_db_errors("Failed to delete password entry")
    @audit_action(
        "DELETE_PASSWORD", lambda args, kwargs: args[2] if len(args) > 2 else kwargs.get("user_id")
    )
    def delete_password_entry(self, entry_id: int, user_id: int) -> bool:
        """
        Delete a password entry

        Args:
            entry_id (int): ID of the entry to delete
            user_id (int): ID of the user (for security verification)

        Returns:
            bool: True if deletion was successful, False if entry not found

        Raises:
            DatabaseError: If deletion fails
            ValueError: If user doesn't own the entry
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Verify entry exists and belongs to user
                cursor.execute(
                    """
                    SELECT user_id FROM passwords WHERE entry_id = ?
                """,
                    (entry_id,),
                )

                result = cursor.fetchone()
                if not result:
                    return False

                if result["user_id"] != user_id:
                    raise ValueError("User does not own this password entry")

                # Delete entry
                cursor.execute("DELETE FROM passwords WHERE entry_id = ?", (entry_id,))
                conn.commit()

                logger.info(f"Password entry {entry_id} deleted successfully")
                return True

        except ValueError:
            raise
        except Exception as e:
            log_exception(logger, e, f"Failed to delete password entry {entry_id}")
            raise DatabaseException(
                f"Password entry deletion failed: {e}",
                error_code="DB001",
                user_message="Could not delete password entry. Please try again.",
            )

    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Get statistics about a user's password entries

        Args:
            user_id (int): ID of the user

        Returns:
            Dict[str, Any]: Statistics including total entries, favorites count, etc.

        Raises:
            DatabaseError: If statistics retrieval fails
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Get total entries count
                cursor.execute(
                    """
                    SELECT COUNT(*) as total_entries FROM passwords WHERE user_id = ?
                """,
                    (user_id,),
                )
                total_entries = cursor.fetchone()["total_entries"]

                # Get favorites count
                cursor.execute(
                    """
                    SELECT COUNT(*) as favorites FROM passwords
                    WHERE user_id = ? AND is_favorite = 1
                """,
                    (user_id,),
                )
                favorites = cursor.fetchone()["favorites"]

                # Get unique websites count
                cursor.execute(
                    """
                    SELECT COUNT(DISTINCT website) as unique_websites FROM passwords
                    WHERE user_id = ?
                """,
                    (user_id,),
                )
                unique_websites = cursor.fetchone()["unique_websites"]

                # Get most recent entry date
                cursor.execute(
                    """
                    SELECT MAX(created_at) as last_entry_date FROM passwords
                    WHERE user_id = ?
                """,
                    (user_id,),
                )
                last_entry_date = cursor.fetchone()["last_entry_date"]

                return {
                    "total_entries": total_entries,
                    "favorites": favorites,
                    "unique_websites": unique_websites,
                    "last_entry_date": last_entry_date,
                }

        except Exception as e:
            log_exception(logger, e, "Failed to get user statistics")
            raise DatabaseException(
                f"Statistics retrieval failed: {e}",
                error_code="DB001",
                user_message="Could not load statistics. Please try again.",
            )

    # ========================================================================
    # Two-Factor Authentication (2FA) Methods
    # ========================================================================

    @handle_db_errors("Failed to enable 2FA")
    @audit_action("ENABLE_2FA", lambda args, kwargs: args[1])
    def enable_2fa(self, user_id: int, totp_secret: str, backup_codes: str) -> bool:
        """
        Enable two-factor authentication for a user

        Args:
            user_id: User ID to enable 2FA for
            totp_secret: Encrypted TOTP secret key
            backup_codes: JSON string of hashed backup codes

        Returns:
            bool: True if 2FA enabled successfully

        Raises:
            DatabaseException: If enabling 2FA fails
        """
        with self._lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE users
                    SET totp_secret = ?,
                        totp_enabled = 1,
                        backup_codes = ?
                    WHERE user_id = ?
                """,
                    (totp_secret, backup_codes, user_id),
                )

                conn.commit()

                if cursor.rowcount == 0:
                    raise RecordNotFoundError(
                        f"User with ID {user_id} not found", record_type="User", record_id=user_id
                    )

                logger.info(f"2FA enabled for user ID: {user_id}")
                log_security_event(
                    "2FA_ENABLED",
                    f"Two-factor authentication enabled for user {user_id}",
                    severity="INFO",
                    user_id=user_id,
                )
                return True

    @handle_db_errors("Failed to disable 2FA")
    @audit_action("DISABLE_2FA", lambda args, kwargs: args[1])
    def disable_2fa(self, user_id: int) -> bool:
        """
        Disable two-factor authentication for a user

        Args:
            user_id: User ID to disable 2FA for

        Returns:
            bool: True if 2FA disabled successfully

        Raises:
            DatabaseException: If disabling 2FA fails
        """
        with self._lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE users
                    SET totp_secret = NULL,
                        totp_enabled = 0,
                        backup_codes = NULL
                    WHERE user_id = ?
                """,
                    (user_id,),
                )

                conn.commit()

                if cursor.rowcount == 0:
                    raise RecordNotFoundError(
                        f"User with ID {user_id} not found", record_type="User", record_id=user_id
                    )

                logger.info(f"2FA disabled for user ID: {user_id}")
                log_security_event(
                    "2FA_DISABLED",
                    f"Two-factor authentication disabled for user {user_id}",
                    severity="WARNING",
                    user_id=user_id,
                )
                return True

    @handle_db_errors("Failed to get 2FA status")
    def get_2fa_status(self, user_id: int) -> Dict[str, Any]:
        """
        Get 2FA status for a user

        Args:
            user_id: User ID to check

        Returns:
            Dict with keys:
                - enabled (bool): Whether 2FA is enabled
                - has_backup_codes (bool): Whether backup codes exist
                - backup_codes_count (int): Number of remaining backup codes

        Raises:
            DatabaseException: If query fails
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT totp_enabled, totp_secret, backup_codes
                FROM users
                WHERE user_id = ?
            """,
                (user_id,),
            )

            row = cursor.fetchone()

            if not row:
                raise RecordNotFoundError(
                    f"User with ID {user_id} not found", record_type="User", record_id=user_id
                )

            # Count backup codes if they exist
            backup_codes_count = 0
            if row["backup_codes"]:
                try:
                    import json

                    codes = json.loads(row["backup_codes"])
                    backup_codes_count = len(codes)
                except Exception:
                    pass

            return {
                "enabled": bool(row["totp_enabled"]),
                "has_secret": bool(row["totp_secret"]),
                "has_backup_codes": bool(row["backup_codes"]),
                "backup_codes_count": backup_codes_count,
            }

    @handle_db_errors("Failed to get TOTP secret")
    def get_totp_secret(self, user_id: int) -> Optional[str]:
        """
        Get the TOTP secret for a user

        Args:
            user_id: User ID

        Returns:
            str: TOTP secret or None if 2FA not enabled

        Raises:
            DatabaseException: If query fails
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT totp_secret
                FROM users
                WHERE user_id = ?
            """,
                (user_id,),
            )

            row = cursor.fetchone()

            if not row:
                raise RecordNotFoundError(
                    f"User with ID {user_id} not found", record_type="User", record_id=user_id
                )

            return row["totp_secret"]

    @handle_db_errors("Failed to get backup codes")
    def get_backup_codes(self, user_id: int) -> Optional[str]:
        """
        Get the backup codes for a user

        Args:
            user_id: User ID

        Returns:
            str: JSON string of backup codes or None if not set

        Raises:
            DatabaseException: If query fails
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT backup_codes
                FROM users
                WHERE user_id = ?
            """,
                (user_id,),
            )

            row = cursor.fetchone()

            if not row:
                raise RecordNotFoundError(
                    f"User with ID {user_id} not found", record_type="User", record_id=user_id
                )

            return row["backup_codes"]

    @handle_db_errors("Failed to update backup codes")
    @audit_action("UPDATE_BACKUP_CODES", lambda args, kwargs: args[1])
    def update_backup_codes(self, user_id: int, backup_codes: str) -> bool:
        """
        Update backup codes for a user (after one is used)

        Args:
            user_id: User ID
            backup_codes: JSON string of remaining backup codes

        Returns:
            bool: True if updated successfully

        Raises:
            DatabaseException: If update fails
        """
        with self._lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE users
                    SET backup_codes = ?
                    WHERE user_id = ?
                """,
                    (backup_codes, user_id),
                )

                conn.commit()

                if cursor.rowcount == 0:
                    raise RecordNotFoundError(
                        f"User with ID {user_id} not found", record_type="User", record_id=user_id
                    )

                logger.info(f"Backup codes updated for user ID: {user_id}")
                return True

    def backup_database(self, backup_path: str = None) -> str:
        """
        Create a backup of the database

        Args:
            backup_path (str, optional): Custom backup file path

        Returns:
            str: Path to the created backup file

        Raises:
            DatabaseError: If backup creation fails
        """
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backups/password_manager_backup_{timestamp}.db"

            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # Use SQLite backup API for consistent backup
            with self.get_connection() as conn:
                backup_conn = sqlite3.connect(str(backup_path))
                conn.backup(backup_conn)
                backup_conn.close()

            logger.info(f"Database backup created at {backup_path}")
            return str(backup_path)

        except Exception as e:
            log_exception(logger, e, "Database backup failed")
            raise DatabaseException(
                f"Backup creation failed: {e}",
                error_code="DB001",
                user_message="Could not create database backup. Please check disk space.",
            )

    def _hash_password(self, password: str, salt: str) -> str:
        """
        Hash a password using bcrypt with additional salt

        Args:
            password (str): Plain text password
            salt (str): Additional salt for extra security

        Returns:
            str: Hashed password
        """
        # Combine password with salt and hash it first to avoid bcrypt 72-byte limit
        import hashlib

        salted_password = password + salt
        # Pre-hash with SHA-256 to ensure length is within bcrypt's limits
        prehashed = hashlib.sha256(salted_password.encode("utf-8")).hexdigest()

        # Use bcrypt for hashing (it includes its own salt)
        password_bytes = prehashed.encode("utf-8")
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12))

        return hashed.decode("utf-8")

    def _verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """
        Verify a password against its hash

        Args:
            password (str): Plain text password to verify
            password_hash (str): Stored password hash
            salt (str): Additional salt used during hashing

        Returns:
            bool: True if password matches, False otherwise
        """
        try:
            # Combine password with salt and pre-hash (same as during hashing)
            import hashlib

            salted_password = password + salt
            prehashed = hashlib.sha256(salted_password.encode("utf-8")).hexdigest()

            password_bytes = prehashed.encode("utf-8")
            hash_bytes = password_hash.encode("utf-8")

            return bcrypt.checkpw(password_bytes, hash_bytes)

        except Exception:
            return False

    # ==========================================
    # USER SETTINGS METHODS (New in Version 2)
    # ==========================================

    def get_user_setting(self, user_id: int, category: str, key: str) -> Optional[str]:
        """
        Get a specific user setting value

        Args:
            user_id (int): User ID to get setting for
            category (str): Setting category (e.g., 'password_viewing')
            key (str): Setting key (e.g., 'view_timeout_minutes')

        Returns:
            Optional[str]: Setting value or None if not found
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT setting_value FROM user_settings
                    WHERE user_id = ? AND setting_category = ? AND setting_key = ?
                """,
                    (user_id, category, key),
                )

                result = cursor.fetchone()
                return result["setting_value"] if result else None

        except sqlite3.Error as e:
            logger.error(f"Failed to get user setting: {e}")
            return None

    def set_user_setting(self, user_id: int, category: str, key: str, value: str) -> bool:
        """
        Set a user setting value

        Args:
            user_id (int): User ID to set setting for
            category (str): Setting category
            key (str): Setting key
            value (str): Setting value (stored as string, can be JSON)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO user_settings
                    (user_id, setting_category, setting_key, setting_value, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (user_id, category, key, value),
                )

                conn.commit()
                logger.debug(f"User setting saved: {category}.{key} for user {user_id}")
                return True

        except sqlite3.Error as e:
            logger.error(f"Failed to set user setting: {e}")
            return False

    def get_all_user_settings(self, user_id: int) -> Dict[str, Dict[str, str]]:
        """
        Get all settings for a user organized by category

        Args:
            user_id (int): User ID to get settings for

        Returns:
            Dict[str, Dict[str, str]]: Settings organized by category and key
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT setting_category, setting_key, setting_value
                    FROM user_settings
                    WHERE user_id = ?
                    ORDER BY setting_category, setting_key
                """,
                    (user_id,),
                )

                settings = {}
                for row in cursor.fetchall():
                    category = row["setting_category"]
                    key = row["setting_key"]
                    value = row["setting_value"]

                    if category not in settings:
                        settings[category] = {}

                    settings[category][key] = value

                return settings

        except sqlite3.Error as e:
            logger.error(f"Failed to get all user settings: {e}")
            return {}

    def delete_user_setting(self, user_id: int, category: str, key: str) -> bool:
        """
        Delete a specific user setting

        Args:
            user_id (int): User ID
            category (str): Setting category
            key (str): Setting key

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    DELETE FROM user_settings
                    WHERE user_id = ? AND setting_category = ? AND setting_key = ?
                """,
                    (user_id, category, key),
                )

                conn.commit()
                return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Failed to delete user setting: {e}")
            return False

    # ==========================================
    # SECURITY AUDIT LOG METHODS (New in Version 2)
    # ==========================================

    def log_security_event(
        self,
        user_id: int,
        session_id: str,
        action_type: str,
        action_result: str = "SUCCESS",
        target_entry_id: Optional[int] = None,
        error_message: Optional[str] = None,
        action_details: Optional[Dict] = None,
        security_level: str = "MEDIUM",
        risk_score: int = 0,
        execution_time_ms: int = 0,
    ) -> bool:
        """
        Log a security event to the audit log

        Args:
            user_id (int): User who performed the action
            session_id (str): Session ID
            action_type (str): Type of action (e.g., 'VIEW_PASSWORD', 'DELETE_PASSWORD')
            action_result (str): Result of action ('SUCCESS', 'FAILURE', 'PARTIAL')
            target_entry_id (int, optional): Password entry ID if applicable
            error_message (str, optional): Error details if action failed
            action_details (Dict, optional): Additional action details
            security_level (str): Security level ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
            risk_score (int): Risk assessment score (0-100)
            execution_time_ms (int): How long the action took in milliseconds

        Returns:
            bool: True if logged successfully, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Convert action_details dict to JSON string
                details_json = json.dumps(action_details) if action_details else None

                cursor.execute(
                    """
                    INSERT INTO security_audit_log
                    (user_id, session_id, action_type, action_result, target_entry_id,
                     error_message, action_details, security_level, risk_score,
                     execution_time_ms, client_version)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '2.2.0')
                """,
                    (
                        user_id,
                        session_id,
                        action_type,
                        action_result,
                        target_entry_id,
                        error_message,
                        details_json,
                        security_level,
                        risk_score,
                        execution_time_ms,
                    ),
                )

                conn.commit()
                logger.debug(f"Security event logged: {action_type} by user {user_id}")
                return True

        except sqlite3.Error as e:
            logger.error(f"Failed to log security event: {e}")
            return False

    def get_security_audit_log(
        self,
        user_id: Optional[int] = None,
        action_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve security audit log entries with optional filtering

        Args:
            user_id (int, optional): Filter by specific user
            action_type (str, optional): Filter by specific action type
            limit (int): Maximum number of entries to return
            offset (int): Number of entries to skip (for pagination)

        Returns:
            List[Dict[str, Any]]: List of audit log entries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Build query with optional filters
                query = """
                    SELECT * FROM security_audit_log
                    WHERE 1=1
                """
                params = []

                if user_id is not None:
                    query += " AND user_id = ?"
                    params.append(user_id)

                if action_type is not None:
                    query += " AND action_type = ?"
                    params.append(action_type)

                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                cursor.execute(query, params)

                entries = []
                for row in cursor.fetchall():
                    entry = dict(row)

                    # Parse JSON action_details if present
                    if entry["action_details"]:
                        try:
                            entry["action_details"] = json.loads(entry["action_details"])
                        except json.JSONDecodeError:
                            entry["action_details"] = None

                    entries.append(entry)

                return entries

        except sqlite3.Error as e:
            logger.error(f"Failed to get security audit log: {e}")
            return []

    def get_security_stats(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get security statistics for a user over specified time period

        Args:
            user_id (int): User ID to get stats for
            days (int): Number of days to look back

        Returns:
            Dict[str, Any]: Security statistics
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Calculate date threshold
                cutoff_date = datetime.now() - timedelta(days=days)

                # Get overall activity counts
                cursor.execute(
                    """
                    SELECT
                        action_type,
                        action_result,
                        COUNT(*) as count
                    FROM security_audit_log
                    WHERE user_id = ? AND timestamp >= ?
                    GROUP BY action_type, action_result
                    ORDER BY count DESC
                """,
                    (user_id, cutoff_date),
                )

                activity_stats = {}
                for row in cursor.fetchall():
                    action = row["action_type"]
                    result = row["action_result"]
                    count = row["count"]

                    if action not in activity_stats:
                        activity_stats[action] = {"SUCCESS": 0, "FAILURE": 0, "PARTIAL": 0}

                    activity_stats[action][result] = count

                # Get risk level distribution
                cursor.execute(
                    """
                    SELECT security_level, COUNT(*) as count
                    FROM security_audit_log
                    WHERE user_id = ? AND timestamp >= ?
                    GROUP BY security_level
                """,
                    (user_id, cutoff_date),
                )

                risk_distribution = {
                    row["security_level"]: row["count"] for row in cursor.fetchall()
                }

                # Get recent high-risk events
                cursor.execute(
                    """
                    SELECT action_type, timestamp, action_details, risk_score
                    FROM security_audit_log
                    WHERE user_id = ? AND security_level IN ('HIGH', 'CRITICAL')
                      AND timestamp >= ?
                    ORDER BY timestamp DESC
                    LIMIT 10
                """,
                    (user_id, cutoff_date),
                )

                high_risk_events = []
                for row in cursor.fetchall():
                    event = dict(row)
                    if event["action_details"]:
                        try:
                            event["action_details"] = json.loads(event["action_details"])
                        except json.JSONDecodeError:
                            event["action_details"] = None
                    high_risk_events.append(event)

                return {
                    "time_period_days": days,
                    "activity_stats": activity_stats,
                    "risk_distribution": risk_distribution,
                    "high_risk_events": high_risk_events,
                    "total_events": sum(sum(stats.values()) for stats in activity_stats.values()),
                }

        except sqlite3.Error as e:
            logger.error(f"Failed to get security stats: {e}")
            return {}

    def cleanup_old_audit_logs(self, days_to_keep: int = 90) -> int:
        """
        Clean up old audit log entries (except critical security events)

        Args:
            days_to_keep (int): Number of days of logs to keep

        Returns:
            int: Number of entries deleted
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Calculate cutoff date
                cutoff_date = datetime.now() - timedelta(days=days_to_keep)

                # Delete old entries except critical ones
                cursor.execute(
                    """
                    DELETE FROM security_audit_log
                    WHERE timestamp < ? AND security_level NOT IN ('CRITICAL')
                """,
                    (cutoff_date,),
                )

                deleted_count = cursor.rowcount
                conn.commit()

                logger.info(f"Cleaned up {deleted_count} old audit log entries")
                return deleted_count

        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup audit logs: {e}")
            return 0

    def close(self):
        """
        Close the database manager and clean up resources

        This method should be called when the application is shutting down
        to ensure proper cleanup of database connections and resources.
        """
        logger.info("Database manager closed")
        # SQLite connections are closed automatically by context manager
        # This method is here for future use if connection pooling is implemented


# Utility functions for external use


def create_database_manager(db_path: str = "data/password_manager.db") -> DatabaseManager:
    """
    Factory function to create a database manager instance

    Args:
        db_path (str): Path to the SQLite database file

    Returns:
        DatabaseManager: Configured database manager instance
    """
    return DatabaseManager(db_path)


def is_database_healthy(db_path: str = "data/password_manager.db") -> bool:
    """
    Check if the database is healthy and accessible

    Args:
        db_path (str): Path to the SQLite database file

    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        db = DatabaseManager(db_path)

        # Try a simple query
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]

            # Should have at least 3 tables: users, passwords, database_metadata
            return table_count >= 3

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


if __name__ == "__main__":
    # Test code for database functionality
    print("Testing Personal Password Manager Database...")

    # Create test database
    db = DatabaseManager("test_database.db")

    try:
        # Test user creation
        user_id = db.create_user("testuser", "testpassword123")
        print(f"✓ User created with ID: {user_id}")

        # Test authentication
        user_info = db.authenticate_user("testuser", "testpassword123")
        if user_info:
            print("✓ Authentication successful")

        # Test statistics
        stats = db.get_user_statistics(user_id)
        print(f"✓ User statistics: {stats}")

        print("✓ All database tests passed!")

    except Exception as e:
        print(f"❌ Database test failed: {e}")

    finally:
        # Clean up test database
        import os

        if os.path.exists("test_database.db"):
            os.remove("test_database.db")
