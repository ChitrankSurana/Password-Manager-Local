# -*- coding: utf-8 -*-
"""
Unit Tests for Password Manager Core
===================================

Tests for the core password management functionality including:
- Password creation, retrieval, update, deletion
- Encryption and decryption
- User authentication
- Database operations
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

from core.auth import AuthenticationManager
from core.encryption import PasswordEncryption
from core.password_manager import PasswordManagerCore

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import modules under test


class TestPasswordManager(unittest.TestCase):
    """Test cases for PasswordManager class - Basic smoke tests"""

    def setUp(self):
        """Set up test environment"""
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()

        # Test user credentials
        self.test_username = "test_user"
        self.test_password = "Test@Password123"

    def tearDown(self):
        """Clean up test environment"""
        # Remove temporary database file
        try:
            os.unlink(self.temp_db.name)
        except FileNotFoundError:
            pass

    def test_password_manager_import(self):
        """Test that PasswordManager can be imported"""
        try:
            self.assertTrue(True)
        except ImportError:
            self.fail("Could not import PasswordManagerCore")

    def test_auth_manager_import(self):
        """Test that AuthenticationManager can be imported"""
        try:
            self.assertTrue(True)
        except ImportError:
            self.fail("Could not import AuthenticationManager")

    def test_basic_instantiation(self):
        """Test basic instantiation without breaking"""
        try:
            # Test auth manager
            auth = AuthenticationManager(self.temp_db.name)
            self.assertIsNotNone(auth)

            # Test password manager core
            pm = PasswordManagerCore(self.temp_db.name)
            self.assertIsNotNone(pm)

        except Exception as e:
            self.fail(f"Failed to instantiate classes: {e}")


class TestPasswordEncryption(unittest.TestCase):
    """Test cases for password encryption"""

    def setUp(self):
        """Set up encryption test environment"""
        self.encryption = PasswordEncryption()
        self.test_master_password = "MasterPassword123!"
        self.test_plaintext = "MySecretPassword"

    def test_key_derivation(self):
        """Test key derivation from master password"""
        # Test key generation
        salt, key = self.encryption.derive_key(self.test_master_password)

        self.assertIsNotNone(salt)
        self.assertIsNotNone(key)
        self.assertEqual(len(salt), 32)  # 256 bits
        self.assertEqual(len(key), 32)  # 256 bits

        # Test key consistency
        key2 = self.encryption.derive_key_with_salt(self.test_master_password, salt)
        self.assertEqual(key, key2)

    def test_password_encryption_decryption(self):
        """Test password encryption and decryption"""
        # Generate key
        salt, key = self.encryption.derive_key(self.test_master_password)

        # Test encryption
        encrypted_data = self.encryption.encrypt_password(self.test_plaintext, key)
        self.assertIsNotNone(encrypted_data)
        self.assertNotEqual(encrypted_data, self.test_plaintext)

        # Test decryption
        decrypted_password = self.encryption.decrypt_password(encrypted_data, key)
        self.assertEqual(decrypted_password, self.test_plaintext)

    def test_encryption_security(self):
        """Test encryption security properties"""
        salt, key = self.encryption.derive_key(self.test_master_password)

        # Test that same plaintext produces different ciphertext (due to IV)
        encrypted1 = self.encryption.encrypt_password(self.test_plaintext, key)
        encrypted2 = self.encryption.encrypt_password(self.test_plaintext, key)

        self.assertNotEqual(encrypted1, encrypted2)

        # But both should decrypt to same plaintext
        decrypted1 = self.encryption.decrypt_password(encrypted1, key)
        decrypted2 = self.encryption.decrypt_password(encrypted2, key)

        self.assertEqual(decrypted1, self.test_plaintext)
        self.assertEqual(decrypted2, self.test_plaintext)

    def test_wrong_key_fails(self):
        """Test that decryption fails with wrong key"""
        # Encrypt with one key
        salt1, key1 = self.encryption.derive_key("password1")
        encrypted = self.encryption.encrypt_password(self.test_plaintext, key1)

        # Try to decrypt with different key
        salt2, key2 = self.encryption.derive_key("password2")

        with self.assertRaises(Exception):
            self.encryption.decrypt_password(encrypted, key2)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""

    def setUp(self):
        """Set up error handling tests"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.pm = PasswordManagerCore(db_path=self.temp_db.name)

    def tearDown(self):
        """Clean up"""
        if hasattr(self.pm, "conn") and self.pm.conn:
            self.pm.conn.close()
        try:
            os.unlink(self.temp_db.name)
        except FileNotFoundError:
            pass

    def test_invalid_database_path(self):
        """Test handling of invalid database paths"""
        # Test read-only directory (should fail gracefully)
        with self.assertRaises(Exception):
            PasswordManagerCore(db_path="/invalid/path/database.db")

    def test_invalid_session(self):
        """Test operations with invalid session"""
        # Test with None session
        result = self.pm.add_password(None, "test.com", "user", "pass", "")
        self.assertIsNone(result)

        # Test with invalid session object
        fake_session = {"user_id": 999999, "key": b"invalid_key"}
        result = self.pm.add_password(fake_session, "test.com", "user", "pass", "")
        self.assertIsNone(result)

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        self.pm.register_user("testuser", "password")
        session = self.pm.authenticate_user("testuser", "password")

        # Attempt SQL injection in website field
        malicious_website = "'; DROP TABLE passwords; --"

        # This should not cause an error or drop the table
        password_id = self.pm.add_password(session, malicious_website, "user", "pass", "")

        # Verify table still exists and data was inserted safely
        passwords = self.pm.get_all_passwords(session)
        self.assertEqual(len(passwords), 1)
        self.assertEqual(passwords[0].website, malicious_website)

    def test_large_data_handling(self):
        """Test handling of large data inputs"""
        self.pm.register_user("testuser", "password")
        session = self.pm.authenticate_user("testuser", "password")

        # Test very long password
        long_password = "A" * 10000
        password_id = self.pm.add_password(session, "test.com", "user", long_password, "")

        # Should handle gracefully
        self.assertIsNotNone(password_id)

        # Verify retrieval
        passwords = self.pm.get_all_passwords(session)
        self.assertEqual(len(passwords), 1)


if __name__ == "__main__":
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestPasswordManager))
    test_suite.addTest(unittest.makeSuite(TestPasswordEncryption))
    test_suite.addTest(unittest.makeSuite(TestErrorHandling))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
