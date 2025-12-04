Password Manager Documentation
=================================

Welcome to the Password Manager documentation. This is a secure, local-first password management application with advanced encryption and modern features.

.. image:: https://img.shields.io/badge/python-3.10+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python Version

.. image:: https://img.shields.io/badge/license-MIT-green.svg
   :alt: License

Features
--------

* **Strong Encryption**: Uses Argon2 for key derivation and Fernet (AES-256) for password encryption
* **Local Storage**: All data stored locally in encrypted SQLite database
* **Password Generation**: Generate secure random passwords with customizable options
* **Password Health**: Monitor weak, reused, and compromised passwords
* **Browser Extension**: Auto-fill passwords in Chrome, Edge, and other Chromium browsers
* **Import/Export**: Backup and restore your passwords securely
* **Cross-Platform**: Works on Windows, macOS, and Linux
* **Modern UI**: Clean, intuitive interface built with CustomTkinter

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   pip install -r requirements.txt
   python main.py

Basic Usage
~~~~~~~~~~~

1. Create an account with a strong master password
2. Log in to access your password vault
3. Add, edit, and manage your passwords
4. Use the browser extension for auto-fill functionality

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user-guide/installation
   user-guide/getting-started
   user-guide/managing-passwords
   user-guide/browser-extension
   user-guide/import-export
   user-guide/settings

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/core
   api/gui
   api/utils

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide

   developer/architecture
   developer/contributing
   developer/testing
   developer/deployment

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
