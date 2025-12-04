Browser Extension
=================

The Password Manager browser extension enables auto-fill, password capture, and generation directly in your web browser.

.. note::
   For complete browser extension documentation, see the Password-Manager-Browser-Extension project in the ``Complete_projects`` folder.

Supported Browsers
------------------

* **Google Chrome**: Version 90+
* **Microsoft Edge**: Version 90+
* **Brave Browser**: Version 1.25+
* **Opera**: Version 76+
* **Vivaldi**: Version 4.0+

.. note::
   Firefox support is planned for future releases.

Installation
------------

Prerequisites
~~~~~~~~~~~~~

1. Desktop Password Manager app installed and running
2. Logged in to your account
3. Administrator access (for native host registration)

Extension Setup
~~~~~~~~~~~~~~~

1. **Load Extension in Browser**:

   * Open ``chrome://extensions/`` (or ``edge://extensions/``)
   * Enable **Developer Mode** (toggle in top-right)
   * Click **Load unpacked**
   * Select the ``Password-Manager-Browser-Extension`` folder

2. **Register Native Messaging Host**:

   On Windows:

   .. code-block:: bash

      cd Password-Manager-Browser-Extension\\native-messaging
      register-host.bat

   Run as Administrator when prompted.

3. **Verify Connection**:

   * Click the extension icon in your browser
   * Status should show "Connected to Password Manager"
   * You should see your password list

Features
--------

Auto-Fill
~~~~~~~~~

**Automatic Detection**:

* Extension detects password fields on web pages
* Shield icon appears next to detected fields
* Click the icon to fill credentials

**Multiple Credentials**:

* If multiple accounts exist for a site
* Dropdown menu shows all options
* Select the account you want to use

**Context Menu**:

* Right-click on a password field
* Select "Fill Password" from menu
* Quick fill without clicking the icon

Password Capture
~~~~~~~~~~~~~~~~

**Save New Passwords**:

1. Fill out a login or signup form
2. Submit the form
3. Extension shows "Save Password?" prompt
4. Click "Save" to store in Password Manager

**Duplicate Prevention**:

* Extension detects existing passwords
* Won't prompt if password already saved
* Keeps your vault clean

**Never Save Option**:

* Click "Never" to skip a site
* Site added to ignore list
* No more prompts for that site

Password Generation
~~~~~~~~~~~~~~~~~~~

**From Context Menu**:

1. Right-click on a password field
2. Select "Generate Password"
3. Strong password generated and filled
4. Automatically copied to clipboard

**From Extension Popup**:

1. Click extension icon
2. Click "Generate Password" button
3. Password generated and copied
4. Paste into any field (Ctrl+V)

**Customization**:

* Configure generation settings in extension options
* Length: 8-64 characters
* Character types: uppercase, lowercase, numbers, symbols
* Settings saved for future generations

Using the Extension
-------------------

Extension Popup
~~~~~~~~~~~~~~~

Click the extension icon to open the popup:

**Password List**:

* Search for passwords by website or username
* Click "Copy" to copy password to clipboard
* Click "Fill" to fill on current page
* Scrollable list with real-time search

**Status Indicator**:

* Green: Connected to desktop app
* Red: Not connected (start desktop app)

**Quick Actions**:

* Generate Password button
* Settings icon (opens options page)
* Refresh button (reload password list)

Options/Settings
~~~~~~~~~~~~~~~~

Click the settings icon in the popup:

**Auto-Fill Settings**:

* Enable/disable auto-fill
* Auto-fill on page load (experimental)
* Show fill icons

**Security Settings**:

* Clear clipboard after X seconds (10-60)
* Never save password list
* Lock on inactivity

**Generation Defaults**:

* Default password length
* Default character types
* Quick generation templates

**Connection**:

* Connection status
* Test connection button
* Reconnect option

Troubleshooting
---------------

Extension Not Working
~~~~~~~~~~~~~~~~~~~~~

**Check Desktop App**:

1. Ensure Password Manager desktop app is running
2. You must be logged in
3. Try restarting the app

**Check Native Host**:

1. Re-run ``register-host.bat`` as Administrator
2. Restart browser after registration
3. Check browser console for errors

**Check Extension Status**:

1. Go to ``chrome://extensions/``
2. Ensure extension is enabled
3. Check for error messages
4. Try reloading the extension

Auto-Fill Not Detecting Fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Common Causes**:

* Dynamic forms loaded after page load
* Non-standard input fields
* Shadow DOM elements

**Solutions**:

1. Refresh the page after it fully loads
2. Try clicking the extension icon and using "Fill on Page"
3. Use copy-paste as fallback

Connection Issues
~~~~~~~~~~~~~~~~~

**"Not Connected" Status**:

1. Start the desktop Password Manager app
2. Log in to your account
3. Click refresh in extension popup

**Native Host Errors**:

1. Check Windows Registry:

   .. code-block:: bash

      reg query "HKCU\\Software\\Google\\Chrome\\NativeMessagingHosts\\com.passwordmanager.native"

2. Verify host path is correct
3. Re-run registration script
4. Check ``native-messaging/logs/native-host.log`` for errors

Passwords Not Appearing
~~~~~~~~~~~~~~~~~~~~~~~~

1. Ensure you're logged in (desktop app)
2. Check database file exists and isn't corrupted
3. Try adding a new password in desktop app
4. Refresh extension

Security Considerations
-----------------------

Data Storage
~~~~~~~~~~~~

* Extension does NOT store passwords locally
* All data retrieved from desktop app on demand
* Passwords remain encrypted in desktop database

Communication
~~~~~~~~~~~~~

* Uses Chrome's Native Messaging protocol
* No network requests made
* All communication local between extension and desktop app

Clipboard Security
~~~~~~~~~~~~~~~~~~

* Clipboard auto-clear prevents password leakage
* Configure timeout in settings
* Use "Fill" instead of "Copy" when possible

Best Practices
~~~~~~~~~~~~~~

* Keep desktop app running when using extension
* Don't leave extension popup open unattended
* Use auto-fill instead of copy-paste when possible
* Enable clipboard clearing
* Log out when done

Tips and Tricks
---------------

Keyboard Shortcuts
~~~~~~~~~~~~~~~~~~

* ``Ctrl+Shift+P`` (or ``Cmd+Shift+P``): Open extension popup
* ``Esc``: Close extension popup
* ``Tab`` + ``Enter``: Navigate and select passwords

Quick Fill
~~~~~~~~~~

1. Focus the password field
2. Press ``Ctrl+Shift+P``
3. Type to search
4. Press ``Enter`` to fill

Organizing for Extension
~~~~~~~~~~~~~~~~~~~~~~~~~

* Use consistent website naming (e.g., "github.com")
* Add subdomains if needed (e.g., "mail.google.com")
* Extension matches based on hostname

Multiple Accounts
~~~~~~~~~~~~~~~~~

* Extension detects all passwords for current site
* Shows username in dropdown to differentiate
* Most recently used appears first

Uninstallation
--------------

Remove Extension
~~~~~~~~~~~~~~~~

1. Go to ``chrome://extensions/``
2. Find Password Manager extension
3. Click "Remove"
4. Confirm removal

Unregister Native Host
~~~~~~~~~~~~~~~~~~~~~~

1. Open Registry Editor (regedit.exe)
2. Navigate to:

   ``HKEY_CURRENT_USER\\Software\\Google\\Chrome\\NativeMessagingHosts\\com.passwordmanager.native``

3. Delete the key
4. Repeat for Edge if applicable:

   ``HKEY_CURRENT_USER\\Software\\Microsoft\\Edge\\NativeMessagingHosts\\com.passwordmanager.native``

Next Steps
----------

* :doc:`import-export` - Backup your passwords
* :doc:`settings` - Customize the application
* :doc:`managing-passwords` - Advanced password management
