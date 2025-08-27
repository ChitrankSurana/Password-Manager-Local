# Personal Password Manager

A comprehensive, secure, and user-friendly password manager built with Python, featuring modern GUI design, advanced encryption, and extensive backup capabilities.

## 🔐 Features

### Security
- **Military-grade encryption**: AES-256-CBC with PBKDF2-HMAC-SHA256 key derivation
- **Multi-user support**: Secure user authentication with bcrypt password hashing
- **Session management**: Cryptographically secure session tokens
- **Local storage only**: All data stays on your computer
- **Zero-knowledge architecture**: Passwords are encrypted before storage

### Password Management
- **Secure storage**: Store unlimited passwords with website, username, and remarks
- **Advanced password generation**: 4 generation methods (random, memorable, pattern-based, pronounceable)
- **Real-time strength analysis**: Advanced password strength checker with entropy calculations
- **Search and filter**: Quickly find passwords with intelligent search
- **Multi-account support**: Store multiple accounts per website

### User Interface
- **Modern design**: Windows 11-inspired interface with dark/light themes
- **Intuitive navigation**: Clean, organized layout with tabbed interface
- **Responsive design**: Adapts to different screen sizes
- **Accessibility**: High contrast themes and keyboard shortcuts

### Backup & Export
- **Database backups**: Complete database backup and restore
- **Encrypted exports**: Export data in multiple formats (JSON, CSV, XML)
- **Browser import**: Import passwords from Chrome, Firefox, and Edge
- **Cross-platform portability**: Take your encrypted database anywhere

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Windows, macOS, or Linux

### Installation

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd Password-Manager-Local
   ```

2. **Check dependencies**
   ```bash
   python check_dependencies.py
   ```
   This will automatically install any missing packages.

3. **Run the application**
   ```bash
   python main.py
   ```

### First-Time Setup

1. **Launch the application** - The login window will appear
2. **Create a new account** - Click "Create Account" and set up your master credentials
3. **Start adding passwords** - Use the main interface to store your first passwords
4. **Generate secure passwords** - Use the built-in generator for new accounts
5. **Set up backups** - Create your first backup from the Backup Manager

## 📋 Detailed Usage Guide

### Creating Your First Account

When you first run the application:

1. Click "Create Account" in the login window
2. Enter a unique username (used to identify your account)
3. Create a strong master password (this encrypts all your data)
4. Click "Create Account" to finish setup

**Important**: Your master password cannot be recovered if forgotten. Keep it safe!

### Adding Passwords

1. Click "Add Password" in the main window
2. Fill in the required fields:
   - **Website**: The site or service name
   - **Username**: Your login name/email
   - **Password**: Your password (or generate one)
   - **Remarks**: Optional notes about this account
3. Click "Save" to encrypt and store the password

### Generating Secure Passwords

Access the password generator from:
- The "Add Password" dialog (Generate button)
- Tools menu → Password Generator

Choose from 4 generation methods:
- **Random**: Cryptographically secure random passwords
- **Memorable**: Dictionary-based passwords that are easier to remember
- **Pattern**: Custom patterns like "Xxxx-0000-xxxx"
- **Pronounceable**: Passwords that sound like words but aren't real words

### Managing Backups

Regular backups are essential for data safety:

1. **Database Backups**:
   - Full database copies with metadata
   - Automatic timestamping and compression
   - One-click restore functionality

2. **Encrypted Exports**:
   - Export in JSON, CSV, or XML format
   - Password-protected encryption
   - Portable across different systems

3. **Browser Imports**:
   - Import existing passwords from Chrome, Firefox, or Edge
   - Automatic format detection and validation
   - Merge with existing data or replace entirely

### Advanced Features

#### Search and Filtering
- Use the search box to quickly find passwords
- Search works across websites, usernames, and remarks
- Case-insensitive and partial matching

#### Password Strength Analysis
- Real-time strength checking as you type
- Detailed analysis with improvement suggestions
- Entropy calculations and security scoring

#### Themes and Customization
- Dark and light themes available
- Multiple color schemes
- Windows 11-inspired modern design

## 🛡️ Security Architecture

### Encryption Details
- **Algorithm**: AES-256-CBC (Advanced Encryption Standard)
- **Key Derivation**: PBKDF2-HMAC-SHA256 with 100,000 iterations
- **Salt Generation**: Cryptographically secure random salts (16 bytes)
- **IV Generation**: Unique initialization vector for each encryption

### Data Protection
- Passwords are encrypted before database storage
- Master passwords are hashed using bcrypt (cost factor 12)
- Session tokens use cryptographically secure random generation
- Memory is cleared after sensitive operations

### Database Security
- SQLite database with encrypted password fields
- Prepared statements prevent SQL injection
- User data isolation through session-based access control
- Automatic database integrity checks

## 📁 File Structure

```
Password-Manager-Local/
├── main.py                     # Application entry point
├── check_dependencies.py       # Dependency checker
├── requirements.txt            # Python dependencies
├── implementation_plan.txt     # Development roadmap
├── src/
│   ├── core/                  # Core functionality
│   │   ├── database.py        # Database management
│   │   ├── encryption.py      # Encryption/decryption
│   │   ├── auth.py           # Authentication system
│   │   └── password_manager.py # High-level API
│   ├── utils/                 # Utility modules
│   │   ├── password_generator.py # Password generation
│   │   ├── strength_checker.py  # Strength analysis
│   │   └── import_export.py     # Backup/export system
│   └── gui/                   # User interface
│       ├── themes.py          # Theme system
│       ├── login_window.py    # Login interface
│       ├── main_window.py     # Main application window
│       └── components/        # UI components
│           ├── password_dialog.py
│           ├── password_generator.py
│           ├── strength_checker.py
│           └── backup_manager.py
└── Code Explanations/         # Technical documentation
    ├── Core Systems/
    ├── GUI Components/
    └── Security Architecture/
```

## 🔧 Configuration

### Database Location
By default, the database is stored in:
- **Windows**: `%APPDATA%/PasswordManager/passwords.db`
- **macOS**: `~/Library/Application Support/PasswordManager/passwords.db`
- **Linux**: `~/.local/share/PasswordManager/passwords.db`

### Backup Location
Backups are stored in:
- **Windows**: `%APPDATA%/PasswordManager/backups/`
- **macOS**: `~/Library/Application Support/PasswordManager/backups/`
- **Linux**: `~/.local/share/PasswordManager/backups/`

## 🧪 Testing

Run the built-in tests to verify functionality:

```bash
# Test database functionality
python -m src.core.database

# Test encryption system
python -m src.core.encryption

# Test password generation
python -m src.utils.password_generator
```

## 🔄 Updates and Maintenance

### Updating Dependencies
```bash
python check_dependencies.py --update
```

### Database Maintenance
The application includes automatic database optimization and integrity checking. Manual maintenance is rarely needed.

### Backup Best Practices
1. Create regular database backups (weekly recommended)
2. Test backup restoration periodically
3. Store backups in multiple locations
4. Keep encrypted exports as additional protection

## 🐛 Troubleshooting

### Common Issues

**Application won't start**:
- Run `python check_dependencies.py` to verify all packages are installed
- Check Python version (3.8+ required)
- Ensure no antivirus software is blocking the application

**Forgot master password**:
- Master passwords cannot be recovered for security reasons
- Restore from a previous backup if available
- As a last resort, delete the database file to start fresh (all data will be lost)

**Database corruption**:
- Restore from the most recent backup
- Check disk space and file permissions
- Run database integrity check from the Tools menu

**Import/Export issues**:
- Verify file formats match expected structure
- Check that export files aren't corrupted
- Ensure sufficient disk space for operations

### Getting Help

1. Check the troubleshooting section above
2. Review the detailed code documentation in `Code Explanations/`
3. Examine log files for error details
4. Create an issue with detailed error information

## 📄 License

This project is provided as-is for personal use. Modify and distribute according to your needs while maintaining security best practices.

## 🔮 Roadmap

### Planned Features
- [ ] Web interface for remote access
- [ ] Cloud synchronization options
- [ ] Mobile app companion
- [ ] Advanced reporting and analytics
- [ ] Plugin system for extensibility

### Contributing
This is a personal project, but suggestions for improvements are welcome. Focus areas include:
- Security enhancements
- User interface improvements
- Cross-platform compatibility
- Performance optimizations

## 📞 Support

For technical questions or security concerns, review the comprehensive documentation in the `Code Explanations/` directory, which provides detailed explanations of all systems and components.

---

**Remember**: Your master password is the key to all your data. Keep it secure, and create regular backups!