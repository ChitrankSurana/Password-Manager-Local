# Changelog - Personal Password Manager

All notable changes to this project will be documented in this file.

---

## [3.0.0] - 2025-12-XX

### Breaking Changes

This is a major release. The old CustomTkinter GUI (`src/gui/`) and Flask web interface (`src/web/`) have been removed entirely. The application now uses a single Flet-based UI for both desktop and web modes.

- `--gui` and `--flask` CLI flags removed — use `--desktop` (default) or `--web`
- AES-256-CBC (v1 blob format) is still readable but all new entries use AES-256-GCM (v2)
- Master password minimum length increased from 8 to 12 characters
- Master password now requires uppercase, lowercase, digit, and special character
- Password cache TTL reduced from 300s to 60s
- PBKDF2 iterations increased from 100,000 to 600,000 (existing entries auto-migrate)

---

### Security Fixes (13 total)

#### Encryption Upgrade: AES-CBC to AES-256-GCM
- Replaced AES-256-CBC with AES-256-GCM authenticated encryption
- New v2 blob format: `VERSION(1) + ITERATIONS(4) + SALT(32) + NONCE(12) + TAG(16) + CIPHERTEXT`
- 16-byte authentication tag detects any ciphertext tampering
- Eliminates padding oracle attack surface entirely
- **File:** `src/core/encryption.py`

#### PBKDF2 Iteration Increase
- Increased from 100,000 to 600,000 iterations (OWASP 2023+ recommendation)
- Iteration count stored in each blob header for forward compatibility
- Makes brute-force attacks require ~1-2 seconds per guess on modern hardware
- **File:** `src/core/encryption.py`, `config/default.py`

#### Automatic CBC-to-GCM Migration
- On login, all v1 (CBC) entries are detected and migrated to v2 (GCM)
- Migration runs in a transaction with rollback on failure
- Progress dialog shown during migration with entry count
- **Files:** `src/core/password_manager.py`, `src/core/database.py`

#### Timing-Safe Comparisons
- All secret comparisons (password hashes, session tokens) now use `hmac.compare_digest()`
- Prevents timing side-channel attacks on authentication
- **File:** `src/core/auth.py`

#### Password Complexity Enforcement
- Minimum 12 characters (was 8)
- Requires uppercase, lowercase, digit, and special character
- Enforced on account creation and master password change
- **Files:** `src/core/auth.py`, `config/default.py`

#### Master Password Cache Hardening
- Cache TTL reduced from 300 seconds to 60 seconds
- Limits exposure window if process memory is compromised
- **File:** `src/core/password_cache.py`

#### Plaintext Export Confirmation Gate
- `export_plain_csv()` now requires `confirm_plaintext=True` parameter
- Prevents accidental plaintext exports from UI or API
- **File:** `src/utils/import_export.py`

#### Import Master Password Verification
- Before importing passwords, the system verifies the master password can decrypt existing entries
- Prevents importing with wrong encryption key
- **File:** `src/core/import_export.py`

#### Salt Size Increase
- Increased from 16 bytes to 32 bytes (256-bit) for PBKDF2 salt generation
- **File:** `config/default.py`

#### Session Security
- Session tokens use cryptographically secure random generation (32 bytes)
- Session cleanup runs hourly to remove expired sessions
- **File:** `src/core/auth.py`

#### Account Lockout
- 5 failed login attempts triggers a 30-minute lockout
- Configurable via `MAX_FAILED_ATTEMPTS` and `LOCKOUT_DURATION_MINUTES`
- **File:** `config/default.py`

#### Debug Mode Disabled by Default
- `DEBUG` defaults to `False` in all configurations
- **File:** `config/default.py`

#### Security Audit Logging
- Login attempts, password changes, exports, and imports are logged
- Security log at `logs/security.log` with 90-day retention
- **File:** `src/core/security_audit_logger.py`

---

### New: Flet UI (Material Design 3)

Replaced both CustomTkinter desktop GUI and Flask web interface with a single Flet codebase that supports desktop window and web browser modes.

#### Application Shell
- Material Design 3 theming with `ft.Theme(color_scheme_seed=...)`
- Client-side routing: `/login`, `/dashboard`, `/add`, `/edit/:id`, `/generator`, `/health`, `/backup`, `/settings`
- `AppState` dataclass holds session, services, and navigation — passed to all pages
- **Files:** `src/flet_app/app.py`, `src/flet_app/state.py`, `src/flet_app/theme.py`

#### Pages (7 total)
- **Login Page** — Login + registration forms, GCM migration progress dialog on first login
- **Dashboard** — Password list with search (debounced 300ms), age filtering (fresh/moderate/old), sort toggle, delete confirmation
- **Add/Edit** — Form with real-time strength indicator, inline password generation
- **Generator** — 4 generation methods with method-specific option panels
- **Health** — Security score display, weak/duplicate/old password tables, recommendations
- **Settings** — Theme picker (5 colors), dark/light toggle, master password change
- **Backup** — Database backup/restore, encrypted export, plaintext CSV export (with confirmation), browser CSV import
- **Files:** `src/flet_app/pages/`

#### Components (5 total)
- **NavigationRail** — Persistent sidebar on all authenticated pages
- **PasswordCard** — Entry display with show/hide toggle, copy, edit, delete actions
- **SearchBar** — Debounced text input (300ms delay)
- **StrengthIndicator** — Color-coded strength bar (very weak → very strong)
- **ConfirmDialog** — Reusable confirmation dialogs and snackbar notifications
- **Files:** `src/flet_app/components/`

#### Theme System
- 5 color schemes: blue, green, purple, red, orange
- Dark and light mode toggle via `page.theme_mode`
- **File:** `src/flet_app/theme.py`

---

### New: Core Services Extracted

Business logic previously embedded in GUI code was extracted to testable core services.

#### Password Health Service
- Analyzes all entries for weak passwords, duplicates, and old passwords (>180 days)
- Produces `HealthReport` dataclass with score (0-100), categorized issues, and recommendations
- `as_dict()` method for JSON serialization
- **File:** `src/core/password_health_service.py`

#### Age Filtering in Core
- `PasswordManagerCore.filter_entries_by_age(entries, category)` — filter by fresh/moderate/old/all
- `PasswordManagerCore.sort_entries_by_age(entries, oldest_first)` — sort by modification date
- Uses `src/utils/password_age.py` for age categorization
- **File:** `src/core/password_manager.py`

---

### New: Test Suite

#### Security Tests (`tests/test_security.py`)
- AES-GCM encrypt/decrypt roundtrip
- Legacy CBC backward compatibility (v1 blobs still decrypt)
- Tampered ciphertext detection (GCM auth tag failure)
- `migrate_entry_to_gcm()` preserves plaintext
- Wrong password raises `DecryptionError`
- PBKDF2 600k iterations benchmark (must complete < 2s)
- `hmac.compare_digest` usage verification
- Password complexity validation (reject weak, accept strong)
- Export requires `confirm_plaintext=True`
- Import verifies master password before encrypting

#### Core Service Tests (`tests/test_core_services.py`)
- `PasswordHealthService.analyze_health()` with known test data
- Weak, duplicate, and old password detection
- Security score range validation
- Age filtering correctness (fresh/moderate/old categories)
- Sort order verification (oldest-first, newest-first)
- Bulk migration progress callback simulation

#### Integration Tests (`tests/test_integration.py`)
- End-to-end flow with real SQLite database (temporary file):
  1. Create user account (with complexity validation)
  2. Authenticate and get session
  3. Cache master password
  4. Add password entry (AES-256-GCM encrypted)
  5. Retrieve and verify decrypted password
  6. Search entries by website
  7. Update password entry
  8. Change master password (re-encrypts all entries)
  9. Verify entries accessible with new master password
  10. Delete entry and verify deletion
  11. Verify new entries use v2 (GCM) blob format

---

### New: Documentation

- **`docs/CODE_EXPLANATION.md`** — Comprehensive architecture document covering encryption system, authentication, database schema, Flet UI structure, health scoring algorithm, import/export, and file-by-file summary
- **`README.md`** — Fully rewritten for v3.0.0

---

### Removed

#### Old UI Frameworks
- **Deleted `src/gui/`** — Entire CustomTkinter desktop GUI (8+ files)
- **Deleted `src/web/`** — Entire Flask web interface (templates, static files, routes)

#### Old Dependencies Removed from `requirements.txt`
- `customtkinter` — CustomTkinter GUI framework
- `pillow` — Image processing (used by CTk)
- `flask` — Flask web framework
- `flask-session` — Flask server-side sessions
- `flask-wtf` — Flask form handling
- `flask-limiter` — Flask rate limiting
- `wtforms` — Form validation
- `jinja2` — Template engine
- `werkzeug` — WSGI utilities
- `itsdangerous` — Token signing
- `selenium` — Browser automation (old tests)
- `mock` — Old mocking library

#### Old Files Moved to `old/`
- 11 root-level test scripts (`test_*.py`)
- 11 utility scripts (`build_exe.py`, `check_dependencies.py`, `lint.py`, etc.)
- `main_enhanced.py`
- `scripts/` directory
- `documentation/` directory (50+ old .md files)
- `Code Explanations/` directory (old .txt docs)
- `distribution/` directory
- 42 root-level .md files from v2.2.0 era
- Old .bat files, .txt files, and misc artifacts

#### Dependencies Added
- `flet>=0.25.0` — Flutter-based Python UI (Material Design 3, desktop + web)

---

### Updated Entry Point

**`main.py`** rewritten for Flet:
```
python main.py                  Desktop window (default)
python main.py --desktop        Desktop window
python main.py --web            Web browser at 127.0.0.1:5000
python main.py --check-deps     Dependency check only
```

Old `--gui` (CustomTkinter) and `--flask` flags are no longer supported.

---

## [2.2.0] - 2025-10-29

### Security Enhancements
- Database file permissions enforcement (chmod 600 on Unix, ACL on Windows)
- Web interface rate limiting (5 login attempts/minute, 3 registrations/hour)

### Performance Improvements
- SQL-based query optimization with `get_password_entries_advanced()`
- Pagination support with `search_password_entries_optimized()`
- 10x faster queries and 90% memory reduction for large datasets

### Technical Improvements
- Enhanced error handling with stack traces
- SQL injection protection with parameterized queries
- Better type hints and docstrings

---

## [2.0.0] - 2024-XX-XX

### Initial Release
- AES-256-CBC encryption for password storage
- PBKDF2 key derivation with 100,000 iterations
- Bcrypt password hashing for user accounts
- SQLite database with foreign key constraints
- CustomTkinter GUI with dark/light themes
- Optional Flask web interface
- Multi-user support with session management
- Password generator (4 methods)
- Password strength checker
- CSV import/export and backup/restore
- Security audit logging

---

## Version Numbering

This project uses Semantic Versioning (SemVer): **MAJOR.MINOR.PATCH**

- **MAJOR:** Incompatible changes (new encryption, removed UI frameworks)
- **MINOR:** New features (backward compatible)
- **PATCH:** Bug fixes (backward compatible)

**Current Version:** 3.0.0
- Major: 3 (AES-GCM encryption, Flet UI, old frameworks removed)
- Minor: 0 (initial v3 release)
- Patch: 0 (no patches yet)

---

**Last Updated:** 2025-12-XX
**Current Version:** 3.0.0
