Import & Export
===============

Learn how to backup, restore, and migrate your passwords safely.

Why Export?
-----------

Regular exports provide:

* **Backup**: Protect against data loss
* **Migration**: Move to another device
* **Archival**: Keep offline copies
* **Peace of Mind**: Security against corruption

We recommend exporting your passwords **monthly** or after significant changes.

Exporting Passwords
-------------------

Export Formats
~~~~~~~~~~~~~~

**1. Encrypted JSON** (Recommended)

* Passwords remain encrypted
* Most secure option
* Can only be imported into Password Manager
* Protected by your master password

**2. Plain Text JSON**

* Passwords in readable format
* Useful for migration to other services
* **Security risk** - handle carefully!
* Delete after use

**3. CSV Format**

* Compatible with most password managers
* Spreadsheet compatible
* Plain text - handle with care
* Good for migration

Starting an Export
~~~~~~~~~~~~~~~~~~

1. Click the **menu icon** (three dots) in top-right
2. Select **"Export Passwords"**
3. Export dialog appears

Encrypted Export
~~~~~~~~~~~~~~~~

1. Select **"Encrypted JSON"** format
2. Choose save location:

   .. code-block:: text

      Recommended:
      Documents/PasswordManager-Backups/backup-2025-12-04.json

3. Click **"Export"**
4. Verify the file was created
5. Store securely (USB drive, encrypted cloud storage)

.. note::
   Encrypted exports use your current master password for encryption. Keep this password safe!

Plain Text Export
~~~~~~~~~~~~~~~~~

1. Select **"Plain JSON"** or **"CSV"** format
2. **Read and accept** the security warning
3. Choose save location
4. Click **"Export"**

.. danger::
   Plain text exports contain unencrypted passwords!

   * Store in encrypted folder
   * Don't email or upload to cloud
   * Delete after migration
   * Use only when necessary

Security Best Practices for Exports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**DO:**

* Use encrypted format whenever possible
* Store on encrypted USB drive
* Use file encryption (7-Zip with password, VeraCrypt)
* Keep multiple backups in different locations
* Test restores occasionally
* Delete old backups (keep last 3-6 months)

**DON'T:**

* Email export files (even encrypted)
* Store in unencrypted cloud storage
* Leave on desktop or downloads folder
* Share with others
* Keep plain text exports long-term

Importing Passwords
-------------------

Supported Formats
~~~~~~~~~~~~~~~~~

1. **Encrypted JSON**: From Password Manager exports
2. **Plain JSON**: From Password Manager or other sources
3. **CSV**: From other password managers

Starting an Import
~~~~~~~~~~~~~~~~~~

1. Click **menu icon** → **"Import Passwords"**
2. Import dialog appears
3. Select file format
4. Choose the file to import
5. Review preview (if available)
6. Click **"Import"**

From Encrypted Backup
~~~~~~~~~~~~~~~~~~~~~~

1. Select **"Encrypted JSON"** format
2. Click **"Choose File"**
3. Select your backup file
4. Enter the master password used during export
5. Click **"Import"**
6. Wait for confirmation

.. note::
   You must use the same master password that was active when you created the encrypted export.

From Plain Text JSON/CSV
~~~~~~~~~~~~~~~~~~~~~~~~~

1. Select format (**"Plain JSON"** or **"CSV"**)
2. Click **"Choose File"**
3. Select your file
4. Review the data preview
5. Configure options:

   * Skip duplicates: Don't import passwords that already exist
   * Update existing: Overwrite matching entries
   * Import all: Keep both versions

6. Click **"Import"**
7. Review import summary

Duplicate Handling
~~~~~~~~~~~~~~~~~~

When importing, duplicates are detected by matching:

* Website/Application name
* Username

**Options:**

* **Skip**: Keep existing, ignore imported
* **Update**: Replace existing with imported
* **Keep Both**: Import as separate entry

Import Validation
~~~~~~~~~~~~~~~~~

The application validates:

* File format correctness
* Required fields present (website, username, password)
* Character encoding (UTF-8)
* Data structure integrity

Invalid entries are skipped and reported in the summary.

Migrating from Other Password Managers
---------------------------------------

From LastPass
~~~~~~~~~~~~~

1. **Export from LastPass**:

   * Log in to LastPass web vault
   * Go to Advanced Options → Export
   * Save as CSV file

2. **Import to Password Manager**:

   * Select CSV format
   * Choose the LastPass export file
   * Skip any service accounts (will have duplicate usernames)
   * Import

From 1Password
~~~~~~~~~~~~~~

1. **Export from 1Password**:

   * Open 1Password app
   * File → Export → All Items
   * Choose CSV format

2. **Import to Password Manager**:

   * Select CSV format
   * Map fields if prompted
   * Import

From Chrome/Edge Password Manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Export from Browser**:

   * Settings → Passwords
   * Click menu (three dots)
   * Export passwords
   * Save CSV file

2. **Import to Password Manager**:

   * Select CSV format
   * Import the file

From Bitwarden
~~~~~~~~~~~~~~

1. **Export from Bitwarden**:

   * Tools → Export Vault
   * Choose .json format
   * Export

2. **Convert JSON** (if needed):

   * May need to convert to Password Manager JSON format
   * Or import as CSV

3. **Import to Password Manager**

Custom CSV Format
~~~~~~~~~~~~~~~~~

If your CSV has a different structure:

**Required Headers:**

* ``website`` (or ``url``, ``title``)
* ``username`` (or ``login``, ``email``)
* ``password``

**Optional Headers:**

* ``remarks`` (or ``notes``, ``comment``)

**Example CSV:**

.. code-block:: text

   website,username,password,remarks
   github.com,user@email.com,SecurePass123!,Personal account
   gmail.com,user@gmail.com,AnotherPass456!,Primary email

Backup Strategy
---------------

Recommended Schedule
~~~~~~~~~~~~~~~~~~~~

* **Daily**: Automatic encrypted backup (configure in settings)
* **Weekly**: Manual verification of backup
* **Monthly**: Export to external storage
* **Quarterly**: Test restore procedure

The 3-2-1 Rule
~~~~~~~~~~~~~~

Keep **3** copies of your data:

1. **Primary**: Active database on your computer
2. **Local Backup**: Encrypted export on external drive
3. **Off-site Backup**: Encrypted export in secure cloud storage

Use **2** different storage media:

* Computer hard drive (primary)
* USB drive (backup 1)
* Cloud storage (backup 2)

Keep **1** backup off-site:

* Encrypted cloud storage
* Safety deposit box
* Trusted family member

Storage Recommendations
~~~~~~~~~~~~~~~~~~~~~~~

**Local:**

* Encrypted USB drive (BitLocker, VeraCrypt)
* External hard drive with encryption
* NAS with encryption enabled

**Cloud:**

* Encrypt before uploading (7-Zip, VeraCrypt)
* Use zero-knowledge cloud storage (SpiderOak, Sync.com)
* Enable two-factor authentication on cloud account

**Physical:**

* Encrypted USB in safety deposit box
* Sealed envelope with encrypted drive

Disaster Recovery
-----------------

Lost Password Database
~~~~~~~~~~~~~~~~~~~~~~

1. Don't panic!
2. Locate your most recent backup
3. Install Password Manager on new device (if needed)
4. Create new account with **same master password**
5. Import from encrypted backup
6. Verify all passwords imported correctly

Forgotten Master Password
~~~~~~~~~~~~~~~~~~~~~~~~~

.. warning::
   There is **NO WAY** to recover your passwords if you forget your master password.

**Prevention:**

* Write down master password and store securely
* Use a memorable passphrase
* Practice typing it regularly
* Store encrypted hint in secure location

Corrupted Database
~~~~~~~~~~~~~~~~~~

1. Close Password Manager
2. Locate most recent backup
3. Import backup into new account
4. Verify data integrity
5. Delete corrupted database

Moving to New Computer
~~~~~~~~~~~~~~~~~~~~~~

1. **On Old Computer**:

   * Export as Encrypted JSON
   * Copy export file to USB drive

2. **On New Computer**:

   * Install Password Manager
   * Create account (same master password!)
   * Import from encrypted backup
   * Verify all data present

3. **Cleanup**:

   * Securely delete export file from USB
   * Continue using Password Manager

Automated Backups
-----------------

Configure Automatic Exports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Go to Settings → Backup
2. Enable **"Automatic Backup"**
3. Configure:

   * Frequency: Daily, Weekly, or Monthly
   * Location: Choose secure folder
   * Format: Encrypted JSON recommended
   * Keep last N backups: 5-10

4. Click **"Save Settings"**

Automatic backups run:

* On application close
* At scheduled time (if app is running)
* After significant changes (> 10 password updates)

Backup Notifications
~~~~~~~~~~~~~~~~~~~~

Enable notifications in Settings:

* Backup successful: Silent notification
* Backup failed: Alert with details
* Backup overdue: Reminder

Troubleshooting
---------------

Export Failed
~~~~~~~~~~~~~

**Possible Causes:**

* Insufficient disk space
* No write permission to destination folder
* File is locked/in use

**Solutions:**

1. Choose different location
2. Check available disk space
3. Run as administrator
4. Close any programs using the file

Import Failed
~~~~~~~~~~~~~

**Common Issues:**

* Invalid file format
* Incorrect encryption password
* Corrupted file
* Encoding issues

**Solutions:**

1. Verify file format matches selection
2. Check encryption password
3. Try different backup file
4. Open CSV in text editor to check encoding

Duplicates After Import
~~~~~~~~~~~~~~~~~~~~~~~

If you accidentally imported duplicates:

1. Use search to find duplicates
2. Manually delete unwanted entries
3. Or: Export clean data, delete all, re-import

Next Steps
----------

* :doc:`settings` - Configure backup automation
* :doc:`managing-passwords` - Organize imported passwords
* :doc:`browser-extension` - Set up for convenience
