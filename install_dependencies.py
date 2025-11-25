#!/usr/bin/env python3
"""
Personal Password Manager v2.2.0 - Dependency Installer
========================================================

This script automatically checks and installs all required dependencies
for the Password Manager application on a new PC.

Features:
- Automatic installation of all missing packages
- No user prompts - fully automated
- Progress tracking and detailed logging
- Verifies Python version compatibility
- Creates required directories
- Comprehensive error handling

Usage: python install_dependencies.py
"""

import sys
import os
import subprocess
import platform
from pathlib import Path
from typing import List, Tuple, Dict

# Minimum Python version required
MIN_PYTHON_VERSION = (3, 8)

def print_header(message: str) -> None:
    """Print a formatted header"""
    separator = "=" * 60
    print(f"\n{separator}")
    print(f"  {message}")
    print(f"{separator}\n")

def print_step(message: str) -> None:
    """Print a step message"""
    print(f"[STEP] {message}")

def print_success(message: str) -> None:
    """Print a success message"""
    print(f"[OK] {message}")

def print_error(message: str) -> None:
    """Print an error message"""
    print(f"[ERROR] {message}")

def print_warning(message: str) -> None:
    """Print a warning message"""
    print(f"[WARNING] {message}")

def check_python_version() -> bool:
    """
    Verify Python version meets minimum requirements

    Returns:
        bool: True if version is compatible
    """
    print_step("Checking Python version...")

    current = sys.version_info
    required = MIN_PYTHON_VERSION

    print(f"  Current: Python {current.major}.{current.minor}.{current.micro}")
    print(f"  Required: Python {required[0]}.{required[1]}+")

    if current >= required:
        print_success("Python version is compatible")
        return True
    else:
        print_error(f"Python {required[0]}.{required[1]}+ is required")
        print_error(f"Please upgrade from https://www.python.org/downloads/")
        return False

def check_pip() -> bool:
    """
    Verify pip is available

    Returns:
        bool: True if pip is available
    """
    print_step("Checking pip availability...")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print(f"  {result.stdout.strip()}")
            print_success("pip is available")
            return True
        else:
            print_error("pip is not working properly")
            return False

    except Exception as e:
        print_error(f"pip check failed: {e}")
        print_error("Install pip from: https://pip.pypa.io/en/stable/installation/")
        return False

def upgrade_pip() -> bool:
    """
    Upgrade pip to latest version

    Returns:
        bool: True if upgrade successful
    """
    print_step("Upgrading pip to latest version...")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            print_success("pip upgraded successfully")
            return True
        else:
            print_warning("pip upgrade failed, continuing with existing version")
            return True  # Non-critical, continue anyway

    except Exception as e:
        print_warning(f"pip upgrade failed: {e}, continuing anyway")
        return True  # Non-critical

def parse_requirements() -> List[str]:
    """
    Parse requirements.txt and return list of packages

    Returns:
        List[str]: List of package specifications (e.g., "cryptography>=41.0.0")
    """
    print_step("Reading requirements.txt...")

    requirements_file = Path(__file__).parent / "requirements.txt"

    if not requirements_file.exists():
        print_error("requirements.txt not found!")
        return []

    packages = []

    try:
        with open(requirements_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Remove inline comments
                if '#' in line:
                    line = line.split('#')[0].strip()

                if line:
                    packages.append(line)

        print(f"  Found {len(packages)} packages to check")
        return packages

    except Exception as e:
        print_error(f"Failed to read requirements.txt: {e}")
        return []

def check_package_installed(package_spec: str) -> Tuple[bool, str]:
    """
    Check if a package is installed

    Args:
        package_spec: Package specification (e.g., "cryptography>=41.0.0")

    Returns:
        Tuple[bool, str]: (is_installed, package_name)
    """
    # Extract package name from spec
    package_name = package_spec
    for separator in ['>=', '==', '<=', '>', '<', '~=']:
        if separator in package_name:
            package_name = package_name.split(separator)[0].strip()
            break

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True,
            timeout=10
        )

        return result.returncode == 0, package_name

    except Exception:
        return False, package_name

def install_package(package_spec: str) -> bool:
    """
    Install a single package

    Args:
        package_spec: Package specification to install

    Returns:
        bool: True if installation successful
    """
    try:
        print(f"  Installing {package_spec}...")

        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_spec],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout per package
        )

        if result.returncode == 0:
            print_success(f"Installed {package_spec}")
            return True
        else:
            print_error(f"Failed to install {package_spec}")
            if result.stderr:
                print(f"  Error: {result.stderr[:200]}")
            return False

    except subprocess.TimeoutExpired:
        print_error(f"Installation timeout for {package_spec}")
        return False
    except Exception as e:
        print_error(f"Installation error for {package_spec}: {e}")
        return False

def install_all_dependencies() -> Tuple[int, int, int]:
    """
    Check and install all dependencies from requirements.txt

    Returns:
        Tuple[int, int, int]: (total, already_installed, newly_installed)
    """
    print_header("DEPENDENCY INSTALLATION")

    packages = parse_requirements()

    if not packages:
        print_error("No packages found in requirements.txt")
        return 0, 0, 0

    total = len(packages)
    already_installed = 0
    newly_installed = 0
    failed = []

    print_step(f"Checking and installing {total} packages...\n")

    for i, package_spec in enumerate(packages, 1):
        print(f"[{i}/{total}] Processing {package_spec}...")

        # Check if already installed
        is_installed, package_name = check_package_installed(package_spec)

        if is_installed:
            print_success(f"{package_name} is already installed")
            already_installed += 1
        else:
            # Install the package
            if install_package(package_spec):
                newly_installed += 1
            else:
                failed.append(package_spec)

        print()  # Empty line for readability

    # Summary
    print_header("INSTALLATION SUMMARY")
    print(f"Total packages: {total}")
    print(f"Already installed: {already_installed}")
    print(f"Newly installed: {newly_installed}")
    print(f"Failed: {len(failed)}")

    if failed:
        print_error("The following packages failed to install:")
        for package in failed:
            print(f"  - {package}")
        print("\nYou can try installing them manually:")
        print(f"  pip install {' '.join(failed)}")

    return total, already_installed, newly_installed

def create_required_directories() -> bool:
    """
    Create required application directories

    Returns:
        bool: True if all directories created successfully
    """
    print_step("Creating required directories...")

    directories = [
        "data",
        "backups",
        "Code Explanations",
        "logs"
    ]

    success = True

    for dir_name in directories:
        dir_path = Path(dir_name)
        try:
            dir_path.mkdir(exist_ok=True)
            print(f"  [OK] {dir_name}/")
        except Exception as e:
            print_error(f"Failed to create {dir_name}/: {e}")
            success = False

    if success:
        print_success("All directories created")

    return success

def verify_installation() -> bool:
    """
    Verify critical packages can be imported

    Returns:
        bool: True if all critical imports work
    """
    print_step("Verifying critical package imports...")

    critical_imports = {
        'cryptography': 'cryptography.fernet',
        'bcrypt': 'bcrypt',
        'customtkinter': 'customtkinter',
        'PIL': 'PIL',
        'pyperclip': 'pyperclip',
        'zxcvbn': 'zxcvbn',
        'flask': 'flask',
    }

    success = True

    for display_name, import_name in critical_imports.items():
        try:
            __import__(import_name)
            print(f"  [OK] {display_name}")
        except ImportError as e:
            print_error(f"Failed to import {display_name}: {e}")
            success = False

    if success:
        print_success("All critical packages verified")
    else:
        print_error("Some critical packages failed to import")

    return success

def main() -> int:
    """
    Main installation routine

    Returns:
        int: Exit code (0 = success, 1 = failure)
    """
    print_header("Personal Password Manager v2.2.0 - Dependency Installer")
    print("This script will automatically install all required dependencies.\n")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}\n")

    # Step 1: Check Python version
    if not check_python_version():
        return 1

    print()

    # Step 2: Check pip
    if not check_pip():
        return 1

    print()

    # Step 3: Upgrade pip
    upgrade_pip()

    print()

    # Step 4: Install all dependencies
    total, already_installed, newly_installed = install_all_dependencies()

    if total == 0:
        return 1

    print()

    # Step 5: Create required directories
    create_required_directories()

    print()

    # Step 6: Verify installation
    verification_success = verify_installation()

    print()

    # Final summary
    print_header("SETUP COMPLETE")

    if verification_success:
        print_success("All dependencies installed and verified!")
        print_success("Your system is ready to run the Password Manager.")
        print("\nTo start the application, run:")
        print("  python main.py")
        print("\nFor first-time setup:")
        print("  1. Run 'python main.py'")
        print("  2. Create a new user account")
        print("  3. Set a strong master password")
        print("\nFor more information, see README.md")
        return 0
    else:
        print_error("Installation completed with some issues.")
        print_error("Some packages may need manual installation.")
        print("\nTry running:")
        print("  python check_dependencies.py")
        print("\nFor detailed diagnostics.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()

        print("\n" + "=" * 60)
        if exit_code == 0:
            print("Press Enter to exit...")
        else:
            print("Installation encountered errors. Press Enter to exit...")

        try:
            input()
        except:
            pass

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
