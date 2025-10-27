# CSV Import Enhancement - Selective Import with Master Password

## Overview

The CSV import feature has been enhanced with a **two-step wizard** that allows you to:
1. **Map columns** from your CSV file to password fields
2. **Select which passwords** you want to import (with checkboxes)
3. **Verify with master password** before importing

This gives you full control over what gets imported into your password manager.

---

## What Changed

### Before (Limited)
```
User clicks Import CSV
    ↓
Select CSV file
    ↓
Map columns
    ↓
Click Import button
    ↓
ALL passwords imported ❌ (no choice)
    ↓
No master password verification ❌
```

**Problems:**
- ❌ No way to select specific passwords
- ❌ Imports everything from the file
- ❌ No master password verification
- ❌ Can't preview what will be imported

### After (Enhanced)
```
User clicks Import CSV
    ↓
Select CSV file
    ↓
STEP 1: Map columns
    ↓
Click "Next: Select Passwords →"
    ↓
STEP 2: Select passwords with checkboxes ✅
    ↓
Click "Import Selected Passwords"
    ↓
Master password verification ✅
    ↓
Only selected passwords imported ✅
```

**Benefits:**
- ✅ Two-step wizard interface
- ✅ Preview ALL rows before importing
- ✅ Select/deselect specific passwords
- ✅ Master password verification required
- ✅ Full control over what gets imported

---

## How to Use

### Step 1: Map Columns

**1. Click Import CSV**
- Located in the "Tools" menu or toolbar
- Select your CSV file

**2. Column Mapping Screen**
```
┌─────────────────────────────────────────────────┐
│  📄 Step 1: Map CSV Columns                     │
├─────────────────────────────────────────────────┤
│  Map the CSV columns to password fields.        │
│  Found 25 rows.                                  │
│                                                  │
│  Column Mapping:                                 │
│  Website:  [Select Column ▼]                    │
│  Username: [Select Column ▼]                    │
│  Password: [Select Column ▼]                    │
│  Remarks:  [Select Column ▼]                    │
│                                                  │
│  Preview (first 5 rows)                          │
│  ┌────────────────────────────────────────┐     │
│  │ Website    │ Username   │ Password    │     │
│  │ google.com │ user@...   │ ********    │     │
│  │ github.com │ dev@...    │ ********    │     │
│  └────────────────────────────────────────┘     │
│                                                  │
│  [ Cancel ]    [ Next: Select Passwords → ]     │
└─────────────────────────────────────────────────┘
```

**3. Map Your Columns**
- **Website**, **Username**, **Password** are REQUIRED
- **Remarks** is optional
- Auto-mapping attempts to detect common column names
- Preview shows first 5 rows

**4. Click "Next: Select Passwords →"**
- Validates that required fields are mapped
- Proceeds to selection step

---

### Step 2: Select Passwords

**Selection Screen**
```
┌─────────────────────────────────────────────────┐
│  ✅ Step 2: Select Passwords to Import          │
├─────────────────────────────────────────────────┤
│  Select which passwords you want to import      │
│  (25 total rows found)                          │
│                                                  │
│  [ ✓ Select All ] [ ✗ Deselect All ]   10 selected │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │ ☑ Website     │ Username    │ Remarks   │   │
│  │ ☑ google.com  │ user@...    │ Personal  │   │
│  │ ☑ github.com  │ dev@...     │ Work      │   │
│  │ ☐ facebook.com│ old@...     │ Unused    │ ← Unchecked
│  │ ☑ twitter.com │ user@...    │ Social    │   │
│  │ ... (scrolls to show ALL rows)           │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
│  [ ← Back to Mapping ] [ Cancel ] [ Import Selected ] │
└─────────────────────────────────────────────────┘
```

**Features:**
- ✅ **All rows displayed** (not just preview)
- ✅ **Checkbox for each password** - select what you want
- ✅ **Select All / Deselect All** buttons
- ✅ **Live selection counter** - shows how many selected
- ✅ **Back button** - return to column mapping if needed
- ✅ **Scrollable list** - handles large CSV files

---

### Step 3: Master Password Verification

**1. Click "Import Selected Passwords"**

**2. Master Password Prompt**
```
┌────────────────────────────────────┐
│  🔒 Verify Master Password         │
├────────────────────────────────────┤
│  Please enter your master password │
│  to confirm import                 │
│                                    │
│  Master Password:                  │
│  [******************]  👁          │
│                                    │
│  Attempts remaining: 3             │
│                                    │
│    [ Cancel ]      [ Verify ]      │
└────────────────────────────────────┘
```

**3. Enter Master Password**
- Required for security
- Same password you use to login
- Maximum 3 attempts

**4. Import Proceeds**
```
┌────────────────────────────────────┐
│  Import Complete                   │
├────────────────────────────────────┤
│  ✅ Successfully imported 10        │
│     passwords                       │
│                                    │
│           [ OK ]                   │
└────────────────────────────────────┘
```

---

## User Scenarios

### Scenario 1: Import Everything
```
1. Select CSV file
2. Map columns (auto-mapping usually works)
3. Click "Next: Select Passwords →"
4. Click "Select All" (default is all selected)
5. Click "Import Selected Passwords"
6. Enter master password
7. All passwords imported ✅
```

### Scenario 2: Import Specific Passwords
```
1. Select CSV file
2. Map columns
3. Click "Next: Select Passwords →"
4. Review the list of 100 passwords
5. Uncheck 50 passwords you don't want
6. Verify 50 passwords are selected
7. Click "Import Selected Passwords"
8. Enter master password
9. Only 50 selected passwords imported ✅
```

### Scenario 3: Preview Before Deciding
```
1. Select CSV file
2. Map columns
3. Click "Next: Select Passwords →"
4. Scroll through ALL rows to review
5. Decide which ones to import
6. Uncheck unwanted entries
7. Click "Import Selected Passwords"
8. Enter master password
9. Selected passwords imported ✅
```

### Scenario 4: Fix Column Mapping
```
1. Select CSV file
2. Map columns (oops, wrong mapping!)
3. Click "Next: Select Passwords →"
4. Notice data looks wrong
5. Click "← Back to Mapping" button ✅
6. Fix the column mapping
7. Click "Next: Select Passwords →" again
8. Now data looks correct
9. Select and import ✅
```

---

## Security Features

### 1. Master Password Required

**Why?**
- Prevents unauthorized imports
- Ensures you're present during the operation
- Protects against malicious CSV files

**How It Works:**
- Master password prompt appears before import
- Password verified using bcrypt
- Maximum 3 attempts before cancellation
- All attempts logged for audit trail

### 2. Selective Import

**Why?**
- Full control over what gets imported
- Prevent duplicate entries
- Skip old/unused passwords
- Review before committing

**How It Works:**
- Every row has a checkbox
- Default: all selected (opt-out model)
- Can select/deselect individually or in bulk
- Only checked rows are imported

### 3. Two-Step Validation

**Why?**
- Catch column mapping errors early
- Preview data before importing
- Ability to go back and fix issues

**How It Works:**
- Step 1: Validate column mapping
- Step 2: Validate data and selections
- Can navigate back and forth
- No import until you confirm

---

## Technical Implementation

### Code Changes

**File**: `src/gui/main_window.py`

**CSVImportDialog Class** (Lines 3104-3525):

#### Constructor Enhancement
```python
def __init__(self, parent, session_id, password_manager, csv_file_path,
             on_success, auth_manager, username):
    # NEW: auth_manager and username for master password verification
    self.auth_manager = auth_manager
    self.username = username
    self.all_data = []  # Store ALL rows, not just preview
    self.row_checkboxes = []  # Store checkbox variables
    self.step = 1  # Track current step (1=mapping, 2=selection)
```

#### New Methods

**1. `_go_to_selection_step()` (Lines 3260-3289)**
- Validates required column mapping
- Creates column index map
- Clears UI and shows selection step

**2. `_create_selection_ui()` (Lines 3291-3400)**
- Shows all rows with checkboxes
- Displays website, username, remarks for each row
- Adds Select All / Deselect All buttons
- Shows selection counter
- Adds Import button with master password

**3. `_select_all()` (Lines 3402-3406)**
- Checks all checkboxes

**4. `_deselect_all()` (Lines 3408-3412)**
- Unchecks all checkboxes

**5. `_update_selection_count()` (Lines 3414-3417)**
- Updates live counter of selected passwords

**6. `_back_to_mapping()` (Lines 3419-3427)**
- Returns to step 1 (column mapping)

**7. `_import_with_master_password()` (Lines 3429-3459)**
- Validates at least one password selected
- Prompts for master password
- Calls import if verified

**8. `_import_passwords()` (Lines 3461-3525) - UPDATED**
- Only imports selected rows
- Uses master password for encryption
- Shows detailed success/error counts

#### MainWindow._import_csv() Update (Lines 1375-1400)
```python
CSVImportDialog(
    parent=self,
    session_id=self.session_id,
    password_manager=self.password_manager,
    csv_file_path=file_path,
    on_success=lambda: self._load_password_entries(),
    auth_manager=self.auth_manager,  # NEW!
    username=self.username  # NEW!
)
```

---

## CSV File Format

### Supported Formats

**Standard Format:**
```csv
Website,Username,Password,Remarks
google.com,user@gmail.com,SecurePass123!,Personal account
github.com,developer@email.com,DevPass456!,Work account
```

**Alternative Column Names (Auto-Detected):**
- **Website**: URL, Site, Domain, Website URL
- **Username**: User, Email, Login, Username
- **Password**: Pass, Password, Pwd
- **Remarks**: Note, Notes, Comment, Comments, Remark

**Flexible Format:**
```csv
Site,Email,Pass,Note
example.com,test@test.com,password123,Test account
```

The auto-mapping will detect and map these automatically!

---

## Error Handling

### Missing Required Fields

**Problem**: Website, Username, or Password not mapped

**Solution**:
```
⚠️ Please map required fields: Website, Password
```
- Error shown at bottom of mapping screen
- Cannot proceed until fixed
- Clear indication of what's missing

### No Passwords Selected

**Problem**: User unchecked all passwords

**Solution**:
```
⚠️ Please select at least one password to import
```
- Error shown when clicking Import
- Must select at least one row

### Master Password Verification Failed

**Problem**: Wrong master password entered

**Solution**:
```
⚠️ Import cancelled - master password not verified
```
- Import aborted
- No changes made
- Can try again

### Row Import Errors

**Problem**: Some rows fail to import

**Solution**:
```
✅ Successfully imported 8 passwords
⚠️ 2 errors occurred
```
- Detailed error count
- Successful imports are saved
- Failed rows are logged

---

## Benefits

### 1. User Control
- ✅ Choose exactly what to import
- ✅ Preview all data before importing
- ✅ Skip duplicates or unwanted entries
- ✅ Navigate back to fix mistakes

### 2. Security
- ✅ Master password verification required
- ✅ Prevents unauthorized imports
- ✅ Audit trail of all imports
- ✅ Protection against malicious CSV files

### 3. Flexibility
- ✅ Works with any CSV column names
- ✅ Auto-detects common formats
- ✅ Handles large files (all rows shown)
- ✅ Easy to use wizard interface

### 4. User Experience
- ✅ Two-step wizard guides the process
- ✅ Clear instructions at each step
- ✅ Visual feedback (checkboxes, counters)
- ✅ Tooltips explain each button
- ✅ Can go back and forward

---

## Tips and Tricks

### Tip 1: Test with Small File First
```
1. Export a few passwords to CSV
2. Test the import process
3. Verify mapping works correctly
4. Then import your full password list
```

### Tip 2: Use Select All, Then Deselect
```
1. Click "Select All" (all checked)
2. Scroll through and uncheck unwanted entries
3. Easier than checking 100 boxes individually
```

### Tip 3: Review Before Importing
```
1. In selection step, scroll through ALL rows
2. Check website and username look correct
3. Uncheck any suspicious entries
4. Then import with confidence
```

### Tip 4: Export First for Backup
```
1. Export current passwords as backup
2. Then import new passwords
3. If something goes wrong, restore from backup
```

### Tip 5: Check Column Mapping Carefully
```
1. Look at the preview (first 5 rows)
2. Verify data appears in correct columns
3. Use "Back to Mapping" if needed
4. Better to fix mapping than import wrong data
```

---

## Comparison: Before vs After

| Feature | Before | After (Enhanced) |
|---------|--------|------------------|
| **Step-by-step wizard** | ❌ Single screen | ✅ Two-step process |
| **View all rows** | ❌ Preview only (5 rows) | ✅ All rows displayed |
| **Select specific passwords** | ❌ Import all | ✅ Checkboxes for each |
| **Select All / Deselect All** | ❌ Not available | ✅ Bulk operations |
| **Selection counter** | ❌ No feedback | ✅ Live counter |
| **Back navigation** | ❌ Start over | ✅ Back button |
| **Master password** | ❌ Not required | ✅ Required |
| **Preview before import** | ⚠️ First 5 only | ✅ All rows |
| **Error handling** | ⚠️ Basic | ✅ Detailed feedback |
| **Tooltips** | ❌ None | ✅ All buttons |

---

## FAQ

**Q: Do I have to select each password individually?**
A: No! By default, all passwords are selected. You can use "Deselect All" to start fresh, or just uncheck the ones you don't want.

**Q: Can I see all passwords before importing?**
A: Yes! Step 2 displays ALL rows from your CSV file, not just a preview. Scroll through to review everything.

**Q: What if I mapped the columns wrong?**
A: Click the "← Back to Mapping" button in Step 2 to return to the mapping screen and fix it.

**Q: Why do I need my master password for import?**
A: Security! This prevents unauthorized users from importing malicious password lists if they access your unlocked computer.

**Q: What happens if I cancel during master password prompt?**
A: The import is cancelled. No passwords are imported. Your data remains unchanged.

**Q: Can I import the same CSV file multiple times?**
A: Yes, but be careful of duplicates! The password manager will create new entries even if they already exist. Use the checkboxes to skip entries you've already imported.

**Q: What if some rows fail to import?**
A: The import continues for successful rows. You'll see a message like "8 successes, 2 errors". Check the logs for details on failed rows.

**Q: How do I know what was imported?**
A: After import, the password list automatically refreshes showing all entries including newly imported ones.

---

## Logging

All import activities are logged for audit purposes:

**Column Mapping Validated:**
```log
INFO: Column mapping validated. Proceeding to selection step.
```

**Master Password Prompt:**
```log
INFO: Prompting for master password to import 10 passwords
```

**Master Password Verified:**
```log
INFO: Master password verified - proceeding with import
```

**Import Results:**
```log
INFO: Importing 10 selected passwords
INFO: Import completed: 10 successes, 0 errors
```

**Master Password Failed:**
```log
WARNING: Master password verification failed (1/3 attempts)
INFO: Master password verification failed or cancelled - import aborted
```

---

## Summary

### What This Enhancement Provides

✅ **Two-step wizard** - Map columns, then select passwords
✅ **Full preview** - See ALL rows before importing
✅ **Selective import** - Choose exactly what to import
✅ **Master password** - Security verification required
✅ **Bulk operations** - Select All / Deselect All
✅ **Navigation** - Go back and forward between steps
✅ **Live feedback** - Selection counter, status messages
✅ **Tooltips** - Help text for every button
✅ **Error handling** - Clear messages for all scenarios
✅ **Audit logging** - All actions logged

### Implementation Stats

- **Lines of code added**: ~240 lines
- **New methods**: 8 methods
- **Steps**: 2-step wizard process
- **Security layers**: Master password verification
- **User controls**: Select/Deselect, Back, Cancel
- **Breaking changes**: None (backward compatible with existing imports)

---

**The CSV import feature now gives you complete control and security!** 🎉

---

*Enhancement Implemented: 2025-10-26*
*Password Manager Version: 2.2.0+*
