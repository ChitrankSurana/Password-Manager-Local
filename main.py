#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Personal Password Manager - Main Entry Point
============================================

This is the main entry point for the Personal Password Manager application.
It provides options to run either the GUI interface or the web interface,
and handles initial setup and configuration.

Features:
- Multi-user password management with strong encryption
- Modern GUI interface with Windows 11 styling and dark mode
- Web interface for browser-based access
- Secure local SQLite database storage
- Password generation and strength checking
- Backup and restore capabilities
- Import/Export functionality

Usage:
    python main.py [--gui|--web|--check-deps]
    
    --gui        Launch GUI interface (default)
    --web        Launch web interface
    --check-deps Run dependency checker only
    --help       Show this help message

Security Note:
    All passwords are encrypted using AES-256 with PBKDF2 key derivation.
    The master password is never stored in plain text.
    Database files are stored locally for maximum security.

Author: Personal Password Manager
Version: 1.0.0
"""

import sys
import os
import argparse
from pathlib import Path

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def print_banner():
    """Print application banner and basic information"""
    banner = """
    ==============================================================
                   Personal Password Manager                     
                        Version 1.0.0                          
                                                                  
    A secure, local password manager with modern GUI and       
    web interfaces, featuring strong encryption and backup     
    capabilities for personal use.                              
                                                                  
    * AES-256 Encryption  * Modern GUI  * Web Interface         
    * Local Storage      * Password Gen  * Import/Export         
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
        directories = ['data', 'backups', 'Code Explanations']
        
        for directory in directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"[OK] Created directory: {directory}")
        
        # Check write permissions
        for directory in directories:
            dir_path = Path(directory)
            test_file = dir_path / '.write_test'
            try:
                test_file.write_text('test')
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

def launch_gui():
    """
    Launch the GUI interface
    
    This function starts the main GUI application with CustomTkinter,
    featuring a modern Windows 11 style interface with dark mode support.
    """
    print("Starting GUI interface...")
    
    try:
        # Import GUI modules
        import customtkinter as ctk
        from src.gui.login_window import LoginWindow
        from src.gui.main_window import MainWindow
        from src.gui.themes import setup_theme
        from src.core.auth import AuthenticationManager
        from src.core.password_manager import PasswordManagerCore
        
        # Initialize theme system
        setup_theme()
        
        # Create a hidden root window for proper Tkinter application structure
        root = ctk.CTk()
        root.withdraw()
        
        # Initialize managers
        auth_manager = AuthenticationManager()
        password_manager = PasswordManagerCore(auth_manager=auth_manager)

        main_window_ref = [None]  # Use list to allow modification in nested function
        login_window_ref = [None]  # Use list to allow modification in nested function

        def show_login_window():
            """Show the login window"""
            def on_login_success(session_id: str, username: str, master_password: str = None):
                """Callback when login is successful"""
                # Cache master password for convenience (if provided)
                if master_password:
                    password_manager._cache_master_password(session_id, master_password)

                # Close the login window
                try:
                    if login_window_ref[0]:
                        login_window_ref[0].destroy()
                        login_window_ref[0] = None
                except:
                    pass

                # Create main window with logout callback
                def on_logout():
                    """Callback when user logs out - reopen login window"""
                    show_login_window()

                main_window = MainWindow(
                    session_id=session_id,
                    username=username,
                    password_manager=password_manager,
                    auth_manager=auth_manager,
                    parent=root,
                    on_logout_callback=on_logout
                )
                main_window_ref[0] = main_window

                # When main window is closed via X button, logout and quit
                def on_main_window_close():
                    try:
                        auth_manager.logout_user(session_id)
                    except:
                        pass
                    try:
                        main_window.destroy()
                    except:
                        pass
                    root.quit()

                main_window.protocol("WM_DELETE_WINDOW", on_main_window_close)

            def on_login_window_close():
                """Handle login window close - quit application"""
                root.quit()

            # Create login window
            login_window = LoginWindow(auth_manager, on_login_success, parent=root)
            login_window.protocol("WM_DELETE_WINDOW", on_login_window_close)
            login_window_ref[0] = login_window

        # Start by showing the login window
        show_login_window()
        
        # Start the application
        root.mainloop()
        
    except ImportError as e:
        print(f"[ERROR] GUI dependencies not found: {e}")
        print("Please run: python check_dependencies.py")
        return False
    except Exception as e:
        print(f"[ERROR] GUI startup failed: {e}")
        return False
    
    return True

def launch_web():
    """
    Launch the web interface
    
    This function starts the Flask web server for browser-based access
    to the password manager.
    """
    print("Starting web interface...")
    
    try:
        # Import web modules
        from src.web.app import create_app
        
        # Create Flask application
        app = create_app()
        
        # Configuration for development
        app.config['DEBUG'] = False  # Set to False for production
        app.config['HOST'] = '127.0.0.1'  # Localhost only for security
        app.config['PORT'] = 5000
        
        print(f"Web interface starting at http://{app.config['HOST']}:{app.config['PORT']}")
        print("Access the password manager through your web browser")
        print("Press Ctrl+C to stop the server")
        
        # Start the web server
        app.run(
            host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG'],
            threaded=True
        )
        
    except ImportError as e:
        print(f"[ERROR] Web dependencies not found: {e}")
        print("Please run: python check_dependencies.py")
        return False
    except Exception as e:
        print(f"[ERROR] Web server startup failed: {e}")
        return False
    
    return True

def show_help():
    """Display help information"""
    help_text = """
Personal Password Manager - Help
===============================

USAGE:
    python main.py [options]

OPTIONS:
    --gui        Launch GUI interface (default)
    --web        Launch web interface  
    --check-deps Run dependency checker only
    --help       Show this help message

EXAMPLES:
    python main.py                    # Start GUI interface
    python main.py --gui              # Start GUI interface
    python main.py --web              # Start web interface
    python main.py --check-deps       # Check dependencies

FIRST TIME SETUP:
    1. Run dependency checker:        python main.py --check-deps
    2. Install missing packages:      pip install -r requirements.txt
    3. Start the application:         python main.py

INTERFACES:
    GUI Interface:
    - Modern Windows 11 style interface
    - Dark mode support
    - Native desktop application feel
    - Recommended for daily use

    Web Interface:
    - Browser-based access
    - Responsive design
    - Access from localhost only (127.0.0.1:5000)
    - Good for remote access via SSH tunneling

SECURITY:
    - All passwords encrypted with AES-256
    - PBKDF2 key derivation
    - Local database storage only
    - No network connections (except optional cloud sync)
    - Master password never stored

FILES:
    data/           Database storage directory
    backups/        Backup files directory
    main.py         Main application entry point
    requirements.txt Python dependencies

For more information, see README.md
    """
    print(help_text)

def parse_arguments():
    """
    Parse command line arguments
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Personal Password Manager - Secure local password management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    Start GUI interface (default)
  python main.py --gui              Start GUI interface
  python main.py --web              Start web interface
  python main.py --check-deps       Check dependencies only

For more help: python main.py --help
        """
    )
    
    # Create mutually exclusive group for interface options
    interface_group = parser.add_mutually_exclusive_group()
    
    interface_group.add_argument(
        '--gui', 
        action='store_true',
        help='Launch GUI interface (default)'
    )
    
    interface_group.add_argument(
        '--web', 
        action='store_true',
        help='Launch web interface'
    )
    
    interface_group.add_argument(
        '--check-deps', 
        action='store_true',
        help='Run dependency checker only'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no interface specified, default to GUI
    if not any([args.gui, args.web, args.check_deps]):
        args.gui = True
    
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
        
        # Check dependencies before starting interfaces
        print("Performing quick dependency check...")
        
        # Basic dependency check (faster than full check)
        try:
            import customtkinter
            import cryptography
            import flask
            print("[OK] Core dependencies available")
        except ImportError as e:
            print(f"[ERROR] Missing core dependency: {e}")
            print("Please run: python main.py --check-deps")
            return 1
        
        # Launch appropriate interface
        success = False
        
        if args.gui:
            success = launch_gui()
        elif args.web:
            success = launch_web()
        
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