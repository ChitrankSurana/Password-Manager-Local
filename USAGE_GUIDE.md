# Usage Guide - Personal Password Manager

This comprehensive guide covers all features and functionality of the Personal Password Manager, from basic operations to advanced techniques.

## Table of Contents
1. [Getting Started](#getting-started)
2. [User Management](#user-management)
3. [Password Management](#password-management)
4. [Password Generation](#password-generation)
5. [Search and Organization](#search-and-organization)
6. [Backup and Export](#backup-and-export)
7. [Security Features](#security-features)
8. [Advanced Features](#advanced-features)
9. [Tips and Best Practices](#tips-and-best-practices)

## Getting Started

### First Launch

When you first start the application:

1. **Login Window**: The application opens with a clean login interface
2. **Create Account**: Since no accounts exist, click "Create Account"
3. **Account Setup**: 
   - Choose a unique username (used for identification)
   - Create a strong master password (encrypts all your data)
   - Confirm the master password
4. **Login**: After account creation, login with your new credentials

### Understanding the Interface

The main window consists of:
- **Menu Bar**: Access to tools and settings
- **Toolbar**: Quick action buttons
- **Password List**: All your stored passwords
- **Search Bar**: Find passwords quickly
- **Status Bar**: Current session and system information

## User Management

### Creating Additional Users

The application supports multiple users on the same system:

1. **Logout**: Use File → Logout or click the logout button
2. **Create Account**: From the login screen, click "Create Account"
3. **New User**: Set up username and master password for the new user
4. **Separate Data**: Each user has completely isolated, encrypted data

### Switching Between Users

1. **Logout**: End current session
2. **Login**: Choose different username from login screen
3. **Session Management**: Each user has independent sessions

### Account Security

- **Master Password**: Cannot be changed after creation (security design)
- **Account Isolation**: Users cannot access each other's data
- **Session Timeout**: Automatic logout after inactivity (configurable)

## Password Management

### Adding New Passwords

#### Manual Entry
1. **Add Password Button**: Click the main "Add Password" button
2. **Fill Information**:
   - **Website**: Service name or URL (e.g., "Gmail", "github.com")
   - **Username**: Your login name or email
   - **Password**: Your password (or generate one)
   - **Remarks**: Optional notes (recovery info, security questions, etc.)
3. **Save**: Click "Save" to encrypt and store

#### Using Password Generator
1. **Generate Button**: In the Add Password dialog, click "Generate"
2. **Customize**: Choose length, character types, generation method
3. **Copy to Password Field**: Generated password fills automatically
4. **Save**: Complete the entry and save

### Viewing and Editing Passwords

#### Viewing Passwords
1. **Select Entry**: Click on any password entry in the list
2. **View Details**: Double-click or use "View" button to see full details
3. **Copy Operations**: Right-click for copy options (username, password, website)

#### Editing Existing Passwords
1. **Select Entry**: Choose the password to edit
2. **Edit Button**: Click "Edit" or double-click the entry
3. **Modify Fields**: Change any information as needed
4. **Update**: Save changes to update the encrypted storage

#### Deleting Passwords
1. **Select Entry**: Choose the password to delete
2. **Delete Button**: Click "Delete" or use Delete key
3. **Confirmation**: Confirm deletion (this cannot be undone)

### Bulk Operations

#### Multiple Selection
- **Ctrl+Click**: Select multiple non-adjacent entries
- **Shift+Click**: Select range of entries
- **Ctrl+A**: Select all entries

#### Bulk Actions
- **Delete Multiple**: Select multiple entries and delete
- **Export Selected**: Export only chosen entries
- **Copy Information**: Copy multiple passwords to clipboard

## Password Generation

### Generation Methods

The application offers four powerful generation methods:

#### 1. Random Generation
- **Cryptographically Secure**: Uses system random number generator
- **Customizable**: Choose length (8-64 characters)
- **Character Sets**: Select uppercase, lowercase, digits, symbols
- **Exclusions**: Avoid ambiguous characters (0, O, l, 1)

#### 2. Memorable Passwords
- **Dictionary-Based**: Uses common English words
- **Separator Options**: Hyphens, numbers, symbols between words
- **Length Control**: 2-6 words with customizable separators
- **Capitalization**: Random or consistent capitalization

#### 3. Pattern-Based Generation
- **Custom Patterns**: Define your own patterns
- **Pattern Symbols**:
  - `X` = Uppercase letter
  - `x` = Lowercase letter  
  - `0` = Digit
  - `$` = Symbol
  - `-` = Literal hyphen
- **Examples**: 
  - `Xxxx-0000-xxxx` → `Pass-1234-word`
  - `XX00xx$$` → `AB12cd!@`

#### 4. Pronounceable Passwords
- **Phonetic Generation**: Creates pronounceable but nonsensical words
- **Easy to Type**: Avoids complex character combinations
- **Memorable**: Sound like words but aren't dictionary words
- **Variable Length**: 8-20 characters

### Using the Password Generator

#### Quick Generation (In Password Dialog)
1. **Generate Button**: Click while adding/editing password
2. **Instant Result**: Password appears in field immediately
3. **Regenerate**: Click again for different password

#### Advanced Generation (Standalone Tool)
1. **Tools Menu**: Select "Password Generator"
2. **Method Selection**: Choose generation method
3. **Customize Options**: Set length, character types, patterns
4. **Real-time Preview**: See passwords as you adjust settings
5. **Copy to Clipboard**: Copy generated password for use

### Password Strength Analysis

#### Real-time Analysis
- **Strength Meter**: Visual indicator as you type
- **Score Display**: Numerical strength score (0-100)
- **Color Coding**: Red (weak) to green (strong)

#### Detailed Analysis
- **Entropy Calculation**: Measures password unpredictability
- **Pattern Detection**: Identifies common patterns and sequences
- **Dictionary Checking**: Detects common passwords and words
- **Improvement Suggestions**: Specific recommendations for strengthening

## Search and Organization

### Search Functionality

#### Basic Search
1. **Search Box**: Type in the main search field
2. **Real-time Results**: List filters as you type
3. **Search Scope**: Searches website names, usernames, and remarks
4. **Case Insensitive**: Matches regardless of capitalization

#### Advanced Search Techniques
- **Partial Matching**: "gmai" finds "gmail.com"
- **Multiple Terms**: "social media" finds Facebook, Twitter, etc.
- **Username Search**: Find all entries for specific email addresses
- **Remarks Search**: Find entries with specific notes or tags

#### Search Tips
- **Clear Search**: Click X or press Escape to clear
- **Quick Navigation**: Use arrow keys to navigate results
- **Multi-word Search**: Use spaces for multiple search terms

### Organizing Passwords

#### Naming Conventions
- **Consistent Naming**: Use consistent website naming
- **Descriptive Names**: "Gmail Personal" vs "Gmail Work"
- **Service Categories**: Group related services

#### Using Remarks Field
- **Recovery Information**: "Security question: Mother's maiden name"
- **Account Types**: "Premium account", "Free trial"
- **Usage Notes**: "Shared with team", "Personal use only"
- **Update Reminders**: "Password expires March 2024"

#### Sorting and Viewing
- **Alphabetical Sorting**: Automatic alphabetical organization
- **Recent Additions**: Newest entries appear at top
- **Usage Tracking**: Frequently accessed entries highlighted

## Backup and Export

### Database Backups

#### Creating Backups
1. **Backup Manager**: Tools → Backup Manager
2. **Database Backup Tab**: Select the backup tab
3. **Create Backup**: Click "Create New Backup"
4. **Automatic Naming**: Backups named with timestamp
5. **Location**: Stored in secure backup directory

#### Managing Backups
- **View List**: See all available backups with dates and sizes
- **Restore**: Select backup and click "Restore"
- **Delete**: Remove old backups to save space
- **Refresh**: Update backup list

#### Backup Best Practices
- **Regular Schedule**: Weekly backups recommended
- **Multiple Locations**: Store backups on different drives/devices
- **Test Restores**: Periodically test backup restoration
- **Before Changes**: Always backup before major operations

### Data Export

#### Export Formats
1. **JSON (Recommended)**: Complete data with metadata
2. **CSV (Compatible)**: Spreadsheet-compatible format
3. **XML (Structured)**: Hierarchical data format

#### Creating Exports
1. **Export Tab**: In Backup Manager, select "Export Data"
2. **Choose Format**: Select desired export format
3. **Master Password**: Enter password for encryption
4. **Save Location**: Choose where to save encrypted export
5. **Encryption**: All exports are password-protected

#### Export Features
- **Complete Data**: All passwords, usernames, websites, and remarks
- **Metadata Included**: Creation dates, modification dates
- **Cross-Platform**: Exports work on any operating system
- **Encrypted Security**: Password protection for export files

### Data Import

#### Import Sources
1. **Encrypted Exports**: From this application
2. **Browser Exports**: Chrome, Firefox, Edge CSV files
3. **Other Formats**: Compatible CSV formats

#### Import Process
1. **Import Tab**: Select "Import Data" in Backup Manager
2. **Choose Source**: Select import type
3. **Select File**: Browse for import file
4. **Authentication**: Enter required passwords
5. **Import Mode**: Choose merge or replace
6. **Processing**: Automatic data validation and import

#### Browser Import
- **Export from Browser**: Use browser's export password feature
- **CSV Format**: Standard browser CSV format
- **Field Mapping**: Automatic detection of URL, username, password fields
- **Duplicate Handling**: Smart duplicate detection and merging

## Security Features

### Encryption Details

#### Data Protection
- **AES-256-CBC**: Military-grade encryption algorithm
- **Unique Keys**: Each password has unique encryption
- **Salt Generation**: Random salts for each operation
- **IV Randomization**: Unique initialization vectors

#### Key Management
- **PBKDF2**: Key derivation from master password
- **100,000 Iterations**: Slows down brute-force attacks
- **Memory Protection**: Keys cleared after use
- **No Key Storage**: Keys regenerated from master password

### Session Security

#### Authentication
- **Master Password**: Required for all access
- **Session Tokens**: Cryptographically secure session management
- **Timeout Protection**: Automatic logout after inactivity
- **Failed Login Protection**: Temporary lockout after failures

#### Access Control
- **User Isolation**: Complete separation between users
- **Permission Checking**: All operations validated
- **Audit Trail**: Security events logged
- **Memory Protection**: Sensitive data cleared from memory

### Security Best Practices

#### Password Security
- **Unique Master Password**: Don't reuse anywhere else
- **Complex Master Password**: Use recommended complexity
- **Regular Backups**: Protect against data loss
- **Secure Environment**: Use on trusted computers

#### Operational Security
- **Lock Screen**: Always lock when away
- **Private Browsing**: Use private/incognito mode when accessing accounts
- **Regular Updates**: Keep application updated
- **Secure Deletion**: Use secure delete for sensitive files

## Advanced Features

### Customization Options

#### Theme Settings
- **Dark/Light Mode**: Switch between appearance modes
- **Color Schemes**: Multiple color options available
- **Font Sizing**: Adjust text size for readability
- **Window Scaling**: Adapt to different screen sizes

#### Behavior Settings
- **Session Timeout**: Adjust automatic logout timing
- **Backup Frequency**: Configure automatic backup reminders
- **Search Behavior**: Customize search result display
- **Clipboard Clearing**: Automatic clipboard clearing for security

### Performance Optimization

#### Database Performance
- **Automatic Optimization**: Database maintenance runs automatically
- **Index Management**: Optimized searching and sorting
- **Memory Efficiency**: Minimal memory footprint
- **Fast Startup**: Quick application launch

#### Large Dataset Handling
- **Efficient Search**: Fast search even with thousands of entries
- **Lazy Loading**: Load data as needed
- **Background Operations**: Non-blocking database operations
- **Progress Indicators**: Visual feedback for long operations

### Integration Features

#### Clipboard Integration
- **Smart Copying**: Copy passwords, usernames, or URLs
- **Automatic Clearing**: Security-focused clipboard management
- **Multiple Formats**: Different copy formats available
- **Keyboard Shortcuts**: Quick copy operations

#### File System Integration
- **Portable Database**: Move database between computers
- **Backup Integration**: Works with backup software
- **Export Compatibility**: Standard file formats
- **Cross-Platform**: Same files work on Windows, Mac, Linux

## Tips and Best Practices

### Password Management Best Practices

#### Creating Strong Passwords
1. **Use Generator**: Always use the built-in generator
2. **Unique Passwords**: Never reuse passwords across sites
3. **Regular Updates**: Change passwords periodically
4. **Length Priority**: Longer passwords are stronger than complex short ones

#### Organization Tips
1. **Consistent Naming**: Use consistent service names
2. **Detailed Remarks**: Include recovery information
3. **Regular Cleanup**: Remove unused accounts
4. **Categorization**: Use remarks for categorization

### Security Best Practices

#### Master Password
1. **Memorable but Complex**: Use passphrase method
2. **Never Share**: Keep master password private
3. **Multiple Backups**: Create multiple backup copies
4. **Recovery Planning**: Have recovery plan if forgotten

#### Regular Maintenance
1. **Weekly Backups**: Schedule regular backup creation
2. **Update Passwords**: Change old or compromised passwords
3. **Review Entries**: Regularly review and cleanup entries
4. **Security Updates**: Keep application updated

### Efficiency Tips

#### Keyboard Shortcuts
- **Ctrl+N**: Add new password
- **Ctrl+F**: Focus search box
- **Delete**: Delete selected entry
- **F5**: Refresh password list
- **Escape**: Clear search or close dialogs

#### Workflow Optimization
1. **Batch Operations**: Add multiple passwords at once
2. **Copy Shortcuts**: Right-click for quick copy options
3. **Search Efficiently**: Use specific terms for faster results
4. **Generator Presets**: Save common generation settings

### Troubleshooting Common Issues

#### Performance Issues
- **Database Size**: Large databases may slow operations
- **Memory Usage**: Close other applications if needed
- **Disk Space**: Ensure adequate free space for backups

#### Access Issues
- **Forgotten Password**: Use backup if master password forgotten
- **Corruption**: Restore from recent backup
- **Permissions**: Ensure write access to database directory

#### Import/Export Issues
- **File Formats**: Ensure correct file format for imports
- **Encoding**: Use UTF-8 encoding for CSV files
- **File Size**: Large exports may take time to process

## Conclusion

The Personal Password Manager provides comprehensive password management with strong security, intuitive interface, and powerful features. Following this guide and the best practices outlined will help you maximize the security and convenience of managing your passwords.

Remember: Your master password is the key to all your data. Keep it secure, create regular backups, and follow security best practices to protect your digital identity.

For technical details and advanced configuration, refer to the documentation in the `Code Explanations/` directory.