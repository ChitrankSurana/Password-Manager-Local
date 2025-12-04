Testing
=======

Comprehensive guide to testing the Password Manager application.

Test Strategy
-------------

Test Pyramid
~~~~~~~~~~~~

We follow the test pyramid approach:

.. code-block:: text

   ┌───────────────┐
   │   E2E Tests   │  ← 5%: Critical user workflows
   │  (Manual/Auto)│
   ├───────────────┤
   │ Integration   │  ← 20%: Component interactions
   │    Tests      │
   ├───────────────┤
   │   Unit Tests  │  ← 75%: Individual functions
   │               │
   └───────────────┘

Testing Tools
~~~~~~~~~~~~~

* **pytest**: Test framework
* **pytest-cov**: Code coverage
* **pytest-mock**: Mocking utilities
* **hypothesis**: Property-based testing
* **selenium**: UI automation (future)

Running Tests
-------------

All Tests
~~~~~~~~~

.. code-block:: bash

   # Run all tests
   pytest

   # Run with verbose output
   pytest -v

   # Run with coverage
   pytest --cov=src --cov-report=html

   # Open coverage report
   open htmlcov/index.html  # macOS/Linux
   start htmlcov\\index.html  # Windows

Specific Tests
~~~~~~~~~~~~~~

.. code-block:: bash

   # Run specific test file
   pytest tests/test_password_manager.py

   # Run specific test function
   pytest tests/test_encryption.py::test_encrypt_password

   # Run tests matching pattern
   pytest -k "encrypt"

   # Run failed tests only
   pytest --lf

By Category
~~~~~~~~~~~

.. code-block:: bash

   # Unit tests only
   pytest tests/unit/

   # Integration tests only
   pytest tests/integration/

   # With markers
   pytest -m "slow"       # Slow tests
   pytest -m "not slow"   # Skip slow tests

Unit Tests
----------

Core Module Tests
~~~~~~~~~~~~~~~~~

**Password Manager Tests** (``tests/unit/test_password_manager.py``):

.. code-block:: python

   def test_add_password_valid_input_creates_entry(setup_manager):
       \"\"\"Test that add_password creates entry with valid input.\"\"\"
       manager, session = setup_manager

       entry = manager.add_password(
           session=session,
           website="github.com",
           username="user@email.com",
           password="SecurePass123!"
       )

       assert entry.password_id is not None
       assert entry.website == "github.com"
       assert entry.username == "user@email.com"

   def test_authenticate_user_invalid_password_raises_error(setup_manager):
       \"\"\"Test that authentication fails with wrong password.\"\"\"
       manager, _ = setup_manager

       with pytest.raises(InvalidCredentialsError):
           manager.authenticate_user("testuser", "wrongpassword")

**Encryption Tests** (``tests/unit/test_encryption.py``):

.. code-block:: python

   def test_encrypt_decrypt_roundtrip():
       \"\"\"Test that encryption and decryption are inverse operations.\"\"\"
       service = EncryptionService()
       key = service.derive_key("masterpassword", b"salt123")
       plaintext = "MySecurePassword123!"

       encrypted = service.encrypt_password(plaintext, key)
       decrypted = service.decrypt_password(encrypted, key)

       assert decrypted == plaintext
       assert encrypted != plaintext

   def test_hash_password_different_salts_produce_different_hashes():
       \"\"\"Test that same password with different salts hashes differently.\"\"\"
       service = EncryptionService()
       password = "password123"
       salt1 = os.urandom(16)
       salt2 = os.urandom(16)

       hash1 = service.hash_password(password, salt1)
       hash2 = service.hash_password(password, salt2)

       assert hash1 != hash2

Fixtures
~~~~~~~~

**Common Fixtures** (``tests/conftest.py``):

.. code-block:: python

   import pytest
   from src.core.password_manager import PasswordManager

   @pytest.fixture
   def temp_db(tmp_path):
       \"\"\"Create a temporary database for testing.\"\"\"
       db_path = tmp_path / "test.db"
       yield str(db_path)
       # Cleanup happens automatically

   @pytest.fixture
   def password_manager(temp_db):
       \"\"\"Create a PasswordManager instance with temp database.\"\"\"
       manager = PasswordManager(db_path=temp_db)
       manager.initialize_database()
       return manager

   @pytest.fixture
   def authenticated_session(password_manager):
       \"\"\"Create a test user and return authenticated session.\"\"\"
       manager = password_manager
       manager.create_user("testuser", "test@email.com", "TestPass123!")
       session = manager.authenticate_user("testuser", "TestPass123!")
       return manager, session

Parameterized Tests
~~~~~~~~~~~~~~~~~~~

Test multiple scenarios:

.. code-block:: python

   @pytest.mark.parametrize("password,expected_strength", [
       ("abc", 0.1),           # Very weak
       ("password123", 0.2),   # Weak
       ("MyP@ssw0rd", 0.6),    # Good
       ("C0rr3ct-H0rs3-B@tt3ry-St@pl3", 0.95),  # Excellent
   ])
   def test_password_strength_calculation(password, expected_strength):
       \"\"\"Test password strength calculation for various inputs.\"\"\"
       generator = PasswordGenerator()
       strength = generator.calculate_strength(password)
       assert abs(strength - expected_strength) < 0.1

Integration Tests
-----------------

Database Integration
~~~~~~~~~~~~~~~~~~~~

Test database operations:

.. code-block:: python

   def test_password_crud_operations(password_manager, authenticated_session):
       \"\"\"Test complete CRUD lifecycle for passwords.\"\"\"
       manager, session = authenticated_session

       # Create
       entry = manager.add_password(
           session, "test.com", "user", "pass123", "Test account"
       )
       password_id = entry.password_id

       # Read
       retrieved = manager.get_password(session, password_id)
       assert retrieved.website == "test.com"

       # Update
       manager.update_password(session, password_id, username="newuser")
       updated = manager.get_password(session, password_id)
       assert updated.username == "newuser"

       # Delete
       manager.delete_password(session, password_id)
       with pytest.raises(PasswordNotFoundError):
           manager.get_password(session, password_id)

Encryption Integration
~~~~~~~~~~~~~~~~~~~~~~

Test encryption in context:

.. code-block:: python

   def test_password_encryption_persists_across_sessions(temp_db):
       \"\"\"Test that passwords remain encrypted in database.\"\"\"
       # Session 1: Create password
       manager1 = PasswordManager(temp_db)
       session1 = manager1.authenticate_user("testuser", "masterpass")
       entry = manager1.add_password(session1, "test.com", "user", "secret")
       manager1.logout(session1)

       # Verify password is encrypted in database
       import sqlite3
       conn = sqlite3.connect(temp_db)
       cursor = conn.execute(
           "SELECT encrypted_password FROM passwords WHERE password_id = ?",
           (entry.password_id,)
       )
       encrypted = cursor.fetchone()[0]
       assert "secret" not in encrypted  # Not plain text

       # Session 2: Retrieve password
       manager2 = PasswordManager(temp_db)
       session2 = manager2.authenticate_user("testuser", "masterpass")
       retrieved = manager2.get_password(session2, entry.password_id)
       assert retrieved.password == "secret"  # Decrypted correctly

Cache Integration
~~~~~~~~~~~~~~~~~

Test caching behavior:

.. code-block:: python

   def test_cache_improves_search_performance(password_manager, authenticated_session):
       \"\"\"Test that cache speeds up repeated searches.\"\"\"
       manager, session = authenticated_session

       # Add test passwords
       for i in range(100):
           manager.add_password(session, f"site{i}.com", f"user{i}", "pass")

       # First search (cache miss)
       import time
       start = time.time()
       results1 = manager.search_password_entries(session, "site50")
       time1 = time.time() - start

       # Second search (cache hit)
       start = time.time()
       results2 = manager.search_password_entries(session, "site50")
       time2 = time.time() - start

       # Verify cache improvement
       assert time2 < time1 * 0.5  # At least 50% faster
       assert results1 == results2  # Same results

GUI Tests
---------

Widget Tests
~~~~~~~~~~~~

Test individual widgets:

.. code-block:: python

   def test_add_password_dialog_validates_input():
       \"\"\"Test that dialog validates required fields.\"\"\"
       dialog = AddPasswordDialog(parent=None)

       # Empty website should show error
       dialog.website_entry.set("")
       dialog.username_entry.set("user")
       dialog.password_entry.set("pass")

       with pytest.raises(ValidationError):
           dialog.on_save()

       # Verify error message displayed
       assert "Website is required" in dialog.error_label.cget("text")

Window Flow Tests
~~~~~~~~~~~~~~~~~

Test navigation between windows:

.. code-block:: python

   def test_login_to_main_window_flow():
       \"\"\"Test successful login opens main window.\"\"\"
       app = App()
       login_window = app.show_login_window()

       # Fill credentials
       login_window.username_entry.insert(0, "testuser")
       login_window.password_entry.insert(0, "testpass")

       # Submit
       login_window.on_login()

       # Verify main window opens
       assert app.main_window is not None
       assert app.main_window.winfo_viewable()
       assert not login_window.winfo_viewable()

Mock Tests
----------

Mocking External Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def test_password_health_check_api_failure_handled(mocker, password_manager):
       \"\"\"Test that API failures don't crash health check.\"\"\"
       # Mock the API call to raise an exception
       mock_api = mocker.patch('src.core.password_health.check_breach_api')
       mock_api.side_effect = requests.ConnectionError("API unavailable")

       manager, session = password_manager
       entry = manager.add_password(session, "test.com", "user", "password123")

       # Should not raise, should return unknown status
       health = manager.check_password_health(session, entry.password_id)
       assert health.breach_status == "unknown"
       assert "API unavailable" in health.breach_message

Property-Based Testing
----------------------

Using Hypothesis
~~~~~~~~~~~~~~~~

Test properties that should always hold:

.. code-block:: python

   from hypothesis import given, strategies as st

   @given(
       password=st.text(min_size=8, max_size=64),
       key=st.binary(min_size=32, max_size=32)
   )
   def test_encryption_always_reversible(password, key):
       \"\"\"Property: encrypt(decrypt(x)) = x for all valid passwords.\"\"\"
       service = EncryptionService()

       encrypted = service.encrypt_password(password, key)
       decrypted = service.decrypt_password(encrypted, key)

       assert decrypted == password

   @given(length=st.integers(min_value=8, max_value=64))
   def test_generated_password_always_correct_length(length):
       \"\"\"Property: Generated passwords always match requested length.\"\"\"
       generator = PasswordGenerator()
       options = GenerationOptions(
           length=length,
           use_uppercase=True,
           use_lowercase=True,
           use_numbers=True,
           use_symbols=True
       )

       password = generator.generate(options)

       assert len(password) == length

Performance Tests
-----------------

Benchmarking
~~~~~~~~~~~~

.. code-block:: python

   import pytest

   @pytest.mark.benchmark
   def test_search_performance_with_large_dataset(benchmark, password_manager):
       \"\"\"Benchmark search performance with 10,000 passwords.\"\"\"
       manager, session = password_manager

       # Setup: Add 10,000 passwords
       for i in range(10000):
           manager.add_password(session, f"site{i}.com", f"user{i}", "pass")

       # Benchmark search
       result = benchmark(
           manager.search_password_entries,
           session,
           "site5000"
       )

       # Verify result
       assert len(result) > 0
       assert result[0].website == "site5000.com"

Run benchmarks:

.. code-block:: bash

   pytest tests/performance/ --benchmark-only

Load Testing
~~~~~~~~~~~~

Test with realistic data volumes:

.. code-block:: python

   @pytest.mark.slow
   def test_handles_1000_passwords(password_manager):
       \"\"\"Test that app handles 1000+ passwords efficiently.\"\"\"
       manager, session = password_manager

       # Add 1000 passwords
       for i in range(1000):
           manager.add_password(
               session,
               f"website{i}.com",
               f"user{i}@email.com",
               f"password{i}"
           )

       # Operations should still be fast
       import time

       # Search
       start = time.time()
       results = manager.search_password_entries(session, "website500")
       search_time = time.time() - start
       assert search_time < 0.1  # < 100ms

       # List all
       start = time.time()
       all_passwords = manager.get_all_passwords(session)
       list_time = time.time() - start
       assert list_time < 0.5  # < 500ms
       assert len(all_passwords) == 1000

Test Coverage
-------------

Measuring Coverage
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Generate coverage report
   pytest --cov=src --cov-report=html --cov-report=term

   # View in browser
   open htmlcov/index.html

Coverage Goals
~~~~~~~~~~~~~~

* **Overall**: 80%+
* **Core modules**: 90%+
* **Encryption**: 100%
* **Authentication**: 100%
* **GUI**: 60%+ (harder to test)

Missing Coverage
~~~~~~~~~~~~~~~~

Identify untested code:

.. code-block:: bash

   pytest --cov=src --cov-report=term-missing

CI/CD Testing
-------------

GitHub Actions
~~~~~~~~~~~~~~

``.github/workflows/test.yml``:

.. code-block:: yaml

   name: Tests

   on: [push, pull_request]

   jobs:
     test:
       runs-on: ${{ matrix.os }}
       strategy:
         matrix:
           os: [ubuntu-latest, windows-latest, macos-latest]
           python-version: ['3.10', '3.11', '3.12']

       steps:
         - uses: actions/checkout@v3

         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: ${{ matrix.python-version }}

         - name: Install dependencies
           run: |
             pip install -r requirements.txt
             pip install pytest pytest-cov

         - name: Run tests
           run: pytest --cov=src --cov-report=xml

         - name: Upload coverage
           uses: codecov/codecov-action@v3
           with:
             file: ./coverage.xml

Manual Testing
--------------

Test Plan
~~~~~~~~~

See the project's ``TESTING.md`` for comprehensive manual test plan with:

* 33 test cases across 10 categories
* Step-by-step procedures
* Expected results
* Acceptance criteria

Critical User Workflows
~~~~~~~~~~~~~~~~~~~~~~~

1. **New User Registration**:

   * Sign up → Create master password → Login → Add first password

2. **Password Management**:

   * Add → Edit → Delete → Search → Copy

3. **Browser Extension**:

   * Install → Connect → Auto-fill → Capture password

4. **Import/Export**:

   * Export encrypted → Restore from backup

Test on Multiple Platforms
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Windows**: 10, 11
* **macOS**: 10.14+
* **Linux**: Ubuntu 20.04+, Fedora, Arch

Debugging Tests
---------------

Verbose Output
~~~~~~~~~~~~~~

.. code-block:: bash

   # Show print statements
   pytest -s

   # Very verbose
   pytest -vv

   # Show locals on failure
   pytest -l

Debugging with pdb
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def test_something():
       result = some_function()
       import pdb; pdb.set_trace()  # Breakpoint
       assert result == expected

Run with:

.. code-block:: bash

   pytest --pdb  # Drop into pdb on failure

Using VS Code
~~~~~~~~~~~~~

Configure ``.vscode/launch.json``:

.. code-block:: json

   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Python: Debug Tests",
         "type": "python",
         "request": "launch",
         "module": "pytest",
         "args": ["-v"],
         "console": "integratedTerminal"
       }
     ]
   }

Best Practices
--------------

1. **Write Tests First** (TDD): Test → Fail → Implement → Pass
2. **Test One Thing**: Each test should verify one behavior
3. **Use Descriptive Names**: Test name should explain what's tested
4. **Arrange-Act-Assert**: Structure tests clearly
5. **Avoid Test Interdependence**: Tests should be isolated
6. **Mock External Dependencies**: Don't hit real APIs/databases
7. **Test Edge Cases**: Empty input, null, max values, etc.
8. **Keep Tests Fast**: Unit tests < 100ms, integration < 1s
9. **Maintain Tests**: Update tests when code changes
10. **Review Coverage**: Aim for high coverage, but prioritize critical paths

Resources
---------

* pytest documentation: https://docs.pytest.org/
* Hypothesis documentation: https://hypothesis.readthedocs.io/
* Testing best practices: https://docs.python-guide.org/writing/tests/
