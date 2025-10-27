# Delete Password Entry Feature - User Guide

## Overview

The Password Manager now includes a **Delete** feature that allows you to permanently remove password entries you no longer need. This feature includes:

✅ **Delete button** on each password entry
✅ **Confirmation dialog** before deletion
✅ **Security enforcement** - can only delete your own entries
✅ **Auto-refresh** after deletion
✅ **User feedback** with success/error messages

---

## How to Delete a Password Entry

### Step-by-Step Instructions

1. **Run the Application**
   ```bash
   python run_gui.py
   ```

2. **Login** to your account with username and master password

3. **Find the Entry** you want to delete in the password list

4. **Click the Delete Button** (🗑️ trash can icon)
   - Located on the right side of each password entry
   - Between the Edit (✏️) and Copy (📋) buttons

5. **Confirm Deletion**
   - A dialog will appear asking for confirmation
   - The dialog shows:
     - Website name
     - Username
     - Warning that action cannot be undone
     - Notice that you will be asked for master password
   - Click **Yes** to confirm deletion
   - Click **No** to cancel

6. **Verify Master Password** (NEW Security Step)
   - A master password prompt will appear
   - Enter your master password
   - Click **Verify** to proceed
   - Click **Cancel** to abort deletion
   - You have 3 attempts before the dialog closes

7. **Done!**
   - Success message appears: "Password entry for '[website]' deleted successfully"
   - The entry disappears from the list
   - Your password list refreshes automatically

---

## Visual Guide

### Before Deletion
```
┌────────────────────────────────────────────────────┐
│ google.com                    📋 🗑️ ✏️ ▶          │
│ Username: user@gmail.com                           │
└────────────────────────────────────────────────────┘
                                   ↑
                            Click this button
```

### Confirmation Dialog (Step 1)
```
┌──────────────────────────────────────┐
│  ⚠️  Delete Password Entry           │
├──────────────────────────────────────┤
│                                      │
│  Are you sure you want to           │
│  permanently delete this password    │
│  entry?                              │
│                                      │
│  Website: google.com                 │
│  Username: user@gmail.com            │
│                                      │
│  This action cannot be undone!       │
│                                      │
│  You will be asked to verify your    │
│  master password.                    │
│                                      │
│         [ No ]      [ Yes ]          │
└──────────────────────────────────────┘
```

### Master Password Verification (Step 2 - NEW!)
```
┌──────────────────────────────────────┐
│  🔒 Verify Master Password           │
├──────────────────────────────────────┤
│                                      │
│  Please enter your master password   │
│  to confirm deletion                 │
│                                      │
│  Username: your_username             │
│                                      │
│  Master Password:                    │
│  [******************]  👁            │
│                                      │
│  Attempts remaining: 3               │
│                                      │
│       [ Cancel ]   [ Verify ]        │
└──────────────────────────────────────┘
```

### After Deletion
```
┌────────────────────────────────────────────────────┐
│ ✅ Password entry for 'google.com' deleted         │
│    successfully                                    │
└────────────────────────────────────────────────────┘

Entry is permanently removed from the list
```

---

## Button Layout

Each password entry has these action buttons (right to left):

| Button | Icon | Function | Tooltip |
|--------|------|----------|---------|
| **Expand** | ▶/▼ | Show/hide details | "Expand or collapse to show/hide details" |
| **Edit** | ✏️ | Edit password | "Edit this password entry" |
| **Delete** | 🗑️ | Delete password | "Delete this password entry permanently" |
| **Copy** | 📋 | Copy password | "Copy password to clipboard (requires master password)" |

---

## Important Notes

### ⚠️ **Permanent Deletion**
- Deleted entries **cannot be recovered**
- There is **no undo** function
- Make sure you have the password saved elsewhere if you still need it
- Consider using **Export/Backup** before deleting important entries

### 🔒 **Security**
- You can **only delete your own** password entries
- Attempting to delete another user's entry will fail
- The database enforces this at the backend level
- Multi-user security is automatically enforced

### 📝 **What Gets Deleted**
When you delete an entry, the following is permanently removed:
- Website/service name
- Username
- Encrypted password
- Remarks/notes
- Creation date
- Last modified date
- Favorite status

---

## Technical Details

### Backend Implementation

The delete functionality uses the existing backend method:

```python
# Backend method (already existed)
password_manager.delete_password_entry(
    session_id=session_id,
    entry_id=entry_id
)
```

**Security Checks:**
1. ✅ Validates session is active
2. ✅ Verifies user owns the entry
3. ✅ Prevents cross-user deletion
4. ✅ Returns success/failure status

### Database Operation

```sql
-- What happens in the database
DELETE FROM passwords
WHERE entry_id = ?
  AND user_id = ?;
```

**Foreign Key Protection:**
- Database ensures user_id matches
- Prevents accidental deletion of other users' data
- Maintains referential integrity

---

## Error Handling

### Possible Errors and Solutions

| Error Message | Cause | Solution |
|---------------|-------|----------|
| "Failed to delete password entry" | Entry doesn't exist or already deleted | Refresh the password list |
| "User does not own this password entry" | Trying to delete another user's entry | Can only delete your own entries |
| "Cannot verify master password" | Session expired | Re-login to the application |
| "Error deleting entry: [details]" | Database/system error | Check logs, contact support |

---

## Testing

All delete functionality has been thoroughly tested:

✅ **Test 1: Basic Deletion**
- Create entries → Delete entries → Verify removal
- Delete non-existent entry (handled gracefully)
- Delete all entries (list becomes empty)

✅ **Test 2: Multi-User Security**
- Alice can delete her entries
- Bob can delete his entries
- Bob **cannot** delete Alice's entries (security enforced)
- Cross-user deletion attempts are blocked

Run tests:
```bash
python test_delete_functionality.py
```

---

## Comparison with Other Actions

| Action | Master Password Required | Confirmation Required | Permanent |
|--------|-------------------------|----------------------|-----------|
| **View Password** | ✅ Yes | ❌ No | ❌ No (auto-hides) |
| **Copy Password** | ✅ Yes | ❌ No | ❌ No |
| **Edit Password** | ⚠️ Only to view original | ❌ No | ❌ No (can undo) |
| **Delete Password** | ✅ Yes (NEW!) | ✅ Yes | ✅ Yes (cannot undo) |

---

## Best Practices

### Before Deleting

1. **Double-check** you're deleting the correct entry
2. **Copy the password** if you might need it later
3. **Export/backup** your database regularly
4. **Verify** you've updated the password elsewhere (if changed)

### When to Delete

- ✅ Account has been permanently closed
- ✅ Service is no longer used
- ✅ Password was created for testing purposes
- ✅ Entry is a duplicate
- ❌ Just want to change the password (use **Edit** instead)
- ❌ Temporarily don't need it (keep it, it's secure)

### After Deleting

- 💾 **Backup** your database regularly
- 🗑️ **Clean up** your clipboard if you copied the password
- 📝 **Update** password in other locations if needed

---

## Troubleshooting

### Delete Button Not Visible
- **Cause**: UI not loaded properly
- **Solution**: Restart the application

### Cannot Delete Entry
- **Cause**: Not logged in or session expired
- **Solution**: Re-login to the application

### Entry Reappears After Deletion
- **Cause**: Database write failed or network issue
- **Solution**: Check database permissions, restart app

### Confirmation Dialog Doesn't Appear
- **Cause**: Dialog hidden or UI issue
- **Solution**: Check if another dialog is open, restart app

---

## Future Enhancements

Potential improvements for the delete feature:

1. **Trash/Recycle Bin** - Temporary storage for deleted entries (30-day recovery)
2. **Bulk Delete** - Delete multiple entries at once
3. **Delete History** - Log of deleted entries (for auditing)
4. **Export Before Delete** - Auto-export deleted entry to CSV
5. **Soft Delete** - Mark as deleted but keep in database (hidden)

---

## FAQ

**Q: Can I recover a deleted password?**
A: No, deletion is permanent. Always keep backups!

**Q: Do I need to enter my master password to delete?**
A: **Yes!** As of the latest version, master password verification is **required** for deletion. This adds an extra security layer to prevent accidental or unauthorized deletions.

**Q: Can I delete multiple entries at once?**
A: Not currently. You must delete one at a time.

**Q: What happens if I accidentally delete an entry?**
A: Unfortunately, there's no undo. Restore from backup if available.

**Q: Will deleting an entry delete my account on the actual website?**
A: No! This only removes the entry from your password manager. Your actual account on the website remains active.

**Q: Can I delete all my passwords at once?**
A: Delete each entry individually. If you want to start fresh, consider creating a new user account.

**Q: Is deletion logged?**
A: Yes, deletion is logged in the application logs for security auditing.

---

## Related Features

- **Edit Password** - Modify existing entries without deleting
- **Export/Backup** - Save your passwords before deleting
- **Search/Filter** - Find specific entries to delete
- **Favorites** - Mark important entries (to avoid accidental deletion)

---

## Summary

The delete feature provides a safe and secure way to remove unwanted password entries:

✅ **Easy to use** - One click + confirmation
✅ **Safe** - Requires explicit confirmation
✅ **Secure** - Multi-user isolation enforced
✅ **Fast** - Auto-refresh after deletion
✅ **Clear feedback** - Success/error messages

**Remember: Deletion is permanent. Always backup important data!**

---

*Last updated: 2025-10-26*
*Password Manager Version: 2.2.0+*
