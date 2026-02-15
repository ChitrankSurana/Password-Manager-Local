# Code Explanation — Personal Password Manager v3.0

This document explains the architecture, security design, and code organization of the Personal Password Manager. It is written so that any developer can understand the entire codebase by reading this file.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Encryption System](#2-encryption-system)
3. [Authentication System](#3-authentication-system)
4. [Database Layer](#4-database-layer)
5. [Flet UI Framework](#5-flet-ui-framework)
6. [Password Health Scoring](#6-password-health-scoring)
7. [Import/Export and Backup](#7-importexport-and-backup)
8. [File-by-File Summary](#8-file-by-file-summary)
9. [How to Run, Build, and Test](#9-how-to-run-build-and-test)

---

## 1. Architecture Overview

The application follows a **three-layer architecture**:

```
┌─────────────────────────────────────────┐
│              UI Layer (Flet)            │
│  Pages: Login, Dashboard, Generator...  │
│  Components: NavRail, PasswordCard...   │
├─────────────────────────────────────────┤
│           Core Services Layer           │
│  AuthenticationManager                  │
│  PasswordManagerCore                    │
│  PasswordHealthService                  │
│  PasswordEncryption                     │
├─────────────────────────────────────────┤
│           Data Layer                    │
│  DatabaseManager (SQLite)               │
│  PasswordCache (in-memory)              │
│  File I/O (backups, exports)            │
└─────────────────────────────────────────┘
```

**Key principle:** The UI layer never accesses the database or encryption directly. It calls Core Services through the `AppState` object, which holds references to all service instances.

### Data Flow (Add Password Example)

1. User fills form on `AddEditPage` and clicks Save
2. `AddEditPage` calls `state.password_manager.add_password_entry()`
3. `PasswordManagerCore` validates the session via `AuthenticationManager`
4. `PasswordManagerCore` calls `PasswordEncryption.encrypt_password()` to encrypt the plaintext
5. The encrypted blob is stored in SQLite via `DatabaseManager`
6. The UI navigates back to the dashboard

---

## 2. Encryption System

**File:** `src/core/encryption.py`

### Algorithm: AES-256-GCM

The password manager uses **AES-256-GCM** (Galois/Counter Mode) — an authenticated encryption algorithm. GCM provides:

- **Confidentiality**: The password is encrypted and unreadable without the key
- **Integrity**: A 16-byte authentication tag detects any tampering with the ciphertext
- **No padding oracle**: Unlike CBC mode, GCM is a streaming cipher that doesn't use padding, eliminating an entire class of attacks

### Key Derivation: PBKDF2-HMAC-SHA256

The user's master password is converted into a 256-bit encryption key using PBKDF2:

```
master_password → PBKDF2(SHA256, salt, 600,000 iterations) → 256-bit AES key
```

- **600,000 iterations**: Follows OWASP 2023+ recommendations. Makes brute-force attacks computationally expensive (~0.3–0.8 seconds per attempt)
- **Unique 32-byte salt per entry**: Prevents rainbow table attacks and ensures identical passwords produce different ciphertexts

### Blob Format

Each encrypted password is stored as a binary blob with a version header:

**v2 (current — AES-256-GCM):**
```
Byte 0:        VERSION = 0x02
Bytes 1-4:     ITERATIONS (4 bytes, big-endian uint32) = 600,000
Bytes 5-36:    SALT (32 bytes, unique per entry)
Bytes 37-48:   NONCE (12 bytes, unique per encryption)
Bytes 49-64:   TAG (16 bytes, GCM authentication tag)
Bytes 65+:     CIPHERTEXT (variable length)
```

Storing iterations in the blob allows future iteration upgrades without breaking existing data — each blob knows its own iteration count.

**v1 (legacy — AES-256-CBC, read-only):**
```
Byte 0:        VERSION = 0x01
Bytes 1-32:    SALT (32 bytes)
Bytes 33-48:   IV (16 bytes)
Bytes 49+:     CIPHERTEXT (PKCS7-padded)
```

v1 blobs are still readable for backward compatibility, but all new encryptions use v2. The auto-migration system converts v1 blobs to v2 on login.

### Why GCM over CBC?

| Property | CBC (v1) | GCM (v2) |
|----------|----------|----------|
| Authentication | None — ciphertext tampering is undetected | 16-byte tag detects any modification |
| Padding | PKCS7 — vulnerable to padding oracle attacks | No padding needed (streaming mode) |
| Iterations in blob | No — hardcoded to 100k | Yes — future-proof upgrades |
| Performance | Slightly faster per-op | Negligible overhead for 16-byte tag |

### Auto-Migration (CBC → GCM)

**File:** `src/core/encryption.py` → `migrate_entry_to_gcm()`

On login, the system checks if any entries use v1 format. If so, it shows a progress dialog and:

1. Decrypts each v1 blob with AES-CBC (using the master password)
2. Re-encrypts the plaintext with AES-GCM (with 600k iterations)
3. Updates the database in a transaction (all-or-nothing)

This is a one-time operation per user.

---

## 3. Authentication System

**File:** `src/core/auth.py`

### Password Hashing

User master passwords are hashed with **bcrypt** before storage:

```
master_password → bcrypt(master_password, cost=12) → hash
```

bcrypt includes its own salt, so two users with the same password get different hashes.

### Session Management

After authentication, a session token (UUID) is issued. All API calls require a valid session token, which is validated on each request.

Sessions have:
- A configurable timeout (default: 30 minutes of inactivity)
- Explicit invalidation on logout
- Server-side storage (not client-side cookies)

### Timing-Safe Comparison

All secret comparisons (password hashes, session tokens) use `hmac.compare_digest()` instead of `==`. This prevents timing side-channel attacks where an attacker measures response times to deduce correct values character-by-character.

```python
# BAD: Short-circuits on first mismatch, leaking timing info
if computed_hash == stored_hash:  # DON'T DO THIS

# GOOD: Always compares all bytes regardless of match position
if hmac.compare_digest(computed_hash, stored_hash):  # CORRECT
```

### Password Complexity Validation

New accounts and password changes enforce:
- Minimum 12 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one digit (0-9)
- At least one special character (!@#$%^&*...)

This is enforced in `_validate_password_complexity()`, called by both `create_user_account()` and `change_master_password()`.

### 2FA (TOTP)

**File:** `src/core/totp_service.py`

Optional two-factor authentication using TOTP (Time-based One-Time Passwords), compatible with Google Authenticator, Authy, etc.

---

## 4. Database Layer

**File:** `src/core/database.py`

### Technology: SQLite

All data is stored in a local SQLite database file (`data/password_manager.db`). No external database server is required.

### Schema

**Users Table:**
```sql
CREATE TABLE users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,          -- bcrypt hash
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    totp_secret   TEXT,                  -- Optional 2FA secret
    ...
);
```

**Password Entries Table:**
```sql
CREATE TABLE password_entries (
    entry_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL,    -- FK to users
    website             TEXT NOT NULL,
    username            TEXT NOT NULL,
    password_encrypted  BLOB NOT NULL,       -- AES-GCM encrypted blob
    remarks             TEXT DEFAULT '',
    is_favorite         BOOLEAN DEFAULT 0,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

The `password_encrypted` column stores the binary blob (v1 or v2 format). The plaintext password never touches the database.

### Password Cache

**File:** `src/core/password_cache.py`

Decrypted entry metadata (website, username, remarks — but NOT passwords) is cached in memory for 60 seconds to avoid repeated database queries and decryption operations. The `password` field is stripped from cached entries as a defense-in-depth measure.

---

## 5. Flet UI Framework

**Directory:** `src/flet_app/`

### What is Flet?

Flet is a Python UI framework based on Flutter. It renders Material Design 3 interfaces and can run as:
- A **native desktop window** (default mode)
- A **web application** in the browser (`--web` flag)

The same Python code powers both modes — no separate HTML/CSS/JS is needed.

### Routing Model

**File:** `src/flet_app/app.py`

The application uses client-side routing. The `navigate()` function in `app.py`:

1. Clears the current page controls
2. Checks if the user is authenticated (redirects to `/login` if not)
3. Lazily imports and instantiates the target page class
4. Adds it to `page.controls` and calls `page.update()`

Routes:
```
/login      → LoginPage
/dashboard  → DashboardPage (default after login)
/add        → AddEditPage (new entry)
/edit/:id   → AddEditPage (edit existing)
/generator  → GeneratorPage
/health     → HealthPage
/backup     → BackupPage
/settings   → SettingsPage
```

### State Management

**File:** `src/flet_app/state.py`

`AppState` is a dataclass created once in `app.py` and passed to every page constructor. It holds:

- **Core service references**: `auth_manager`, `password_manager`, `health_service`, etc.
- **Session data**: `session_id`, `username`, `user_id`
- **Navigation callback**: `navigate("/route")` to switch pages
- **User settings**: Theme preferences, etc.

Pages interact with the backend exclusively through `AppState` — they never import database or encryption modules directly. This makes the UI layer fully swappable and testable.

### Page Lifecycle

Each page is a `ft.Container` subclass. When the router navigates to a page:

1. The page constructor receives `AppState`
2. It builds its layout (Flet widgets) in `__init__`
3. It starts any background data loading (e.g., `DashboardPage` fetches entries)
4. Background threads call `self.update()` when data arrives

When navigating away, the old page is garbage collected.

### Components

Reusable widgets shared across pages:

| Component | File | Purpose |
|-----------|------|---------|
| `NavRail` | `nav_rail.py` | Sidebar navigation with Dashboard, Generator, Health, Backup, Settings, Logout |
| `PasswordCard` | `password_card.py` | Displays one password entry with show/hide, copy, edit, delete actions |
| `SearchBar` | `search_bar.py` | Text input with 300ms debounce for filtering |
| `StrengthIndicator` | `strength_indicator.py` | Color-coded progress bar showing password strength |
| `show_confirm_dialog` | `confirm_dialog.py` | Modal confirmation dialog for destructive actions |
| `show_snack_bar` | `confirm_dialog.py` | Temporary status message at the bottom |

### Theme System

**File:** `src/flet_app/theme.py`

Maps color scheme names (blue, green, purple, red, orange) to Material Design 3 seed colors. Flet generates a full tonal palette from each seed. Dark/light mode is toggled via `page.theme_mode`.

---

## 6. Password Health Scoring

**File:** `src/core/password_health_service.py`

### How It Works

`PasswordHealthService.analyze_health(entries)` takes a list of decrypted password entries and produces a `HealthReport` containing:

1. **Weak Passwords**: Identified using `AdvancedPasswordStrengthChecker`. Passwords scoring below "good" are flagged.

2. **Duplicate Passwords**: Detected by hashing each plaintext with SHA-256 and grouping entries with the same hash. The actual passwords are never compared directly — only hashes.

3. **Old Passwords**: Entries whose `modified_at` date is more than 180 days ago.

4. **Strength Distribution**: Counts of entries at each strength level (very_weak through very_strong).

### Scoring Algorithm

The security score (0-100) is calculated by starting at 100 and subtracting penalties:

- Each weak password: -3 points
- Each duplicate group: -5 points per group
- Each old password: -2 points
- If > 50% are weak: additional -10 points

The final score is clamped to [0, 100].

### Recommendations

The service generates prioritized recommendations:
- **High priority**: "Change X weak passwords", "X passwords are reused across sites"
- **Medium priority**: "X passwords haven't been changed in 6+ months"
- Sorted by priority (high first) for UI display

---

## 7. Import/Export and Backup

**File:** `src/utils/import_export.py`

### Backup

`BackupManager.create_database_backup()` copies the SQLite file to the `backups/` directory with a timestamp. It also:
- Verifies backup integrity after copy
- Creates a `.meta.json` file with checksum and metadata

### Restore

`restore_database_backup(path, confirm_restore=True)` replaces the current database with a backup file. The `confirm_restore` parameter is required to prevent accidental restores.

### Export

Two export modes:

1. **Encrypted JSON**: `export_encrypted_data()` — exports all entries with passwords still encrypted. Safe to store.

2. **Plaintext CSV**: `export_plain_csv()` — exports passwords in cleartext. Security controls:
   - Requires `confirm_plaintext=True` (defaults to False)
   - Sets file permissions to `0o600` (owner-only read/write)
   - Logs a security audit event

### Import

`import_browser_passwords()` imports from Chrome, Firefox, or Edge CSV exports. Before encrypting the imported data, it **verifies the master password** by:
1. Decrypting an existing entry (if any exist)
2. If no entries exist, doing a trial encrypt/decrypt roundtrip

This prevents importing with the wrong master password, which would create entries that can never be decrypted.

---

## 8. File-by-File Summary

### Root Files

| File | Purpose |
|------|---------|
| `main.py` | Application entry point. Parses `--desktop`/`--web` flags and launches the appropriate Flet mode |
| `requirements.txt` | Python dependencies (flet, cryptography, bcrypt, etc.) |
| `.env` | Environment variables (PBKDF2 iterations, cache timeout, etc.) |

### `src/core/` — Core Business Logic

| File | Purpose |
|------|---------|
| `auth.py` | `AuthenticationManager` — user creation, login, session management, master password change, timing-safe comparison, password complexity validation |
| `encryption.py` | `PasswordEncryption` — AES-256-GCM encrypt/decrypt, PBKDF2 key derivation, v1 (CBC) backward compat, CBC→GCM migration |
| `password_manager.py` | `PasswordManagerCore` — high-level password CRUD, search, bulk operations, age filtering/sorting, master password caching |
| `database.py` | `DatabaseManager` — SQLite operations, table creation, CRUD queries |
| `database_migrations.py` | Schema migrations for database upgrades |
| `password_cache.py` | `PasswordCache` — in-memory cache with TTL (60s), strips passwords from cached entries |
| `password_health_service.py` | `PasswordHealthService` — analyzes weak/duplicate/old passwords, produces security score and recommendations |
| `settings_service.py` | `SettingsService` — per-user settings with validation, persistence, and defaults |
| `import_export.py` | Core import/export service (alternative to utils version) |
| `totp_service.py` | TOTP 2FA service (Google Authenticator compatible) |
| `exceptions.py` | Custom exception classes for all core operations |
| `error_handlers.py` | Decorators for security error handling |
| `logging_config.py` | Structured logging configuration |
| `security_audit_logger.py` | Security event audit trail |
| `performance_monitor.py` | Performance tracking for database and encryption operations |
| `service_integration.py` | Service integrator pattern for wiring core services together |
| `config.py` | Runtime configuration loading from .env |
| `types.py` | Custom type aliases |
| `view_auth_service.py` | View-level authentication helpers |

### `src/utils/` — Utilities

| File | Purpose |
|------|---------|
| `import_export.py` | `BackupManager` — database backup/restore, encrypted/plaintext export, browser CSV import |
| `password_generator.py` | `PasswordGenerator` — random, memorable, pattern, and pronounceable password generation |
| `strength_checker.py` | `AdvancedPasswordStrengthChecker` — multi-factor password strength analysis (entropy, patterns, dictionary, breaches) |
| `password_age.py` | Age calculation and categorization (fresh/moderate/old) |
| `font_manager.py` | Font size management |

### `src/flet_app/` — Flet UI

| File | Purpose |
|------|---------|
| `app.py` | Main Flet entry point — initializes services, sets up routing, provides `run_desktop()` and `run_web()` |
| `state.py` | `AppState` dataclass — centralized session + service references passed to all pages |
| `theme.py` | Material Design 3 theme with 5 color schemes + dark/light mode |

### `src/flet_app/pages/`

| File | Purpose |
|------|---------|
| `login_page.py` | Login/register form, AES-CBC→GCM migration dialog with progress bar |
| `dashboard_page.py` | Password list with search, age filtering, sorting, delete confirmation |
| `add_edit_page.py` | Add/edit password form with inline strength indicator and quick-generate button |
| `generator_page.py` | Password generator with method selection (random/memorable/pattern/pronounceable) |
| `health_page.py` | Password health dashboard — score, weak/duplicate/old tables, recommendations |
| `settings_page.py` | Theme picker, dark/light toggle, change master password form |
| `backup_page.py` | Backup, restore, encrypted export, plaintext CSV export, browser CSV import |

### `src/flet_app/components/`

| File | Purpose |
|------|---------|
| `nav_rail.py` | `NavRail` — persistent sidebar with Dashboard, Generator, Health, Backup, Settings + Logout |
| `password_card.py` | `PasswordCard` — entry display card with show/hide password, copy, edit, delete |
| `search_bar.py` | `SearchBar` — text field with 300ms debounce timer |
| `strength_indicator.py` | `StrengthIndicator` — color-coded progress bar (red→green) |
| `confirm_dialog.py` | `show_confirm_dialog()` and `show_snack_bar()` utility functions |

### `tests/`

| File | Purpose |
|------|---------|
| `test_security.py` | Security tests: GCM roundtrip, tamper detection, migration, complexity, export gate |
| `test_core_services.py` | Service tests: health analysis, age filtering, bulk migration progress |
| `test_integration.py` | End-to-end tests: create user → login → add/retrieve/update/delete → master password change |
| `test_password_manager.py` | Original unit tests for password manager operations |

### `config/`

| File | Purpose |
|------|---------|
| `default.py` | Default configuration values (PBKDF2 iterations, min password length, cache TTL, etc.) |

---

## 9. How to Run, Build, and Test

### Prerequisites

- Python 3.9+
- pip

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Application

```bash
# Desktop mode (default) — opens a native window
python main.py

# Web mode — opens in browser at http://127.0.0.1:5000
python main.py --web
```

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run security tests only
pytest tests/test_security.py -v

# Run integration tests only
pytest tests/test_integration.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### Build Executable

```bash
pyinstaller --onefile --windowed main.py
```

### Project Structure

```
Password-Manager-Local/
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
├── .env                     # Configuration
├── config/
│   └── default.py           # Default settings
├── data/                    # SQLite database (created on first run)
├── backups/                 # Database backups
├── exports/                 # Exported files
├── docs/
│   ├── CODE_EXPLANATION.md  # This file
│   ├── MIGRATION_PLAN.md    # v2→v3 migration plan
│   └── PRD.md               # Product requirements
├── src/
│   ├── core/                # Business logic (encryption, auth, DB)
│   ├── utils/               # Utilities (generator, checker, import/export)
│   └── flet_app/            # Flet UI (pages + components)
└── tests/                   # Test suite
```
