#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Personal Password Manager - Enhanced Main Entry Point
====================================================

Enhanced version of the main application entry point that integrates the new
password viewing and deletion features with comprehensive service management.

This enhanced version includes:
- ServiceIntegrator for centralized service coordination
- Enhanced password viewing with time-based authentication
- Comprehensive deletion confirmation workflows
- Advanced settings management with user preferences
- Security audit logging and monitoring

New Features in Version 2.0:
- PasswordViewAuthService: Time-based password viewing with master password authentication
- SettingsService: Comprehensive user preference management with validation
- SecurityAuditLogger: Complete security event logging and monitoring
- Enhanced UI components with modern security workflows

Author: Personal Password Manager Enhancement Team
Version: 2.0.0
Date: September 21, 2025
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def print_banner():
    """Print enhanced application banner with new features"""
    banner = """
    ==============================================================
                   Personal Password Manager                     
                        Version 2.0.0 Enhanced                          
                                                                  
    A secure, local password manager with advanced security    
    features, time-based password viewing, and comprehensive   
    audit logging for enterprise-grade password management.    
                                                                  
    NEW in v2.0:                                               
    * Time-based Password Viewing  * Enhanced Deletion Security 
    * Comprehensive Settings UI    * Security Audit Logging    
    * Master Password Caching      * Advanced Service Architecture
    * Real-time Permission Management * Configurable Security Levels
    ==============================================================
    """
    print(banner)

def setup_logging():
    """Setup comprehensive logging for the enhanced application"""
    try:
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "password_manager.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Set specific log levels for components
        logging.getLogger('src.core.service_integration').setLevel(logging.INFO)
        logging.getLogger('src.core.view_auth_service').setLevel(logging.INFO)
        logging.getLogger('src.core.settings_service').setLevel(logging.INFO)
        logging.getLogger('src.core.security_audit_logger').setLevel(logging.INFO)
        
        logging.info("Enhanced logging system initialized")
        return True
        
    except Exception as e:
        print(f"[WARNING] Could not setup enhanced logging: {e}")
        print("Continuing with basic logging...")
        return False

def check_enhanced_dependencies():
    """Check if enhanced feature dependencies are available"""
    print("Checking enhanced feature dependencies...")
    
    required_packages = [
        'customtkinter',    # GUI framework
        'cryptography',     # Encryption
        'sqlite3',          # Database (built-in)
        'threading',        # Multi-threading (built-in) 
        'json',             # JSON handling (built-in)
        'datetime',         # Date/time (built-in)
        'pathlib',          # Path handling (built-in)
        'hashlib',          # Hashing (built-in)
        'secrets',          # Secure random (built-in)
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"[ERROR] Missing enhanced dependencies: {', '.join(missing_packages)}")
        return False
    
    print("[OK] All enhanced dependencies available")
    return True

def initialize_enhanced_services(password_manager, auth_manager):
    """
    Initialize enhanced services with proper integration
    
    Args:
        password_manager: Core password manager instance
        auth_manager: Authentication manager instance
        
    Returns:
        ServiceIntegrator: Configured service integrator or None if failed
    """
    try:
        # Import enhanced services
        from src.core.service_integration import create_service_integrator
        from src.core.database import DatabaseManager
        
        logging.info("Initializing enhanced services...")
        
        # Get database manager from password manager
        database_manager = password_manager.database_manager if hasattr(password_manager, 'database_manager') else None
        
        # If no database manager, create one
        if not database_manager:
            database_manager = DatabaseManager()
            logging.info("Created new database manager for enhanced services")
        
        # Configuration for services
        service_config = {
            'default_view_timeout': 1,          # 1 minute default
            'enable_security_alerts': True,     # Enable real-time security alerts
            'enable_audit_logging': True,       # Enable comprehensive audit logging
            'max_concurrent_views': 5,          # Maximum concurrent password views
            'cleanup_interval_minutes': 5,      # Background cleanup interval
        }
        
        # Create service integrator
        service_integrator = create_service_integrator(
            database_manager=database_manager,
            config=service_config
        )
        
        # Verify service health
        health_status = service_integrator.get_service_health()
        if health_status['overall_status'] not in ['healthy', 'degraded']:
            logging.error(f"Service initialization failed: {health_status}")
            return None
        
        logging.info(f"Enhanced services initialized successfully - Status: {health_status['overall_status']}")
        logging.info(f"Services available: {list(health_status['services'].keys())}")
        
        return service_integrator
        
    except ImportError as e:
        logging.error(f"Enhanced services not available: {e}")
        return None
    except Exception as e:
        logging.error(f"Failed to initialize enhanced services: {e}")
        return None

def launch_enhanced_gui():
    """
    Launch the enhanced GUI interface with integrated services
    
    This enhanced version includes all the new features:
    - Time-based password viewing
    - Enhanced deletion workflows  
    - Comprehensive settings management
    - Security audit logging
    """
    print("Starting enhanced GUI interface...")
    logging.info("Launching enhanced GUI with integrated services")
    
    try:
        # Import GUI modules
        import customtkinter as ctk
        from src.gui.login_window import LoginWindow
        from src.gui.main_window import MainWindow
        from src.gui.themes import setup_theme
        from src.core.auth import AuthenticationManager
        from src.core.password_manager import PasswordManagerCore
        
        # Import enhanced components
        from src.gui.main_window_enhanced import create_enhanced_main_window, check_enhanced_features_available
        
        # Initialize theme system
        setup_theme()
        
        # Create a hidden root window
        root = ctk.CTk()
        root.withdraw()
        
        # Initialize core managers
        auth_manager = AuthenticationManager()
        password_manager = PasswordManagerCore(auth_manager=auth_manager)
        
        # Initialize enhanced services
        service_integrator = initialize_enhanced_services(password_manager, auth_manager)
        
        if not service_integrator:
            logging.warning("Enhanced services not available - running in legacy mode")
            service_integrator = None
        
        main_window_ref = [None]  # Reference holder
        
        def on_login_success(session_id: str, username: str, master_password: str = None):
            """Enhanced login success callback with service integration"""
            try:
                logging.info(f"Login successful for user: {username}")
                
                # Cache master password for convenience
                if master_password:
                    password_manager._cache_master_password(session_id, master_password)
                    logging.debug("Master password cached for session")
                
                # Log login event if enhanced services available
                if service_integrator and service_integrator._security_audit_logger:
                    # Get user ID (for now, use a placeholder - in real app would be from database)
                    user_id = 1  # This would be retrieved from the auth system
                    
                    service_integrator._security_audit_logger.log_authentication_attempt(
                        user_id=user_id,
                        username=username,
                        success=True
                    )
                
                # Close login window
                try:
                    login_window.destroy()
                except:
                    pass
                
                # Create enhanced main window
                user_id = 1  # This would be retrieved from the auth system in a real implementation
                
                main_window = create_enhanced_main_window(
                    session_id=session_id,
                    username=username,
                    password_manager=password_manager,
                    auth_manager=auth_manager,
                    service_integrator=service_integrator,
                    user_id=user_id,
                    parent=root
                )
                
                main_window_ref[0] = main_window
                
                # Setup cleanup on close
                def on_main_window_close():
                    cleanup_application(session_id, auth_manager, main_window, service_integrator, root)
                
                main_window.protocol("WM_DELETE_WINDOW", on_main_window_close)
                
                logging.info("Enhanced main window created successfully")
                
            except Exception as e:
                logging.error(f"Error in login success handler: {e}")
                show_error_and_quit(f"Failed to initialize main application: {e}", root)
        
        def on_login_window_close():
            """Handle login window close"""
            cleanup_application(None, auth_manager, None, service_integrator, root)
        
        # Create login window
        login_window = LoginWindow(auth_manager, on_login_success, parent=root)
        login_window.protocol("WM_DELETE_WINDOW", on_login_window_close)
        
        # Start the application
        logging.info("Starting main application loop")
        root.mainloop()
        
        return True
        
    except ImportError as e:
        error_msg = f"Enhanced GUI dependencies not found: {e}"
        logging.error(error_msg)
        print(f"[ERROR] {error_msg}")
        print("Please ensure all dependencies are installed")
        return False
    except Exception as e:
        error_msg = f"Enhanced GUI startup failed: {e}"
        logging.error(error_msg)
        print(f"[ERROR] {error_msg}")
        return False

# Enhanced main window creation is now handled by main_window_enhanced.py

def cleanup_application(session_id, auth_manager, main_window, service_integrator, root):
    """Comprehensive application cleanup"""
    try:
        logging.info("Starting application cleanup...")
        
        # Logout user session
        if session_id and auth_manager:
            try:
                auth_manager.logout_user(session_id)
                logging.debug(f"User session {session_id[:8]}... logged out")
            except Exception as e:
                logging.warning(f"Error during logout: {e}")
        
        # Shutdown enhanced services
        if service_integrator:
            try:
                service_integrator.shutdown()
                logging.info("Enhanced services shutdown completed")
            except Exception as e:
                logging.error(f"Error shutting down services: {e}")
        
        # Close main window
        if main_window:
            try:
                main_window.destroy()
            except Exception as e:
                logging.warning(f"Error closing main window: {e}")
        
        # Quit root
        try:
            root.quit()
        except Exception as e:
            logging.warning(f"Error quitting root window: {e}")
        
        logging.info("Application cleanup completed")
        
    except Exception as e:
        logging.error(f"Error during application cleanup: {e}")

def show_error_and_quit(message, root):
    """Show error message and quit application"""
    try:
        from tkinter import messagebox
        messagebox.showerror("Application Error", message)
    except:
        print(f"[ERROR] {message}")
    
    try:
        root.quit()
    except:
        pass

def main_enhanced():
    """
    Enhanced main application entry point
    
    This enhanced version includes all the new security features and
    comprehensive service integration.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        # Setup enhanced logging first
        setup_logging()
        
        # Parse command line arguments (use same as original)
        args = parse_arguments()
        
        # Show enhanced banner
        if not args.check_deps:
            print_banner()
        
        logging.info("Starting Personal Password Manager v2.0.0 Enhanced")
        
        # Handle dependency check
        if args.check_deps:
            basic_check = check_dependencies()
            enhanced_check = check_enhanced_dependencies()
            return 0 if (basic_check and enhanced_check) else 1
        
        # Set up environment
        if not setup_environment():
            logging.error("Environment setup failed")
            print("[ERROR] Environment setup failed. Please check permissions.")
            return 1
        
        # Check dependencies
        print("Performing comprehensive dependency check...")
        
        try:
            # Check basic dependencies
            import customtkinter
            import cryptography
            print("[OK] Core dependencies available")
            
            # Check enhanced dependencies
            enhanced_available = check_enhanced_dependencies()
            if not enhanced_available:
                print("[WARNING] Some enhanced features may not be available")
                logging.warning("Enhanced dependencies not fully available")
            
        except ImportError as e:
            logging.error(f"Missing core dependency: {e}")
            print(f"[ERROR] Missing core dependency: {e}")
            print("Please run: python main_enhanced.py --check-deps")
            return 1
        
        # Launch appropriate interface
        success = False
        
        if args.gui:
            success = launch_enhanced_gui()
        elif args.web:
            # For now, fall back to standard web interface
            # Enhanced web interface could be implemented in the future
            print("Enhanced web interface not yet implemented, launching standard web interface...")
            success = launch_web()
        
        if success:
            logging.info("Application exited successfully")
        else:
            logging.error("Application exited with errors")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user. Goodbye!")
        logging.info("Application interrupted by user")
        return 0
    except Exception as e:
        logging.critical(f"Unexpected error: {e}", exc_info=True)
        print(f"\n[ERROR] Unexpected error: {e}")
        print("For help, run: python main_enhanced.py --help")
        return 1

# Import utility functions from original main.py
def setup_environment():
    """Set up application environment - imported from original main.py"""
    try:
        # Ensure required directories exist
        directories = ['data', 'backups', 'logs', 'Code Explanations']
        
        for directory in directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
        
        logging.info("Environment setup completed")
        return True
        
    except Exception as e:
        logging.error(f"Environment setup failed: {e}")
        return False

def check_dependencies():
    """Check basic dependencies - imported from original main.py"""
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

def launch_web():
    """Launch web interface - imported from original main.py"""
    print("Starting web interface...")
    logging.info("Launching web interface (standard version)")
    
    try:
        # Import web modules
        from src.web.app import create_app
        
        # Create Flask application
        app = create_app()
        
        # Configuration
        app.config['DEBUG'] = False
        app.config['HOST'] = '127.0.0.1'
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
        
        return True
        
    except ImportError as e:
        logging.error(f"Web dependencies not found: {e}")
        print(f"[ERROR] Web dependencies not found: {e}")
        return False
    except Exception as e:
        logging.error(f"Web server startup failed: {e}")
        print(f"[ERROR] Web server startup failed: {e}")
        return False

def parse_arguments():
    """Parse command line arguments - same as original"""
    parser = argparse.ArgumentParser(
        description='Personal Password Manager v2.0.0 Enhanced - Advanced password management with security features',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Create mutually exclusive group for interface options
    interface_group = parser.add_mutually_exclusive_group()
    
    interface_group.add_argument(
        '--gui', 
        action='store_true',
        help='Launch enhanced GUI interface (default)'
    )
    
    interface_group.add_argument(
        '--web', 
        action='store_true',
        help='Launch web interface'
    )
    
    interface_group.add_argument(
        '--check-deps', 
        action='store_true',
        help='Run comprehensive dependency checker'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no interface specified, default to GUI
    if not any([args.gui, args.web, args.check_deps]):
        args.gui = True
    
    return args

if __name__ == "__main__":
    # Set the exit code based on the enhanced main function result
    exit_code = main_enhanced()
    sys.exit(exit_code)
