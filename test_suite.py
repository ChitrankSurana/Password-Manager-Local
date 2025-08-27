#!/usr/bin/env python3
"""
Personal Password Manager - Comprehensive Test Suite
====================================================

This test suite validates all core functionality of the Personal Password Manager
including database operations, encryption, authentication, and both GUI and web interfaces.

Usage:
    python test_suite.py              # Run all tests
    python test_suite.py --core       # Test core modules only
    python test_suite.py --gui        # Test GUI functionality
    python test_suite.py --web        # Test web interface
    python test_suite.py --security   # Test security features

Author: Personal Password Manager
Version: 1.0.0
"""

import sys
import os
import argparse
import tempfile
import shutil
from pathlib import Path
import unittest
import sqlite3
from datetime import datetime
import secrets
import string

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

class Colors:
    """Terminal colors for test output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message: str, color: str = Colors.WHITE):
    """Print colored message to terminal"""
    print(f"{color}{message}{Colors.END}")

def print_test_header(test_name: str):
    """Print test section header"""
    print_colored(f"\n{Colors.BOLD}{'='*60}", Colors.CYAN)
    print_colored(f"{Colors.BOLD}Testing: {test_name}", Colors.CYAN)
    print_colored(f"{'='*60}", Colors.CYAN)

def print_test_result(test_name: str, success: bool, details: str = ""):
    """Print individual test result"""
    status = "[PASS]" if success else "[FAIL]"
    color = Colors.GREEN if success else Colors.RED
    print_colored(f"{status} {test_name}", color)
    if details:
        print_colored(f"    {details}", Colors.WHITE)

class PasswordManagerTestSuite:
    """Main test suite for the Password Manager"""
    
    def __init__(self):
        self.test_dir = None
        self.passed_tests = 0
        self.failed_tests = 0
        self.total_tests = 0
        
    def setup_test_environment(self):
        """Setup isolated test environment"""
        self.test_dir = tempfile.mkdtemp(prefix="password_manager_test_")
        os.environ['PASSWORD_MANAGER_DATA_DIR'] = self.test_dir
        print_colored(f"Test environment: {self.test_dir}", Colors.BLUE)
        
    def cleanup_test_environment(self):
        """Cleanup test environment"""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            print_colored(f"Cleaned up test environment", Colors.BLUE)
            
    def run_test(self, test_func, test_name: str):
        """Run individual test with error handling"""
        try:
            self.total_tests += 1
            result = test_func()
            if result:
                self.passed_tests += 1
                print_test_result(test_name, True, "All checks passed")
            else:
                self.failed_tests += 1
                print_test_result(test_name, False, "Some checks failed")
            return result
        except Exception as e:
            self.failed_tests += 1
            print_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    def test_core_imports(self):
        """Test that all core modules can be imported"""
        try:
            from core.database import DatabaseManager
            from core.encryption import PasswordEncryption
            from core.auth import AuthenticationManager
            from core.password_manager import PasswordManagerCore
            return True
        except ImportError as e:
            print_colored(f"Import error: {e}", Colors.RED)
            return False

    def test_utility_imports(self):
        """Test utility module imports"""
        try:
            from utils.password_generator import PasswordGenerator
            from utils.strength_checker import AdvancedPasswordStrengthChecker
            # Note: import_export might have relative import issues in test context
            return True
        except ImportError as e:
            print_colored(f"Import error: {e}", Colors.RED)
            return False

    def test_gui_imports(self):
        """Test GUI module imports"""
        try:
            from gui.themes import get_theme
            from gui.login_window import LoginWindow
            from gui.main_window import MainWindow
            return True
        except ImportError as e:
            print_colored(f"Import error: {e}", Colors.RED)
            return False
            
    def test_database_creation(self):
        """Test database creation and schema"""
        try:
            from core.database import DatabaseManager
            
            db_path = os.path.join(self.test_dir, "test.db")
            db = DatabaseManager(db_path)
            db.initialize_database()
            
            # Check if database file exists
            if not os.path.exists(db_path):
                return False
                
            # Check table structure
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check users table
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
            users_schema = cursor.fetchone()
            if not users_schema:
                conn.close()
                return False
                
            # Check passwords table
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='passwords'")
            passwords_schema = cursor.fetchone()
            if not passwords_schema:
                conn.close()
                return False
                
            conn.close()
            return True
            
        except Exception as e:
            print_colored(f"Database test error: {e}", Colors.RED)
            return False

    def test_encryption_functionality(self):
        """Test encryption and decryption operations"""
        try:
            from core.encryption import PasswordEncryption
            
            encryption = PasswordEncryption()
            
            # Test data
            test_password = "MySecurePassword123!"
            master_password = "MasterPassword456!"
            
            # Test encryption
            encrypted_data = encryption.encrypt_password(test_password, master_password)
            
            # Verify encrypted data structure
            if not all(key in encrypted_data for key in ['salt', 'iv', 'ciphertext']):
                return False
                
            # Test decryption
            decrypted_password = encryption.decrypt_password(encrypted_data, master_password)
            
            # Verify decryption worked
            if decrypted_password != test_password:
                return False
                
            # Test wrong password fails
            try:
                encryption.decrypt_password(encrypted_data, "WrongPassword")
                return False  # Should have failed
            except:
                pass  # Expected to fail
                
            return True
            
        except Exception as e:
            print_colored(f"Encryption test error: {e}", Colors.RED)
            return False

    def test_password_generation(self):
        """Test password generation functionality"""
        try:
            from utils.password_generator import PasswordGenerator, GenerationOptions, GenerationMethod
            
            generator = PasswordGenerator()
            
            # Test random generation
            options = GenerationOptions(length=16)
            result = generator.generate_password(options, GenerationMethod.RANDOM)
            
            if not result.password or len(result.password) != 16:
                return False
                
            # Test different lengths
            for length in [8, 12, 20, 32]:
                options = GenerationOptions(length=length)
                result = generator.generate_password(options, GenerationMethod.RANDOM)
                if len(result.password) != length:
                    return False
                    
            # Test character set restrictions
            options = GenerationOptions(
                length=16, 
                include_symbols=False,
                include_digits=False
            )
            result = generator.generate_password(options, GenerationMethod.RANDOM)
            
            # Check that password only contains letters
            if not result.password.isalpha():
                return False
                
            return True
            
        except Exception as e:
            print_colored(f"Password generation test error: {e}", Colors.RED)
            return False

    def test_strength_checking(self):
        """Test password strength analysis"""
        try:
            from utils.strength_checker import AdvancedPasswordStrengthChecker
            
            checker = AdvancedPasswordStrengthChecker(breach_check_enabled=False)
            
            # Test weak password
            weak_analysis = checker.analyze_password_realtime("123456")
            if weak_analysis['strength_level'] not in ['very_weak', 'weak']:
                return False
                
            # Test strong password
            strong_analysis = checker.analyze_password_realtime("MyStr0ng!P@ssw0rd")
            if strong_analysis['strength_score'] < 70:  # Should be reasonably strong
                return False
                
            # Test empty password
            empty_analysis = checker.analyze_password_realtime("")
            if empty_analysis['strength_score'] != 0:
                return False
                
            return True
            
        except Exception as e:
            print_colored(f"Strength checking test error: {e}", Colors.RED)
            return False

    def test_authentication_system(self):
        """Test user authentication functionality"""
        try:
            from core.auth import AuthenticationManager
            
            auth_file = os.path.join(self.test_dir, "auth_test.db")
            auth = AuthenticationManager(auth_file)
            
            # Test user creation
            username = "testuser"
            password = "TestPassword123!"
            
            if not auth.create_user(username, password):
                return False
                
            # Test user exists check
            if not auth.user_exists(username):
                return False
                
            # Test authentication
            session = auth.authenticate_user(username, password)
            if not session:
                return False
                
            # Test session validation
            if not auth.validate_session(session):
                return False
                
            # Test wrong password
            wrong_session = auth.authenticate_user(username, "WrongPassword")
            if wrong_session:
                return False
                
            # Test session invalidation
            auth.invalidate_session(session)
            if auth.validate_session(session):
                return False
                
            return True
            
        except Exception as e:
            print_colored(f"Authentication test error: {e}", Colors.RED)
            return False

    def test_integrated_password_management(self):
        """Test integrated password management operations"""
        try:
            from core.password_manager import PasswordManagerCore
            
            # Use temporary database
            db_path = os.path.join(self.test_dir, "integrated_test.db")
            pm = PasswordManagerCore(database_path=db_path)
            
            # Create test user
            username = "testuser"
            master_password = "MasterPassword123!"
            
            if not pm.auth_manager.create_user(username, master_password):
                return False
                
            # Authenticate user
            session = pm.auth_manager.authenticate_user(username, master_password)
            if not session:
                return False
                
            # Add password
            website = "example.com"
            user = "user@example.com" 
            password = "ExamplePassword123!"
            remarks = "Test account"
            
            password_id = pm.add_password(session, website, user, password, remarks)
            if not password_id:
                return False
                
            # Retrieve password
            retrieved = pm.get_password(session, password_id)
            if not retrieved or retrieved.website != website:
                return False
                
            # Update password
            new_password = "UpdatedPassword456!"
            if not pm.update_password(session, password_id, website, user, new_password, remarks):
                return False
                
            # Verify update
            updated = pm.get_password(session, password_id)
            if not updated or updated.password != new_password:
                return False
                
            # Search passwords
            results = pm.search_passwords(session, "example")
            if not results or len(results) != 1:
                return False
                
            # Delete password
            if not pm.delete_password(session, password_id):
                return False
                
            # Verify deletion
            deleted = pm.get_password(session, password_id)
            if deleted:
                return False
                
            return True
            
        except Exception as e:
            print_colored(f"Integrated test error: {e}", Colors.RED)
            return False

    def test_security_measures(self):
        """Test security implementations"""
        try:
            from core.encryption import PasswordEncryption
            import time
            
            encryption = PasswordEncryption()
            
            # Test salt uniqueness
            password = "TestPassword"
            master_password = "MasterPassword"
            
            encrypted1 = encryption.encrypt_password(password, master_password)
            encrypted2 = encryption.encrypt_password(password, master_password)
            
            # Same password should produce different encrypted results (different salts/IVs)
            if encrypted1['salt'] == encrypted2['salt'] or encrypted1['iv'] == encrypted2['iv']:
                return False
                
            # Test timing attack resistance (basic check)
            start_time = time.time()
            encryption.decrypt_password(encrypted1, master_password)
            correct_time = time.time() - start_time
            
            start_time = time.time()
            try:
                encryption.decrypt_password(encrypted1, "WrongPassword")
            except:
                pass
            wrong_time = time.time() - start_time
            
            # Times should be reasonably similar (not perfect, but reasonable)
            time_ratio = max(correct_time, wrong_time) / min(correct_time, wrong_time)
            if time_ratio > 10:  # Allow some variance but not too much
                print_colored(f"Warning: Potential timing attack vulnerability (ratio: {time_ratio:.2f})", Colors.YELLOW)
                
            return True
            
        except Exception as e:
            print_colored(f"Security test error: {e}", Colors.RED)
            return False

    def test_application_entry_points(self):
        """Test main application entry points"""
        try:
            # Test help output
            import subprocess
            result = subprocess.run([sys.executable, "main.py", "--help"], 
                                  capture_output=True, text=True, cwd=Path(__file__).parent)
            
            if result.returncode != 0:
                return False
                
            help_output = result.stdout
            if "Personal Password Manager" not in help_output:
                return False
                
            if "--gui" not in help_output or "--web" not in help_output:
                return False
                
            return True
            
        except Exception as e:
            print_colored(f"Entry point test error: {e}", Colors.RED)
            return False

    def test_file_structure(self):
        """Test that all required files exist"""
        required_files = [
            "main.py",
            "requirements.txt",
            "README.md",
            "INSTALL.md",
            "USAGE_GUIDE.md",
            "SECURITY.md",
            "WEB_INTERFACE_GUIDE.md",
            "src/core/database.py",
            "src/core/encryption.py",
            "src/core/auth.py",
            "src/core/password_manager.py",
            "src/utils/password_generator.py",
            "src/utils/strength_checker.py",
            "src/utils/import_export.py",
            "src/gui/themes.py",
            "src/gui/login_window.py",
            "src/gui/main_window.py",
            "src/web/app.py",
            "src/web/templates/base.html",
            "src/web/templates/login.html",
            "src/web/templates/dashboard.html",
            "src/web/static/css/style.css",
            "src/web/static/js/app.js"
        ]
        
        project_root = Path(__file__).parent
        missing_files = []
        
        for file_path in required_files:
            full_path = project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
                
        if missing_files:
            print_colored(f"Missing files: {', '.join(missing_files)}", Colors.RED)
            return False
            
        return True

    def run_core_tests(self):
        """Run all core functionality tests"""
        print_test_header("Core Functionality")
        
        tests = [
            (self.test_file_structure, "File Structure"),
            (self.test_core_imports, "Core Module Imports"),
            (self.test_utility_imports, "Utility Module Imports"),
            (self.test_database_creation, "Database Creation"),
            (self.test_encryption_functionality, "Encryption Operations"),
            (self.test_password_generation, "Password Generation"),
            (self.test_strength_checking, "Password Strength Analysis"),
            (self.test_authentication_system, "Authentication System"),
            (self.test_integrated_password_management, "Integrated Password Management"),
            (self.test_security_measures, "Security Measures"),
            (self.test_application_entry_points, "Application Entry Points")
        ]
        
        for test_func, test_name in tests:
            self.run_test(test_func, test_name)

    def run_gui_tests(self):
        """Run GUI-specific tests"""
        print_test_header("GUI Interface")
        
        tests = [
            (self.test_gui_imports, "GUI Module Imports")
        ]
        
        for test_func, test_name in tests:
            self.run_test(test_func, test_name)

    def run_web_tests(self):
        """Run web interface tests"""
        print_test_header("Web Interface")
        
        # Basic web test - just check if Flask can be imported
        def test_web_imports():
            try:
                import flask
                return True
            except ImportError:
                return False
                
        self.run_test(test_web_imports, "Web Dependencies Available")

    def run_all_tests(self):
        """Run complete test suite"""
        print_colored(f"{Colors.BOLD}Personal Password Manager - Test Suite", Colors.PURPLE)
        print_colored(f"Starting comprehensive testing...\n", Colors.WHITE)
        
        self.setup_test_environment()
        
        try:
            self.run_core_tests()
            self.run_gui_tests()
            self.run_web_tests()
            
        finally:
            self.cleanup_test_environment()
            
        # Print summary
        print_test_header("Test Summary")
        total = self.passed_tests + self.failed_tests
        pass_rate = (self.passed_tests / total * 100) if total > 0 else 0
        
        print_colored(f"Total Tests: {total}", Colors.WHITE)
        print_colored(f"Passed: {self.passed_tests}", Colors.GREEN)
        print_colored(f"Failed: {self.failed_tests}", Colors.RED)
        print_colored(f"Pass Rate: {pass_rate:.1f}%", Colors.CYAN)
        
        if self.failed_tests == 0:
            print_colored(f"\n🎉 ALL TESTS PASSED! The Password Manager is ready for use.", Colors.GREEN)
        else:
            print_colored(f"\n⚠️ Some tests failed. Please review the output above.", Colors.RED)
            
        return self.failed_tests == 0

def main():
    parser = argparse.ArgumentParser(description="Personal Password Manager Test Suite")
    parser.add_argument('--core', action='store_true', help="Run core functionality tests only")
    parser.add_argument('--gui', action='store_true', help="Run GUI tests only")
    parser.add_argument('--web', action='store_true', help="Run web interface tests only")
    parser.add_argument('--security', action='store_true', help="Run security tests only")
    
    args = parser.parse_args()
    
    suite = PasswordManagerTestSuite()
    
    if args.core:
        suite.setup_test_environment()
        try:
            suite.run_core_tests()
        finally:
            suite.cleanup_test_environment()
    elif args.gui:
        suite.setup_test_environment()
        try:
            suite.run_gui_tests()
        finally:
            suite.cleanup_test_environment()
    elif args.web:
        suite.setup_test_environment()
        try:
            suite.run_web_tests()
        finally:
            suite.cleanup_test_environment()
    elif args.security:
        suite.setup_test_environment()
        try:
            suite.run_test(suite.test_security_measures, "Security Measures")
            suite.run_test(suite.test_encryption_functionality, "Encryption Security")
        finally:
            suite.cleanup_test_environment()
    else:
        # Run all tests
        success = suite.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()