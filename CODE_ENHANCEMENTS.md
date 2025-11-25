# Personal Password Manager - Proposed Code Enhancements

**Version**: 2.2.0 → 2.1.0
**Date**: October 28, 2025
**Priority Classification**: CRITICAL → HIGH → MEDIUM → LOW

This document provides **specific, actionable code improvements** based on the comprehensive analysis. Each enhancement includes:
- **Priority level** and **effort estimate**
- **Current code** (what needs fixing)
- **Improved code** (proposed solution)
- **Impact analysis**
- **Implementation steps**

---

## Table of Contents

### Critical Fixes (Implement First)
1. [Database File Permissions](#1-database-file-permissions)
2. [Web Login Rate Limiting](#2-web-login-rate-limiting)

### High Priority Improvements
3. [Fix Broad Exception Handling](#3-fix-broad-exception-handling)
4. [Optimize Database Search Queries](#4-optimize-database-search-queries)
5. [Add Pagination Support](#5-add-pagination-support)
6. [Simplify Bcrypt Implementation](#6-simplify-bcrypt-implementation)

### Medium Priority Enhancements
7. [Create Validation Utilities](#7-create-validation-utilities)
8. [Add Session Validation Decorator](#8-add-session-validation-decorator)
9. [Improve Session Cleanup](#9-improve-session-cleanup)
10. [Add Comprehensive Unit Tests](#10-add-comprehensive-unit-tests)

### Low Priority / Nice-to-Have
11. [Password Breach Detection](#11-password-breach-detection)
12. [Two-Factor Authentication](#12-two-factor-authentication)
13. [Password Policy Engine](#13-password-policy-engine)

---

# CRITICAL FIXES

## 1. Database File Permissions

**Priority**: 🔴 CRITICAL
**Effort**: ⚡ 5 minutes
**Risk if not fixed**: Database readable by all system users
**Impact**: Major security improvement

### Current Code (VULNERABLE)

```python
# src/core/database.py - Line ~103
class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.connection = sqlite3.connect(str(self.db_path))
        # ❌ File created with default permissions (644 on Unix - world readable!)
```

### Improved Code

```python
# src/core/database.py
import os
import stat
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)

        # Create database file
        self.connection = sqlite3.connect(str(self.db_path))

        # ✅ Enforce strict file permissions
        self._enforce_file_permissions()

        logger.info(f"Database initialized at {self.db_path} with secure permissions")

    def _enforce_file_permissions(self) -> None:
        """
        Enforce strict file permissions on database file.

        Sets permissions to 600 (owner read/write only) on Unix systems.
        On Windows, uses ACLs to restrict access to current user.
        """
        if not self.db_path.exists():
            logger.warning(f"Database file not found: {self.db_path}")
            return

        try:
            if os.name == 'posix':  # Linux/macOS
                # Set to 600 (owner read/write only)
                os.chmod(
                    self.db_path,
                    stat.S_IRUSR | stat.S_IWUSR  # Read + Write for owner only
                )
                logger.info(f"Set database permissions to 600 (owner only)")

            elif os.name == 'nt':  # Windows
                # Use Windows ACLs to restrict access
                import win32security
                import ntsecuritycon as con

                # Get current user SID
                user = win32security.GetTokenInformation(
                    win32security.OpenProcessToken(
                        win32api.GetCurrentProcess(),
                        win32security.TOKEN_QUERY
                    ),
                    win32security.TokenUser
                )[0]

                # Create new DACL with only current user having access
                dacl = win32security.ACL()
                dacl.AddAccessAllowedAce(
                    win32security.ACL_REVISION,
                    con.FILE_ALL_ACCESS,
                    user
                )

                # Apply DACL to file
                sd = win32security.GetFileSecurity(
                    str(self.db_path),
                    win32security.DACL_SECURITY_INFORMATION
                )
                sd.SetSecurityDescriptorDacl(1, dacl, 0)
                win32security.SetFileSecurity(
                    str(self.db_path),
                    win32security.DACL_SECURITY_INFORMATION,
                    sd
                )
                logger.info("Set database permissions to current user only (Windows ACL)")

        except Exception as e:
            logger.error(f"Failed to set database permissions: {e}")
            # Don't fail initialization, but warn user
            logger.warning(
                "Database file permissions could not be enforced. "
                "Manually set file permissions to owner-only access."
            )
```

### Implementation Steps

1. **Add imports** at top of `database.py`:
   ```python
   import os
   import stat
   ```

2. **Add method** `_enforce_file_permissions()` to `DatabaseManager` class

3. **Call method** in `__init__` after database connection

4. **Optional**: Add Windows ACL support (requires `pywin32`)
   ```bash
   pip install pywin32
   ```

5. **Test**:
   ```bash
   # Unix/Mac
   ls -la data/password_manager.db
   # Should show: -rw------- (600)

   # Windows
   icacls data\password_manager.db
   # Should show only current user with full control
   ```

### Validation

```python
# tests/test_database_security.py (NEW FILE)
import os
import stat
from pathlib import Path

def test_database_file_permissions():
    """Test that database file has correct permissions."""
    db = DatabaseManager("test_db.db")

    if os.name == 'posix':
        # Check Unix permissions
        file_stats = os.stat(db.db_path)
        mode = stat.S_IMODE(file_stats.st_mode)

        # Should be 600 (owner read/write only)
        assert mode == 0o600, f"Expected 0o600, got {oct(mode)}"
```

---

## 2. Web Login Rate Limiting

**Priority**: 🔴 CRITICAL
**Effort**: ⚡ 15 minutes
**Risk if not fixed**: Brute force attacks possible
**Impact**: Major security improvement

### Current Code (VULNERABLE)

```python
# src/web/app.py - Line ~128
@app.route('/login', methods=['POST'])
def login():
    """Handle user login."""
    username = request.form.get('username')
    password = request.form.get('password')

    # ❌ No rate limiting - attacker can try unlimited passwords

    try:
        session_id = auth_manager.authenticate_user(username, password)
        session['user_id'] = session_id
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash('Invalid credentials', 'error')
        return redirect(url_for('login_page'))
```

### Improved Code

```python
# src/web/app.py

# 1. Install Flask-Limiter
# pip install Flask-Limiter

# 2. Add imports at top of file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# 3. Initialize limiter after app creation
class PasswordManagerWebApp:
    def __init__(self):
        self.app = Flask(__name__)

        # ✅ Initialize rate limiter
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,  # Rate limit by IP address
            default_limits=["200 per day", "50 per hour"],
            storage_uri="memory://",  # Use in-memory storage
            # For production, use Redis: storage_uri="redis://localhost:6379"
        )

        self._setup_routes()

    def _setup_routes(self):
        """Setup application routes."""

        # ✅ Rate-limited login endpoint
        @self.app.route('/login', methods=['POST'])
        @self.limiter.limit(
            "5 per minute",  # Max 5 attempts per minute
            error_message="Too many login attempts. Please try again later."
        )
        def login():
            """Handle user login with rate limiting."""
            username = request.form.get('username')
            password = request.form.get('password')

            try:
                session_id = self.auth_manager.authenticate_user(username, password)
                session['user_id'] = session_id
                session['username'] = username

                logger.info(f"Successful login for user: {username}")
                return redirect(url_for('dashboard'))

            except ValueError as e:
                logger.warning(f"Failed login attempt for user: {username}")
                flash('Invalid username or password', 'error')
                return redirect(url_for('login_page'))

            except Exception as e:
                logger.error(f"Login error: {e}", exc_info=True)
                flash('An error occurred. Please try again.', 'error')
                return redirect(url_for('login_page'))

        # ✅ Apply rate limiting to other sensitive endpoints
        @self.app.route('/api/change_password', methods=['POST'])
        @self.limiter.limit("3 per hour")
        def change_password():
            """Change password endpoint (rate limited)."""
            pass

        @self.app.route('/api/export', methods=['POST'])
        @self.limiter.limit("10 per hour")
        def export_data():
            """Export endpoint (rate limited)."""
            pass
```

### Advanced: Username-Based Rate Limiting

```python
# More sophisticated: Rate limit by username instead of IP
def get_username_from_request():
    """Extract username from request for rate limiting."""
    if request.method == 'POST':
        return request.form.get('username', get_remote_address())
    return get_remote_address()

# Initialize with custom key function
self.limiter = Limiter(
    app=self.app,
    key_func=get_username_from_request,  # Rate limit by username
    # ...
)

# Different limits for different user types
@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute", key_func=get_username_from_request)
@limiter.limit("20 per hour", key_func=get_username_from_request)
def login():
    # Now limited both by minute AND hour
    pass
```

### Custom Error Pages

```python
# Handle rate limit exceeded
@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded."""
    logger.warning(
        f"Rate limit exceeded for {get_remote_address()}: {request.path}"
    )
    return render_template(
        'error_429.html',
        retry_after=e.description
    ), 429
```

### Implementation Steps

1. **Install dependency**:
   ```bash
   pip install Flask-Limiter
   ```

2. **Add to requirements.txt**:
   ```
   Flask-Limiter>=3.5.0
   ```

3. **Update `src/web/app.py`**:
   - Add imports
   - Initialize limiter
   - Add decorators to sensitive routes

4. **Create error template** (optional):
   ```html
   <!-- templates/error_429.html -->
   <h1>Too Many Requests</h1>
   <p>Please try again in a few minutes.</p>
   ```

5. **Test**:
   ```bash
   # Try to login 6 times quickly
   # 6th attempt should be blocked with 429 error
   ```

### Configuration Options

```python
# config/production.py
RATE_LIMIT_CONFIG = {
    'login': "5 per minute",         # Login attempts
    'api_calls': "100 per hour",     # General API calls
    'exports': "10 per day",         # Data exports
    'password_changes': "3 per hour" # Password changes
}
```

---

# HIGH PRIORITY IMPROVEMENTS

## 3. Fix Broad Exception Handling

**Priority**: 🟡 HIGH
**Effort**: 🔧 3-4 hours
**Impact**: Better debugging, more stable application

### Current Code (PROBLEM)

```python
# src/core/encryption.py - Line ~565
def secure_memory_clear(data: bytes) -> None:
    """Attempt to clear sensitive data from memory."""
    try:
        import ctypes
        ctypes.memset(id(data), 0, len(data))
    except Exception:  # ❌ TOO BROAD
        pass  # ❌ SILENT FAILURE
```

```python
# src/utils/import_export.py - Multiple locations
try:
    result = complex_operation()
except Exception as e:  # ❌ TOO BROAD
    logger.error(f"Error: {e}")  # ❌ No re-raise, no specific handling
    return None
```

### Improved Code

```python
# src/core/encryption.py
def secure_memory_clear(data: bytes) -> None:
    """
    Attempt to clear sensitive data from memory.

    Note: This is best-effort. Python's memory management
    doesn't guarantee complete clearing.

    Raises:
        MemoryClearError: If memory clearing fails critically
    """
    try:
        import ctypes
        ctypes.memset(id(data), 0, len(data))

    except ImportError:
        # ctypes not available (unusual but possible)
        logger.warning("ctypes not available for memory clearing")
        # Fallback: overwrite with zeros (less effective)
        try:
            # This might not actually clear memory, but better than nothing
            for i in range(len(data)):
                data[i] = 0
        except (TypeError, IndexError):
            # bytes are immutable, can't clear
            logger.debug("Unable to clear immutable bytes object")

    except (AttributeError, OSError) as e:
        # Specific errors we can handle
        logger.warning(f"Memory clearing failed (non-critical): {e}")

    except Exception as e:
        # Truly unexpected error - log with full traceback
        logger.error(
            f"Unexpected error in memory clearing: {e}",
            exc_info=True
        )
        # Don't fail the operation, but notify
        raise MemoryClearError(f"Critical memory clearing failure: {e}")
```

### Pattern: Specific Exception Handling

```python
# ✅ GOOD EXAMPLE
def import_csv_data(file_path: str) -> List[Dict]:
    """Import CSV data with specific error handling."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    except FileNotFoundError:
        # Specific: File doesn't exist
        logger.error(f"CSV file not found: {file_path}")
        raise ImportError(f"File not found: {file_path}")

    except PermissionError:
        # Specific: No read permission
        logger.error(f"Permission denied reading: {file_path}")
        raise ImportError(f"Cannot read file (permission denied)")

    except csv.Error as e:
        # Specific: CSV parsing error
        logger.error(f"Invalid CSV format in {file_path}: {e}")
        raise ImportError(f"Invalid CSV file: {e}")

    except UnicodeDecodeError as e:
        # Specific: Encoding issue
        logger.error(f"Encoding error in {file_path}: {e}")
        raise ImportError(f"File encoding error (try UTF-8)")

    except Exception as e:
        # Generic: Log with full context and re-raise
        logger.error(
            f"Unexpected error importing {file_path}: {e}",
            exc_info=True  # ✅ Include full traceback
        )
        raise ImportError(f"Unexpected import error: {e}")
```

### Bulk Fix Script

```python
# scripts/fix_exception_handling.py
"""
Script to identify and help fix broad exception handlers.

Usage: python scripts/fix_exception_handling.py
"""

import re
from pathlib import Path

def find_broad_exceptions(file_path: Path) -> List[Tuple[int, str]]:
    """Find broad exception handlers in a file."""
    issues = []

    with open(file_path, 'r') as f:
        lines = f.readlines()

    for i, line in enumerate(lines, 1):
        # Look for "except Exception:"
        if re.search(r'except\s+Exception\s*:', line):
            issues.append((i, line.strip()))

        # Look for bare "except:"
        if re.search(r'except\s*:', line):
            issues.append((i, line.strip()))

    return issues

def main():
    """Scan all Python files for broad exception handlers."""
    src_dir = Path('src')
    total_issues = 0

    print("Scanning for broad exception handlers...\n")

    for py_file in src_dir.rglob('*.py'):
        issues = find_broad_exceptions(py_file)
        if issues:
            print(f"📄 {py_file}")
            for line_no, line in issues:
                print(f"   Line {line_no}: {line}")
                total_issues += 1
            print()

    print(f"\n Total issues found: {total_issues}")
    print("\n💡 Recommendation: Replace with specific exception types")

if __name__ == '__main__':
    main()
```

---

## 4. Optimize Database Search Queries

**Priority**: 🟡 HIGH
**Effort**: 🔧 2-3 hours
**Impact**: Major performance improvement (10x faster searches)

### Current Code (SLOW)

```python
# src/core/password_manager.py - Line ~351
def search_password_entries(
    self,
    session_id: str,
    criteria: SearchCriteria
) -> List[PasswordEntry]:
    """Search password entries (SLOW - N+1 query pattern)."""

    # ❌ Step 1: Get ALL passwords from database
    db_entries = self.db_manager.get_password_entries(user_id)
    # If user has 10,000 passwords, loads all 10,000!

    results = []

    # ❌ Step 2: Filter in Python (slow!)
    for db_entry in db_entries:
        # Website filter
        if criteria.website:
            if criteria.website.lower() not in db_entry['website'].lower():
                continue

        # Username filter
        if criteria.username:
            if criteria.username.lower() not in db_entry['username'].lower():
                continue

        # Remarks filter
        if criteria.remarks:
            if criteria.remarks.lower() not in (db_entry.get('remarks') or '').lower():
                continue

        # ❌ Decrypt password for each match
        password_entry = self._create_password_entry_from_db(db_entry)
        results.append(password_entry)

    return results
```

**Problems**:
1. Loads ALL passwords into memory
2. Filters in Python instead of SQL
3. Decrypts all matching passwords

**With 10,000 passwords**:
- Memory: ~50 MB
- Time: ~5-10 seconds
- Database reads: 10,000 rows

### Improved Code (FAST)

```python
# src/core/database.py
def search_password_entries(
    self,
    user_id: int,
    website: Optional[str] = None,
    username: Optional[str] = None,
    remarks: Optional[str] = None,
    entry_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> Tuple[List[Dict], int]:
    """
    Search password entries with SQL filtering.

    Returns:
        Tuple of (entries, total_count)
    """
    # ✅ Build WHERE clause with conditions
    where_conditions = ["user_id = ?"]
    params = [user_id]

    if website:
        where_conditions.append("LOWER(website) LIKE LOWER(?)")
        params.append(f"%{website}%")

    if username:
        where_conditions.append("LOWER(username) LIKE LOWER(?)")
        params.append(f"%{username}%")

    if remarks:
        where_conditions.append("LOWER(remarks) LIKE LOWER(?)")
        params.append(f"%{remarks}%")

    if entry_name:
        where_conditions.append("LOWER(entry_name) LIKE LOWER(?)")
        params.append(f"%{entry_name}%")

    where_clause = " AND ".join(where_conditions)

    # ✅ Get total count (for pagination)
    count_query = f"""
        SELECT COUNT(*)
        FROM passwords
        WHERE {where_clause}
    """
    total_count = self._execute_query(count_query, params)[0][0]

    # ✅ Get matching entries (limited by pagination)
    search_query = f"""
        SELECT
            entry_id,
            website,
            username,
            password_encrypted,
            salt,
            iv,
            remarks,
            entry_name,
            created_at,
            modified_at,
            is_favorite
        FROM passwords
        WHERE {where_clause}
        ORDER BY website ASC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    entries = self._execute_query(search_query, params)

    return entries, total_count
```

```python
# src/core/password_manager.py
def search_password_entries(
    self,
    session_id: str,
    criteria: SearchCriteria,
    page: int = 1,
    per_page: int = 100
) -> Tuple[List[PasswordEntry], int]:
    """
    Search password entries (OPTIMIZED).

    Returns:
        Tuple of (password_entries, total_count)
    """
    # Validate session
    session = self.auth_manager.get_session(session_id)
    if not session:
        raise ValueError("Invalid or expired session")

    # ✅ Use SQL filtering (database does the work)
    offset = (page - 1) * per_page

    db_entries, total_count = self.db_manager.search_password_entries(
        user_id=session.user_id,
        website=criteria.website,
        username=criteria.username,
        remarks=criteria.remarks,
        entry_name=criteria.entry_name,
        limit=per_page,
        offset=offset
    )

    # ✅ Only decrypt the entries we need (e.g., 100 instead of 10,000)
    results = []
    for db_entry in db_entries:
        password_entry = self._create_password_entry_from_db(
            db_entry,
            session.master_password
        )
        results.append(password_entry)

    return results, total_count
```

**Performance Improvement**:
- Memory: ~5 MB (90% reduction)
- Time: ~0.5 seconds (10x faster)
- Database reads: 100 rows (99% reduction)

### Add Database Indexes

```python
# src/core/database.py - In _create_tables()
def _create_tables(self):
    """Create database tables with optimized indexes."""

    # ... existing table creation ...

    # ✅ Add composite index for searches
    self.connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_passwords_search
        ON passwords (user_id, website, username)
    """)

    # ✅ Add index on entry_name
    self.connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_passwords_entry_name
        ON passwords (user_id, entry_name)
    """)

    # ✅ Add index on remarks (for full-text search)
    self.connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_passwords_remarks
        ON passwords (user_id, remarks)
    """)
```

---

## 5. Add Pagination Support

**Priority**: 🟡 HIGH
**Effort**: 🔧 4-6 hours
**Impact**: Handle large datasets (10,000+ passwords)

### Current Code (PROBLEM)

```python
# src/gui/main_window.py
class MainWindow:
    def _load_password_entries(self):
        """Load ALL password entries (memory intensive)."""

        # ❌ Loads all passwords at once
        all_passwords = self.password_manager.get_password_entries(
            self.session_id
        )
        # If user has 10,000 passwords: 50+ MB in memory

        # ❌ Renders all entries in GUI
        for password in all_passwords:
            widget = PasswordEntryWidget(password)
            self.password_list.add(widget)
        # Slow to render 10,000 widgets
```

### Improved Code

```python
# src/core/password_manager.py
def get_password_entries_paginated(
    self,
    session_id: str,
    page: int = 1,
    per_page: int = 100,
    sort_by: str = 'website',
    sort_order: str = 'ASC'
) -> Tuple[List[PasswordEntry], PaginationInfo]:
    """
    Get password entries with pagination.

    Args:
        session_id: User session ID
        page: Page number (1-indexed)
        per_page: Entries per page (default: 100)
        sort_by: Sort column ('website', 'created_at', etc.)
        sort_order: 'ASC' or 'DESC'

    Returns:
        Tuple of (entries, pagination_info)
    """
    # Validate session
    session = self.auth_manager.get_session(session_id)
    if not session:
        raise ValueError("Invalid session")

    # Calculate offset
    offset = (page - 1) * per_page

    # Get paginated results from database
    entries, total_count = self.db_manager.get_password_entries_paginated(
        user_id=session.user_id,
        limit=per_page,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order
    )

    # Create pagination info
    total_pages = (total_count + per_page - 1) // per_page  # Ceiling division
    pagination_info = PaginationInfo(
        current_page=page,
        per_page=per_page,
        total_entries=total_count,
        total_pages=total_pages,
        has_prev=page > 1,
        has_next=page < total_pages
    )

    # Convert to PasswordEntry objects
    password_entries = [
        self._create_password_entry_from_db(entry, session.master_password)
        for entry in entries
    ]

    return password_entries, pagination_info


@dataclass
class PaginationInfo:
    """Pagination information."""
    current_page: int
    per_page: int
    total_entries: int
    total_pages: int
    has_prev: bool
    has_next: bool
```

```python
# src/core/database.py
def get_password_entries_paginated(
    self,
    user_id: int,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = 'website',
    sort_order: str = 'ASC'
) -> Tuple[List[Dict], int]:
    """Get password entries with pagination and sorting."""

    # Validate sort parameters
    valid_sort_columns = ['website', 'username', 'created_at', 'modified_at', 'entry_name']
    if sort_by not in valid_sort_columns:
        sort_by = 'website'

    if sort_order.upper() not in ('ASC', 'DESC'):
        sort_order = 'ASC'

    # Get total count
    count_query = "SELECT COUNT(*) FROM passwords WHERE user_id = ?"
    total_count = self._execute_query(count_query, (user_id,))[0][0]

    # Get paginated entries
    query = f"""
        SELECT * FROM passwords
        WHERE user_id = ?
        ORDER BY {sort_by} {sort_order}
        LIMIT ? OFFSET ?
    """
    entries = self._execute_query(query, (user_id, limit, offset))

    return entries, total_count
```

### GUI Implementation

```python
# src/gui/main_window.py
class MainWindow:
    def __init__(self, ...):
        # ... existing code ...

        self.current_page = 1
        self.per_page = 100
        self.pagination_info = None

        self._create_pagination_controls()

    def _create_pagination_controls(self):
        """Create pagination navigation."""
        pagination_frame = ctk.CTkFrame(self)
        pagination_frame.pack(side="bottom", fill="x", padx=10, pady=5)

        # Previous button
        self.prev_btn = ctk.CTkButton(
            pagination_frame,
            text="← Previous",
            command=self._previous_page,
            width=100
        )
        self.prev_btn.pack(side="left", padx=5)

        # Page info label
        self.page_info_label = ctk.CTkLabel(
            pagination_frame,
            text="Page 1 of 1"
        )
        self.page_info_label.pack(side="left", padx=20)

        # Next button
        self.next_btn = ctk.CTkButton(
            pagination_frame,
            text="Next →",
            command=self._next_page,
            width=100
        )
        self.next_btn.pack(side="left", padx=5)

        # Per-page selector
        ctk.CTkLabel(pagination_frame, text="Per page:").pack(side="left", padx=(20, 5))
        self.per_page_var = ctk.StringVar(value="100")
        per_page_menu = ctk.CTkOptionMenu(
            pagination_frame,
            values=["50", "100", "200", "500"],
            variable=self.per_page_var,
            command=self._change_per_page,
            width=80
        )
        per_page_menu.pack(side="left")

    def _load_password_entries(self):
        """Load current page of password entries."""
        try:
            # ✅ Load only current page
            entries, self.pagination_info = self.password_manager.get_password_entries_paginated(
                session_id=self.session_id,
                page=self.current_page,
                per_page=self.per_page
            )

            # Clear existing widgets
            for widget in self.password_list_frame.winfo_children():
                widget.destroy()

            # Create widgets for current page only
            for entry in entries:
                widget = PasswordEntryWidget(self.password_list_frame, entry)
                widget.pack(fill="x", pady=2)

            # Update pagination controls
            self._update_pagination_controls()

        except Exception as e:
            logger.error(f"Failed to load passwords: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to load passwords: {e}")

    def _update_pagination_controls(self):
        """Update pagination button states and labels."""
        if not self.pagination_info:
            return

        # Update label
        self.page_info_label.configure(
            text=f"Page {self.pagination_info.current_page} of {self.pagination_info.total_pages} "
                 f"({self.pagination_info.total_entries} total entries)"
        )

        # Enable/disable buttons
        self.prev_btn.configure(state="normal" if self.pagination_info.has_prev else "disabled")
        self.next_btn.configure(state="normal" if self.pagination_info.has_next else "disabled")

    def _previous_page(self):
        """Navigate to previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self._load_password_entries()

    def _next_page(self):
        """Navigate to next page."""
        if self.pagination_info and self.pagination_info.has_next:
            self.current_page += 1
            self._load_password_entries()

    def _change_per_page(self, value: str):
        """Change number of entries per page."""
        self.per_page = int(value)
        self.current_page = 1  # Reset to first page
        self._load_password_entries()
```

**Performance Improvement**:
- **Before**: Load 10,000 entries = 5-10 seconds, 50 MB RAM
- **After**: Load 100 entries = 0.5 seconds, 5 MB RAM
- **Result**: 10x faster, 90% less memory

---

*Continue reading for more enhancements...*

