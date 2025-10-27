# Database Viewer Guide

## Overview

The Database Viewer is a tool to inspect and verify the data stored in your Password Manager database (`password_manager.db`). This helps you:

- View what data is being saved
- Verify data integrity
- Debug issues
- Understand the database structure

## Installation

### Prerequisites

Install the required Python package:

```bash
pip install tabulate
```

## Usage

### Method 1: Interactive Mode (Recommended)

**Windows:**
```bash
# Double-click this file:
view_database.bat

# Or run from command line:
python view_database.py
```

**Interactive Menu:**
```
1. Show all tables          - Lists all tables with row counts
2. Show table schema        - Shows column structure of a table
3. Show users               - Lists all user accounts
4. Show password entries    - Shows all passwords (encrypted)
5. Show password entries    - Shows passwords with encrypted data visible
   (with encrypted data)
6. Show database metadata   - Shows database version and settings
7. Show statistics          - Overall database statistics
8. Verify data integrity    - Checks for database issues
9. Exit                     - Close the viewer
```

### Method 2: Command Line Mode

Run specific views directly:

```bash
# Show all tables
python view_database.py --tables

# Show all users
python view_database.py --users

# Show password entries (encrypted shown as [ENCRYPTED])
python view_database.py --passwords

# Show password entries with encrypted values visible
python view_database.py --passwords --show-encrypted

# Show database metadata
python view_database.py --metadata

# Show statistics
python view_database.py --stats

# Verify data integrity
python view_database.py --verify

# Show help
python view_database.py --help
```

## What You'll See

### 1. Database Tables

The password manager uses these main tables:

- **`users`** - User accounts and authentication data
- **`passwords`** - Encrypted password entries
- **`database_metadata`** - Database version and schema info

### 2. Users Table

Example output:
```
╔═════╦════════════╦═══════════════╦═════════════════════╦═════════════════════╦════════╗
║ ID  ║ Username   ║ Email         ║ Created             ║ Last Login          ║ Active ║
╠═════╬════════════╬═══════════════╬═════════════════════╬═════════════════════╬════════╣
║ 1   ║ john       ║ john@email.com║ 2025-10-27 14:30:00 ║ 2025-10-27 15:45:00 ║ ✓      ║
╚═════╩════════════╩═══════════════╩═════════════════════╩═════════════════════╩════════╝
```

**What this tells you:**
- User accounts exist and are active
- Login timestamps are recorded
- User IDs match between tables

### 3. Password Entries

Example output:
```
╔══════════╦═════════╦═══════════════════╦════════════════╦═════════════╦═════╦═════════════════════╗
║ Entry ID ║ User ID ║ Website           ║ Username       ║ Password    ║ Fav ║ Created             ║
╠══════════╬═════════╬═══════════════════╬════════════════╬═════════════╬═════╬═════════════════════╣
║ 1        ║ 1       ║ github.com        ║ johndoe        ║ [ENCRYPTED] ║ ⭐  ║ 2025-10-27 14:35:00 ║
║ 2        ║ 1       ║ google.com        ║ john@gmail.com ║ [ENCRYPTED] ║     ║ 2025-10-27 14:36:00 ║
╚══════════╩═════════╩═══════════════════╩════════════════╩═════════════╩═════╩═════════════════════╝
```

**What this tells you:**
- ✅ Passwords ARE being saved to the database
- ✅ Passwords are ENCRYPTED (shown as `[ENCRYPTED]`)
- ✅ Usernames and websites are stored correctly
- ✅ Timestamps are recorded
- ⭐ Shows favorite status

### 4. Encrypted Password Data

If you choose option 5 (show with encrypted data), you'll see:
```
║ Password                                              ║
╠═══════════════════════════════════════════════════════╣
║ gAAAAABmX1Y2Z... (truncated)                          ║
```

**What this tells you:**
- Passwords start with `gAAAAAB` - This is correct! It's Fernet encryption
- The encrypted data is long (100+ characters)
- Each password has unique encrypted text

### 5. Statistics

Example output:
```
╔═════════════════════════╦═══════╗
║ Metric                  ║ Count ║
╠═════════════════════════╬═══════╣
║ Total Users             ║ 3     ║
║ Active Users            ║ 3     ║
║ Total Password Entries  ║ 45    ║
║ Favorite Entries        ║ 8     ║
╚═════════════════════════╩═══════╝

📊 Passwords per User:
╔════════════╦════════════════╗
║ Username   ║ Password Count ║
╠════════════╬════════════════╣
║ john       ║ 25             ║
║ alice      ║ 15             ║
║ bob        ║ 5              ║
╚════════════╩════════════════╝
```

### 6. Data Integrity Check

Example output:
```
🔍 DATA INTEGRITY CHECK
══════════════════════════════════════════════════════════

✅ No data integrity issues found
✅ SQLite Integrity Check: ok
```

**If there are issues:**
```
❌ Issues Found:
  ⚠️  2 password entries with missing users
  ⚠️  5 entries with NULL/empty encrypted passwords
```

## Verification Checklist

Use this tool to verify:

### ✅ Data is Being Saved
1. Run: `python view_database.py --stats`
2. Check if password count > 0
3. Check if it matches what you added

### ✅ Passwords Are Encrypted
1. Run: `python view_database.py --passwords --show-encrypted`
2. Look at password column
3. Should start with `gAAAAAB` (Fernet encryption)
4. Should be 100+ characters long
5. Should be different for each entry

### ✅ All Data Fields Are Present
1. Run: `python view_database.py --passwords`
2. Check for:
   - Website names
   - Usernames
   - Encrypted passwords
   - Timestamps
   - User IDs

### ✅ No Database Corruption
1. Run: `python view_database.py --verify`
2. Should show: "✅ No data integrity issues found"
3. Should show: "✅ SQLite Integrity Check: ok"

### ✅ Users Exist and Are Active
1. Run: `python view_database.py --users`
2. Check:
   - Your username appears
   - Status shows ✓ (active)
   - Last login timestamp is recent

## Alternative: DB Browser for SQLite

If you prefer a GUI tool:

1. **Download:** https://sqlitebrowser.org/
2. **Install:** Follow installation instructions
3. **Open Database:**
   - File → Open Database
   - Navigate to: `data/password_manager.db`
4. **Browse Data:**
   - Click "Browse Data" tab
   - Select table from dropdown
   - View all rows and columns

## Troubleshooting

### ❌ "Database not found"
- Check you're in the project root directory
- Verify path: `data/password_manager.db` exists
- Try absolute path in script

### ❌ "tabulate module not found"
- Run: `pip install tabulate`
- Or use: `view_database.bat` (auto-installs)

### ❌ No password entries shown
- Check if you've added any passwords
- Verify you're logged in as the correct user
- Check user_id matches in passwords table

### ❌ Passwords look corrupted
- Encrypted passwords should start with `gAAAAAB`
- If they're plain text, encryption is broken
- If they're random characters, this is correct (encrypted)

## Security Notes

⚠️ **Important:**
- This tool only views the database, it cannot decrypt passwords
- Encrypted passwords are shown as encrypted blobs
- To decrypt, you need the master password (tool doesn't do this)
- Never share the database file - it contains encrypted passwords
- The encryption format (Fernet) is industry-standard

## Understanding the Data

### Password Encryption
```
Original password: MySecretPass123
              ↓
Encrypted:    gAAAAABmX1Y2ZhJ3L8k9mNpQrStUvWxYz...
              ↓
Stored in DB: (what you see in the tool)
```

The tool shows the encrypted version. This is correct and secure!

### Database Schema Version
Check with: `python view_database.py --metadata`

Should show:
```
║ schema_version ║ 2 ║
```

Version 2 is the current version with all features.

## Additional Resources

- **DB Browser for SQLite:** https://sqlitebrowser.org/
- **SQLite Documentation:** https://www.sqlite.org/docs.html
- **Fernet Encryption:** https://cryptography.io/en/latest/fernet/

## Example Session

```bash
# Start interactive mode
python view_database.py

# Select option 1 - Show tables
> 1
📊 AVAILABLE TABLES
══════════════════════════════════════════════════════════
  • database_metadata    (3 rows)
  • passwords            (25 rows)
  • users                (1 rows)

# Select option 7 - Show statistics
> 7
📈 DATABASE STATISTICS
══════════════════════════════════════════════════════════
║ Total Users             ║ 1     ║
║ Total Password Entries  ║ 25    ║
║ Favorite Entries        ║ 5     ║

# Select option 8 - Verify integrity
> 8
🔍 DATA INTEGRITY CHECK
══════════════════════════════════════════════════════════
✅ No data integrity issues found
✅ SQLite Integrity Check: ok

# All good!
```

---

**Questions?** Check the main README.md or create an issue on GitHub.
