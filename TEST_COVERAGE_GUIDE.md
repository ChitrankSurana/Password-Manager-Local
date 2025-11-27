# Test Coverage Measurement Guide

## What is Test Coverage?

Test coverage tells you **what percentage of your code is being tested**. It identifies untested code paths that might have bugs.

## Why Measure Coverage?

- **Find gaps**: Discover what's not being tested
- **Improve quality**: Add tests for critical untested code
- **Confidence**: Know how much of your code is verified
- **Trends**: Track coverage over time

---

## Quick Setup (5 Minutes)

### Step 1: Install Coverage Tools

```bash
pip install pytest-cov coverage
```

### Step 2: Run Tests with Coverage

```bash
# Run all tests and generate coverage report
pytest --cov=src --cov-report=html --cov-report=term tests/

# Or use coverage directly
coverage run -m pytest tests/
coverage report
coverage html
```

### Step 3: View Results

```bash
# Terminal report shows immediately
# HTML report opens in browser:
start htmlcov/index.html   # Windows
open htmlcov/index.html    # Mac
xdg-open htmlcov/index.html # Linux
```

---

## Understanding Coverage Reports

### Terminal Output Example:
```
Name                              Stmts   Miss  Cover
-----------------------------------------------------
src/core/auth.py                    245     12    95%
src/core/database.py                389     45    88%
src/core/encryption.py              156      8    95%
src/core/password_manager.py        298     67    78%
src/gui/main_window.py              892    456    49%  ⚠️
src/utils/password_generator.py     187     23    88%
-----------------------------------------------------
TOTAL                              4523    892    80%
```

### What the Numbers Mean:
- **Stmts**: Total executable statements
- **Miss**: Statements not executed by tests
- **Cover**: Percentage covered (Stmts - Miss) / Stmts

### Coverage Goals:
- **90%+**: Excellent (critical security code)
- **80-90%**: Good (most production code)
- **70-80%**: Acceptable (UI code, less critical)
- **<70%**: Needs improvement

---

## Create Coverage Script

Create `run_coverage.py`:

```python
#!/usr/bin/env python3
"""
Generate test coverage report for Password Manager
"""

import subprocess
import sys
import os
from pathlib import Path

def run_coverage():
    """Run tests with coverage and generate reports"""
    print("=" * 70)
    print("Running Test Coverage Analysis")
    print("=" * 70)
    print()

    # Step 1: Run tests with coverage
    print("[1/3] Running tests with coverage...")
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "--cov=src",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-report=json",
        "tests/"
    ])

    if result.returncode != 0:
        print("\n❌ Tests failed! Fix test failures before analyzing coverage.")
        return 1

    # Step 2: Generate detailed HTML report
    print("\n[2/3] Generating detailed HTML report...")
    subprocess.run([sys.executable, "-m", "coverage", "html"])

    # Step 3: Show summary
    print("\n[3/3] Coverage Summary:")
    subprocess.run([sys.executable, "-m", "coverage", "report"])

    print("\n" + "=" * 70)
    print("✅ Coverage analysis complete!")
    print("=" * 70)
    print(f"\n📊 View detailed report: htmlcov/index.html")
    print(f"📁 Report location: {Path('htmlcov').absolute()}")

    # Open HTML report
    html_path = Path("htmlcov/index.html")
    if html_path.exists():
        print("\n🌐 Opening report in browser...")
        if os.name == 'nt':  # Windows
            os.startfile(html_path)
        elif sys.platform == 'darwin':  # Mac
            subprocess.run(['open', html_path])
        else:  # Linux
            subprocess.run(['xdg-open', html_path])

    return 0

if __name__ == "__main__":
    sys.exit(run_coverage())
```

**Usage:**
```bash
python run_coverage.py
```

---

## Interpreting Results

### Green Lines (Covered):
```python
def add_password(self, password):
    self.passwords.append(password)  # ✅ Tested
    return True  # ✅ Tested
```

### Red Lines (Not Covered):
```python
def delete_all_passwords(self):
    if not self.confirm_deletion():  # ❌ Not tested
        return False  # ❌ Not tested
    self.passwords.clear()  # ✅ Tested
    return True  # ✅ Tested
```

**Action:** Write test for the error path (confirm_deletion returns False)

---

## What to Test First

### Priority 1: Critical Security Code (Target: 95%+)
- `src/core/encryption.py`
- `src/core/auth.py`
- `src/core/database.py`

### Priority 2: Core Business Logic (Target: 85%+)
- `src/core/password_manager.py`
- `src/utils/password_generator.py`
- `src/utils/import_export.py`

### Priority 3: UI Code (Target: 70%+)
- `src/gui/main_window.py`
- `src/gui/login_window.py`

### Priority 4: Optional/Experimental (Target: 60%+)
- `src/web/app.py`
- Cloud sync modules

---

## Common Coverage Pitfalls

### 1. **Error Handling Not Tested**
```python
try:
    result = risky_operation()
except Exception as e:
    logger.error(f"Failed: {e}")  # ❌ Often not tested
    return None
```

**Fix:** Write test that triggers the exception

### 2. **Defensive Code Not Tested**
```python
if user is None:  # ❌ "This should never happen" = not tested
    raise ValueError("User cannot be None")
```

**Fix:** Write test with None user

### 3. **Platform-Specific Code**
```python
if os.name == 'nt':  # Only tested on Windows
    do_windows_thing()
else:  # Never tested on Windows
    do_unix_thing()
```

**Fix:** Mock `os.name` in tests

---

## Continuous Coverage Tracking

### Add to Git Pre-commit Hook

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Run tests and check coverage before commit

echo "Running tests with coverage..."
python -m pytest --cov=src --cov-fail-under=75 tests/

if [ $? -ne 0 ]; then
    echo "❌ Tests failed or coverage below 75%. Commit aborted."
    exit 1
fi

echo "✅ Tests passed with adequate coverage"
exit 0
```

### Add Coverage Badge to README

Use shields.io or codecov.io:
```markdown
![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)
```

---

## Advanced: Coverage by Module

```bash
# Coverage for specific module
pytest --cov=src/core/encryption tests/

# Exclude specific files
pytest --cov=src --cov-config=.coveragerc tests/
```

Create `.coveragerc`:
```ini
[run]
source = src
omit =
    */tests/*
    */__init__.py
    */gui/*  # Exclude GUI for now

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov
title = Password Manager Coverage Report
```

---

## What Good Coverage Looks Like

### ✅ Good Example:
```
Name                          Stmts   Miss  Cover
-------------------------------------------------
src/core/auth.py               245      8    97%  ✅
src/core/encryption.py         156      4    97%  ✅
src/core/database.py           389     32    92%  ✅
src/core/password_manager.py   298     45    85%  ✅
```

### ⚠️ Needs Improvement:
```
Name                          Stmts   Miss  Cover
-------------------------------------------------
src/gui/main_window.py         892    456    49%  ⚠️
src/web/app.py                 253    167    34%  ⚠️
```

**Action Items:**
1. Focus on critical security code first (97%+ achieved ✅)
2. Improve core business logic (85%+ on track ✅)
3. Add basic UI tests (currently 49%, target 70%)
4. Web interface can wait (34%, non-critical)

---

## Integration with CI/CD

### GitHub Actions Example:

`.github/workflows/test-coverage.yml`:
```yaml
name: Test Coverage

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests with coverage
      run: |
        pytest --cov=src --cov-report=xml tests/

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

---

## Quick Commands Reference

```bash
# Basic coverage
pytest --cov=src tests/

# With HTML report
pytest --cov=src --cov-report=html tests/

# Show missing lines
pytest --cov=src --cov-report=term-missing tests/

# Fail if below threshold
pytest --cov=src --cov-fail-under=80 tests/

# Coverage for single module
pytest --cov=src/core/encryption tests/test_encryption.py

# Generate all report types
pytest --cov=src \
       --cov-report=html \
       --cov-report=term \
       --cov-report=json \
       tests/
```

---

## Recommended Target Coverage

| Module Type | Target | Priority |
|-------------|--------|----------|
| Security (encryption, auth) | 95%+ | Critical |
| Core business logic | 85%+ | High |
| Database operations | 85%+ | High |
| Utilities | 80%+ | Medium |
| GUI code | 70%+ | Medium |
| Web interface | 60%+ | Low |
| Experimental features | 50%+ | Low |

**Overall Project Target: 80%**

---

## Next Steps

1. **Run coverage now**:
   ```bash
   pip install pytest-cov
   pytest --cov=src --cov-report=html tests/
   start htmlcov/index.html
   ```

2. **Identify gaps**: Look for red (uncovered) lines in critical modules

3. **Write tests**: Focus on security and core logic first

4. **Track progress**: Re-run coverage after adding tests

5. **Integrate**: Add coverage check to your build process

---

## Summary

✅ **Easy to set up** (5 minutes)
✅ **Actionable insights** (see exactly what's not tested)
✅ **Improves quality** (find bugs before users do)
✅ **Tracks progress** (coverage trends over time)

**Start with:** `pytest --cov=src --cov-report=html tests/`

Then gradually improve coverage in critical modules!
