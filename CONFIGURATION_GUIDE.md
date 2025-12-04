# Configuration Management Guide

**Personal Password Manager - Centralized Configuration System**

This guide explains how to configure and customize the Password Manager using the centralized configuration system.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Configuration Architecture](#configuration-architecture)
3. [Environment Variables](#environment-variables)
4. [Configuration Files](#configuration-files)
5. [Using Configuration in Code](#using-configuration-in-code)
6. [Environment-Specific Settings](#environment-specific-settings)
7. [Security Best Practices](#security-best-practices)
8. [Common Configuration Tasks](#common-configuration-tasks)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Create Your .env File

```bash
# Copy the example file
cp .env.example .env

# Edit with your settings
nano .env  # or use your preferred editor
```

### 2. Set Essential Values

Minimum required settings for `.env`:

```bash
# Environment
APP_ENV=production

# Flask Secret (CRITICAL!)
FLASK_SECRET_KEY=your-random-secret-key-here
```

### 3. Generate Secure Secret Key

```bash
# Generate a random secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Copy the output to FLASK_SECRET_KEY in .env
```

### 4. Start Using Configuration

```python
from src.core.config import config

# Access any setting
db_path = config.DB_PATH
debug_mode = config.DEBUG
iterations = config.PBKDF2_ITERATIONS
```

---

## Configuration Architecture

### File Structure

```
Password-Manager-Local/
├── config/
│   ├── __init__.py           # Configuration package
│   ├── default.py            # Base configuration (all defaults)
│   ├── development.py        # Development overrides
│   └── production.py         # Production overrides
├── src/core/
│   └── config.py             # Configuration loader
├── .env                      # Your local environment variables (gitignored)
└── .env.example              # Template for .env file
```

### Configuration Hierarchy

Settings are loaded in this order (later overrides earlier):

1. **Default Config** (`config/default.py`)
   - Base settings that work out-of-the-box
   - Sensible defaults for all values

2. **Environment-Specific Config** (`config/development.py` or `config/production.py`)
   - Overrides specific to the environment
   - Selected by `APP_ENV` variable

3. **Environment Variables** (`.env` file or system environment)
   - Final override for any setting
   - Highest priority

**Example:**
```python
# config/default.py
PBKDF2_ITERATIONS = 100000  # Default value

# config/development.py
PBKDF2_ITERATIONS = 10000   # Faster for dev

# .env file
PBKDF2_ITERATIONS=150000    # Your custom value (WINS!)

# Result: 150000 is used
```

---

## Environment Variables

### Using .env File

The `.env` file allows you to customize settings without modifying code.

**Format:**
```bash
# Comments start with #
KEY=VALUE                    # No spaces around =

# Boolean values
DEBUG=True                   # or False, true, false, 1, 0, yes, no

# Numeric values
FLASK_PORT=5000             # Just the number

# String values
LOG_LEVEL=INFO              # No quotes needed

# Strings with spaces
FLASK_RATE_LIMIT=100 per hour
```

### Key Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APP_ENV` | string | `production` | Environment: `development`, `production`, `testing` |
| `DEBUG` | boolean | `False` | Enable debug mode (never in production!) |
| `FLASK_SECRET_KEY` | string | - | **Required** in production! Secret key for sessions |
| `DB_TIMEOUT` | int | `30` | Database connection timeout (seconds) |
| `PBKDF2_ITERATIONS` | int | `100000` | Key derivation iterations (higher = more secure) |
| `BCRYPT_ROUNDS` | int | `12` | Password hashing rounds (higher = more secure) |
| `SESSION_TIMEOUT_HOURS` | int | `8` | Session expiration time |
| `LOG_LEVEL` | string | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR |
| `FLASK_PORT` | int | `5000` | Web interface port |
| `DEFAULT_THEME` | string | `dark` | GUI theme: `dark` or `light` |
| `CACHE_ENABLED` | boolean | `True` | Enable caching for performance |

See `.env.example` for complete list with explanations.

---

## Configuration Files

### `config/default.py` - Base Configuration

Contains all default settings with sensible values.

**Categories:**
- Application Settings
- Database Settings
- Security Settings
- Logging Settings
- GUI Settings
- Web Interface Settings
- Password Generator Settings
- Performance Settings
- Feature Flags

**Example:**
```python
class DefaultConfig:
    APP_NAME = "Personal Password Manager"
    APP_VERSION = "2.2.0"

    DB_PATH = str(DATA_DIR / "password_manager.db")
    DB_TIMEOUT = 30

    PBKDF2_ITERATIONS = 100000
    BCRYPT_ROUNDS = 12

    # ... 100+ more settings
```

### `config/development.py` - Development Overrides

Relaxed settings for development:
- Lower security iterations (faster)
- More verbose logging (DEBUG level)
- Longer session timeouts (convenience)
- Detailed error messages
- Profiling enabled

**Example:**
```python
class DevelopmentConfig(DefaultConfig):
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    PBKDF2_ITERATIONS = 10000  # Faster
    MASK_PASSWORDS_IN_LOGS = False  # See everything
```

### `config/production.py` - Production Overrides

Strict settings for production:
- Strong security settings
- Minimal logging (INFO level)
- Short session timeouts
- Secrets validation
- Error hiding

**Example:**
```python
class ProductionConfig(DefaultConfig):
    DEBUG = False
    LOG_LEVEL = "INFO"
    MASK_PASSWORDS_IN_LOGS = True

    # CRITICAL: Validates FLASK_SECRET_KEY is set!
    if not FLASK_SECRET_KEY:
        raise ValueError("FLASK_SECRET_KEY required!")
```

---

## Using Configuration in Code

### Import Configuration

```python
from src.core.config import config

# Now use config.SETTING_NAME anywhere
```

### Access Settings

```python
# Database path
db_path = config.DB_PATH

# Security settings
iterations = config.PBKDF2_ITERATIONS
rounds = config.BCRYPT_ROUNDS

# GUI settings
theme = config.DEFAULT_THEME
font_size = config.DEFAULT_FONT_SIZE

# Boolean settings
if config.DEBUG:
    print("Debug mode enabled")

if config.CACHE_ENABLED:
    enable_caching()
```

### Example Usage in Database Manager

```python
from src.core.config import config

class DatabaseManager:
    def __init__(self):
        # Use config instead of hardcoded values
        self.db_path = config.DB_PATH
        self.timeout = config.DB_TIMEOUT
        self.max_backups = config.DB_MAX_BACKUPS

    def connect(self):
        return sqlite3.connect(
            self.db_path,
            timeout=config.DB_TIMEOUT
        )
```

### Example Usage in Encryption

```python
from src.core.config import config

class Encryptor:
    def derive_key(self, password, salt):
        return PBKDF2(
            password,
            salt,
            dkLen=32,
            count=config.PBKDF2_ITERATIONS,  # From config!
            hmac_hash_module=SHA256
        )
```

---

## Environment-Specific Settings

### Development Environment

**Setup:**
```bash
# In .env file
APP_ENV=development
DEBUG=True
LOG_LEVEL=DEBUG
```

**Features:**
- Fast encryption (lower iterations)
- Verbose logging
- Detailed error messages
- SQL query logging
- Profiling enabled
- Relaxed security (for convenience)

**Use when:**
- Developing new features
- Debugging issues
- Running local tests

### Production Environment

**Setup:**
```bash
# In .env file
APP_ENV=production
DEBUG=False
LOG_LEVEL=INFO
FLASK_SECRET_KEY=<generated-secret-key>
```

**Features:**
- Strong encryption (100K+ iterations)
- Minimal logging
- Hidden error details
- Strict security
- Performance optimizations
- Audit logging enabled

**Use when:**
- Running in production
- Handling real user data
- Deployed to server

### Testing Environment

**Setup:**
```bash
# In .env file
APP_ENV=testing
TESTING=True
```

**Features:**
- In-memory database
- Fast operations
- Minimal logging
- Isolated from production data

**Use when:**
- Running pytest tests
- Automated CI/CD
- Integration testing

---

## Security Best Practices

### 1. Never Commit .env File

```bash
# Verify .env is in .gitignore
cat .gitignore | grep .env

# Output should show:
# .env
# .env.local
```

### 2. Generate Strong Secret Keys

```bash
# For FLASK_SECRET_KEY
python -c "import secrets; print('FLASK_SECRET_KEY=' + secrets.token_hex(32))"

# Add to .env file (not in code!)
```

### 3. Use Environment Variables for Secrets

**❌ Bad - Hardcoded in code:**
```python
SECRET_KEY = "my-secret-key-123"
```

**✓ Good - From environment:**
```python
SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
```

**✓ Better - With validation:**
```python
SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("FLASK_SECRET_KEY must be set!")
```

### 4. Different Secrets Per Environment

```bash
# development/.env
FLASK_SECRET_KEY=dev-secret-key-12345

# production/.env
FLASK_SECRET_KEY=prod-secure-random-key-abc...xyz
```

### 5. Validate Production Config

```python
# config/production.py automatically validates:
- DEBUG must be False
- FLASK_SECRET_KEY must be set
- PBKDF2_ITERATIONS >= 100000
- BCRYPT_ROUNDS >= 12
- Passwords masked in logs
```

### 6. Review Security Settings

| Setting | Development | Production |
|---------|-------------|------------|
| `DEBUG` | True | **False** |
| `PBKDF2_ITERATIONS` | 10,000 | **100,000+** |
| `BCRYPT_ROUNDS` | 10 | **12+** |
| `SESSION_TIMEOUT_HOURS` | 24 | **8** |
| `MASK_PASSWORDS_IN_LOGS` | False | **True** |
| `FLASK_SECRET_KEY` | dev-key | **Random** |

---

## Common Configuration Tasks

### Change Database Location

```bash
# In .env file
DB_PATH=/path/to/custom/database.db
```

Or programmatically:
```python
# config/default.py
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "password_manager.db"))
```

### Adjust Security Levels

**More Secure (slower):**
```bash
PBKDF2_ITERATIONS=200000
BCRYPT_ROUNDS=14
SESSION_TIMEOUT_HOURS=4
```

**Less Secure (faster - dev only):**
```bash
PBKDF2_ITERATIONS=10000
BCRYPT_ROUNDS=10
SESSION_TIMEOUT_HOURS=24
```

### Enable Features

```bash
# Feature flags
FEATURE_WEB_INTERFACE=True
FEATURE_PASSWORD_HEALTH=True
FEATURE_IMPORT_EXPORT=True
FEATURE_2FA=False  # Not yet implemented
```

### Change Web Interface Port

```bash
# If port 5000 is in use
FLASK_PORT=8080
FLASK_HOST=127.0.0.1
```

### Customize GUI Appearance

```bash
DEFAULT_THEME=light
DEFAULT_COLOR_SCHEME=green
DEFAULT_FONT_SIZE=14
DEFAULT_FONT_SCALE=1.2
WINDOW_WIDTH=1200
WINDOW_HEIGHT=800
```

### Adjust Logging

```bash
# More verbose
LOG_LEVEL=DEBUG
LOG_TO_CONSOLE=True
LOG_TO_FILE=True

# Less verbose
LOG_LEVEL=WARNING
LOG_TO_CONSOLE=False
```

### Performance Tuning

```bash
# Enable caching
CACHE_ENABLED=True
CACHE_TTL=600          # 10 minutes
CACHE_MAX_SIZE=2000

# Database pooling
DB_POOL_SIZE=10
DB_POOL_MAX_OVERFLOW=20
```

---

## Troubleshooting

### Configuration Not Loading

**Symptom:** Changes to .env file not taking effect

**Solutions:**
```bash
# 1. Check .env file location (must be in project root)
ls -la .env

# 2. Check python-dotenv is installed
pip install python-dotenv

# 3. Verify syntax (no spaces around =)
KEY=VALUE  # ✓ Correct
KEY = VALUE  # ✗ Wrong

# 4. Restart application after changes
```

### "FLASK_SECRET_KEY must be set" Error

**Symptom:** Error on startup in production

**Solution:**
```bash
# Generate a secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Add to .env
echo "FLASK_SECRET_KEY=<generated-key>" >> .env
```

### Configuration Validation Fails

**Symptom:** ValueError on startup

**Common causes:**
```bash
# PBKDF2_ITERATIONS too low
PBKDF2_ITERATIONS=5000  # ✗ Must be >= 10000

# Invalid APP_ENV
APP_ENV=staging  # ✗ Must be: development, production, testing

# DEBUG=True in production
APP_ENV=production
DEBUG=True  # ✗ Not allowed!
```

### Wrong Environment Loaded

**Symptom:** Development settings in production

**Solution:**
```bash
# Check APP_ENV
echo $APP_ENV  # or check .env file

# Should be:
APP_ENV=production  # For production
APP_ENV=development  # For development
```

### Print Current Configuration

```bash
# Run config module directly
python -m src.core.config

# Or in Python:
python
>>> from src.core.config import print_config
>>> print_config()
```

### Check Which Config is Loaded

```python
from src.core.config import config

print(f"Environment: {config.APP_ENV}")
print(f"Config Class: {config.__name__}")
print(f"Debug Mode: {config.DEBUG}")
print(f"DB Path: {config.DB_PATH}")
```

---

## Advanced Topics

### Creating Custom Environments

Create `config/staging.py`:

```python
from .production import ProductionConfig

class StagingConfig(ProductionConfig):
    """Staging environment (production-like with relaxed security)"""
    APP_ENV = "staging"
    DEBUG = True
    LOG_LEVEL = "DEBUG"
```

Register in `src/core/config.py`:

```python
from config.staging import StagingConfig

config_map = {
    ...
    "staging": StagingConfig,
}
```

### Environment-Specific .env Files

```bash
# .env.development
APP_ENV=development
DEBUG=True
LOG_LEVEL=DEBUG

# .env.production
APP_ENV=production
DEBUG=False
FLASK_SECRET_KEY=<production-secret>
```

Load specific file:

```python
from dotenv import load_dotenv

load_dotenv(".env.production")
```

### Programmatic Configuration

```python
from src.core.config import reload_config, config

# Switch environments at runtime
reload_config("development")

# Access settings
print(config.DEBUG)  # True

reload_config("production")
print(config.DEBUG)  # False
```

---

## Summary

**Key Points:**
1. All configuration centralized in `config/` directory
2. Use `.env` file for local customization
3. Never commit `.env` file
4. Generate random `FLASK_SECRET_KEY` for production
5. Use `APP_ENV` to switch environments
6. Import with: `from src.core.config import config`
7. Access with: `config.SETTING_NAME`

**Quick Reference:**
```bash
# Setup
cp .env.example .env
nano .env  # Edit settings

# Usage in code
from src.core.config import config
value = config.SETTING_NAME

# Test configuration
python -m src.core.config
```

---

**For more details, see:**
- `.env.example` - All available settings
- `config/default.py` - Default values
- `src/core/config.py` - Loader implementation

**Configuration system is ready to use!** 🎉
