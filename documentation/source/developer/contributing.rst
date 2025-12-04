Contributing
============

Thank you for your interest in contributing to the Password Manager project!

Getting Started
---------------

Prerequisites
~~~~~~~~~~~~~

* Python 3.10 or later
* Git for version control
* Text editor or IDE (VS Code, PyCharm recommended)
* Basic knowledge of Python and Tkinter

Setting Up Development Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Fork and Clone:**

   .. code-block:: bash

      git clone https://github.com/yourusername/password-manager.git
      cd password-manager

2. **Create Virtual Environment:**

   .. code-block:: bash

      python -m venv venv
      source venv/bin/activate  # On Windows: venv\\Scripts\\activate

3. **Install Dependencies:**

   .. code-block:: bash

      pip install -r requirements.txt
      pip install -r requirements-dev.txt  # Development dependencies

4. **Install Pre-commit Hooks:**

   .. code-block:: bash

      pre-commit install

5. **Verify Setup:**

   .. code-block:: bash

      python main.py  # Should launch the application
      pytest          # Should run tests

Development Workflow
--------------------

Branching Strategy
~~~~~~~~~~~~~~~~~~

We use Git Flow:

* ``main``: Production-ready code
* ``develop``: Integration branch for features
* ``feature/*``: New features
* ``bugfix/*``: Bug fixes
* ``hotfix/*``: Critical production fixes

**Creating a Feature Branch:**

.. code-block:: bash

   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name

Making Changes
~~~~~~~~~~~~~~

1. **Write Code:**

   * Follow the code style guide (below)
   * Add type hints to functions
   * Write docstrings for public APIs

2. **Write Tests:**

   * Unit tests for new functions
   * Integration tests for features
   * Aim for 80%+ code coverage

3. **Update Documentation:**

   * Update docstrings
   * Add/update user guide sections if needed
   * Update CHANGELOG.md

4. **Test Locally:**

   .. code-block:: bash

      pytest                    # Run all tests
      pytest tests/test_foo.py  # Run specific test
      mypy src/                 # Type checking
      pylint src/               # Linting

5. **Commit Changes:**

   .. code-block:: bash

      git add .
      git commit -m "feat: add password strength indicator

      - Implement zxcvbn-based strength calculation
      - Add visual strength meter to UI
      - Update tests and documentation"

Code Style Guide
----------------

Python Style
~~~~~~~~~~~~

We follow **PEP 8** with some modifications:

**General:**

* Line length: 100 characters (not 80)
* Indentation: 4 spaces (no tabs)
* Encoding: UTF-8

**Naming Conventions:**

.. code-block:: python

   # Classes: PascalCase
   class PasswordManager:
       pass

   # Functions/Methods: snake_case
   def authenticate_user(username: str) -> bool:
       pass

   # Constants: UPPER_SNAKE_CASE
   MAX_PASSWORD_LENGTH = 64

   # Private: prefix with underscore
   def _internal_method():
       pass

**Type Hints:**

Always use type hints:

.. code-block:: python

   from typing import Optional, List, Dict

   def search_passwords(
       query: str,
       user_id: int,
       include_favorites: bool = True
   ) -> List[PasswordEntry]:
       \"\"\"Search for passwords matching query.\"\"\"
       pass

Docstring Format
~~~~~~~~~~~~~~~~

Use Google-style docstrings:

.. code-block:: python

   def add_password(
       self,
       session: Session,
       website: str,
       username: str,
       password: str,
       remarks: Optional[str] = None
   ) -> PasswordEntry:
       \"\"\"Add a new password entry.

       Args:
           session: Active user session with valid encryption key.
           website: Website or application name (e.g., "github.com").
           username: Username or email address.
           password: Plain text password to encrypt and store.
           remarks: Optional notes about this password.

       Returns:
           The newly created password entry with generated ID.

       Raises:
           InvalidSessionError: If session is invalid or expired.
           ValidationError: If required fields are missing or invalid.
           EncryptionError: If password encryption fails.

       Example:
           >>> entry = manager.add_password(
           ...     session=session,
           ...     website="github.com",
           ...     username="user@email.com",
           ...     password="SecurePass123!"
           ... )
           >>> print(entry.password_id)
           42
       \"\"\"
       pass

Import Organization
~~~~~~~~~~~~~~~~~~~

Order imports as follows:

.. code-block:: python

   # 1. Standard library
   import os
   import sys
   from datetime import datetime
   from typing import Optional, List

   # 2. Third-party libraries
   import customtkinter as ctk
   from cryptography.fernet import Fernet

   # 3. Local application imports
   from src.core.password_manager import PasswordManager
   from src.core.types import Session, PasswordEntry

Testing Guidelines
------------------

Writing Tests
~~~~~~~~~~~~~

**Test File Naming:**

* ``test_<module_name>.py``
* Place in ``tests/`` directory
* Mirror source structure

**Test Function Naming:**

.. code-block:: python

   def test_<function_name>_<scenario>_<expected_result>():
       \"\"\"Test that function_name does X when Y.\"\"\"
       pass

   # Examples
   def test_add_password_valid_input_creates_entry():
       pass

   def test_authenticate_user_invalid_password_raises_error():
       pass

**Test Structure (AAA Pattern):**

.. code-block:: python

   def test_encrypt_password_valid_input_returns_encrypted():
       # Arrange
       encryption_service = EncryptionService()
       key = encryption_service.derive_key("master", b"salt")
       plaintext = "SecurePassword123!"

       # Act
       encrypted = encryption_service.encrypt_password(plaintext, key)

       # Assert
       assert encrypted != plaintext
       assert isinstance(encrypted, str)
       assert len(encrypted) > len(plaintext)

Test Coverage
~~~~~~~~~~~~~

Aim for:

* **80%+ overall** code coverage
* **100%** for critical paths (encryption, authentication)
* **60%+** for UI code (harder to test)

Check coverage:

.. code-block:: bash

   pytest --cov=src --cov-report=html
   open htmlcov/index.html

Integration Tests
~~~~~~~~~~~~~~~~~

Test component interactions:

.. code-block:: python

   def test_full_password_lifecycle():
       \"\"\"Test complete password add-edit-delete flow.\"\"\"
       # Setup
       manager = PasswordManager(":memory:")
       session = manager.authenticate_user("testuser", "testpass")

       # Add
       entry = manager.add_password(session, "test.com", "user", "pass")
       assert entry.password_id is not None

       # Edit
       manager.update_password(session, entry.password_id, username="newuser")
       updated = manager.get_password(session, entry.password_id)
       assert updated.username == "newuser"

       # Delete
       manager.delete_password(session, entry.password_id)
       with pytest.raises(PasswordNotFoundError):
           manager.get_password(session, entry.password_id)

Commit Message Format
----------------------

We use **Conventional Commits**:

.. code-block:: text

   <type>(<scope>): <subject>

   <body>

   <footer>

**Types:**

* ``feat``: New feature
* ``fix``: Bug fix
* ``docs``: Documentation changes
* ``style``: Code style changes (formatting)
* ``refactor``: Code refactoring
* ``test``: Adding/updating tests
* ``chore``: Maintenance tasks

**Examples:**

.. code-block:: text

   feat(encryption): add Argon2 password hashing

   Replace PBKDF2 with Argon2id for better security against
   GPU-based attacks. Maintains backwards compatibility through
   hash type detection.

   Closes #123

.. code-block:: text

   fix(gui): prevent password field from accepting empty input

   Add validation to ensure password field is not empty before
   submission. Show error message to user if validation fails.

   Fixes #456

Pull Request Process
--------------------

Creating a Pull Request
~~~~~~~~~~~~~~~~~~~~~~~

1. **Push Your Branch:**

   .. code-block:: bash

      git push origin feature/your-feature-name

2. **Open Pull Request:**

   * Go to GitHub repository
   * Click "New Pull Request"
   * Select your branch
   * Fill out the PR template

3. **PR Template Fields:**

   * **Description**: What does this PR do?
   * **Type**: Feature / Bug Fix / Documentation / etc.
   * **Breaking Changes**: Yes / No
   * **Tested**: How did you test this?
   * **Screenshots**: If UI changes
   * **Checklist**: Complete all items

PR Review Process
~~~~~~~~~~~~~~~~~

**Automatic Checks:**

* All tests must pass
* Code coverage must not decrease
* Linting must pass (pylint, mypy)
* Documentation builds successfully

**Manual Review:**

* At least one maintainer approval required
* Code follows style guide
* Changes are well-tested
* Documentation is updated

**Addressing Feedback:**

* Make requested changes
* Push new commits to same branch
* PR updates automatically
* Request re-review when ready

Merging
~~~~~~~

* **Squash and Merge**: For feature branches
* **Merge Commit**: For release branches
* **Rebase and Merge**: For small fixes

Code of Conduct
---------------

Be Respectful
~~~~~~~~~~~~~

* Treat all contributors with respect
* Welcome newcomers
* Be patient with questions
* Provide constructive feedback

Be Professional
~~~~~~~~~~~~~~~

* Focus on the code, not the person
* Avoid personal attacks
* Keep discussions on-topic
* Respect differing opinions

Be Collaborative
~~~~~~~~~~~~~~~~

* Help others succeed
* Share knowledge
* Give credit where due
* Celebrate contributions

Reporting Issues
----------------

Bug Reports
~~~~~~~~~~~

Include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Numbered steps
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**:

   * OS and version
   * Python version
   * Application version

6. **Logs**: Attach relevant log files
7. **Screenshots**: If applicable

Feature Requests
~~~~~~~~~~~~~~~~

Include:

1. **Problem**: What problem does this solve?
2. **Proposed Solution**: How should it work?
3. **Alternatives**: Other approaches considered
4. **Use Case**: When would you use this?
5. **Priority**: How important is this?

Getting Help
------------

* **Documentation**: Start with this documentation
* **Issues**: Search existing issues first
* **Discussions**: Use GitHub Discussions for questions
* **Email**: contact@passwordmanager.dev (for private matters)

Recognition
-----------

Contributors are recognized in:

* CONTRIBUTORS.md file
* Release notes
* About dialog in application
* Annual contributor list

Thank you for contributing to Password Manager!
