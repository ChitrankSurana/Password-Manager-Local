#!/usr/bin/env python3
"""
Personal Password Manager - Database Migration System
====================================================

This module provides comprehensive database migration functionality for the
Personal Password Manager. It handles schema updates, data migrations, and
maintains backward compatibility while adding new features.

Key Features:
- Automatic schema version detection and migration
- Safe migration with automatic backup creation
- Rollback capability for failed migrations
- Comprehensive error handling and logging
- Support for complex data transformations during migration

Security Features:
- Automatic database backup before any changes
- Transaction-based migrations (all-or-nothing)
- Migration validation to prevent data corruption
- Detailed audit logging of migration activities

Author: Personal Password Manager Enhancement
Version: 2.0.0
Date: September 21, 2025
"""

import sqlite3
import logging
import shutil
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from contextlib import contextmanager

# Configure logging for migration operations
logger = logging.getLogger(__name__)

class MigrationError(Exception):
    """Exception raised when database migration fails"""
    pass

class MigrationValidationError(MigrationError):
    """Exception raised when migration validation fails"""
    pass

class MigrationBackupError(MigrationError):
    """Exception raised when backup creation fails"""
    pass

class DatabaseMigrationManager:
    """
    Manages database schema migrations with safety and reliability
    
    This class provides a comprehensive migration system that safely updates
    the database schema while preserving existing data. It includes automatic
    backup creation, transaction-based migrations, and detailed logging.
    
    Features:
    - Automatic backup before any migration
    - Version-based migration tracking
    - Transaction-based safety (all-or-nothing)
    - Detailed logging and error reporting
    - Migration validation and rollback support
    """
    
    def __init__(self, db_path: str, backup_dir: str = "data/backups"):
        """
        Initialize the migration manager
        
        Args:
            db_path (str): Path to the main database file
            backup_dir (str): Directory to store database backups
        """
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Migration registry - maps version numbers to migration functions
        self._migrations: Dict[int, Callable] = {}
        
        # Register all available migrations
        self._register_migrations()
        
        logger.info(f"Migration manager initialized for database: {self.db_path}")
    
    def _register_migrations(self):
        """Register all available migrations"""
        # Migration from version 1 to version 2: Add user settings and audit logging
        self._migrations[2] = self._migrate_to_version_2

        # Migration from version 2 to version 3: Add entry_name field to passwords table
        self._migrations[3] = self._migrate_to_version_3

        logger.info(f"Registered {len(self._migrations)} migrations")
    
    @contextmanager
    def get_connection(self, db_path: Optional[Path] = None):
        """
        Context manager for database connections during migrations
        
        Args:
            db_path (Path, optional): Path to database file (defaults to main database)
            
        Yields:
            sqlite3.Connection: Database connection with proper configuration
        """
        target_path = db_path or self.db_path
        connection = None
        
        try:
            # Create connection with extended timeout for migrations
            connection = sqlite3.connect(
                str(target_path),
                timeout=60,  # Longer timeout for migration operations
                check_same_thread=False
            )
            
            # Configure connection for migrations
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = FULL")  # Extra safety during migration
            
            yield connection
            
        except sqlite3.Error as e:
            logger.error(f"Migration database connection error: {e}")
            if connection:
                connection.rollback()
            raise MigrationError(f"Database connection failed during migration: {e}")
        
        finally:
            if connection:
                connection.close()
    
    def get_current_schema_version(self) -> int:
        """
        Get the current schema version from the database
        
        Returns:
            int: Current schema version (defaults to 1 if not found)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT value FROM database_metadata WHERE key = 'schema_version'"
                )
                result = cursor.fetchone()
                
                if result:
                    return int(result['value'])
                else:
                    # If no version found, assume version 1 (original schema)
                    logger.info("No schema version found, assuming version 1")
                    return 1
                    
        except sqlite3.Error as e:
            logger.error(f"Failed to get schema version: {e}")
            # If we can't read the version, assume it's version 1
            return 1
    
    def needs_migration(self) -> bool:
        """
        Check if database needs migration to latest version
        
        Returns:
            bool: True if migration is needed, False otherwise
        """
        current_version = self.get_current_schema_version()
        latest_version = max(self._migrations.keys()) if self._migrations else current_version
        
        needs_update = current_version < latest_version
        
        if needs_update:
            logger.info(f"Migration needed: current version {current_version}, latest version {latest_version}")
        else:
            logger.info(f"Database is up to date at version {current_version}")
            
        return needs_update
    
    def create_backup(self, backup_name: Optional[str] = None) -> Path:
        """
        Create a backup of the current database
        
        Args:
            backup_name (str, optional): Custom name for backup file
            
        Returns:
            Path: Path to the created backup file
            
        Raises:
            MigrationBackupError: If backup creation fails
        """
        try:
            if not self.db_path.exists():
                raise MigrationBackupError(f"Database file not found: {self.db_path}")
            
            # Generate backup filename with timestamp
            if backup_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                current_version = self.get_current_schema_version()
                backup_name = f"password_manager_v{current_version}_backup_{timestamp}.db"
            
            backup_path = self.backup_dir / backup_name
            
            # Create backup using file copy (safer than SQL backup for SQLite)
            shutil.copy2(self.db_path, backup_path)
            
            # Verify backup integrity
            self._verify_backup_integrity(backup_path)
            
            logger.info(f"Database backup created successfully: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            raise MigrationBackupError(f"Backup creation failed: {e}")
    
    def _verify_backup_integrity(self, backup_path: Path):
        """
        Verify that the backup file is a valid SQLite database
        
        Args:
            backup_path (Path): Path to backup file to verify
            
        Raises:
            MigrationBackupError: If backup is corrupted or invalid
        """
        try:
            with self.get_connection(backup_path) as conn:
                cursor = conn.cursor()
                
                # Run integrity check
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                
                if result and result[0] != 'ok':
                    raise MigrationBackupError(f"Backup integrity check failed: {result[0]}")
                
                # Verify essential tables exist
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = {'users', 'passwords', 'database_metadata'}
                missing_tables = required_tables - set(tables)
                
                if missing_tables:
                    raise MigrationBackupError(f"Backup missing required tables: {missing_tables}")
                
                logger.info("Backup integrity verified successfully")
                
        except sqlite3.Error as e:
            raise MigrationBackupError(f"Backup verification failed: {e}")
    
    def apply_migrations(self) -> bool:
        """
        Apply all necessary migrations to bring database to latest version
        
        Returns:
            bool: True if migrations applied successfully, False otherwise
        """
        if not self.needs_migration():
            logger.info("No migrations needed")
            return True
        
        current_version = self.get_current_schema_version()
        
        # Create backup before starting migrations
        try:
            backup_path = self.create_backup()
            logger.info(f"Pre-migration backup created: {backup_path}")
        except MigrationBackupError as e:
            logger.error(f"Failed to create backup before migration: {e}")
            return False
        
        # Apply migrations in sequence
        try:
            for target_version in sorted(self._migrations.keys()):
                if target_version > current_version:
                    logger.info(f"Applying migration to version {target_version}")
                    
                    # Apply single migration in transaction
                    success = self._apply_single_migration(target_version)
                    
                    if not success:
                        logger.error(f"Migration to version {target_version} failed")
                        return False
                    
                    # Update current version
                    current_version = target_version
                    logger.info(f"Successfully migrated to version {target_version}")
            
            logger.info("All migrations completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Migration process failed: {e}")
            return False
    
    def _apply_single_migration(self, target_version: int) -> bool:
        """
        Apply a single migration in a transaction
        
        Args:
            target_version (int): Target schema version to migrate to
            
        Returns:
            bool: True if migration successful, False otherwise
        """
        if target_version not in self._migrations:
            logger.error(f"No migration available for version {target_version}")
            return False
        
        try:
            with self.get_connection() as conn:
                # Start transaction
                conn.execute("BEGIN IMMEDIATE")
                
                try:
                    # Execute migration function
                    migration_func = self._migrations[target_version]
                    migration_func(conn)
                    
                    # Update schema version
                    conn.execute("""
                        INSERT OR REPLACE INTO database_metadata (key, value, updated_at)
                        VALUES ('schema_version', ?, CURRENT_TIMESTAMP)
                    """, (str(target_version),))
                    
                    # Commit transaction
                    conn.commit()
                    
                    logger.info(f"Migration to version {target_version} completed successfully")
                    return True
                    
                except Exception as e:
                    # Rollback transaction on any error
                    conn.rollback()
                    logger.error(f"Migration to version {target_version} failed, rolled back: {e}")
                    raise
                    
        except sqlite3.Error as e:
            logger.error(f"Database error during migration to version {target_version}: {e}")
            return False
    
    def _migrate_to_version_2(self, conn: sqlite3.Connection):
        """
        Migration from version 1 to version 2: Add user settings and audit logging
        
        This migration adds:
        1. user_settings table for per-user preferences
        2. security_audit_log table for detailed security tracking
        3. Indexes for performance optimization
        
        Args:
            conn (sqlite3.Connection): Database connection (within transaction)
        """
        cursor = conn.cursor()
        
        logger.info("Starting migration to version 2: Adding user settings and audit logging")
        
        # 1. Create user_settings table for per-user preferences
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                setting_category TEXT NOT NULL,
                setting_key TEXT NOT NULL,
                setting_value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE(user_id, setting_category, setting_key)
            )
        """)
        logger.info("Created user_settings table")
        
        # 2. Create security_audit_log table for detailed security tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                target_entry_id INTEGER,
                
                -- Enhanced fields for detailed tracking
                action_result TEXT NOT NULL DEFAULT 'SUCCESS',
                error_message TEXT,
                request_source TEXT DEFAULT 'GUI',
                affected_fields TEXT,
                old_values TEXT,
                new_values TEXT,
                security_level TEXT DEFAULT 'MEDIUM',
                risk_score INTEGER DEFAULT 0,
                
                -- Context information
                action_details TEXT,
                ip_address TEXT DEFAULT '127.0.0.1',
                user_agent TEXT DEFAULT 'Desktop Application',
                client_version TEXT,
                execution_time_ms INTEGER DEFAULT 0,
                
                -- Timestamps
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        logger.info("Created security_audit_log table")
        
        # 3. Create performance indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_settings_lookup 
            ON user_settings(user_id, setting_category, setting_key)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_user_time 
            ON security_audit_log(user_id, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_action 
            ON security_audit_log(action_type, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_security_level 
            ON security_audit_log(security_level, timestamp)
        """)
        
        logger.info("Created performance indexes")
        
        # 4. Create trigger for automatic timestamp updates on user_settings
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_user_settings_timestamp
            AFTER UPDATE ON user_settings
            BEGIN
                UPDATE user_settings SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END
        """)
        
        logger.info("Created automatic timestamp trigger")
        
        # 5. Insert default settings for existing users (if any)
        cursor.execute("SELECT user_id FROM users")
        existing_users = cursor.fetchall()
        
        if existing_users:
            logger.info(f"Setting up default settings for {len(existing_users)} existing users")
            
            # Default settings for password viewing
            default_viewing_settings = [
                ('password_viewing', 'view_timeout_minutes', '1'),
                ('password_viewing', 'require_master_password', 'true'),
                ('password_viewing', 'auto_hide_on_focus_loss', 'true'),
                ('password_viewing', 'show_view_timer', 'true'),
                ('password_viewing', 'allow_copy_when_visible', 'true'),
                ('password_viewing', 'max_concurrent_views', '5')
            ]
            
            # Default settings for password deletion
            default_deletion_settings = [
                ('password_deletion', 'require_confirmation', 'true'),
                ('password_deletion', 'confirmation_type', 'type_website'),
                ('password_deletion', 'require_master_password', 'false'),
                ('password_deletion', 'show_deleted_count', 'true')
            ]
            
            # Default security settings
            default_security_settings = [
                ('security', 'audit_logging', 'true'),
                ('security', 'max_failed_attempts', '3'),
                ('security', 'lockout_duration_minutes', '5')
            ]
            
            all_default_settings = default_viewing_settings + default_deletion_settings + default_security_settings
            
            # Insert default settings for each existing user
            for user_row in existing_users:
                user_id = user_row['user_id']
                
                for category, key, value in all_default_settings:
                    cursor.execute("""
                        INSERT OR IGNORE INTO user_settings 
                        (user_id, setting_category, setting_key, setting_value)
                        VALUES (?, ?, ?, ?)
                    """, (user_id, category, key, value))
            
            logger.info("Default settings applied to existing users")
        
        # 6. Add migration audit log entry
        cursor.execute("""
            INSERT INTO security_audit_log 
            (user_id, session_id, action_type, action_result, action_details, 
             security_level, client_version, request_source)
            VALUES (0, 'SYSTEM_MIGRATION', 'DATABASE_MIGRATION', 'SUCCESS', 
                    ?, 'HIGH', '2.0.0', 'MIGRATION_SYSTEM')
        """, (json.dumps({
            'migration_version': 2,
            'migration_type': 'SCHEMA_UPDATE',
            'tables_added': ['user_settings', 'security_audit_log'],
            'indexes_added': ['idx_user_settings_lookup', 'idx_audit_user_time', 'idx_audit_action', 'idx_audit_security_level'],
            'triggers_added': ['update_user_settings_timestamp'],
            'existing_users_updated': len(existing_users) if existing_users else 0
        }),))
        
        logger.info("Migration to version 2 completed successfully")

    def _migrate_to_version_3(self, conn: sqlite3.Connection):
        """
        Migration from version 2 to version 3: Add entry_name field to passwords table

        This migration adds:
        1. entry_name column to passwords table for custom entry names/labels
        2. Index for better search performance on entry names

        Args:
            conn (sqlite3.Connection): Database connection (within transaction)
        """
        cursor = conn.cursor()

        logger.info("Starting migration to version 3: Adding entry_name field to passwords table")

        # 1. Add entry_name column to passwords table
        try:
            cursor.execute("""
                ALTER TABLE passwords ADD COLUMN entry_name TEXT DEFAULT NULL
            """)
            logger.info("Added entry_name column to passwords table")
        except sqlite3.OperationalError as e:
            # Column might already exist (e.g., if migration was partially completed before)
            if "duplicate column" in str(e).lower():
                logger.warning("entry_name column already exists, skipping column addition")
            else:
                raise

        # 2. Create index for entry_name for better search performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_passwords_entry_name
            ON passwords(entry_name)
        """)
        logger.info("Created index on entry_name column")

        # 3. Add migration audit log entry (if table exists)
        try:
            cursor.execute("""
                INSERT INTO security_audit_log
                (user_id, session_id, action_type, action_result, action_details,
                 security_level, client_version, request_source)
                VALUES (0, 'SYSTEM_MIGRATION', 'DATABASE_MIGRATION', 'SUCCESS',
                        ?, 'HIGH', '3.0.0', 'MIGRATION_SYSTEM')
            """, (json.dumps({
                'migration_version': 3,
                'migration_type': 'SCHEMA_UPDATE',
                'tables_modified': ['passwords'],
                'columns_added': ['entry_name'],
                'indexes_added': ['idx_passwords_entry_name'],
                'description': 'Added entry_name field for custom password entry labels'
            }),))
            logger.info("Added migration audit log entry")
        except sqlite3.OperationalError as e:
            # Audit log table might not exist in older database versions
            if "no such table" in str(e).lower():
                logger.warning("security_audit_log table does not exist, skipping audit log entry")
            else:
                raise

        logger.info("Migration to version 3 completed successfully")

    def cleanup_old_backups(self, keep_days: int = 30):
        """
        Clean up backup files older than specified days
        
        Args:
            keep_days (int): Number of days to keep backups (default: 30)
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            deleted_count = 0
            for backup_file in self.backup_dir.glob("*.db"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old backup: {backup_file}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old backup files")
            else:
                logger.info("No old backup files to clean up")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """
        Get history of database migrations from audit log
        
        Returns:
            List[Dict]: List of migration records with details
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT action_details, timestamp, client_version
                    FROM security_audit_log
                    WHERE action_type = 'DATABASE_MIGRATION'
                    ORDER BY timestamp DESC
                """)
                
                migrations = []
                for row in cursor.fetchall():
                    try:
                        details = json.loads(row['action_details']) if row['action_details'] else {}
                        migrations.append({
                            'timestamp': row['timestamp'],
                            'client_version': row['client_version'],
                            'details': details
                        })
                    except json.JSONDecodeError:
                        # Skip corrupted entries
                        continue
                
                return migrations
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get migration history: {e}")
            return []
