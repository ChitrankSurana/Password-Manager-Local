# Personal Password Manager

A secure, local password manager built with Python, featuring a Material Design 3 interface (powered by Flet), AES-256-GCM authenticated encryption, and both desktop and web modes from a single codebase.

**Version: 3.0.0**

## Features

### Security
- **AES-256-GCM authenticated encryption** with PBKDF2-HMAC-SHA256 key derivation (600,000 iterations)
- **Tamper detection** via GCM authentication tags — any ciphertext modification is caught on decrypt
- **bcrypt password hashing** (cost factor 12) for master password storage
- **Timing-safe comparisons** using `hmac.compare_digest()` for all secret checks
- **Password complexity enforcement** — 12+ characters with uppercase, lowercase, digit, and special character required
- **Local storage only** — all data stays on your machine, zero cloud dependency
- **Automatic CBC-to-GCM migration** — legacy v1 entries are upgraded on login

### Password Management
- Store unlimited passwords with website, username, password, and remarks
- 4 password generation methods: random, memorable, pattern-based, pronounceable
- Real-time password strength analysis with entropy calculations (powered by zxcvbn)
- Search and filter with debounced input
- Age-based filtering (fresh / moderate / old) and sorting
- Password health dashboard with security scoring and recommendations

### User Interface
- **Material Design 3** interface powered by Flet
- **Desktop mode** (default) — native window
- **Web mode** — browser-based, bound to localhost only
- Dark and light themes with multiple color schemes (blue, green, purple, red, orange)
- Navigation rail with quick access to all sections

### Backup and Import/Export
- Full database backup and one-click restore
- Encrypted export (password-protected)
- Plaintext CSV export (requires explicit confirmation)
- Browser CSV import (Chrome, Firefox, Edge format)

## Quick Start

### Prerequisites
- Python 3.8 or higher
- Windows, macOS, or Linux

### Installation

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd Password-Manager-Local
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   # Desktop mode (default)
   python main.py

   # Web mode (opens in browser at http://127.0.0.1:5000)
   python main.py --web
   ```

### First-Time Setup

1. Launch the application — the login page appears
2. Click "Create Account" and choose a username
3. Set a master password (must be 12+ characters with uppercase, lowercase, digit, and special character)
4. Log in with your new credentials
5. Start adding passwords from the dashboard

**Important**: Your master password cannot be recovered if forgotten. It is the encryption key for all your data.

## Usage

### Command Line Options

```
python main.py                  Launch desktop window (default)
python main.py --desktop        Launch desktop window
python main.py --web            Launch web interface at 127.0.0.1:5000
python main.py --check-deps     Run dependency checker only
python main.py --help           Show help
```

### Navigation (after login)

| Section | Description |
|---------|-------------|
| Dashboard | View, search, filter, and manage all password entries |
| Generator | Generate passwords using 4 different methods |
| Health | Security score, weak/duplicate/old password detection, recommendations |
| Backup | Database backup/restore, encrypted export, CSV import/export |
| Settings | Theme, dark/light mode, change master password |

### Adding Passwords

1. Click the **+** button on the dashboard
2. Fill in website, username, and password (or click Generate)
3. The strength indicator updates in real time as you type
4. Click Save — the password is encrypted with AES-256-GCM before storage

### Password Generation

Four methods available:
- **Random** — cryptographically secure random characters with configurable length and character sets
- **Memorable** — dictionary words joined by separators (e.g., `correct-horse-battery-staple`)
- **Pattern** — custom patterns like `Xxxx-0000-xxxx` where X=upper, x=lower, 0=digit
- **Pronounceable** — pronounceable syllable combinations that aren't real words

### Password Health

The health dashboard analyzes all your stored passwords and reports:
- **Security score** (0-100) based on overall password quality
- **Weak passwords** that don't meet strength thresholds
- **Duplicate passwords** reused across multiple sites
- **Old passwords** not changed in over 180 days
- **Actionable recommendations** to improve your security posture

## Security Architecture

### Encryption

| Property | Value |
|----------|-------|
| Algorithm | AES-256-GCM (authenticated encryption) |
| Key derivation | PBKDF2-HMAC-SHA256, 600,000 iterations |
| Salt | 32 bytes (256-bit), unique per entry |
| GCM nonce | 12 bytes (96-bit) per NIST SP 800-38D |
| Auth tag | 16 bytes (128-bit) tamper detection |

**Encrypted blob format (v2):**
```
VERSION(1 byte) + ITERATIONS(4 bytes big-endian) + SALT(32) + NONCE(12) + TAG(16) + CIPHERTEXT
```

Legacy v1 (AES-CBC) blobs are automatically migrated to v2 (GCM) on login.

### Authentication
- Master passwords are hashed with **bcrypt** (cost factor 12)
- All hash/token comparisons use **`hmac.compare_digest()`** to prevent timing attacks
- Session tokens are cryptographically random (32 bytes)
- Sessions expire after 8 hours
- Account lockout after 5 failed login attempts (30-minute cooldown)

### Master Password Requirements
- Minimum 12 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

## File Structure

```
Password-Manager-Local/
├── main.py                          # Entry point (--desktop / --web)
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Project configuration
├── config/
│   └── default.py                   # Default settings (encryption, UI, logging)
├── src/
│   ├── core/                        # Core business logic
│   │   ├── auth.py                  # Authentication (bcrypt, sessions, complexity)
│   │   ├── encryption.py            # AES-256-GCM encrypt/decrypt, v1→v2 migration
│   │   ├── database.py              # SQLite database management
│   │   ├── password_manager.py      # High-level API (CRUD, search, filtering)
│   │   ├── password_health_service.py  # Health analysis and scoring
│   │   ├── password_cache.py        # Master password caching (60s TTL)
│   │   └── import_export.py         # Import/export orchestration
│   ├── utils/                       # Utility modules
│   │   ├── password_generator.py    # 4-method password generation
│   │   ├── strength_checker.py      # Real-time strength analysis (zxcvbn)
│   │   ├── password_age.py          # Age categorization (fresh/moderate/old)
│   │   └── import_export.py         # Backup/restore/CSV operations
│   └── flet_app/                    # Flet UI (Material Design 3)
│       ├── app.py                   # App entry, routing, service init
│       ├── state.py                 # AppState dataclass (session + services)
│       ├── theme.py                 # Theme colors, dark/light mode
│       ├── pages/
│       │   ├── login_page.py        # Login, registration, GCM migration dialog
│       │   ├── dashboard_page.py    # Password list, search, filter, sort
│       │   ├── add_edit_page.py     # Add/edit entry with strength indicator
│       │   ├── generator_page.py    # Password generator UI
│       │   ├── health_page.py       # Health dashboard and recommendations
│       │   ├── settings_page.py     # Theme, security, master password change
│       │   └── backup_page.py       # Backup, restore, import, export
│       └── components/
│           ├── nav_rail.py          # Navigation rail sidebar
│           ├── password_card.py     # Password entry card
│           ├── search_bar.py        # Debounced search input
│           ├── strength_indicator.py # Password strength bar
│           └── confirm_dialog.py    # Confirmation dialogs and snackbars
├── tests/
│   ├── test_security.py             # Encryption, GCM, migration, timing-safe tests
│   ├── test_core_services.py        # Health service, age filtering, migration tests
│   └── test_integration.py          # End-to-end flow (create user → manage passwords)
├── docs/
│   └── CODE_EXPLANATION.md          # Detailed architecture and code documentation
├── data/                            # SQLite database (created at runtime)
├── backups/                         # Database backups
└── logs/                            # Application and security logs
```

## Testing

Run the test suite with pytest:

```bash
# Run all tests
pytest tests/ -v

# Run specific test files
pytest tests/test_security.py -v        # Encryption and security tests
pytest tests/test_core_services.py -v   # Health service and filtering tests
pytest tests/test_integration.py -v     # End-to-end integration tests

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

## Configuration

Settings are in `config/default.py` and can be overridden via environment variables or a `.env` file.

Key settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `PBKDF2_ITERATIONS` | 600,000 | Key derivation iterations |
| `BCRYPT_ROUNDS` | 12 | Master password hash cost |
| `SESSION_TIMEOUT_HOURS` | 8 | Session expiry |
| `MASTER_PASSWORD_CACHE_TIMEOUT` | 60 | Cache TTL in seconds |
| `MIN_PASSWORD_LENGTH` | 12 | Minimum master password length |
| `DEFAULT_THEME` | dark | UI theme (dark/light) |
| `DEFAULT_COLOR_SCHEME` | blue | Color scheme |

### Database Location

The SQLite database is stored at `data/password_manager.db` within the project directory. Backups go to `backups/`.

## Troubleshooting

**Application won't start:**
- Run `pip install -r requirements.txt` to ensure all dependencies are installed
- Check Python version: `python --version` (3.8+ required)
- Verify Flet is installed: `pip show flet`

**Forgot master password:**
- Master passwords cannot be recovered (by design)
- Restore from a database backup if available
- As a last resort, delete `data/password_manager.db` to start fresh (all data will be lost)

**Web mode not loading:**
- Ensure port 5000 is not in use by another application
- Web mode binds to `127.0.0.1` only — access via `http://127.0.0.1:5000`

## License

This project is provided as-is for personal use. Modify and distribute according to your needs while maintaining security best practices.

---

**Remember**: Your master password is the key to all your data. Keep it secure, and create regular backups.
