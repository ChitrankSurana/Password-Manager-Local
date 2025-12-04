# TODO - Pending Issues and Improvements

**Created:** 2025-12-05
**Status:** Active
**Priority:** Medium

---

## 🔴 **CRITICAL - Pre-commit Hook Failures**

### 1. Fix Broken F-Strings (17 files)
**Priority:** HIGH
**Estimated Time:** 25-30 minutes
**Status:** ❌ Not Started

**Issue:** Autopep8 incorrectly split multi-line f-strings, creating invalid syntax.

**Affected Files:**
```
- check_dependencies.py (line 119)
- src/core/database.py (line 581)
- src/core/import_export.py (line 418)
- src/core/security_audit_logger.py (line 932)
- src/core/service_integration.py (line 820)
- src/gui/components/password_generator.py (line 102)
- src/gui/enhanced_password_list.py (line 413)
- src/gui/components/backup_manager.py (line 972)
- src/gui/main_window.py (line 423)
- src/gui/password_health.py (line 489)
- src/gui/password_view_dialog.py (line 529)
- src/gui/themes.py (line 103)
- src/utils/password_generator.py (line 204)
- src/gui/settings_window.py (line 597)
- src/utils/strength_checker.py (line 258)
- test_multiuser_portability.py (line 103)
- test_suite.py (line 423)
```

**Error Pattern:**
```python
# BROKEN (current state)
f"text {
    variable}"

# FIX OPTION 1 (single line)
f"text {variable}"

# FIX OPTION 2 (multi-line with parentheses)
(f"text "
 f"{variable}")
```

**Action Items:**
- [ ] Write automated script to detect broken f-strings
- [ ] Fix all 17 files
- [ ] Run Black formatter to verify
- [ ] Test pre-commit hooks

---

### 2. Fix Bandit Configuration
**Priority:** HIGH
**Estimated Time:** 2 minutes
**Status:** ❌ Not Started

**Issue:** Unknown test B106 in .bandit.yaml

**File:** `.bandit.yaml` (line ~20)

**Fix:**
```yaml
# Remove or comment out:
- B106  # hardcoded_password_funcarg
```

**Action Items:**
- [ ] Remove B106 from skips list in .bandit.yaml
- [ ] Test bandit hook

---

### 3. Fix MyPy Unicode Encoding Issues
**Priority:** MEDIUM
**Estimated Time:** 5 minutes
**Status:** ❌ Not Started

**Issue:** MyPy can't encode checkmark character in test_theme_fix.py

**File:** `test_theme_fix.py`

**Errors:**
```
test_theme_fix.py:16:18: Incompatible types in assignment
test_theme_fix.py:17:18: Incompatible types in assignment
test_theme_fix.py:100:13: Statement is unreachable
```

**Action Items:**
- [ ] Review test_theme_fix.py unicode handling
- [ ] Fix type annotations for sys.stdout/stderr assignments
- [ ] Remove unreachable code or add proper guards
- [ ] Consider disabling MyPy for test files if needed

---

## 🟡 **CODE QUALITY - Non-Critical Issues**

### 4. Remaining Flake8 Warnings (Ignored for now)
**Priority:** LOW
**Estimated Time:** 30-60 minutes
**Status:** ⏸️ Deferred

Currently ignored in .pre-commit-config.yaml:
- **C901** - Function complexity (8 instances)
- **F811** - Redefinition of unused names (8 instances)
- **F841** - Unused variables (13 instances)
- **F402** - Import shadowing (2 instances)

**Files with complexity issues (C901):**
```
- src/core/password_manager.py:405 (search_password_entries)
- src/gui/password_health.py:321 (_analyze_password_health)
```

**Action Items:**
- [ ] Refactor complex functions to reduce cyclomatic complexity
- [ ] Remove unused variables or prefix with underscore
- [ ] Fix function redefinitions
- [ ] Address import shadowing

---

### 5. Clean Up Duplicate/Redefined Functions
**Priority:** LOW
**Estimated Time:** 15 minutes
**Status:** ⏸️ Deferred

**Files with redefinitions (F811):**
```
- src/gui/main_window.py (lines 1618, 1637, 1646, 1683)
  - _add_password_entry (redefined)
  - _show_settings (redefined)
  - _show_password_generator (redefined)
  - _edit_password_entry (redefined)
```

**Action Items:**
- [ ] Review and remove duplicate function definitions
- [ ] Ensure proper method override patterns
- [ ] Test functionality after cleanup

---

## 🟢 **ENHANCEMENTS - Future Improvements**

### 6. Apply Font Manager to All Dialogs
**Priority:** MEDIUM
**Estimated Time:** 2-3 hours
**Status:** 📋 Planned

**Current State:**
- ✅ Font manager created and working
- ✅ Theme system integrated
- ✅ First-time setup wizard implemented
- ✅ Settings window has font selector

**Remaining Work:**
- [ ] Update all remaining dialogs to use font manager:
  - [ ] Add Password dialog
  - [ ] Edit Password dialog
  - [ ] Password Generator dialog
  - [ ] Backup Manager dialog
  - [ ] About dialog
  - [ ] Confirmation dialogs

**Action Items:**
- [ ] Audit all dialog classes for hardcoded font sizes
- [ ] Replace with FontManager calls
- [ ] Test at all font sizes (small, medium, large, extra_large)
- [ ] Update documentation

---

### 7. Improve Password Health Dashboard
**Priority:** LOW
**Estimated Time:** 1-2 hours
**Status:** 💡 Idea

**Potential Enhancements:**
- [ ] Add export functionality for health reports (PDF/CSV)
- [ ] Implement scheduled health checks with notifications
- [ ] Add password strength trends over time
- [ ] Create remediation workflows (bulk update old passwords)
- [ ] Add customizable age thresholds in settings

---

### 8. Optimize Database Queries
**Priority:** LOW
**Estimated Time:** 2-3 hours
**Status:** 💡 Idea

**Areas to optimize:**
- [ ] Add database indexing for frequently queried fields
- [ ] Implement query result caching
- [ ] Optimize search_password_entries complexity
- [ ] Add pagination for large password lists
- [ ] Profile and optimize slow queries

---

### 9. Enhanced Testing Coverage
**Priority:** LOW
**Estimated Time:** 4-6 hours
**Status:** 💡 Idea

**Test Coverage Improvements:**
- [ ] Add unit tests for font manager
- [ ] Add integration tests for first-time setup wizard
- [ ] Add tests for password age calculations
- [ ] Add tests for age-based filtering/sorting
- [ ] Increase overall test coverage to >80%
- [ ] Add performance benchmarks

---

### 10. Documentation Updates
**Priority:** LOW
**Estimated Time:** 2-3 hours
**Status:** 💡 Idea

**Documentation Needs:**
- [ ] Complete Sphinx API documentation
- [ ] Add user guide with screenshots
- [ ] Document font size feature
- [ ] Document password age tracking feature
- [ ] Create developer contribution guide
- [ ] Add troubleshooting section

---

## 📝 **NOTES**

### Recent Changes (2025-12-05)
- ✅ Implemented Password Age Tracking feature
- ✅ Implemented Font Size Settings with first-time setup
- ✅ Fixed 155+ linting issues (Flake8, MyPy, Bandit)
- ✅ Added comprehensive error handling
- ✅ Set up pre-commit hooks
- ✅ Created automated linting fix script

### Known Issues
1. Pre-commit hooks currently failing due to formatting issues
2. Some f-strings broken by autopep8 (need manual fix)
3. Minor MyPy type annotation issues in test files

### Technical Debt
1. Complexity in search_password_entries function (C901)
2. Complexity in _analyze_password_health function (C901)
3. Some duplicate function definitions need cleanup
4. Unused variables in test files

---

## 🎯 **NEXT SESSION PRIORITIES**

**Immediate (Next Session):**
1. Fix broken f-strings (17 files) - 30 minutes
2. Fix Bandit B106 config - 2 minutes
3. Fix MyPy unicode issues - 5 minutes
4. Verify all pre-commit hooks pass - 5 minutes

**Short Term (Within Week):**
1. Apply font manager to remaining dialogs
2. Clean up duplicate functions
3. Address code complexity warnings

**Long Term (Future):**
1. Enhanced testing coverage
2. Performance optimizations
3. Complete documentation
4. Additional password health features

---

## 🔗 **REFERENCES**

- **Pre-commit Config:** `.pre-commit-config.yaml`
- **Linting Guide:** `LINTING_GUIDE.md`
- **Fix Script:** `fix_linting.py`
- **Font Manager:** `src/utils/font_manager.py`
- **Password Age Utils:** `src/utils/password_age.py`

---

**Last Updated:** 2025-12-05
**Maintained By:** Project Team
**Repository:** https://github.com/ChitrankSurana/Password-Manager-Local.git
