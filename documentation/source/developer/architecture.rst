Architecture
============

This document describes the architecture and design of the Password Manager application.

Overview
--------

The Password Manager follows a layered architecture with clear separation of concerns:

.. code-block:: text

   ┌─────────────────────────────────────────┐
   │          Presentation Layer              │
   │     (GUI - CustomTkinter Windows)        │
   └──────────────┬──────────────────────────┘
                  │
   ┌──────────────▼──────────────────────────┐
   │          Business Logic Layer            │
   │     (Password Manager, Encryption)       │
   └──────────────┬──────────────────────────┘
                  │
   ┌──────────────▼──────────────────────────┐
   │           Data Access Layer              │
   │    (Database Manager, Migrations)        │
   └──────────────┬──────────────────────────┘
                  │
   ┌──────────────▼──────────────────────────┐
   │          Storage Layer                   │
   │        (SQLite Database)                 │
   └──────────────────────────────────────────┘

Project Structure
-----------------

Directory Layout
~~~~~~~~~~~~~~~~

.. code-block:: text

   Password-Manager-Local/
   ├── src/
   │   ├── core/                 # Core business logic
   │   │   ├── password_manager.py
   │   │   ├── encryption.py
   │   │   ├── database_manager.py
   │   │   ├── session_manager.py
   │   │   ├── database_migrations.py
   │   │   ├── password_cache.py
   │   │   ├── performance_monitor.py
   │   │   ├── import_export.py
   │   │   └── types.py
   │   ├── gui/                  # User interface
   │   │   ├── main_window.py
   │   │   ├── login_window.py
   │   │   ├── signup_window.py
   │   │   ├── add_password_dialog.py
   │   │   ├── edit_password_dialog.py
   │   │   ├── export_dialog.py
   │   │   └── settings_dialog.py
   │   └── utils/                # Utilities
   │       └── logger.py
   ├── data/                     # Application data
   │   └── password_manager.db   # SQLite database
   ├── logs/                     # Log files
   ├── tests/                    # Unit and integration tests
   ├── documentation/            # Sphinx documentation
   ├── main.py                   # Application entry point
   ├── requirements.txt          # Python dependencies
   └── README.md                 # Project README

Core Components
---------------

Password Manager (``password_manager.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Responsibilities:**

* High-level password CRUD operations
* User authentication and authorization
* Business logic for password management
* Integration point for all core services

**Key Classes:**

.. code-block:: python

   class PasswordManager:
       def __init__(self, db_path, encryption_service, session_manager)
       def authenticate_user(username, password) -> Session
       def add_password(session, website, username, password) -> PasswordEntry
       def get_password(session, password_id) -> PasswordEntry
       def update_password(session, password_id, **updates)
       def delete_password(session, password_id)
       def search_password_entries(session, criteria) -> List[PasswordEntry]

**Design Patterns:**

* **Facade Pattern**: Simplifies interaction with complex subsystems
* **Service Layer**: Coordinates operations across multiple components

Encryption (``encryption.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Responsibilities:**

* Master password hashing using Argon2
* Password encryption/decryption using Fernet (AES-256)
* Key derivation and management
* Secure password generation

**Key Classes:**

.. code-block:: python

   class EncryptionService:
       def hash_password(password: str, salt: bytes) -> bytes
       def verify_password(password: str, salt: bytes, hash: bytes) -> bool
       def derive_key(master_password: str, salt: bytes) -> bytes
       def encrypt_password(password: str, key: bytes) -> str
       def decrypt_password(encrypted: str, key: bytes) -> str

   class PasswordGenerator:
       def generate(length: int, options: GenerationOptions) -> str
       def calculate_strength(password: str) -> float

**Security Features:**

* Argon2id for password hashing (memory-hard, GPU-resistant)
* Fernet symmetric encryption (AES-256-CBC + HMAC-SHA256)
* Cryptographically secure random generation
* Constant-time comparison for password verification

Database Manager (``database_manager.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Responsibilities:**

* SQL database operations
* Connection management
* Transaction handling
* Query execution

**Key Classes:**

.. code-block:: python

   class DatabaseManager:
       def __init__(self, db_path: str)
       def execute_query(query: str, params: tuple) -> Cursor
       def fetch_one(query: str, params: tuple) -> Dict
       def fetch_all(query: str, params: tuple) -> List[Dict]
       def commit()
       def rollback()

**Design Patterns:**

* **Repository Pattern**: Abstracts data access
* **Unit of Work**: Manages transactions

**Database Schema:**

.. code-block:: sql

   CREATE TABLE users (
       user_id INTEGER PRIMARY KEY AUTOINCREMENT,
       username TEXT UNIQUE NOT NULL,
       email TEXT UNIQUE NOT NULL,
       master_password_hash BLOB NOT NULL,
       salt BLOB NOT NULL,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       last_login TIMESTAMP
   );

   CREATE TABLE passwords (
       password_id INTEGER PRIMARY KEY AUTOINCREMENT,
       user_id INTEGER NOT NULL,
       website TEXT NOT NULL,
       username TEXT NOT NULL,
       encrypted_password TEXT NOT NULL,
       remarks TEXT,
       is_favorite BOOLEAN DEFAULT 0,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
   );

   CREATE INDEX idx_passwords_user_id ON passwords(user_id);
   CREATE INDEX idx_passwords_website ON passwords(website);
   CREATE INDEX idx_passwords_created_at ON passwords(created_at DESC);

Session Manager (``session_manager.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Responsibilities:**

* User session lifecycle management
* Session validation and timeout
* Encryption key caching
* Security context management

**Key Classes:**

.. code-block:: python

   class Session:
       user_id: int
       username: str
       encryption_key: bytes
       created_at: datetime
       last_activity: datetime
       timeout_minutes: int

   class SessionManager:
       def create_session(user_id, username, encryption_key, timeout) -> Session
       def validate_session(session: Session) -> bool
       def update_activity(session: Session)
       def terminate_session(session: Session)
       def is_expired(session: Session) -> bool

**Security Features:**

* Automatic session timeout
* Activity tracking
* Secure key storage in memory
* Session invalidation on logout

Database Migrations (``database_migrations.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Responsibilities:**

* Schema version control
* Automated database upgrades
* Data migration between versions
* Rollback capabilities

**Key Classes:**

.. code-block:: python

   class DatabaseMigration:
       def get_current_version() -> int
       def migrate_to_latest()
       def migrate_to_version(target_version: int)
       def rollback_to_version(target_version: int)

**Migration System:**

* Version tracking in ``schema_version`` table
* Incremental migrations (v1 → v2 → v3)
* Each migration is a transaction
* Failed migrations roll back automatically

Performance Optimization
------------------------

Password Cache (``password_cache.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:**

* Reduce database queries
* Improve search and list performance
* Cache frequently accessed passwords

**Implementation:**

* LRU (Least Recently Used) cache
* TTL (Time To Live) expiration
* Thread-safe operations
* Automatic invalidation on updates

**Cache Strategy:**

.. code-block:: python

   # Cache Key Structure
   CacheKey = f"{user_id}:{operation}:{parameters}"

   # Example Keys
   "123:all_passwords"
   "123:search:github"
   "123:website:github.com"

**Eviction Policy:**

1. LRU: Removes least recently used when full
2. TTL: Expires entries after configured duration
3. Explicit: Invalidates on create/update/delete

Performance Monitor (``performance_monitor.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:**

* Track operation performance
* Identify bottlenecks
* Monitor cache effectiveness
* Generate performance reports

**Tracked Metrics:**

* Operation duration
* Cache hit/miss rates
* Database query times
* Memory usage
* Error rates

**Usage:**

.. code-block:: python

   with PerformanceTracker(monitor, "search_passwords"):
       results = password_manager.search_password_entries(criteria)

GUI Architecture
----------------

CustomTkinter Framework
~~~~~~~~~~~~~~~~~~~~~~~

**Why CustomTkinter:**

* Modern, clean UI out of the box
* Built-in dark/light theme support
* Responsive widgets
* Cross-platform consistency
* Easy to customize

**Window Hierarchy:**

.. code-block:: text

   App (CTk)
   ├── LoginWindow (CTkToplevel)
   ├── SignupWindow (CTkToplevel)
   └── MainWindow (CTkToplevel)
       ├── AddPasswordDialog (CTkToplevel)
       ├── EditPasswordDialog (CTkToplevel)
       ├── ExportDialog (CTkToplevel)
       └── SettingsDialog (CTkToplevel)

Main Window Components
~~~~~~~~~~~~~~~~~~~~~~

**Layout:**

.. code-block:: python

   MainWindow
   ├── Header Frame
   │   ├── Search Entry
   │   ├── Add Button
   │   ├── Settings Button
   │   └── Logout Button
   ├── Content Frame
   │   ├── Password List (CTkScrollableFrame)
   │   │   └── Password Entry Widgets
   │   └── Empty State (when no passwords)
   └── Footer Frame
       ├── Health Indicator
       └── Status Labels

**Event Handling:**

* Command callbacks for buttons
* Variable traces for search
* Keyboard shortcuts
* Context menus

Data Flow
---------

User Authentication Flow
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   User Input
       ↓
   LoginWindow.on_login()
       ↓
   PasswordManager.authenticate_user()
       ↓
   Encryption.verify_password()  ←  DatabaseManager.get_user()
       ↓
   SessionManager.create_session()
       ↓
   MainWindow.show()

Password Addition Flow
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   User Input
       ↓
   AddPasswordDialog.on_save()
       ↓
   PasswordManager.add_password()
       ↓
   ├─→ Encryption.encrypt_password()
   └─→ DatabaseManager.insert()
       ↓
   PasswordCache.invalidate()
       ↓
   MainWindow.refresh_password_list()

Password Search Flow
~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Search Input
       ↓
   MainWindow.on_search_change()  (debounced)
       ↓
   PasswordManager.search_password_entries()
       ↓
   PasswordCache.get()  ←─  Cache Hit?
       ↓ (Cache Miss)
   DatabaseManager.query()
       ↓
   PasswordCache.set()
       ↓
   MainWindow.update_password_list()

Security Architecture
---------------------

Encryption Chain
~~~~~~~~~~~~~~~~

.. code-block:: text

   Master Password
       ↓
   [Argon2id Hash] → Verification Hash (stored)
       ↓
   [Key Derivation] → Encryption Key (in memory)
       ↓
   [Fernet Encrypt] → Encrypted Password (stored)

**Key Points:**

* Master password never stored
* Encryption key exists only in session memory
* Each password encrypted independently
* Salt unique per user

Defense in Depth
~~~~~~~~~~~~~~~~

**Layer 1 - Application:**

* Input validation
* SQL injection prevention (parameterized queries)
* XSS prevention (not applicable, desktop app)
* Session timeout

**Layer 2 - Encryption:**

* Strong algorithms (Argon2, AES-256)
* Proper key derivation
* Secure random generation

**Layer 3 - Storage:**

* Encrypted passwords at rest
* Database file permissions
* Secure deletion

**Layer 4 - Memory:**

* Encryption keys in memory only
* No password caching in plain text
* Secure string handling

Error Handling
--------------

Exception Hierarchy
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   PasswordManagerException (base)
   ├── AuthenticationError
   │   ├── InvalidCredentialsError
   │   ├── UserNotFoundError
   │   └── SessionExpiredError
   ├── DatabaseError
   │   ├── ConnectionError
   │   ├── QueryError
   │   └── MigrationError
   ├── EncryptionError
   │   ├── DecryptionFailedError
   │   └── KeyDerivationError
   └── ValidationError
       ├── InvalidPasswordError
       └── InvalidUsernameError

Error Propagation
~~~~~~~~~~~~~~~~~

1. **Data Layer**: Raise specific exceptions
2. **Business Layer**: Catch, log, re-raise or handle
3. **Presentation Layer**: Display user-friendly messages

Logging Strategy
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Log Levels
   DEBUG: Detailed information for debugging
   INFO: General operational events
   WARNING: Warning messages, but app continues
   ERROR: Errors that affect specific operations
   CRITICAL: Critical errors requiring immediate attention

   # Log Locations
   - logs/password_manager.log: Application logs
   - logs/database.log: Database operations
   - logs/security.log: Security-related events

Testing Strategy
----------------

See :doc:`testing` for detailed testing documentation.

**Test Pyramid:**

.. code-block:: text

   ┌───────────────┐
   │      E2E      │  ← Few, critical user workflows
   ├───────────────┤
   │  Integration  │  ← Moderate, component interactions
   ├───────────────┤
   │     Unit      │  ← Many, individual functions
   └───────────────┘

Deployment Architecture
-----------------------

See :doc:`deployment` for detailed deployment documentation.

**Packaging:**

* PyInstaller for standalone executables
* Platform-specific installers
* Auto-update mechanism (planned)

Future Architecture Considerations
-----------------------------------

Planned Enhancements
~~~~~~~~~~~~~~~~~~~~

1. **Plugin System**: Allow third-party extensions
2. **Cloud Sync**: Optional encrypted cloud backup
3. **Multi-User**: Shared vaults for teams
4. **Mobile Apps**: iOS and Android clients
5. **Web Vault**: Browser-based access

Scalability
~~~~~~~~~~~

* Current: Single-user, local database
* Future: Multi-user with proper concurrency control
* Potential: Client-server architecture for cloud sync

Extensibility
~~~~~~~~~~~~~

* Plugin API for custom password generators
* Import/export adapters for other password managers
* Theme customization API
* Webhook support for integrations

References
----------

* :doc:`../api/core` - Core API documentation
* :doc:`../api/gui` - GUI API documentation
* :doc:`contributing` - Contributing guidelines
* :doc:`testing` - Testing guide
