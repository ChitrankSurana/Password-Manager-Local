Settings
========

Customize the Password Manager to suit your preferences and workflow.

Accessing Settings
------------------

Click the **settings icon** (gear) in the top-right corner of the main window.

Appearance Settings
-------------------

Theme
~~~~~

Choose your preferred visual theme:

* **Light Mode**: Traditional light background
* **Dark Mode**: Easy on the eyes, ideal for low-light environments
* **System**: Follow operating system theme automatically

**To Change:**

1. Go to Settings → Appearance
2. Select theme from dropdown
3. Click **Apply**
4. Theme changes immediately

Font Size
~~~~~~~~~

Adjust text size for better readability:

* **Small**: Compact view, more passwords visible
* **Medium** (Default): Balanced readability
* **Large**: Better for accessibility
* **Extra Large**: Maximum readability

**To Change:**

1. Settings → Appearance → Font Size
2. Select size
3. Click **Apply**

Compact Mode
~~~~~~~~~~~~

Reduce spacing to fit more passwords on screen:

* Smaller row height in password list
* Reduced padding in dialogs
* More items visible at once

Toggle: Settings → Appearance → Compact Mode

Security Settings
-----------------

Session Timeout
~~~~~~~~~~~~~~~

Automatically log out after period of inactivity:

* **Options**: 5, 15, 30, 60 minutes, Never
* **Default**: 15 minutes
* **Recommended**: 15-30 minutes

**To Configure:**

1. Settings → Security → Session Timeout
2. Select duration
3. Click **Save**

.. note::
   Activity includes mouse movement, keyboard input, or any interaction with the app.

Clipboard Auto-Clear
~~~~~~~~~~~~~~~~~~~~

Automatically clear clipboard after copying passwords:

* **Options**: 10, 20, 30, 60 seconds, Never
* **Default**: 30 seconds
* **Recommended**: 20-30 seconds

**Why This Matters:**

Prevents password leakage if you:

* Copy password
* Leave computer unattended
* Someone else uses computer

Lock on Minimize
~~~~~~~~~~~~~~~~

Require login when application is minimized or hidden:

* **Enabled**: Application locks immediately when minimized
* **Disabled**: Stays logged in when minimized

**Recommendation**: Enable for shared computers

Clear Clipboard on Lock
~~~~~~~~~~~~~~~~~~~~~~~

Wipe clipboard contents when locking or logging out:

* **Enabled**: Clipboard cleared on lock/logout
* **Disabled**: Clipboard contents persist

**Recommendation**: Enable for maximum security

Master Password Settings
-------------------------

Change Master Password
~~~~~~~~~~~~~~~~~~~~~~

Update your master password:

1. Settings → Security → Change Master Password
2. Enter current master password
3. Enter new master password (twice)
4. Strength meter updates in real-time
5. Click **Change Password**

.. warning::
   * All passwords will be re-encrypted with new master password
   * This operation cannot be undone
   * Export a backup before changing (recommended)

.. note::
   Changing master password does not affect encrypted backups created with old password.

Master Password Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Minimum 8 characters
* Recommended 16+ characters
* Mix of uppercase, lowercase, numbers, symbols
* Not previously used
* Not similar to username

Password Generation Settings
-----------------------------

Default Length
~~~~~~~~~~~~~~

Set default length for generated passwords:

* **Range**: 8-64 characters
* **Default**: 16 characters
* **Recommended**: 16-20 characters

Settings → Generation → Default Length

Default Character Sets
~~~~~~~~~~~~~~~~~~~~~~

Choose which character types to include by default:

* **Uppercase** (A-Z): Enabled
* **Lowercase** (a-z): Enabled
* **Numbers** (0-9): Enabled
* **Symbols** (!@#$%): Enabled

**Recommendation**: Keep all enabled for maximum security

Exclude Similar Characters
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Avoid confusing characters in generated passwords:

* **Enabled**: Excludes 0, O, l, I, 1
* **Disabled**: Uses all characters

**Use When:**

* Manually typing passwords
* Characters are hard to distinguish in your font

Custom Symbols
~~~~~~~~~~~~~~

Define which symbols to include:

* **Default**: ``!@#$%^&*()_+-=[]{}|;:,.<>?``
* **Custom**: Specify your own set
* **Minimal**: ``!@#$%`` (for services with symbol restrictions)

Settings → Generation → Custom Symbols

Password Health Settings
-------------------------

Check Interval
~~~~~~~~~~~~~~

How often to check password health:

* **On Startup**: Every time you log in
* **Daily**: Once per day
* **Weekly**: Once per week
* **Manual**: Only when you click "Check Now"

**Recommendation**: Daily or On Startup

Weak Password Threshold
~~~~~~~~~~~~~~~~~~~~~~~

Strength percentage below which passwords are considered weak:

* **Range**: 20-60%
* **Default**: 40%
* **Stricter**: 60% (more passwords flagged as weak)
* **Lenient**: 20% (only very weak passwords flagged)

Breach Database Updates
~~~~~~~~~~~~~~~~~~~~~~~

Automatically update compromised password database:

* **Enabled**: Downloads updates weekly
* **Disabled**: Uses packaged database

**Recommendation**: Enable for latest breach data

Auto-Save Settings
------------------

Prompt to Save
~~~~~~~~~~~~~~

When editing passwords, prompt before saving:

* **Enabled**: Confirmation dialog appears
* **Disabled**: Saves immediately

**Recommendation**: Enable to prevent accidental changes

Backup Before Major Actions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Automatically backup before:

* Master password change
* Bulk imports
* Bulk deletions

**Recommendation**: Enable for safety

Backup Settings
---------------

Auto-Backup
~~~~~~~~~~~

Automatically create encrypted backups:

* **Frequency**: Daily, Weekly, Monthly
* **Location**: Choose secure folder
* **Format**: Encrypted JSON (recommended)

**To Enable:**

1. Settings → Backup → Enable Auto-Backup
2. Choose frequency
3. Select backup location
4. Choose format
5. Click **Save**

Backup Retention
~~~~~~~~~~~~~~~~

Number of automatic backups to keep:

* **Range**: 3-30 backups
* **Default**: 10
* **Recommendation**: 7-10 (balance between safety and disk space)

Older backups are automatically deleted when limit is reached.

Backup Notifications
~~~~~~~~~~~~~~~~~~~~

Get notified about backup status:

* **Success**: Silent notification
* **Failure**: Alert with details
* **Overdue**: Reminder if backup missed

Database Settings
-----------------

Database Location
~~~~~~~~~~~~~~~~~

View or change where your password database is stored:

* **Default**: ``data/password_manager.db``
* **Custom**: Choose any location

**To Change:**

1. Export all passwords (encrypted backup)
2. Settings → Database → Change Location
3. Choose new location
4. Restart application
5. Import from backup

.. warning::
   Changing location requires re-importing passwords. Export first!

Database Maintenance
~~~~~~~~~~~~~~~~~~~~

**Optimize Database:**

* Reclaims unused space
* Improves query performance
* Run monthly

Settings → Database → Optimize

**Repair Database:**

* Fixes corruption
* Rebuilds indexes
* Use if experiencing errors

Settings → Database → Repair

**Verify Integrity:**

* Checks for corruption
* Validates encryption
* Confirms data consistency

Settings → Database → Verify Integrity

Cache Settings
--------------

Enable Cache
~~~~~~~~~~~~

Cache frequently accessed passwords for faster loading:

* **Enabled**: Passwords cached in memory (encrypted)
* **Disabled**: Always read from database

**Recommendation**: Enable (default)

Cache Size
~~~~~~~~~~

Maximum number of password entries to cache:

* **Range**: 100-10,000
* **Default**: 1,000
* **Higher**: Better performance, more memory
* **Lower**: Less memory, slower for large vaults

Cache TTL
~~~~~~~~~

How long to keep items in cache:

* **Range**: 1-60 minutes
* **Default**: 5 minutes
* **Longer**: Fewer database reads, slightly stale data
* **Shorter**: More up-to-date, more database reads

Advanced Settings
-----------------

Debug Mode
~~~~~~~~~~

Enable detailed logging for troubleshooting:

* **Enabled**: Verbose logs written to ``logs/`` directory
* **Disabled**: Normal logging

.. warning::
   Debug logs may contain sensitive information. Disable after troubleshooting.

Performance Monitoring
~~~~~~~~~~~~~~~~~~~~~~

Track operation performance:

* **Enabled**: Collects timing data
* **Disabled**: No performance tracking

View metrics: Settings → Advanced → View Performance Metrics

Developer Mode
~~~~~~~~~~~~~~

Enable features for developers:

* SQL query logging
* Database schema viewer
* API documentation link
* Debug menu in application

Settings → Advanced → Developer Mode

Experimental Features
---------------------

.. warning::
   Experimental features may be unstable. Use at your own risk.

**Available Experiments:**

* **Auto-Fill on Page Load**: Fill passwords as soon as page loads
* **Biometric Unlock**: Use fingerprint/face recognition
* **Cloud Sync**: Sync across devices (coming soon)
* **Password Sharing**: Share passwords with team members

Enable: Settings → Experimental → [Feature Name]

Resetting Settings
------------------

Reset to Defaults
~~~~~~~~~~~~~~~~~

Restore all settings to their default values:

1. Settings → Advanced → Reset Settings
2. Choose what to reset:

   * All settings
   * Appearance only
   * Security only
   * Generation only

3. Confirm reset
4. Settings restored immediately

.. note::
   This does NOT affect your passwords or database. Only settings are reset.

Import/Export Settings
~~~~~~~~~~~~~~~~~~~~~~

**Export Settings:**

1. Settings → Advanced → Export Settings
2. Save settings.json file
3. Use to restore or transfer to another device

**Import Settings:**

1. Settings → Advanced → Import Settings
2. Choose settings.json file
3. Settings applied immediately

Keyboard Shortcuts
------------------

Customize keyboard shortcuts:

Settings → Keyboard Shortcuts

**Default Shortcuts:**

* ``Ctrl+N`` (Cmd+N): New password
* ``Ctrl+F`` (Cmd+F): Search
* ``Ctrl+S`` (Cmd+S): Save changes
* ``Ctrl+Q`` (Cmd+Q): Quit application
* ``Ctrl+,`` (Cmd+,): Open settings
* ``Ctrl+L`` (Cmd+L): Lock application
* ``Ctrl+G`` (Cmd+G): Generate password

**To Customize:**

1. Click shortcut to change
2. Press new key combination
3. Click **Save**

Troubleshooting Settings
-------------------------

Settings Not Saving
~~~~~~~~~~~~~~~~~~~

1. Check file permissions in settings directory
2. Ensure not running multiple instances
3. Try resetting settings to defaults
4. Check logs for errors

Settings Causing Issues
~~~~~~~~~~~~~~~~~~~~~~~

1. Reset to defaults
2. Close and restart application
3. Re-apply settings one at a time
4. Identify problematic setting

Best Practices
--------------

Security
~~~~~~~~

* Enable session timeout (15-30 min)
* Enable clipboard auto-clear (20-30 sec)
* Enable lock on minimize (if shared computer)
* Enable auto-backup (daily or weekly)

Performance
~~~~~~~~~~~

* Enable caching for large vaults (1000+ passwords)
* Optimize database monthly
* Keep backup retention reasonable (7-10)

Usability
~~~~~~~~~

* Choose comfortable font size
* Set reasonable generation defaults
* Enable password health checks
* Configure keyboard shortcuts

Next Steps
----------

* :doc:`managing-passwords` - Organize your passwords
* :doc:`browser-extension` - Set up auto-fill
* :doc:`import-export` - Configure automatic backups
