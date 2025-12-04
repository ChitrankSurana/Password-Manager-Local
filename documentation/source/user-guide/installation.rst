Installation
============

This guide will help you install the Password Manager application on your system.

System Requirements
-------------------

* **Operating System**: Windows 10/11, macOS 10.14+, or Linux
* **Python**: Version 3.10 or later
* **RAM**: Minimum 4GB recommended
* **Disk Space**: At least 200MB free space

Prerequisites
-------------

Python Installation
~~~~~~~~~~~~~~~~~~~

If you don't have Python installed:

**Windows:**

1. Download Python from https://www.python.org/downloads/
2. Run the installer
3. Check "Add Python to PATH"
4. Click "Install Now"

**macOS:**

.. code-block:: bash

   # Using Homebrew
   brew install python@3.10

**Linux (Ubuntu/Debian):**

.. code-block:: bash

   sudo apt update
   sudo apt install python3.10 python3-pip python3-venv

Installation Steps
------------------

1. Clone or Download the Repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Option A: Using Git**

.. code-block:: bash

   git clone https://github.com/yourusername/password-manager.git
   cd password-manager

**Option B: Download ZIP**

1. Download the ZIP file from the repository
2. Extract it to your desired location
3. Open a terminal/command prompt in that directory

2. Create a Virtual Environment (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Create virtual environment
   python -m venv venv

   # Activate it
   # On Windows:
   venv\\Scripts\\activate

   # On macOS/Linux:
   source venv/bin/activate

3. Install Dependencies
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install -r requirements.txt

This will install all required packages:

* customtkinter - Modern UI framework
* cryptography - Encryption library
* argon2-cffi - Password hashing
* pillow - Image processing
* pyzxcvbn - Password strength checking

4. Verify Installation
~~~~~~~~~~~~~~~~~~~~~~~

Run the application:

.. code-block:: bash

   python main.py

If the login window appears, installation was successful!

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Issue: "ModuleNotFoundError"**

Solution: Make sure you activated the virtual environment and installed all dependencies.

.. code-block:: bash

   pip install -r requirements.txt

**Issue: "Python not found"**

Solution: Ensure Python is in your PATH or use the full path to python executable.

**Issue: Application doesn't start**

Solution: Check the logs in ``logs/password_manager.log`` for error details.

**Issue: "Permission denied" on Linux/macOS**

Solution: Make the main script executable:

.. code-block:: bash

   chmod +x main.py

Getting Help
~~~~~~~~~~~~

If you encounter issues:

1. Check the troubleshooting section in the README
2. Review the logs in the ``logs/`` directory
3. Open an issue on GitHub with:

   * Your operating system
   * Python version (``python --version``)
   * Error message or logs
   * Steps to reproduce

Next Steps
----------

After installation, proceed to :doc:`getting-started` to create your first account and start using the Password Manager.
