#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Personal Password Manager - Main Entry Point
============================================

This is the main entry point for the Personal Password Manager application.
It launches the Flet-based UI in either desktop window mode (default) or
web browser mode (--web flag).

Usage:
    python main.py [--desktop|--web|--check-deps]

    --desktop    Launch Flet desktop window (default)
    --web        Launch Flet web interface in browser
    --check-deps Run dependency checker only
    --help       Show this help message

Security Note:
    All passwords are encrypted using AES-256-GCM with PBKDF2 key derivation
    (600,000 iterations). The master password is never stored in plain text.
    Database files are stored locally for maximum security.

Author: Personal Password Manager
Version: 3.0.0
"""

import argparse
import sys
from pathlib import Path

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def print_banner():
    """Print application banner and basic information"""
    banner = """
    ==============================================================
                   Personal Password Manager
                        Version 3.0.0

    A secure, local password manager with AES-256-GCM
    encryption, featuring desktop and web interfaces
    powered by Flet (Material Design 3).

    * AES-256-GCM       * Desktop + Web   * Password Gen
    * PBKDF2 (600k)     * Local Storage    * Import/Export
    ==============================================================
    """
    print(banner)


def check_dependencies():
    """
    Check if all required dependencies are installed

    Returns:
        bool: True if all dependencies are satisfied, False otherwise
    """
    print("Checking dependencies...")

    try:
        # Import dependency checker
        import check_dependencies

        # Run the dependency check
        result = check_dependencies.main()
        return result == 0

    except ImportError:
        print("[ERROR] Dependency checker not found!")
        return False
    except Exception as e:
        print(f"[ERROR] Error during dependency check: {e}")
        return False


def setup_environment():
    """
    Set up the application environment and create necessary directories

    Returns:
        bool: True if setup successful, False otherwise
    """
    try:
        # Ensure required directories exist
        directories = ["data", "backups", "exports", "Code Explanations"]

        for directory in directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"[OK] Created directory: {directory}")

        # Check write permissions
        for directory in directories:
            dir_path = Path(directory)
            test_file = dir_path / ".write_test"
            try:
                test_file.write_text("test")
                test_file.unlink()
            except PermissionError:
                print(f"[ERROR] No write permission for directory: {directory}")
                return False
            except Exception as e:
                print(f"[ERROR] Permission check failed for {directory}: {e}")
                return False

        print("[OK] Environment setup complete")
        return True

    except Exception as e:
        print(f"[ERROR] Environment setup failed: {e}")
        return False


def launch_flet_desktop():
    """
    Launch the Flet desktop application (default mode).

    Opens a native desktop window powered by Flet / Material Design 3.
    """
    print("Starting Flet desktop interface...")

    try:
        from src.flet_app.app import run_desktop
        run_desktop()
    except ImportError as e:
        print(f"[ERROR] Flet not installed: {e}")
        print("Please run: pip install flet>=0.25.0")
        return False
    except Exception as e:
        print(f"[ERROR] Flet desktop startup failed: {e}")
        return False

    return True


def launch_flet_web():
    """
    Launch the Flet web application.

    Opens the password manager in the user's default web browser.
    Binds to 127.0.0.1 (localhost) only for security.
    """
    print("Starting Flet web interface...")

    try:
        from src.flet_app.app import run_web
        print("Web interface starting at http://127.0.0.1:5000")
        print("Press Ctrl+C to stop the server")
        run_web(host="127.0.0.1", port=5000)
    except ImportError as e:
        print(f"[ERROR] Flet not installed: {e}")
        print("Please run: pip install flet>=0.25.0")
        return False
    except Exception as e:
        print(f"[ERROR] Flet web startup failed: {e}")
        return False

    return True


def parse_arguments():
    """
    Parse command line arguments.

    The default mode (no flags) launches the Flet desktop window.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Personal Password Manager - Secure local password management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    Start Flet desktop (default)
  python main.py --desktop          Start Flet desktop
  python main.py --web              Start Flet web interface
  python main.py --check-deps       Check dependencies only

For more help: python main.py --help
        """,
    )

    # Create mutually exclusive group for interface options
    interface_group = parser.add_mutually_exclusive_group()

    interface_group.add_argument(
        "--desktop", action="store_true", help="Launch Flet desktop window (default)"
    )

    interface_group.add_argument(
        "--web", action="store_true", help="Launch Flet web interface in browser"
    )

    interface_group.add_argument(
        "--check-deps", action="store_true", help="Run dependency checker only"
    )

    # Parse arguments
    args = parser.parse_args()

    # If no interface specified, default to Flet desktop
    if not any([args.desktop, args.web, args.check_deps]):
        args.desktop = True

    return args


def main():
    """
    Main application entry point

    Handles command line arguments and starts the appropriate interface.

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        # Parse command line arguments
        args = parse_arguments()

        # Show banner (unless just checking dependencies)
        if not args.check_deps:
            print_banner()

        # Handle dependency check only
        if args.check_deps:
            return 0 if check_dependencies() else 1

        # Set up environment
        if not setup_environment():
            print("[ERROR] Environment setup failed. Please check permissions.")
            return 1

        # Launch appropriate interface
        success = False

        if args.desktop:
            success = launch_flet_desktop()
        elif args.web:
            success = launch_flet_web()

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user. Goodbye!")
        return 0
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        print("For help, run: python main.py --help")
        return 1


if __name__ == "__main__":
    # Set the exit code based on the main function result
    sys.exit(main())
