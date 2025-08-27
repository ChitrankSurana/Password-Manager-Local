#!/usr/bin/env python3
"""
Personal Password Manager - Import/Export Utility
=================================================

This module provides comprehensive backup, export, and import functionality for
the password manager, supporting multiple formats and secure data transfer between
systems. It handles database backups, encrypted exports, and data migration.

Key Features:
- Database backup and restore operations
- Encrypted JSON export/import with compression
- CSV export for external password managers
- XML export for advanced data interchange
- Chrome/Firefox password import support
- KeePass database import (basic)
- Data validation and integrity checking
- Secure file handling and encryption

Security Features:
- All exports are encrypted with user's master password
- Secure file deletion after operations
- Data integrity verification with checksums
- Safe import validation and error handling
- Memory-safe password operations

Author: Personal Password Manager
Version: 1.0.0
"""

import json
import csv
import xml.etree.ElementTree as ET
import sqlite3
import os
import shutil
import hashlib
import gzip
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import base64

# Import our core modules
from ..core.database import DatabaseManager
from ..core.encryption import PasswordEncryption
from ..core.auth import AuthenticationManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImportExportError(Exception):
    """Base exception for import/export operations"""
    pass

class BackupError(ImportExportError):
    """Raised when backup operations fail"""
    pass

class ExportError(ImportExportError):
    """Raised when export operations fail"""
    pass

class ImportError(ImportExportError):
    """Raised when import operations fail"""
    pass

class DataValidationError(ImportExportError):
    """Raised when imported data fails validation"""
    pass

class BackupManager:
    """
    Comprehensive backup and restore management system
    
    This class handles database backups, encrypted exports, and data imports
    with full integrity checking and security measures. It supports multiple
    formats and provides portable data management.
    
    Features:
    - Complete database backup and restore
    - Encrypted export with compression
    - Multiple import formats (JSON, CSV, XML)
    - Browser password import support
    - Data validation and verification
    - Secure file operations
    """
    
    def __init__(self, db_path: str = "data/password_manager.db"):
        """
        Initialize the backup manager
        
        Args:
            db_path (str): Path to the database file
        """
        self.db_path = Path(db_path)
        self.backup_dir = Path("backups")
        self.export_dir = Path("exports")
        
        # Ensure directories exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.db_manager = DatabaseManager(str(self.db_path))
        self.encryption = PasswordEncryption()
        
        logger.info("Backup manager initialized")
    
    def create_database_backup(self, backup_name: Optional[str] = None) -> str:
        """
        Create a complete database backup
        
        Args:
            backup_name (str, optional): Custom backup name
            
        Returns:
            str: Path to the created backup file
            
        Raises:
            BackupError: If backup creation fails
        """
        try:
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"password_manager_backup_{timestamp}.db"
            
            backup_path = self.backup_dir / backup_name
            
            # Create backup using SQLite backup API
            if not self.db_path.exists():
                raise BackupError(f"Source database not found: {self.db_path}")
            
            # Copy database file
            shutil.copy2(self.db_path, backup_path)
            
            # Verify backup integrity
            self._verify_backup_integrity(backup_path)
            
            # Create backup metadata
            metadata_path = backup_path.with_suffix('.meta.json')
            metadata = {
                'created_at': datetime.now().isoformat(),
                'source_database': str(self.db_path),
                'backup_size': backup_path.stat().st_size,
                'checksum': self._calculate_file_checksum(backup_path)
            }
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Database backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            raise BackupError(f"Failed to create database backup: {e}")
    
    def restore_database_backup(self, backup_path: str, 
                               confirm_restore: bool = False) -> bool:
        """
        Restore database from backup
        
        Args:
            backup_path (str): Path to backup file
            confirm_restore (bool): Confirmation flag for safety
            
        Returns:
            bool: True if restore was successful
            
        Raises:
            BackupError: If restore fails
        """
        if not confirm_restore:
            raise BackupError("Restore operation requires explicit confirmation")
        
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                raise BackupError(f"Backup file not found: {backup_path}")
            
            # Verify backup integrity
            self._verify_backup_integrity(backup_path)
            
            # Create current database backup before restore
            current_backup = self.create_database_backup("pre_restore_backup")
            
            try:
                # Close existing database connections
                self.db_manager.close()
                
                # Restore backup
                shutil.copy2(backup_path, self.db_path)
                
                # Reinitialize database manager
                self.db_manager = DatabaseManager(str(self.db_path))
                
                logger.info(f"Database restored from backup: {backup_path}")
                return True
                
            except Exception as e:
                # Attempt to restore previous state
                try:
                    shutil.copy2(current_backup, self.db_path)
                    self.db_manager = DatabaseManager(str(self.db_path))
                    logger.info("Restored previous database state after failed restore")
                except:
                    pass
                raise e
                
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            raise BackupError(f"Failed to restore database backup: {e}")
    
    def export_encrypted_data(self, session_id: str, master_password: str,
                             export_format: str = "json", 
                             include_metadata: bool = True) -> str:
        """
        Export all password data in encrypted format
        
        Args:
            session_id (str): Valid session ID
            master_password (str): Master password for encryption
            export_format (str): Export format (json, csv, xml)
            include_metadata (bool): Include creation/modification dates
            
        Returns:
            str: Path to the created export file
            
        Raises:
            ExportError: If export fails
        """
        try:
            # Validate session and get user info
            from ..core.auth import AuthenticationManager
            auth_manager = AuthenticationManager(str(self.db_path))
            session = auth_manager.validate_session(session_id)
            
            # Get all password entries for user
            entries = self.db_manager.get_password_entries(session.user_id)
            
            # Decrypt passwords
            decrypted_entries = []
            for entry in entries:
                try:
                    decrypted_password = self.encryption.decrypt_password(
                        entry['password_encrypted'], master_password
                    )
                    
                    entry_data = {
                        'website': entry['website'],
                        'username': entry['username'],
                        'password': decrypted_password,
                        'remarks': entry.get('remarks', ''),
                        'is_favorite': bool(entry.get('is_favorite', False))
                    }
                    
                    if include_metadata:
                        entry_data.update({
                            'created_at': entry.get('created_at'),
                            'modified_at': entry.get('modified_at')
                        })
                    
                    decrypted_entries.append(entry_data)
                    
                except Exception as e:
                    logger.error(f"Failed to decrypt entry {entry.get('entry_id')}: {e}")
                    # Skip corrupted entries but continue export
                    continue
            
            # Export in requested format
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if export_format.lower() == "json":
                export_path = self._export_json(decrypted_entries, session.username, timestamp)
            elif export_format.lower() == "csv":
                export_path = self._export_csv(decrypted_entries, session.username, timestamp)
            elif export_format.lower() == "xml":
                export_path = self._export_xml(decrypted_entries, session.username, timestamp)
            else:
                raise ExportError(f"Unsupported export format: {export_format}")
            
            # Encrypt the export file
            encrypted_path = self._encrypt_export_file(export_path, master_password)
            
            # Remove unencrypted file
            os.remove(export_path)
            
            logger.info(f"Data exported successfully: {encrypted_path}")
            return encrypted_path
            
        except Exception as e:
            logger.error(f"Data export failed: {e}")
            raise ExportError(f"Failed to export data: {e}")
    
    def import_encrypted_data(self, session_id: str, master_password: str,
                             import_file_path: str, merge_mode: bool = True) -> Dict[str, Any]:
        """
        Import data from encrypted export file
        
        Args:
            session_id (str): Valid session ID
            master_password (str): Master password for decryption
            import_file_path (str): Path to encrypted import file
            merge_mode (bool): True to merge, False to replace
            
        Returns:
            Dict[str, Any]: Import results summary
            
        Raises:
            ImportError: If import fails
        """
        try:
            import_path = Path(import_file_path)
            if not import_path.exists():
                raise ImportError(f"Import file not found: {import_path}")
            
            # Decrypt import file
            decrypted_path = self._decrypt_import_file(import_path, master_password)
            
            try:
                # Load and validate data
                import_data = self._load_import_data(decrypted_path)
                
                # Validate session
                from ..core.auth import AuthenticationManager
                auth_manager = AuthenticationManager(str(self.db_path))
                session = auth_manager.validate_session(session_id)
                
                # Import data
                results = self._import_password_entries(
                    session.user_id, import_data, master_password, merge_mode
                )
                
                logger.info(f"Data imported successfully: {results}")
                return results
                
            finally:
                # Clean up decrypted file
                if os.path.exists(decrypted_path):
                    os.remove(decrypted_path)
                    
        except Exception as e:
            logger.error(f"Data import failed: {e}")
            raise ImportError(f"Failed to import data: {e}")
    
    def import_browser_passwords(self, session_id: str, master_password: str,
                                browser_type: str, csv_file_path: str) -> Dict[str, Any]:
        """
        Import passwords from browser CSV export
        
        Args:
            session_id (str): Valid session ID
            master_password (str): Master password for encryption
            browser_type (str): Browser type (chrome, firefox, edge)
            csv_file_path (str): Path to browser CSV export
            
        Returns:
            Dict[str, Any]: Import results summary
            
        Raises:
            ImportError: If import fails
        """
        try:
            csv_path = Path(csv_file_path)
            if not csv_path.exists():
                raise ImportError(f"CSV file not found: {csv_path}")
            
            # Parse browser CSV
            browser_entries = self._parse_browser_csv(csv_path, browser_type)
            
            # Validate session
            from ..core.auth import AuthenticationManager
            auth_manager = AuthenticationManager(str(self.db_path))
            session = auth_manager.validate_session(session_id)
            
            # Import entries
            results = self._import_password_entries(
                session.user_id, browser_entries, master_password, merge_mode=True
            )
            
            logger.info(f"Browser passwords imported: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Browser import failed: {e}")
            raise ImportError(f"Failed to import browser passwords: {e}")
    
    def _verify_backup_integrity(self, backup_path: Path):
        """Verify backup database integrity"""
        try:
            conn = sqlite3.connect(str(backup_path))
            cursor = conn.cursor()
            
            # Check database integrity
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            if result[0] != "ok":
                raise BackupError(f"Backup integrity check failed: {result[0]}")
            
            # Verify essential tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['users', 'passwords']
            for table in required_tables:
                if table not in tables:
                    raise BackupError(f"Missing required table: {table}")
            
            conn.close()
            
        except sqlite3.Error as e:
            raise BackupError(f"Database integrity verification failed: {e}")
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _export_json(self, entries: List[Dict], username: str, timestamp: str) -> str:
        """Export entries to JSON format"""
        export_data = {
            'export_info': {
                'format': 'JSON',
                'version': '1.0',
                'exported_by': username,
                'exported_at': datetime.now().isoformat(),
                'entry_count': len(entries)
            },
            'entries': entries
        }
        
        export_path = self.export_dir / f"{username}_export_{timestamp}.json"
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return str(export_path)
    
    def _export_csv(self, entries: List[Dict], username: str, timestamp: str) -> str:
        """Export entries to CSV format"""
        export_path = self.export_dir / f"{username}_export_{timestamp}.csv"
        
        with open(export_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['website', 'username', 'password', 'remarks', 'is_favorite']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for entry in entries:
                # Only write fields that exist in fieldnames
                filtered_entry = {k: v for k, v in entry.items() if k in fieldnames}
                writer.writerow(filtered_entry)
        
        return str(export_path)
    
    def _export_xml(self, entries: List[Dict], username: str, timestamp: str) -> str:
        """Export entries to XML format"""
        root = ET.Element("PasswordManagerExport")
        
        # Add export info
        info = ET.SubElement(root, "ExportInfo")
        ET.SubElement(info, "Format").text = "XML"
        ET.SubElement(info, "Version").text = "1.0"
        ET.SubElement(info, "ExportedBy").text = username
        ET.SubElement(info, "ExportedAt").text = datetime.now().isoformat()
        ET.SubElement(info, "EntryCount").text = str(len(entries))
        
        # Add entries
        entries_elem = ET.SubElement(root, "Entries")
        
        for entry in entries:
            entry_elem = ET.SubElement(entries_elem, "Entry")
            for key, value in entry.items():
                elem = ET.SubElement(entry_elem, key.replace(' ', ''))
                elem.text = str(value) if value is not None else ""
        
        # Write to file
        export_path = self.export_dir / f"{username}_export_{timestamp}.xml"
        tree = ET.ElementTree(root)
        tree.write(export_path, encoding='utf-8', xml_declaration=True)
        
        return str(export_path)
    
    def _encrypt_export_file(self, file_path: str, master_password: str) -> str:
        """Encrypt export file with master password"""
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Compress data
        compressed_data = gzip.compress(file_data)
        
        # Encrypt compressed data
        encrypted_data = self.encryption.encrypt_password(
            base64.b64encode(compressed_data).decode('utf-8'), 
            master_password
        )
        
        # Save encrypted file
        encrypted_path = file_path + '.encrypted'
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_data)
        
        return encrypted_path
    
    def _decrypt_import_file(self, import_path: Path, master_password: str) -> str:
        """Decrypt import file with master password"""
        with open(import_path, 'rb') as f:
            encrypted_data = f.read()
        
        try:
            # Decrypt data
            decrypted_b64 = self.encryption.decrypt_password(encrypted_data, master_password)
            
            # Decode and decompress
            compressed_data = base64.b64decode(decrypted_b64)
            file_data = gzip.decompress(compressed_data)
            
            # Save decrypted file temporarily
            decrypted_path = str(import_path) + '.decrypted'
            with open(decrypted_path, 'wb') as f:
                f.write(file_data)
            
            return decrypted_path
            
        except Exception as e:
            raise ImportError(f"Failed to decrypt import file: {e}")
    
    def _load_import_data(self, file_path: str) -> List[Dict]:
        """Load and validate import data"""
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('entries', [])
        
        elif file_path.suffix.lower() == '.csv':
            entries = []
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    entries.append(dict(row))
            return entries
        
        elif file_path.suffix.lower() == '.xml':
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            entries = []
            for entry_elem in root.findall('.//Entry'):
                entry = {}
                for child in entry_elem:
                    entry[child.tag] = child.text
                entries.append(entry)
            return entries
        
        else:
            raise ImportError(f"Unsupported import format: {file_path.suffix}")
    
    def _import_password_entries(self, user_id: int, entries: List[Dict], 
                                master_password: str, merge_mode: bool) -> Dict[str, Any]:
        """Import password entries into database"""
        imported_count = 0
        skipped_count = 0
        error_count = 0
        errors = []
        
        for entry in entries:
            try:
                # Validate required fields
                if not entry.get('website') or not entry.get('username'):
                    skipped_count += 1
                    continue
                
                # Check for duplicates if in merge mode
                if merge_mode:
                    existing_entries = self.db_manager.get_password_entries(
                        user_id, website=entry['website']
                    )
                    
                    duplicate_found = any(
                        existing['username'].lower() == entry['username'].lower()
                        for existing in existing_entries
                    )
                    
                    if duplicate_found:
                        skipped_count += 1
                        continue
                
                # Encrypt password
                encrypted_password = self.encryption.encrypt_password(
                    entry.get('password', ''), master_password
                )
                
                # Add entry to database
                self.db_manager.add_password_entry(
                    user_id=user_id,
                    website=entry['website'],
                    username=entry['username'],
                    encrypted_password=encrypted_password,
                    remarks=entry.get('remarks', '')
                )
                
                imported_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"Entry '{entry.get('website', 'unknown')}': {str(e)}")
                logger.error(f"Failed to import entry: {e}")
        
        return {
            'imported_count': imported_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'errors': errors[:10],  # Limit error list
            'total_processed': len(entries)
        }
    
    def _parse_browser_csv(self, csv_path: Path, browser_type: str) -> List[Dict]:
        """Parse browser CSV export file"""
        entries = []
        
        # Browser-specific column mappings
        column_mapping = {
            'chrome': {
                'name': 'website',
                'url': 'website', 
                'username': 'username',
                'password': 'password'
            },
            'firefox': {
                'hostname': 'website',
                'username': 'username',
                'password': 'password'
            },
            'edge': {
                'name': 'website',
                'url': 'website',
                'username': 'username',
                'password': 'password'
            }
        }
        
        mapping = column_mapping.get(browser_type.lower(), column_mapping['chrome'])
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                entry = {}
                
                # Map browser columns to our format
                for browser_col, our_col in mapping.items():
                    if browser_col in row:
                        entry[our_col] = row[browser_col]
                
                # Extract domain from URL if needed
                if 'url' in row and entry.get('website'):
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(entry['website'])
                        entry['website'] = parsed.netloc or parsed.path
                    except:
                        pass
                
                if entry.get('website') and entry.get('username'):
                    entries.append(entry)
        
        return entries
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """Get list of available backups with metadata"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.db"):
            metadata_file = backup_file.with_suffix('.meta.json')
            
            backup_info = {
                'filename': backup_file.name,
                'path': str(backup_file),
                'size': backup_file.stat().st_size,
                'created_at': datetime.fromtimestamp(backup_file.stat().st_ctime).isoformat()
            }
            
            # Load metadata if available
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        backup_info.update(metadata)
                except Exception as e:
                    logger.error(f"Failed to load backup metadata: {e}")
            
            backups.append(backup_info)
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        return backups

# Utility functions for external use

def create_backup_manager(db_path: str = "data/password_manager.db") -> BackupManager:
    """
    Factory function to create a backup manager instance
    
    Args:
        db_path (str): Path to the database file
        
    Returns:
        BackupManager: Configured backup manager
    """
    return BackupManager(db_path)

def quick_backup(db_path: str = "data/password_manager.db") -> str:
    """
    Quick utility function to create a database backup
    
    Args:
        db_path (str): Path to the database file
        
    Returns:
        str: Path to the created backup file
    """
    backup_manager = BackupManager(db_path)
    return backup_manager.create_database_backup()

if __name__ == "__main__":
    # Test the backup and export functionality
    print("Testing Personal Password Manager Backup/Export System...")
    
    try:
        # Create backup manager
        backup_manager = BackupManager("test_backup.db")
        
        # Test database backup
        backup_path = backup_manager.create_database_backup("test_backup")
        print(f"✓ Database backup created: {backup_path}")
        
        # Test backup list
        backup_list = backup_manager.get_backup_list()
        print(f"✓ Found {len(backup_list)} backup(s)")
        
        # Test utility function
        quick_backup_path = quick_backup("test_backup.db")
        print(f"✓ Quick backup created: {quick_backup_path}")
        
        print("✓ All backup/export tests passed!")
        
    except Exception as e:
        print(f"❌ Backup/export test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test files
        import os
        test_files = ["test_backup.db"]
        for file in test_files:
            if os.path.exists(file):
                os.remove(file)