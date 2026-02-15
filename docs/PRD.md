# Product Requirements Document (PRD)
# Password Manager v3.0 — Security Upgrade + UI Modernization

---

## 1. Executive Summary

**Product:** Personal Password Manager
**Current Version:** 2.2.0
**Target Version:** 3.0.0
**Goal:** Fix all identified security vulnerabilities and replace the dual-UI architecture (CustomTkinter + Flask) with a single modern Flet-based interface.

**Key Outcomes:**
1. All 13 security vulnerabilities resolved
2. Modern Material Design 3 UI via Flet
3. Single codebase for desktop and web (web is opt-in)
4. Zero data loss — backward-compatible encryption migration
5. Improved code maintainability (one UI instead of two)

---

## 2. Problem Statement

### Security Issues
The current implementation has 13 security vulnerabilities ranging from critical to important:
- **AES-CBC without authentication** — padding oracle attack risk on all stored passwords
- **Hardcoded Flask secret key** — complete web session bypass
- **No timing-safe comparisons** — password hash leakage via timing side-channel
- **Session fixation** — session hijacking in web interface
- **Insecure cookie defaults** — cookies sent over HTTP
- **Low PBKDF2 iterations** — 100,000 vs recommended 600,000
- **Plaintext CSV export** without safeguards
- **Long password cache TTL** — decrypted passwords in memory for 5 minutes
- **Memory-based rate limiting** — resets on restart, enabling brute force
- **Debug mode enabled by default** — stack traces and RCE via Werkzeug debugger
- **Account enumeration** — registration reveals valid usernames
- **Import without master password verification** — data encrypted with wrong key
- **No password complexity requirements** — allows "11111111" as master password

### UI/UX Issues
- Two separate UIs (CustomTkinter desktop + Flask web) require double maintenance
- CustomTkinter looks dated compared to modern desktop applications
- Flask web interface duplicates business logic from the GUI layer
- Business logic (age filtering, health scoring) embedded in GUI code

---

## 3. Target Users

- **Primary:** Individual users who want a local, offline-first password manager
- **Secondary:** Power users who want optional browser-based access on their local network
- **Assumption:** Users run the application on their own computer in a trusted environment

---

## 4. Functional Requirements

### FR-1: Encryption Upgrade (AES-CBC → AES-GCM)
- **FR-1.1:** All new password entries MUST be encrypted with AES-256-GCM
- **FR-1.2:** Existing AES-CBC entries MUST remain decryptable (backward compatibility)
- **FR-1.3:** On first login after upgrade, all CBC entries MUST be automatically re-encrypted to GCM
- **FR-1.4:** Migration MUST show a progress bar with current/total count
- **FR-1.5:** Migration MUST be atomic — if any entry fails, all changes roll back
- **FR-1.6:** The encrypted blob format MUST include a version byte to distinguish CBC (0x01) from GCM (0x02)
- **FR-1.7:** The GCM blob format MUST store the PBKDF2 iteration count for future-proofing

### FR-2: PBKDF2 Iteration Upgrade
- **FR-2.1:** New encryptions MUST use 600,000 PBKDF2-HMAC-SHA256 iterations
- **FR-2.2:** Legacy blobs (version 0x01) MUST be decrypted with 100,000 iterations
- **FR-2.3:** Key derivation at 600,000 iterations MUST complete in under 2 seconds on target hardware

### FR-3: Authentication Hardening
- **FR-3.1:** All secret comparisons MUST use constant-time comparison (`hmac.compare_digest`)
- **FR-3.2:** Web sessions MUST be regenerated after successful login
- **FR-3.3:** Session cookies MUST set `Secure=True` and `SameSite=Strict` in production
- **FR-3.4:** Registration errors MUST NOT reveal whether a username exists
- **FR-3.5:** Debug mode MUST be `False` by default
- **FR-3.6:** Flask secret key MUST be randomly generated if not explicitly configured

### FR-4: Password Complexity
- **FR-4.1:** Master password MUST be at least 12 characters
- **FR-4.2:** Master password MUST contain uppercase, lowercase, digit, and special character
- **FR-4.3:** Complexity requirements MUST be enforced on account creation and password change
- **FR-4.4:** Clear error messages MUST indicate which requirements are not met

### FR-5: Export/Import Security
- **FR-5.1:** Plaintext CSV export MUST require explicit confirmation parameter
- **FR-5.2:** Exported plaintext files MUST have restrictive file permissions (owner read/write only)
- **FR-5.3:** Import MUST verify the master password is correct before encrypting imported data
- **FR-5.4:** Security audit events MUST be logged for all export operations

### FR-6: Password Cache Security
- **FR-6.1:** Cache TTL MUST default to 60 seconds (reduced from 300)
- **FR-6.2:** Cached entries MUST NOT include decrypted password text — only metadata

### FR-7: Flet Desktop UI
- **FR-7.1:** Application MUST launch as a desktop window by default
- **FR-7.2:** UI MUST use Material Design 3 via Flet's Flutter rendering
- **FR-7.3:** UI MUST support dark and light themes with user persistence
- **FR-7.4:** UI MUST support multiple color schemes (blue, green, purple, red, orange)
- **FR-7.5:** All existing features MUST be available in the new UI:
  - Login with optional 2FA
  - Password list with search, filter by age, sort
  - Add/edit/delete password entries
  - Password generator (random, memorable, pattern-based, pronounceable)
  - Password health dashboard with security score
  - Backup/restore
  - Import/export (CSV, JSON, browser formats)
  - User settings
- **FR-7.6:** Navigation MUST use a persistent sidebar (NavigationRail)
- **FR-7.7:** Clipboard operations MUST use Flet's built-in `page.set_clipboard()`

### FR-8: Flet Web Mode (Opt-In)
- **FR-8.1:** Web mode MUST be activated via `--web` command-line flag
- **FR-8.2:** Web mode MUST bind to `127.0.0.1` only (not `0.0.0.0`)
- **FR-8.3:** Web mode MUST use the same Flet codebase as desktop (no separate templates)
- **FR-8.4:** Web mode MUST default to port 5000

### FR-9: Migration Path
- **FR-9.1:** During transition, old `--gui` (CustomTkinter) and `--flask` flags MUST continue working
- **FR-9.2:** After migration is verified, old UI code MUST be removed
- **FR-9.3:** Old UI dependencies MUST be removed from requirements.txt

---

## 5. Non-Functional Requirements

### NFR-1: Security
- No plaintext passwords in logs, error messages, or stack traces
- All cryptographic operations use the `cryptography` library (not custom implementations)
- All random values use `secrets` module (cryptographically secure)
- Memory containing sensitive data cleared after use (best-effort in Python)

### NFR-2: Performance
- Application startup in under 3 seconds
- Password list rendering for 500+ entries in under 1 second
- AES-GCM encryption/decryption per entry in under 50ms
- PBKDF2 key derivation (600k iterations) in under 2 seconds

### NFR-3: Compatibility
- Python 3.10+ required
- Windows 10/11 primary platform
- SQLite database format unchanged (same tables, new encrypted blob format coexists)
- Existing databases work without manual intervention

### NFR-4: Code Quality
- All security-critical code commented with explanations
- Type hints on all public methods
- Code explanation document provided for onboarding

### NFR-5: Reliability
- Encryption migration is atomic (transaction-based)
- Application handles interruption during migration gracefully
- Backup recommended before migration (prompted in UI)

---

## 6. Out of Scope

- Mobile native app (Flet supports it, but not in this release)
- Cloud sync / remote server deployment
- Browser extension
- Multi-device sync
- Password sharing between users
- Biometric authentication (fingerprint/face)

---

## 7. Success Criteria

1. All 13 security vulnerabilities are resolved and verified by tests
2. Existing databases migrate automatically with zero data loss
3. New Flet UI has feature parity with the old CustomTkinter + Flask UIs
4. Single codebase serves both desktop and web modes
5. All existing tests pass; new security tests cover all fixes
6. Code explanation document complete

---

## 8. Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Data corruption during AES migration | Critical | Low | Atomic transactions, backup before migration, extensive testing |
| PBKDF2 600k too slow on old hardware | Medium | Low | Benchmark on target hardware, make configurable |
| Flet missing required widget | Medium | Low | Verify all needed widgets before starting Phase 3 |
| Flet web mode security issues | Medium | Medium | Default to desktop-only, web is opt-in, bind localhost only |
| Breaking existing user workflows | Medium | Medium | Keep old UI flags during transition period |

---

## 9. Dependencies

### New
- `flet>=0.25.0` — UI framework

### Kept
- `cryptography>=41.0.0` — AES-GCM, PBKDF2
- `bcrypt>=4.0.0` — master password hashing
- `zxcvbn>=4.4.28` — password strength analysis
- `pandas>=2.1.0` — CSV import/export
- All other utility dependencies unchanged

### Removed (after migration)
- `customtkinter` — replaced by Flet
- `flask`, `flask-session`, `flask-wtf`, `flask-limiter` — replaced by Flet
- `wtforms`, `jinja2`, `werkzeug`, `itsdangerous` — Flask dependencies
- `pillow` — no longer needed (Flet handles icons natively)

---

## 10. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-07 | Initial PRD for v3.0 migration |
