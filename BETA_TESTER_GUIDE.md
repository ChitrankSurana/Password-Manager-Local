# Beta Tester Guide - Personal Password Manager v2.2.0

**Welcome, Beta Tester!** Thank you for helping test this password manager! 🎉

---

## 📦 What You'll Receive

A ZIP file containing:
```
Password_Manager_v2.2.0/
├── Personal_Password_Manager.exe  (The application)
├── README.txt                     (This file)
└── data/                          (Empty - app will use this)
```

---

## 🚀 Installation (2 Minutes)

### Step 1: Extract the ZIP
- Right-click the ZIP file
- Select "Extract All..."
- Choose a location (e.g., `C:\Users\YourName\Password Manager\`)
- Click "Extract"

### Step 2: Run the Application
- Open the extracted folder
- **Double-click** `Personal_Password_Manager.exe`

### Step 3: Handle Windows Warning (First Time Only)

**You WILL see this warning - it's normal:**
```
Windows protected your PC
Microsoft Defender SmartScreen prevented an unrecognized app from starting
```

**This is safe! Here's why:**
- The app isn't "signed" with an expensive certificate
- Windows shows this for ANY unsigned software
- This is my password manager - it's safe!

**To proceed:**
1. Click "More info"
2. Click "Run anyway"
3. ✅ Done! This warning won't appear again

---

## 👤 Creating Your Account (2 Minutes)

### First Launch:

1. **The login window appears**

2. **Click "Create New Account"** (NOT "Sign In"!)
   - Don't click "Sign In" yet - you don't have an account!

3. **Enter your information:**
   - **Username:** Choose any username (e.g., "john", "mary123")
   - **Master Password:** Create a STRONG password
     - At least 8 characters
     - Mix of letters, numbers, symbols
     - Something you'll remember!
   - **Confirm Password:** Type it again

4. **Click "Create Account"**

5. **Remember your master password!**
   - ⚠️ There's NO password recovery
   - If you forget it, your passwords are gone
   - This is by design - for YOUR security

### Logging In (Next Time):

1. Open the app
2. Enter your username
3. Enter your master password
4. Click "Sign In"

---

## ✨ Using the Password Manager

### Adding Your First Password:

1. Click **"Add Password"** button
2. Fill in the form:
   - **Website:** e.g., "gmail.com", "facebook.com"
   - **Username:** Your email or username
   - **Password:** Your password (or click "Generate")
   - **Entry Name:** (Optional) e.g., "Work Email", "Personal Account"
   - **Remarks:** (Optional) e.g., "Security question: pet name"
3. Click **"Save"**

### Viewing a Password:

1. Find the password in the list
2. Click **"View"** button
3. **Enter your master password** (security!)
4. See your password
5. Click **"Copy"** to copy to clipboard
   - ⏰ Auto-clears from clipboard in 30 seconds

### Generating Strong Passwords:

1. When adding/editing a password, click **"Generate"**
2. Choose options:
   - **Length:** 8-64 characters
   - **Include:** Uppercase, lowercase, numbers, symbols
   - **Method:** Random, Memorable, Pattern, Pronounceable
3. Click **"Generate"**
4. Click **"Use This Password"**

### Searching Passwords:

1. Use the search box at the top
2. Type website name or username
3. Results filter in real-time

### Editing a Password:

1. Select the password in the list
2. Click **"Edit"**
3. Make changes
4. Click **"Save"**

### Deleting a Password:

1. Select the password in the list
2. Click **"Delete"**
3. **Enter your master password** (security!)
4. Confirm deletion

---

## 🛡️ Security Features

### Session Timeout:
- Your session expires after **8 hours** of inactivity
- You'll need to log in again
- This prevents unauthorized access if you leave your computer

### Account Lockout:
- After **5 failed login attempts**, your account locks for **30 minutes**
- This prevents brute force attacks
- Wait 30 minutes or restart the app

### Encrypted Storage:
- All passwords encrypted with **military-grade AES-256**
- Master password never stored anywhere
- Data stored locally in the `data` folder

---

## 💾 Backing Up Your Passwords

**IMPORTANT:** Backup regularly to prevent data loss!

### Method 1: Built-in Backup

1. Go to **Settings** → **Backup Manager**
2. Click **"Create Backup"**
3. Choose location (USB drive, cloud folder, etc.)
4. Save with date in filename: `backup_2025-01-15.db`

### Method 2: Manual Backup

1. Close the Password Manager
2. Copy the entire `data` folder
3. Paste to safe location (USB, cloud, etc.)
4. Label with date: `data_backup_2025-01-15`

### Restoring from Backup:

1. Open **Settings** → **Backup Manager**
2. Click **"Restore from Backup"**
3. Select your backup file
4. Restart the application

---

## ❓ Common Issues & Solutions

### "Invalid username or password" on first run

**Problem:** You clicked "Sign In" instead of "Create New Account"

**Solution:**
1. Click **"Create New Account"** button
2. Set up your account first
3. Then you can sign in

---

### App won't start / Immediately closes

**Causes:**
1. Antivirus blocking it
2. Missing Visual C++ Redistributable
3. Corrupted download

**Solutions:**
1. **Check Antivirus:**
   - Open Windows Security
   - Check "Protection history"
   - If quarantined, restore it and add exception

2. **Install Visual C++ Redistributable:**
   - Download from: microsoft.com/en-us/download/details.aspx?id=48145
   - Install and restart computer

3. **Re-download:**
   - Delete the current ZIP
   - Download fresh copy
   - Extract and try again

---

### "Windows protected your PC" won't go away

**Problem:** You didn't click "More info"

**Solution:**
1. Don't click "Don't run"
2. Click "More info" link (small text)
3. Then "Run anyway" button appears
4. Click "Run anyway"

---

### Forgot Master Password

**Bad News:** There's no recovery option

**Why:** Your security! If I could recover it, so could hackers.

**Options:**
1. If you have a backup with the old password, restore it
2. Create a new account (old data will be lost)
3. Try to remember - write it down safely next time

---

### App is Slow

**First Launch:** Takes 10-20 seconds (Windows scanning)
**Subsequent Launches:** Should be 2-3 seconds

**If Always Slow:**
1. Close other programs
2. Check antivirus isn't constantly scanning
3. Move to SSD (if on slow hard drive)

---

## 🐛 Beta Testing - What to Report

### I Need Your Feedback On:

#### 1. **Installation Experience**
- Was it easy to download and extract?
- Did Windows warning confuse you?
- Any problems running the app?

#### 2. **First-Time Setup**
- Was "Create New Account" clear?
- Did you accidentally click "Sign In" first?
- Was the process intuitive?

#### 3. **Daily Usage**
- Is adding passwords easy?
- Is finding passwords quick?
- Is the password generator useful?
- Are any features confusing?

#### 4. **Performance**
- How fast does it start?
- Is searching fast?
- Any lag or freezing?

#### 5. **Bugs/Issues**
- Does anything crash?
- Any error messages?
- Features not working?

#### 6. **Feature Requests**
- What's missing?
- What would make it better?
- What features do you want?

---

## 📝 Bug Report Template

When reporting issues, please include:

```
**What happened:**
(Describe what went wrong)

**What you expected:**
(What should have happened?)

**Steps to reproduce:**
1. First I did...
2. Then I clicked...
3. Then this happened...

**Error message:**
(Copy any error messages you saw)

**Your setup:**
- Windows version: (e.g., Windows 11)
- When it happened: (e.g., "When adding password")
- How often: (e.g., "Every time" or "Just once")
```

**Send to:** [Your Email]

---

## 🌟 Feature Request Template

```
**Feature:** (Brief title)

**Description:**
(What feature do you want?)

**Why it's useful:**
(How would this help you?)

**Example:**
(Give an example of using it)
```

**Send to:** [Your Email]

---

## ✅ Beta Testing Checklist

Help me by testing these scenarios:

### Basic Features:
- [ ] Create account
- [ ] Log in
- [ ] Add a password
- [ ] View a password
- [ ] Edit a password
- [ ] Delete a password
- [ ] Search for a password
- [ ] Generate a strong password
- [ ] Copy password to clipboard

### Advanced Features:
- [ ] Create a backup
- [ ] Restore from backup
- [ ] Import passwords (if you have a CSV)
- [ ] Export passwords
- [ ] Change theme (dark/light)
- [ ] Adjust settings

### Stress Tests:
- [ ] Add 50+ passwords
- [ ] Search with many passwords
- [ ] Create multiple accounts
- [ ] Leave app open for hours
- [ ] Close and reopen multiple times

### Edge Cases:
- [ ] Try wrong password 3 times
- [ ] Use special characters in passwords
- [ ] Use very long passwords (50+ characters)
- [ ] Add password with no website
- [ ] Search for non-existent password

---

## 📊 Optional: Usage Metrics

If you're comfortable, please share:
- **How many passwords did you store?**
- **How often did you use it?** (Daily, weekly)
- **What did you use it for?** (Personal, work, both)
- **Would you recommend it?** (Yes/No, why?)

---

## 🎁 Thank You!

Your feedback is invaluable! You're helping make this password manager:
- More secure
- Easier to use
- More reliable
- Better for everyone

### What Happens Next?

1. **Week 1-2:** I gather all feedback
2. **Week 2-3:** I fix bugs and improve UX
3. **Week 3-4:** You get updated version
4. **Week 4+:** Ready for wider release!

---

## 📞 Contact & Support

**Questions?** [Your Email]
**Bug reports?** [Your Email]
**Feature ideas?** [Your Email]

**Response time:** Within 24-48 hours

---

## 🔒 Privacy Promise

- ✅ Your passwords stay on YOUR computer
- ✅ No internet connection required
- ✅ No data sent to me or anyone
- ✅ No telemetry or tracking
- ✅ 100% private, 100% local

---

## ⚖️ License & Terms

**Beta Version - For Testing Only**
- Use at your own risk (it's beta!)
- Report bugs and issues
- Don't use for critical passwords yet
- Free forever - no charges ever

---

**Happy Testing!** 🔐✨

Thanks for being an early adopter and helping improve this password manager!

---

**Version:** 2.2.0 Beta
**Release Date:** January 2025
**Tested On:** Windows 10/11 (64-bit)
