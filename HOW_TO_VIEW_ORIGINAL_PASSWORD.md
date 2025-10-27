# How to View Original Password in Edit Dialog

## Overview

When you edit a password entry, the password field is **intentionally blank** for security. This prevents someone looking over your shoulder from seeing your password.

To view the original password, use the **"View Original" button** (🔍).

---

## Step-by-Step Guide

### 1. Open Edit Dialog

Click the Edit button (✏️) on any password entry.

### 2. Locate the Password Field

The Edit dialog shows:
```
┌─────────────────────────────────────────────────┐
│ Edit Password - google.com                      │
├─────────────────────────────────────────────────┤
│                                                  │
│ Website: [google.com                    ]       │
│                                                  │
│ Username: [user@gmail.com               ]       │
│                                                  │
│ Password: [                             ] 👁 🎲 🔍│
│           └─ EMPTY (for security)        │  │  │ │
│                                          │  │  └─ View Original ← Click here!
│                                          │  └──── Generate
│                                          └─────── Show/Hide
│                                                  │
│ [Password strength indicator]                   │
│                                                  │
│ Remarks: [Optional notes                ]       │
│                                                  │
│ ☐ Mark as favorite                              │
│                                                  │
│          [Cancel]           [Update Password]   │
└─────────────────────────────────────────────────┘
```

### 3. Click the "View Original" Button (🔍)

The **magnifying glass icon** (🔍) is on the right side of the password field.

**Tooltip**: "View the current saved password (requires master password)"

### 4. Enter Your Master Password

A dialog will appear:
```
┌──────────────────────────────────────┐
│ 🔒 Verify Master Password            │
├──────────────────────────────────────┤
│                                      │
│ Please enter your master password   │
│                                      │
│ Username: your_username              │
│                                      │
│ Master Password:                     │
│ [******************]  👁             │
│                                      │
│ Attempts remaining: 3                │
│                                      │
│    [ Cancel ]      [ Verify ]        │
└──────────────────────────────────────┘
```

Enter your master password and click **Verify**.

### 5. View the Original Password

After verification:
- ✅ **Password appears** in the password field
- ✅ **Timer starts**: "Password visible for 30 seconds"
- ✅ **Button changes** to 🔒 (lock icon)
- ✅ **Countdown** displayed below the field (green → yellow → orange → red)

```
┌─────────────────────────────────────────────────┐
│ Password: [MyOriginalPassword123!   ] 👁 🎲 🔒│
│           └─ NOW VISIBLE!                      │ │
│                                                  │
│ Password visible for 28 seconds (green)         │
│                                                  │
└─────────────────────────────────────────────────┘
```

### 6. Auto-Hide or Manual Hide

**Option 1: Wait 30 seconds**
- Password automatically hides
- Field clears
- Button changes back to 🔍

**Option 2: Click Hide button (🔒)**
- Password hides immediately
- Field clears
- Button changes back to 🔍

---

## Visual Layout

### Button Locations (Right to Left)

```
Password Field Layout:
┌───────────────────────────────────────────────────┐
│ [Password entry field - expands to fill space]   │
│                                      👁  🎲  🔍  │
│                                      │   │   │   │
│                                      │   │   └── View Original (🔍)
│                                      │   └────── Generate (🎲)
│                                      └────────── Show/Hide (👁)
└───────────────────────────────────────────────────┘
```

### Button Order

| Position | Button | Icon | Function |
|----------|--------|------|----------|
| **Rightmost** | View Original | 🔍 | View saved password (requires master password) |
| **Middle** | Generate | 🎲 | Generate random password |
| **Left** | Show/Hide | 👁 | Show/hide typed password |

---

## Why Is the Field Empty?

### Security by Design

**Problem**: If the password field showed the original password immediately:
- ❌ Anyone walking behind you could see it
- ❌ Shoulder surfing vulnerability
- ❌ No verification required

**Solution**: Password field starts empty:
- ✅ Password hidden from shoulder surfers
- ✅ Master password required to view
- ✅ Timed viewing (auto-hide after 30 seconds)
- ✅ You control when it's visible

### Use Cases

**Scenario 1: Change Password**
```
1. Open Edit dialog
2. Password field is empty
3. Type new password directly
4. Click "Update Password"
5. ✅ Password updated (no need to view original)
```

**Scenario 2: View Original Password**
```
1. Open Edit dialog
2. Click View Original button (🔍)
3. Enter master password
4. ✅ See original password
5. Optional: Copy it or modify it
6. Click "Update Password" or "Cancel"
```

**Scenario 3: Update Username Only**
```
1. Open Edit dialog
2. Change username
3. Click "Update Password"
4. ✅ Username updated (password unchanged)
5. No need to view password!
```

---

## Common Questions

**Q: The password field is blank - is something broken?**
A: No! This is intentional for security. Click the 🔍 button to view the original password.

**Q: Where is the View Original button?**
A: Look on the **right side** of the password field. It's the **magnifying glass icon** (🔍).

**Q: I clicked the eye icon (👁) but nothing happened?**
A: That's the **Show/Hide** button for passwords you *type*. To view the *original saved* password, click the **magnifying glass** (🔍).

**Q: Do I need to view the original password to update the entry?**
A: **No!** You only need to view it if you want to see what it was. You can:
- Update website/username without viewing password
- Type a new password without viewing the old one
- View original only when you need to copy it or reference it

**Q: Why do I need to enter my master password again?**
A: Extra security! This prevents unauthorized access if someone gets to your unlocked computer.

**Q: How long can I view the password?**
A: 30 seconds by default. The timer shows countdown with color changes. You can hide it manually anytime by clicking the 🔒 button.

**Q: What if I forget to hide it?**
A: No worries! It auto-hides after 30 seconds.

**Q: Can I extend the viewing time?**
A: Yes! Click the 🔍 button again while the password is visible. The timer resets to 30 seconds.

---

## Troubleshooting

### Button Not Visible

**Check these:**
1. ✅ Make sure you're in the Edit dialog (not Add New)
2. ✅ Look on the **right side** of the password field
3. ✅ It's the **rightmost** button (after 👁 and 🎲)
4. ✅ Icon is 🔍 (magnifying glass)

### Master Password Prompt Doesn't Appear

**Possible issues:**
1. Dialog might be hidden behind other windows
2. Check if another dialog is already open
3. Try closing and reopening the Edit dialog

### Password Still Blank After Verification

**Check:**
1. Did you enter the **correct** master password?
2. Did you click **Verify** (not Cancel)?
3. Check if there's an error message at the bottom

### Timer Not Showing

**This is normal if:**
- You haven't clicked View Original yet
- Password is not currently visible
- You clicked Cancel on the master password prompt

---

## Comparison: Add vs Edit

| Dialog | Password Field | View Original Button |
|--------|---------------|---------------------|
| **Add New Password** | Empty (you type new password) | ❌ No button (no original password exists) |
| **Edit Password** | Empty (for security) | ✅ Yes (🔍 button to view original) |

---

## Quick Reference

### To View Original Password:
```
1. Click Edit (✏️) on password entry
2. Click View Original (🔍) on right side
3. Enter master password
4. Click Verify
5. Password appears with timer
```

### To Update Password Without Viewing:
```
1. Click Edit (✏️) on password entry
2. Type new password directly in field
3. Click "Update Password"
4. Done! (never needed to view original)
```

### To Cancel Password Viewing:
```
While master password prompt is open:
- Click "Cancel" button
- Or press Escape key
```

### To Hide Password Manually:
```
While password is visible:
- Click lock button (🔒)
- Password hides immediately
```

---

## Security Features

✅ **Master password required** - Prevents unauthorized viewing
✅ **Timed viewing** - Auto-hide after 30 seconds
✅ **Visual countdown** - Color-coded timer (green → red)
✅ **Manual hide** - Lock button for immediate hide
✅ **Attempt limiting** - Maximum 3 attempts before lockout
✅ **Audit logging** - All view attempts logged

---

## Summary

**The password field is blank for security!**

To view the original password:
1. Click the **🔍 button** (magnifying glass, rightmost)
2. Enter your **master password**
3. Click **Verify**
4. See password with **30-second countdown**
5. Auto-hides or click **🔒 to hide** manually

**You don't need to view the original if you're just changing it!**

---

*User Guide Created: 2025-10-26*
*Password Manager Version: 2.2.0+*
