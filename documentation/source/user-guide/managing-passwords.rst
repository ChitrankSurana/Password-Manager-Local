Managing Passwords
==================

This guide covers advanced password management features.

Adding Passwords
----------------

Manual Entry
~~~~~~~~~~~~

1. Click the **+ Add Password** button
2. Fill in the details:

   * **Website/Application**: Service name (required)
   * **Username**: Your username or email (required)
   * **Password**: The password (required)
   * **Remarks**: Optional notes

3. Click **Save**

Using Password Generator
~~~~~~~~~~~~~~~~~~~~~~~~

1. In the Add Password dialog, click **Generate**
2. Configure generation options:

   * **Length**: 8-64 characters (default: 16)
   * **Include Uppercase**: A-Z
   * **Include Lowercase**: a-z
   * **Include Numbers**: 0-9
   * **Include Symbols**: !@#$%^&*()

3. Click **Generate Password**
4. Preview the generated password
5. Click **Use This Password** or regenerate
6. Save the entry

Editing Passwords
-----------------

Update Existing Entries
~~~~~~~~~~~~~~~~~~~~~~~

1. Find the password in your list
2. Click the **edit icon** (pencil)
3. Modify any fields
4. Click **Save Changes**

.. note::
   Changes are immediately encrypted and saved. No undo is available.

Best Practices for Editing
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Update passwords when services require it
* Add remarks for password requirements
* Update usernames if email changes
* Keep website/app names consistent

Deleting Passwords
------------------

Single Entry
~~~~~~~~~~~~

1. Locate the password to delete
2. Click the **delete icon** (trash bin)
3. Confirm deletion in the popup

.. warning::
   Deletion is permanent! Export backups regularly.

Bulk Deletion
~~~~~~~~~~~~~

Currently not supported. Delete entries individually.

Password Health Monitoring
---------------------------

The Password Health panel shows:

Weak Passwords
~~~~~~~~~~~~~~

Passwords identified as weak (less than 40% strength):

* Too short (< 8 characters)
* Common patterns (123456, password)
* Dictionary words
* Repeated characters (aaaaaa)

**Action**: Click **"View Weak Passwords"** to see the list and update them.

Reused Passwords
~~~~~~~~~~~~~~~~

Same password used for multiple services:

* Security risk if one service is compromised
* All accounts with that password are vulnerable

**Action**: Generate unique passwords for each service.

Compromised Passwords
~~~~~~~~~~~~~~~~~~~~~

Passwords found in known data breaches:

* Checked against Have I Been Pwned database
* High security risk

**Action**: Change immediately!

Updating Weak Passwords
~~~~~~~~~~~~~~~~~~~~~~~~

1. Click **"View Weak Passwords"**
2. For each weak password:

   * Click **Edit**
   * Click **Generate** for a strong password
   * **Save Changes**

3. Update the password on the actual website/service

Password Search and Filtering
------------------------------

Quick Search
~~~~~~~~~~~~

Use the search box at the top:

* Type any text
* Searches website names, usernames, and remarks
* Real-time results
* Case-insensitive

Advanced Filtering
~~~~~~~~~~~~~~~~~~

Combine search with other features:

* Search + Sort: Find and organize results
* Search + Favorites: Quickly access starred items

Keyboard Shortcuts
~~~~~~~~~~~~~~~~~~

* ``Ctrl+F`` or ``Cmd+F``: Focus search box
* ``Esc``: Clear search
* ``Enter``: Select first result

Organizing with Remarks
------------------------

Use the Remarks field to add context:

Examples
~~~~~~~~

.. code-block:: text

   "Personal account - recovery email: backup@email.com"
   "Work account - expires 2025-06-01"
   "Shared with team - don't change without notice"
   "Security question: Mother's maiden name = Smith"

Benefits
~~~~~~~~

* Remember account details
* Track password requirements
* Note security questions
* Store recovery information

.. warning::
   Don't store sensitive answers in plain text. Use hints instead of actual answers.

Password Strength Guidelines
-----------------------------

Strong Password Characteristics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Length**: 16+ characters
* **Complexity**: Mix of uppercase, lowercase, numbers, symbols
* **Unpredictability**: Avoid personal info, common words
* **Uniqueness**: Different for each service

Password Strength Levels
~~~~~~~~~~~~~~~~~~~~~~~~~

* **0-20%**: Very Weak - Crackable in seconds
* **20-40%**: Weak - Crackable in minutes
* **40-60%**: Fair - Moderate protection
* **60-80%**: Good - Strong protection
* **80-100%**: Excellent - Very strong protection

Aim for 80%+ on all passwords.

Creating Memorable Strong Passwords
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Passphrases**: Multiple random words

.. code-block:: text

   "correct-horse-battery-staple"
   "blue-piano-elephant-mountain"

**Sentence Method**: First letters + numbers + symbols

.. code-block:: text

   "My dog ate 3 pizzas!" → "Mda3p!"
   "I love coffee at 7 AM" → "Ilc@7AM"

**Pattern Method**: Keyboard patterns with substitutions

.. code-block:: text

   "QaZ123!@#WsX"

Regular Maintenance
-------------------

Monthly Tasks
~~~~~~~~~~~~~

* Review password health
* Update weak passwords
* Remove unused accounts
* Export backup

Quarterly Tasks
~~~~~~~~~~~~~~~

* Change important passwords (email, banking)
* Review favorite list
* Update master password (optional)

Annual Tasks
~~~~~~~~~~~~

* Comprehensive password audit
* Update all passwords if possible
* Review security settings
* Archive old backups securely

Tips for Efficiency
-------------------

1. **Use Browser Extension**: Auto-fill passwords quickly
2. **Mark Favorites**: Quick access to frequently used passwords
3. **Consistent Naming**: Use consistent website names (e.g., always "github.com" not "GitHub")
4. **Add Remarks**: Future-you will thank you
5. **Regular Backups**: Export monthly to prevent data loss
6. **Password Generator**: Don't waste time creating passwords manually

Next Steps
----------

* :doc:`browser-extension` - Set up auto-fill
* :doc:`import-export` - Learn about backups
* :doc:`settings` - Customize your experience
