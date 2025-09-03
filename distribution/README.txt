====================================================================
              Personal Password Manager v1.0.0
                  Standalone Executable
====================================================================

INSTALLATION & USAGE:
=====================

1. FIRST TIME SETUP:
   - Extract all files to any folder on your computer
   - Double-click "Personal_Password_Manager.exe" to run
   - The application will create a "data" folder automatically

2. RUNNING THE APPLICATION:
   - Simply double-click "Personal_Password_Manager.exe"
   - No additional software installation required
   - Works offline - no internet connection needed

FEATURES:
=========

🔐 SECURITY:
   - AES-256 encryption for all passwords
   - PBKDF2 key derivation (100,000+ iterations)
   - Master password never stored on disk
   - All data encrypted locally

📱 USER INTERFACE:
   - Modern GUI with dark/light theme support
   - Resizable windows and scrollable content
   - Hover tooltips on all buttons
   - Grouped password entries by website

📊 IMPORT/EXPORT:
   - CSV import from Google Password Manager & others
   - Auto-mapping of common column names
   - Bulk password import with preview
   - Smart website grouping

🎲 PASSWORD TOOLS:
   - Built-in secure password generator
   - Customizable length and character sets
   - One-click clipboard copying
   - Password strength analysis

SYSTEM REQUIREMENTS:
===================

- Windows 10/11 (64-bit)
- 100 MB free disk space
- No additional software required

DATA STORAGE:
=============

Your password database is stored in the "data" folder:
- data/password_manager.db (encrypted database)
- data/settings.json (application preferences)

BACKUP YOUR DATA:
- Copy the entire "data" folder to backup your passwords
- Store backups in multiple secure locations
- Test backups regularly by restoring them

SECURITY NOTES:
==============

✅ YOUR DATA IS SECURE:
   - Passwords encrypted with AES-256
   - Master password required for access
   - No cloud storage - all data stays local
   - No telemetry or data collection

⚠️ IMPORTANT REMINDERS:
   - Remember your master password - it cannot be recovered
   - Backup your data folder regularly
   - Use a strong, unique master password
   - Keep the application updated

TROUBLESHOOTING:
===============

If the application won't start:
1. Run as Administrator if needed
2. Ensure Windows Defender/antivirus allows the file
3. Check that the "data" folder has write permissions
4. Try running from a folder without spaces in the path

If you forget your master password:
- Your data cannot be recovered without the master password
- This is by design for maximum security
- Restore from a backup if available

TECHNICAL DETAILS:
=================

Built with:
- Python 3.13 + CustomTkinter for modern UI
- SQLite for local database storage
- Cryptography library for AES-256 encryption
- PyInstaller for standalone executable

File size: ~50 MB (includes Python runtime)
Created: 2024

LICENSE:
========
Personal Password Manager v1.0.0
Free for personal use.

For support or questions, refer to the documentation.

====================================================================
                    Stay Secure! 🔒
====================================================================