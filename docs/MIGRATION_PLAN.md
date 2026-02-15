# Password Manager: Security Fixes + Flet UI Migration Plan

## Context

The Password Manager (v2.2.0) has 13 security vulnerabilities identified in a code review, and uses two separate UI frameworks (CustomTkinter for desktop, Flask for web) creating maintenance burden. This plan fixes all security issues and consolidates both UIs into a single Flet codebase. Desktop is the default mode; web is opt-in via `--web` flag.

---

## Phase 1: Critical Security Fixes

All changes in `src/core/` and `config/`. No UI changes. Each sub-phase is independently testable and committable.

### 1A. AES-CBC to AES-GCM + PBKDF2 Iteration Upgrade

**Files:** `src/core/encryption.py`, `config/default.py`

- Define new blob format version `0x02`:
  ```
  VERSION(1) + ITERATIONS(4 bytes big-endian) + SALT(32) + NONCE(12) + TAG(16) + CIPHERTEXT
  ```
- Add constants: `VERSION_GCM = b"\x02"`, `GCM_NONCE_LENGTH = 12`, `GCM_TAG_LENGTH = 16`
- `encrypt_password()`: Use `modes.GCM(nonce)` instead of `modes.CBC(iv)`. Remove PKCS7 padding. Store `encryptor.tag` in blob. Write 600,000 iterations into the blob header
- `decrypt_password()`: Branch on version byte:
  - `0x01` (legacy): existing CBC logic with hardcoded 100,000 iterations
  - `0x02`: extract iterations, nonce, tag, ciphertext. Use `modes.GCM(nonce, tag)`. No unpadding
- Add `migrate_entry_to_gcm(encrypted_blob, master_password) -> bytes` method
- Update `DEFAULT_ITERATIONS` from `100000` to `600000`
- Update `config/default.py`: `PBKDF2_ITERATIONS = 600000`, `ENCRYPTION_ALGORITHM = "AES-256-GCM"`

### 1B. Auto-Migration on Login (with progress bar)

**Files:** `src/core/password_manager.py`, `src/core/database.py`

- Add `migrate_all_entries_to_gcm(session_id, master_password, progress_callback=None)` to `PasswordManagerCore`
  - Queries all entries for the user
  - For each entry with version `0x01`: decrypt CBC, re-encrypt GCM, update in DB
  - Calls `progress_callback(current, total)` for UI progress bar
  - Runs in a transaction — rollback on any failure
- Add `needs_encryption_migration(user_id) -> bool` to `DatabaseManager` — checks if any entries have version byte `0x01`
- The UI layer (Phase 3) calls this after login and shows a progress dialog

### 1C. Timing-Safe Comparison

**File:** `src/core/auth.py`

- Add `import hmac` at top
- Replace all `==` comparisons on `master_password_hash` and session tokens with `hmac.compare_digest()`
- Salt the session hash: `hashlib.sha256((password + session_id).encode()).hexdigest()`

### 1D. Flask Security Hardening

**Files:** `src/web/app.py`, `.env`, `config/default.py`

- **Secret key**: Generate random key at startup if none configured. Remove hardcoded `"dev-key-change-in-production"` from `__main__` block
- **Session fixation**: After successful login, call `session.clear()` then repopulate with auth data
- **Cookie defaults**: `SESSION_COOKIE_SECURE = not DEBUG`, `SESSION_COOKIE_SAMESITE = "Strict"`
- **Debug mode**: Change `__main__` block to `debug=False`
- **Account enumeration**: Replace "Username already exists" with generic message
- **Rate limiting**: Document memory-based limitation; add config option for Redis URI
- Regenerate `.env` secret key, ensure `.env` is in `.gitignore`

### 1E. Export/Import Security

**Files:** `src/utils/import_export.py`, `src/core/import_export.py`

- `export_plain_csv()`: Add `confirm_plaintext: bool` parameter (must be `True`). Set file permissions to `0o600` after write. Log security audit event
- `_import_password_entries()`: Before importing, verify master password by attempting to decrypt one existing entry

### 1F. Password Cache + Password Complexity

**Files:** `src/core/password_cache.py`, `config/default.py`, `src/core/auth.py`

- Reduce default cache TTL from 300s to 60s
- Strip decrypted `password` field from cached entries — cache metadata only
- Update `config/default.py`: `MIN_PASSWORD_LENGTH = 12`, all `REQUIRE_*` to `True`
- Add `_validate_password_complexity(password)` to `AuthenticationManager`
- Enforce in `create_user_account()` and `change_master_password()`

---

## Phase 2: Extract Business Logic from GUI to Core

### 2A. Password Health Service

**Create:** `src/core/password_health_service.py`

- Move health analysis from `src/web/app.py:638-801` and `src/gui/password_health.py` into `PasswordHealthService`
- Methods: `analyze_health()`, `get_security_score()`, `get_recommendations()`

### 2B. Age Filtering in Core

**File:** `src/core/password_manager.py`

- Move from `src/gui/main_window.py:1290-1345` into `PasswordManagerCore`
- Methods: `filter_entries_by_age()`, `sort_entries_by_age()`

---

## Phase 3: Flet UI Implementation

### 3A. Project Setup

**Create:** `src/flet_app/` package with full directory structure
**Modify:** `requirements.txt` — add `flet>=0.25.0`

### 3B. App Entry Point and Routing

**File:** `src/flet_app/app.py` — main app, service init, routing

### 3C. Theme System

**File:** `src/flet_app/theme.py` — Material Design 3, dark/light, color schemes

### 3D. Page Implementations

| Page | Replaces |
|------|----------|
| `login_page.py` | `gui/login_window.py` + web login |
| `dashboard_page.py` | `gui/main_window.py` + web dashboard |
| `add_edit_page.py` | GUI dialogs + web forms |
| `health_page.py` | `gui/password_health.py` + web health |
| `settings_page.py` | `gui/settings_window.py` |
| `generator_page.py` | `gui/components/password_generator.py` + web generator |
| `backup_page.py` | `gui/components/backup_manager.py` + `gui/export_dialog.py` |
| `migration_dialog.py` | New — AES-CBC→GCM progress |

### 3E. Shared Components

`password_card.py`, `strength_indicator.py`, `search_bar.py`, `nav_rail.py`, `confirm_dialog.py`

### 3F. Update Entry Point

**File:** `main.py` — default `--desktop` (Flet window), `--web` (Flet browser mode on 127.0.0.1:5000)

### 3G. Remove Old UI Code

Delete `src/gui/`, `src/web/`, remove old dependencies from `requirements.txt`

---

## Phase 4: Testing

- `tests/test_security.py` — AES-GCM, legacy CBC compat, tampered data, PBKDF2, timing-safe, complexity
- `tests/test_core_services.py` — health service, age filtering, bulk migration
- `tests/test_flet_ui.py` — routing, login flow, CRUD, migration dialog, themes
- `tests/test_integration.py` — full end-to-end flow

---

## Execution Order

```
Phase 1A → 1B → 1C → 1D → 1E → 1F  (Security)
Phase 2A → 2B                        (Logic extraction)
Phase 3A → 3B → 3C → 3D → 3E → 3F → 3G  (Flet UI)
Phase 4                               (Testing throughout)
```
