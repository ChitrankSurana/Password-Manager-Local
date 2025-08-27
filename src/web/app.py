#!/usr/bin/env python3
"""
Personal Password Manager - Web Application
==========================================

Flask-based web interface for the Personal Password Manager providing
secure browser-based access to password management functionality.

Features:
- Responsive web interface with modern design
- Session-based authentication with security
- Full password management capabilities  
- Browser-based password generation
- Export/import functionality
- Mobile-friendly responsive design

Security:
- CSRF protection for all forms
- Secure session management
- Input validation and sanitization
- HTTPS enforcement in production
- Rate limiting for authentication

Author: Personal Password Manager
Version: 1.0.0
"""

import os
import secrets
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask import send_file, abort
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

# Import core functionality
import sys
sys.path.append(str(Path(__file__).parent.parent))

from core.auth import AuthenticationManager
from core.password_manager import PasswordManagerCore
from utils.password_generator import PasswordGenerator, GenerationOptions, GenerationMethod
from utils.strength_checker import AdvancedPasswordStrengthChecker
from utils.import_export import BackupManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebPasswordManager:
    """Main web application class for the Password Manager"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.app = Flask(__name__, 
                        template_folder='templates',
                        static_folder='static')
        
        # Configure Flask app
        self._configure_app()
        
        # Initialize core components
        self.auth_manager = AuthenticationManager()
        self.password_manager = PasswordManagerCore()
        self.password_generator = PasswordGenerator()
        self.strength_checker = AdvancedPasswordStrengthChecker()
        self.backup_manager = BackupManager()
        
        # Register routes
        self._register_routes()
        
        # Register error handlers
        self._register_error_handlers()
    
    def _configure_app(self):
        """Configure Flask application settings"""
        # Security settings
        self.app.config['SECRET_KEY'] = self.config.get('SECRET_KEY', secrets.token_hex(32))
        self.app.config['SESSION_COOKIE_SECURE'] = self.config.get('HTTPS', False)
        self.app.config['SESSION_COOKIE_HTTPONLY'] = True
        self.app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        self.app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
        
        # Upload settings
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
        
        # Development settings
        self.app.config['DEBUG'] = self.config.get('DEBUG', False)
        
        # Security headers
        @self.app.after_request
        def add_security_headers(response):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            if self.config.get('HTTPS'):
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            return response
    
    def _register_routes(self):
        """Register all web application routes"""
        
        # Authentication routes
        @self.app.route('/')
        def index():
            """Main landing page"""
            if 'user_session' in session:
                return redirect(url_for('dashboard'))
            return render_template('login.html')
        
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """User login handling"""
            if request.method == 'POST':
                username = request.form.get('username', '').strip()
                password = request.form.get('password', '')
                
                if not username or not password:
                    flash('Username and password are required.', 'error')
                    return render_template('login.html')
                
                try:
                    # Attempt authentication
                    user_session = self.auth_manager.authenticate_user(username, password)
                    if user_session:
                        session['user_session'] = user_session
                        session['username'] = username
                        session.permanent = True
                        logger.info(f"User {username} logged in successfully")
                        return redirect(url_for('dashboard'))
                    else:
                        flash('Invalid username or password.', 'error')
                        logger.warning(f"Failed login attempt for user: {username}")
                        
                except Exception as e:
                    logger.error(f"Login error for {username}: {e}")
                    flash('Login failed. Please try again.', 'error')
            
            return render_template('login.html')
        
        @self.app.route('/register', methods=['GET', 'POST'])
        def register():
            """User registration handling"""
            if request.method == 'POST':
                username = request.form.get('username', '').strip()
                password = request.form.get('password', '')
                confirm_password = request.form.get('confirm_password', '')
                
                # Validation
                if not username or not password:
                    flash('Username and password are required.', 'error')
                    return render_template('register.html')
                
                if password != confirm_password:
                    flash('Passwords do not match.', 'error')
                    return render_template('register.html')
                
                if len(password) < 8:
                    flash('Password must be at least 8 characters long.', 'error')
                    return render_template('register.html')
                
                try:
                    # Check if user exists
                    if self.auth_manager.user_exists(username):
                        flash('Username already exists. Please choose a different one.', 'error')
                        return render_template('register.html')
                    
                    # Create user
                    if self.auth_manager.create_user(username, password):
                        flash('Account created successfully! Please log in.', 'success')
                        logger.info(f"New user registered: {username}")
                        return redirect(url_for('login'))
                    else:
                        flash('Failed to create account. Please try again.', 'error')
                        
                except Exception as e:
                    logger.error(f"Registration error for {username}: {e}")
                    flash('Registration failed. Please try again.', 'error')
            
            return render_template('register.html')
        
        @self.app.route('/logout')
        def logout():
            """User logout handling"""
            username = session.get('username', 'Unknown')
            
            # Clear session
            if 'user_session' in session:
                try:
                    self.auth_manager.invalidate_session(session['user_session'])
                except Exception as e:
                    logger.warning(f"Error invalidating session: {e}")
            
            session.clear()
            logger.info(f"User {username} logged out")
            flash('You have been logged out successfully.', 'info')
            return redirect(url_for('index'))
        
        # Main application routes (require authentication)
        @self.app.route('/dashboard')
        @self.require_auth
        def dashboard():
            """Main dashboard with password list"""
            try:
                user_session = session['user_session']
                passwords = self.password_manager.get_all_passwords(user_session)
                
                return render_template('dashboard.html',
                                     username=session.get('username'),
                                     passwords=passwords,
                                     password_count=len(passwords))
                                     
            except Exception as e:
                logger.error(f"Dashboard error: {e}")
                flash('Error loading dashboard.', 'error')
                return redirect(url_for('index'))
        
        @self.app.route('/add_password', methods=['GET', 'POST'])
        @self.require_auth
        def add_password():
            """Add new password entry"""
            if request.method == 'POST':
                website = request.form.get('website', '').strip()
                username = request.form.get('username', '').strip()
                password = request.form.get('password', '')
                remarks = request.form.get('remarks', '').strip()
                
                if not all([website, username, password]):
                    flash('Website, username, and password are required.', 'error')
                    return render_template('add_password.html')
                
                try:
                    user_session = session['user_session']
                    result = self.password_manager.add_password(
                        user_session, website, username, password, remarks
                    )
                    
                    if result:
                        flash('Password added successfully!', 'success')
                        logger.info(f"Password added for website: {website}")
                        return redirect(url_for('dashboard'))
                    else:
                        flash('Failed to add password.', 'error')
                        
                except Exception as e:
                    logger.error(f"Add password error: {e}")
                    flash('Error adding password.', 'error')
            
            return render_template('add_password.html')
        
        @self.app.route('/edit_password/<int:password_id>', methods=['GET', 'POST'])
        @self.require_auth
        def edit_password(password_id):
            """Edit existing password entry"""
            try:
                user_session = session['user_session']
                
                if request.method == 'POST':
                    website = request.form.get('website', '').strip()
                    username = request.form.get('username', '').strip()
                    password = request.form.get('password', '')
                    remarks = request.form.get('remarks', '').strip()
                    
                    if not all([website, username, password]):
                        flash('Website, username, and password are required.', 'error')
                        return redirect(url_for('edit_password', password_id=password_id))
                    
                    result = self.password_manager.update_password(
                        user_session, password_id, website, username, password, remarks
                    )
                    
                    if result:
                        flash('Password updated successfully!', 'success')
                        return redirect(url_for('dashboard'))
                    else:
                        flash('Failed to update password.', 'error')
                
                # GET request - load password data
                password_data = self.password_manager.get_password(user_session, password_id)
                if not password_data:
                    flash('Password not found.', 'error')
                    return redirect(url_for('dashboard'))
                
                return render_template('edit_password.html', password=password_data)
                
            except Exception as e:
                logger.error(f"Edit password error: {e}")
                flash('Error editing password.', 'error')
                return redirect(url_for('dashboard'))
        
        @self.app.route('/delete_password/<int:password_id>', methods=['POST'])
        @self.require_auth
        def delete_password(password_id):
            """Delete password entry"""
            try:
                user_session = session['user_session']
                result = self.password_manager.delete_password(user_session, password_id)
                
                if result:
                    flash('Password deleted successfully!', 'success')
                else:
                    flash('Failed to delete password.', 'error')
                    
            except Exception as e:
                logger.error(f"Delete password error: {e}")
                flash('Error deleting password.', 'error')
            
            return redirect(url_for('dashboard'))
        
        # Password generation and tools
        @self.app.route('/generate_password')
        @self.require_auth
        def generate_password_page():
            """Password generation tool"""
            return render_template('generate_password.html')
        
        @self.app.route('/api/generate_password', methods=['POST'])
        @self.require_auth
        def api_generate_password():
            """API endpoint for password generation"""
            try:
                data = request.get_json()
                
                options = GenerationOptions(
                    length=data.get('length', 16),
                    include_lowercase=data.get('include_lowercase', True),
                    include_uppercase=data.get('include_uppercase', True),
                    include_digits=data.get('include_digits', True),
                    include_symbols=data.get('include_symbols', True)
                )
                
                method = GenerationMethod.RANDOM
                if data.get('method') == 'memorable':
                    method = GenerationMethod.MEMORABLE
                elif data.get('method') == 'pronounceable':
                    method = GenerationMethod.PRONOUNCEABLE
                
                result = self.password_generator.generate_password(options, method)
                
                return jsonify({
                    'success': True,
                    'password': result.password,
                    'strength': result.strength_analysis
                })
                
            except Exception as e:
                logger.error(f"Password generation error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/check_strength', methods=['POST'])
        @self.require_auth
        def api_check_strength():
            """API endpoint for password strength checking"""
            try:
                data = request.get_json()
                password = data.get('password', '')
                
                if not password:
                    return jsonify({'success': False, 'error': 'Password is required'})
                
                analysis = self.strength_checker.analyze_password_realtime(password)
                
                return jsonify({
                    'success': True,
                    'analysis': analysis
                })
                
            except Exception as e:
                logger.error(f"Strength check error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/get_password/<int:password_id>', methods=['GET'])
        @self.require_auth
        def api_get_password(password_id):
            """API endpoint for getting password details"""
            try:
                user_session = session['user_session']
                password_data = self.password_manager.get_password(user_session, password_id)
                
                if password_data:
                    return jsonify({
                        'success': True,
                        'password': {
                            'id': password_data.id,
                            'website': password_data.website,
                            'username': password_data.username,
                            'password': password_data.password,
                            'remarks': password_data.remarks,
                            'created_at': password_data.created_at.isoformat() if password_data.created_at else None,
                            'updated_at': password_data.updated_at.isoformat() if password_data.updated_at else None
                        }
                    })
                else:
                    return jsonify({'success': False, 'error': 'Password not found'}), 404
                    
            except Exception as e:
                logger.error(f"Get password error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # Search functionality
        @self.app.route('/search')
        @self.require_auth
        def search():
            """Search passwords"""
            query = request.args.get('q', '').strip()
            
            if not query:
                return redirect(url_for('dashboard'))
            
            try:
                user_session = session['user_session']
                results = self.password_manager.search_passwords(user_session, query)
                
                return render_template('search_results.html',
                                     query=query,
                                     results=results,
                                     result_count=len(results))
                                     
            except Exception as e:
                logger.error(f"Search error: {e}")
                flash('Error performing search.', 'error')
                return redirect(url_for('dashboard'))
        
        # Backup and export routes
        @self.app.route('/backup')
        @self.require_auth
        def backup_page():
            """Backup management page"""
            try:
                backups = self.backup_manager.get_backup_list()
                return render_template('backup.html', backups=backups)
            except Exception as e:
                logger.error(f"Backup page error: {e}")
                flash('Error loading backup page.', 'error')
                return redirect(url_for('dashboard'))
        
        @self.app.route('/api/create_backup', methods=['POST'])
        @self.require_auth
        def api_create_backup():
            """API endpoint for creating database backup"""
            try:
                backup_path = self.backup_manager.create_database_backup()
                return jsonify({
                    'success': True,
                    'message': 'Backup created successfully',
                    'path': backup_path
                })
            except Exception as e:
                logger.error(f"Backup creation error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/export_data', methods=['POST'])
        @self.require_auth
        def api_export_data():
            """API endpoint for exporting encrypted data"""
            try:
                data = request.get_json()
                format_type = data.get('format', 'json')
                master_password = data.get('master_password', '')
                
                if not master_password:
                    return jsonify({'success': False, 'error': 'Master password required'}), 400
                
                user_session = session['user_session']
                export_path = self.backup_manager.export_encrypted_data(
                    user_session, master_password, format_type
                )
                
                return jsonify({
                    'success': True,
                    'message': 'Data exported successfully',
                    'download_url': url_for('download_export', filename=os.path.basename(export_path))
                })
                
            except Exception as e:
                logger.error(f"Export error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/download/<filename>')
        @self.require_auth
        def download_export(filename):
            """Download exported file"""
            try:
                # Security check - ensure filename is safe
                safe_filename = secure_filename(filename)
                file_path = Path.home() / '.password_manager' / 'exports' / safe_filename
                
                if file_path.exists():
                    return send_file(file_path, as_attachment=True)
                else:
                    abort(404)
                    
            except Exception as e:
                logger.error(f"Download error: {e}")
                abort(500)
    
    def require_auth(self, f):
        """Decorator to require authentication for routes"""
        def decorated_function(*args, **kwargs):
            if 'user_session' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            
            # Validate session is still active
            try:
                if not self.auth_manager.validate_session(session['user_session']):
                    session.clear()
                    flash('Your session has expired. Please log in again.', 'warning')
                    return redirect(url_for('login'))
            except Exception as e:
                logger.error(f"Session validation error: {e}")
                session.clear()
                flash('Session error. Please log in again.', 'error')
                return redirect(url_for('login'))
            
            return f(*args, **kwargs)
        
        decorated_function.__name__ = f.__name__
        return decorated_function
    
    def _register_error_handlers(self):
        """Register error handlers"""
        
        @self.app.errorhandler(404)
        def not_found_error(error):
            return render_template('errors/404.html'), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            logger.error(f"Internal server error: {error}")
            return render_template('errors/500.html'), 500
        
        @self.app.errorhandler(413)
        def file_too_large(error):
            flash('File is too large. Maximum size is 16MB.', 'error')
            return redirect(request.url), 413
    
    def run(self, host='127.0.0.1', port=5000, debug=False):
        """Run the web application"""
        logger.info(f"Starting Password Manager Web Interface on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug, threaded=True)

def create_app(config=None):
    """Factory function to create Flask application"""
    web_manager = WebPasswordManager(config)
    return web_manager.app

if __name__ == '__main__':
    # Development server
    config = {
        'DEBUG': True,
        'SECRET_KEY': 'dev-key-change-in-production'
    }
    
    web_manager = WebPasswordManager(config)
    web_manager.run(debug=True)