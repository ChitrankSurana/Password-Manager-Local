Getting Started
===============

This guide will walk you through your first steps with the Password Manager.

Creating Your Account
---------------------

1. Launch the Application
~~~~~~~~~~~~~~~~~~~~~~~~~

Run the password manager:

.. code-block:: bash

   python main.py

2. Sign Up
~~~~~~~~~~

On the login screen, click the **"Sign Up"** button.

Fill in the registration form:

* **Username**: Choose a unique username (3-50 characters)
* **Email**: Enter a valid email address
* **Master Password**: Create a strong master password

.. warning::
   Your master password is crucial! It:

   * Encrypts all your passwords
   * Cannot be recovered if forgotten
   * Should be strong and memorable

   **Tip**: Use a passphrase like "correct-horse-battery-staple" or "MyDog@te3Pizzas!"

3. Complete Registration
~~~~~~~~~~~~~~~~~~~~~~~~~

Click **"Sign Up"** to create your account. You'll be automatically logged in.

First Time Login
----------------

For subsequent logins:

1. Enter your username
2. Enter your master password
3. Click **"Login"**

Main Interface Overview
-----------------------

After logging in, you'll see the main window with four sections:

Top Bar
~~~~~~~

* **Search Box**: Quickly find passwords
* **Add Password Button** (+): Create new password entries
* **Settings Icon**: Access application settings
* **Logout Button**: Sign out securely

Password List
~~~~~~~~~~~~~

The main area displays your saved passwords in a table:

* **Website/App**: The service name
* **Username**: Associated username
* **Password**: Masked by default (click eye icon to reveal)
* **Actions**: Copy, edit, delete buttons

Bottom Bar
~~~~~~~~~~

* **Password Health**: Quick overview of weak/compromised passwords
* **Total Passwords**: Count of saved entries

Adding Your First Password
---------------------------

Let's add a password for a website:

1. Click the **+ Add Password** button
2. Fill in the form:

   * **Website/Application**: e.g., "github.com"
   * **Username**: Your GitHub username
   * **Password**: Your GitHub password
   * **Remarks** (optional): Any notes about this password

3. Use Password Generator (Optional):

   * Click **"Generate"** button
   * Adjust settings (length, character types)
   * Click **"Generate Password"**
   * The generated password will be filled in

4. Click **"Save"** to store the password

Viewing and Copying Passwords
------------------------------

View Password
~~~~~~~~~~~~~

1. Locate the password in the list
2. Click the **eye icon** next to it
3. Click again to hide

Copy Password
~~~~~~~~~~~~~

1. Find the password entry
2. Click the **copy icon**
3. The password is copied to your clipboard
4. Paste it where needed (Ctrl+V or Cmd+V)

.. note::
   For security, the clipboard is automatically cleared after 30 seconds.

Organizing Your Passwords
--------------------------

Search
~~~~~~

Use the search box at the top to quickly find passwords:

* Type website name, username, or remarks
* Results update in real-time
* Clear the search to see all passwords

Favorites
~~~~~~~~~

Mark frequently used passwords as favorites:

1. Click the **star icon** on a password entry
2. Starred passwords appear at the top of your list

Sorting
~~~~~~~

Click column headers to sort by:

* Website (alphabetically)
* Username (alphabetically)
* Created date (newest/oldest)

Security Best Practices
-----------------------

Master Password
~~~~~~~~~~~~~~~

* Never share your master password
* Don't write it down in plain text
* Change it periodically (every 6-12 months)
* Use a unique master password (don't reuse it elsewhere)

Password Generation
~~~~~~~~~~~~~~~~~~~

* Use generated passwords when possible
* Aim for at least 16 characters
* Include symbols, numbers, and mixed case
* Avoid personal information

Regular Maintenance
~~~~~~~~~~~~~~~~~~~

* Check Password Health regularly
* Update weak passwords
* Remove unused entries
* Export backups monthly

Next Steps
----------

* :doc:`managing-passwords` - Learn advanced password management
* :doc:`browser-extension` - Set up auto-fill in your browser
* :doc:`import-export` - Backup your passwords
* :doc:`settings` - Customize the application
