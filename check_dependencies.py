#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dependency Checker for Personal Password Manager
===============================================

This script verifies that all required software dependencies are installed
on the system before running the password manager application.

It checks for:
1. Python version compatibility (3.8+)
2. Required Python packages from requirements.txt
3. System-level dependencies
4. Database file permissions
5. Optional cloud sync dependencies

Usage: python check_dependencies.py
"""

import sys
import os
import subprocess
import importlib
import platform
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Enable Windows console color support
if platform.system() == "Windows":
    try:
        # Enable ANSI color codes on Windows 10+
        os.system('color')
        # Alternative method for older Windows versions
        import colorama
        colorama.init()
    except ImportError:
        # colorama not available, colors will be disabled
        pass

# Color codes for terminal output
class Colors:
    """ANSI color codes for terminal output formatting"""
    if platform.system() == "Windows":
        # Use simpler colors for Windows compatibility
        GREEN = ''     # Success messages
        RED = ''       # Error messages  
        YELLOW = ''    # Warning messages
        BLUE = ''      # Info messages
        PURPLE = ''    # Header messages
        CYAN = ''      # Subheader messages
        END = ''       # Reset color
        BOLD = ''      # Bold text
    else:
        GREEN = '\033[92m'    # Success messages
        RED = '\033[91m'      # Error messages
        YELLOW = '\033[93m'   # Warning messages
        BLUE = '\033[94m'     # Info messages
        PURPLE = '\033[95m'   # Header messages
        CYAN = '\033[96m'     # Subheader messages
        END = '\033[0m'       # Reset color
        BOLD = '\033[1m'      # Bold text

def print_colored(message: str, color: str = Colors.END) -> None:
    """Print a message with color formatting"""
    if platform.system() == "Windows":
        # On Windows, add prefix instead of color codes
        if color == Colors.GREEN:
            print(f"[OK] {message}")
        elif color == Colors.RED:
            print(f"[ERROR] {message}")
        elif color == Colors.YELLOW:
            print(f"[WARNING] {message}")
        elif color == Colors.BLUE:
            print(f"[INFO] {message}")
        else:
            print(message)
    else:
        print(f"{color}{message}{Colors.END}")

def print_header(message: str) -> None:
    """Print a formatted header message"""
    print_colored(f"\n{Colors.BOLD}{'=' * len(message)}", Colors.PURPLE)
    print_colored(f"{Colors.BOLD}{message}", Colors.PURPLE)
    print_colored(f"{'=' * len(message)}", Colors.PURPLE)

def print_subheader(message: str) -> None:
    """Print a formatted subheader message"""
    print_colored(f"\n{Colors.BOLD}{message}", Colors.CYAN)
    print_colored("-" * len(message), Colors.CYAN)

def check_python_version() -> bool:
    """
    Check if Python version is 3.8 or higher
    
    Returns:
        bool: True if version is compatible, False otherwise
    """
    print_subheader("Checking Python Version")
    
    current_version = sys.version_info
    required_version = (3, 8)
    
    version_string = f"{current_version.major}.{current_version.minor}.{current_version.micro}"
    print(f"Current Python version: {version_string}")
    print(f"Required Python version: {required_version[0]}.{required_version[1]}+")
    
    if current_version >= required_version:
        print_colored("[OK] Python version is compatible", Colors.GREEN)
        return True
    else:
        print_colored("[ERROR] Python version is too old", Colors.RED)
        print_colored(f"Please upgrade to Python {required_version[0]}.{required_version[1]} or higher", Colors.YELLOW)
        print_colored("Download from: https://www.python.org/downloads/", Colors.BLUE)
        return False

def check_pip_availability() -> bool:
    """
    Check if pip is available and working
    
    Returns:
        bool: True if pip is available, False otherwise
    """
    print_subheader("Checking Package Manager (pip)")
    
    try:
        import pip
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"pip version: {result.stdout.strip()}")
            print_colored("[OK] pip is available", Colors.GREEN)
            return True
        else:
            print_colored("[ERROR] pip is not working properly", Colors.RED)
            return False
    except (ImportError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        print_colored("[ERROR] pip is not installed", Colors.RED)
        print_colored("Please install pip: https://pip.pypa.io/en/stable/installation/", Colors.YELLOW)
        return False

def get_required_packages() -> Dict[str, str]:
    """
    Parse requirements.txt to get required packages and versions
    
    Returns:
        Dict[str, str]: Dictionary mapping package names to version requirements
    """
    required_packages = {}
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print_colored("Warning: requirements.txt not found", Colors.YELLOW)
        return {}
    
    try:
        with open(requirements_file, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                # Skip comments and empty lines
                if line.startswith('#') or not line:
                    continue
                
                # Parse package name and version
                if '>=' in line:
                    package_name = line.split('>=')[0].strip()
                    version_req = line.split('>=')[1].strip()
                    # Remove comments from version requirement
                    version_req = version_req.split('#')[0].strip()
                    required_packages[package_name] = version_req
                elif '==' in line:
                    package_name = line.split('==')[0].strip()
                    version_req = line.split('==')[1].strip()
                    # Remove comments from version requirement
                    version_req = version_req.split('#')[0].strip()
                    required_packages[package_name] = version_req
                else:
                    # No version specified
                    package_name = line.strip().split('#')[0].strip()
                    required_packages[package_name] = "any"
    
    except Exception as e:
        print_colored(f"Error reading requirements.txt: {e}", Colors.RED)
    
    return required_packages

def check_package_installation(package_name: str, required_version: str = "any") -> bool:
    """
    Check if a specific package is installed with the correct version
    
    Args:
        package_name (str): Name of the package to check
        required_version (str): Required version or "any"
    
    Returns:
        bool: True if package is installed with correct version, False otherwise
    """
    try:
        # Handle package name variations
        import_name = package_name
        if package_name == "pillow":
            import_name = "PIL"
        elif package_name == "python-dateutil":
            import_name = "dateutil"
        elif package_name == "google-api-python-client":
            import_name = "googleapiclient"
        elif package_name == "flask-session":
            import_name = "flask_session"
        elif package_name == "flask-wtf":
            import_name = "flask_wtf"
        elif package_name == "pytest-mock":
            import_name = "pytest_mock"
        elif package_name == "pytest-cov":
            import_name = "pytest_cov"
        
        # Try to import the package
        module = importlib.import_module(import_name)
        
        # Check version if specified
        if required_version != "any" and hasattr(module, '__version__'):
            installed_version = module.__version__
            print(f"  {package_name}: {installed_version} (required: {required_version}+)")
            
            # Simple version comparison (works for most cases)
            try:
                from packaging import version
                if version.parse(installed_version) >= version.parse(required_version):
                    return True
                else:
                    print_colored(f"    [ERROR] Version too old", Colors.RED)
                    return False
            except ImportError:
                # If packaging is not available, assume version is OK
                print_colored(f"    ? Cannot verify version (assuming OK)", Colors.YELLOW)
                return True
        else:
            print(f"  {package_name}: installed")
            return True
            
    except ImportError:
        print(f"  {package_name}: NOT INSTALLED")
        return False
    except Exception as e:
        print(f"  {package_name}: ERROR - {e}")
        return False

def check_python_packages() -> Tuple[bool, List[str]]:
    """
    Check all required Python packages
    
    Returns:
        Tuple[bool, List[str]]: (all_installed, list_of_missing_packages)
    """
    print_subheader("Checking Python Packages")
    
    required_packages = get_required_packages()
    if not required_packages:
        print_colored("No requirements.txt found, skipping package check", Colors.YELLOW)
        return True, []
    
    missing_packages = []
    installed_count = 0
    total_count = len(required_packages)
    
    # Core packages (required)
    core_packages = [
        "cryptography", "bcrypt", "customtkinter", "pillow", 
        "pyperclip", "zxcvbn", "python-dateutil", "flask", 
        "flask-session", "jinja2", "werkzeug", "requests"
    ]
    
    # Optional packages (for advanced features)
    optional_packages = [
        "google-api-python-client", "dropbox", "pandas", 
        "openpyxl", "lxml"
    ]
    
    print("Core Packages (Required):")
    for package in core_packages:
        if package in required_packages:
            if check_package_installation(package, required_packages[package]):
                installed_count += 1
                print_colored(f"  [OK] {package}", Colors.GREEN)
            else:
                missing_packages.append(package)
                print_colored(f"  [MISSING] {package}", Colors.RED)
    
    print("\nOptional Packages (Advanced Features):")
    for package in optional_packages:
        if package in required_packages:
            if check_package_installation(package, required_packages[package]):
                print_colored(f"  [OK] {package} (optional)", Colors.GREEN)
            else:
                print_colored(f"  - {package} (optional - not installed)", Colors.YELLOW)
    
    # Check remaining packages
    other_packages = set(required_packages.keys()) - set(core_packages) - set(optional_packages)
    if other_packages:
        print("\nOther Packages:")
        for package in other_packages:
            if check_package_installation(package, required_packages[package]):
                installed_count += 1
                print_colored(f"  [OK] {package}", Colors.GREEN)
            else:
                missing_packages.append(package)
                print_colored(f"  [MISSING] {package}", Colors.RED)
    
    # Summary
    core_missing = [p for p in missing_packages if p in core_packages]
    all_core_installed = len(core_missing) == 0
    
    print(f"\nPackage Summary:")
    print(f"Core packages installed: {len(core_packages) - len(core_missing)}/{len(core_packages)}")
    print(f"Total packages checked: {total_count}")
    
    return all_core_installed, missing_packages

def check_system_requirements() -> bool:
    """
    Check system-level requirements
    
    Returns:
        bool: True if all system requirements are met, False otherwise
    """
    print_subheader("Checking System Requirements")
    
    # Check operating system
    system = platform.system()
    print(f"Operating System: {system} {platform.release()}")
    
    supported_systems = ["Windows", "Linux", "Darwin"]  # Darwin is macOS
    if system in supported_systems:
        print_colored(f"[OK] Operating system is supported", Colors.GREEN)
        system_ok = True
    else:
        print_colored(f"? Operating system may not be fully supported", Colors.YELLOW)
        system_ok = True  # Don't fail, just warn
    
    # Check available disk space
    try:
        import shutil
        free_space = shutil.disk_usage(".").free / (1024**3)  # GB
        print(f"Available disk space: {free_space:.1f} GB")
        
        if free_space >= 1.0:  # At least 1 GB free space
            print_colored("[OK] Sufficient disk space available", Colors.GREEN)
            space_ok = True
        else:
            print_colored("[WARNING] Low disk space - may cause issues with database and backups", Colors.YELLOW)
            space_ok = True  # Don't fail, just warn
    except Exception as e:
        print_colored(f"? Could not check disk space: {e}", Colors.YELLOW)
        space_ok = True
    
    return system_ok and space_ok

def check_permissions() -> bool:
    """
    Check file system permissions for required directories
    
    Returns:
        bool: True if all permissions are correct, False otherwise
    """
    print_subheader("Checking File Permissions")
    
    # Directories that need to be writable
    required_dirs = ["data", "backups", "Code Explanations"]
    
    permissions_ok = True
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        
        try:
            # Create directory if it doesn't exist
            dir_path.mkdir(exist_ok=True)
            
            # Test write permission
            test_file = dir_path / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()  # Delete test file
            
            print_colored(f"[OK] {dir_name}/ is writable", Colors.GREEN)
            
        except PermissionError:
            print_colored(f"[ERROR] {dir_name}/ is not writable", Colors.RED)
            permissions_ok = False
        except Exception as e:
            print_colored(f"? {dir_name}/ permission check failed: {e}", Colors.YELLOW)
    
    return permissions_ok

def install_missing_packages(missing_packages: List[str]) -> None:
    """
    Offer to install missing packages
    
    Args:
        missing_packages (List[str]): List of package names to install
    """
    if not missing_packages:
        return
    
    print_subheader("Installing Missing Packages")
    print(f"The following packages are missing: {', '.join(missing_packages)}")
    
    try:
        response = input("Would you like to install them now? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            print("Installing packages...")
            
            for package in missing_packages:
                print(f"Installing {package}...")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", package
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print_colored(f"[OK] {package} installed successfully", Colors.GREEN)
                else:
                    print_colored(f"[ERROR] Failed to install {package}", Colors.RED)
                    print(f"Error: {result.stderr}")
        else:
            print("Installation skipped.")
            print_colored("Manual installation command:", Colors.BLUE)
            print_colored(f"pip install {' '.join(missing_packages)}", Colors.BLUE)
    
    except KeyboardInterrupt:
        print("\nInstallation cancelled.")
    except Exception as e:
        print_colored(f"Installation error: {e}", Colors.RED)

def generate_dependency_report() -> str:
    """
    Generate a detailed dependency report
    
    Returns:
        str: Formatted report string
    """
    report = []
    report.append("DEPENDENCY CHECK REPORT")
    report.append("=" * 50)
    report.append(f"Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Python Version: {sys.version}")
    report.append(f"Platform: {platform.platform()}")
    report.append("")
    
    # Add check results here
    # This would be called from main() with results
    
    return "\n".join(report)

def main() -> int:
    """
    Main function to run all dependency checks
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    print_colored("Personal Password Manager - Dependency Checker", Colors.PURPLE + Colors.BOLD)
    print_colored("This tool will verify all required dependencies are installed.\n", Colors.BLUE)
    
    all_checks_passed = True
    
    # Check Python version
    if not check_python_version():
        all_checks_passed = False
    
    # Check pip
    if not check_pip_availability():
        all_checks_passed = False
        return 1  # Cannot continue without pip
    
    # Check Python packages
    packages_ok, missing_packages = check_python_packages()
    if not packages_ok:
        all_checks_passed = False
        
        # Offer to install missing packages
        if missing_packages:
            install_missing_packages(missing_packages)
            
            # Re-check after installation attempt
            print_colored("\nRe-checking packages after installation...", Colors.BLUE)
            packages_ok, still_missing = check_python_packages()
            if packages_ok:
                print_colored("[OK] All core packages are now installed!", Colors.GREEN)
                all_checks_passed = True
            else:
                print_colored(f"[ERROR] Some packages still missing: {', '.join(still_missing)}", Colors.RED)
    
    # Check system requirements
    if not check_system_requirements():
        all_checks_passed = False
    
    # Check permissions
    if not check_permissions():
        all_checks_passed = False
    
    # Final summary
    print_header("DEPENDENCY CHECK SUMMARY")
    
    if all_checks_passed:
        print_colored("[SUCCESS] ALL CHECKS PASSED!", Colors.GREEN + Colors.BOLD)
        print_colored("Your system is ready to run the Password Manager!", Colors.GREEN)
        print_colored("\nTo start the application, run:", Colors.BLUE)
        print_colored("python main.py", Colors.BLUE + Colors.BOLD)
    else:
        print_colored("[FAILED] SOME CHECKS FAILED", Colors.RED + Colors.BOLD)
        print_colored("Please resolve the issues above before running the application.", Colors.RED)
        print_colored("\nFor help, check the README.md file or the documentation.", Colors.YELLOW)
    
    return 0 if all_checks_passed else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_colored("\n\nDependency check interrupted by user.", Colors.YELLOW)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\nUnexpected error during dependency check: {e}", Colors.RED)
        sys.exit(1)