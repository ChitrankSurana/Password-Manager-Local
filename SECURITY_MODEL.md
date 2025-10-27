# Password Manager - Security Model Explanation

## Understanding "Password Not Loaded"

### What It Means

When you see "Password not loaded" in the password manager, it means the actual password is **not decrypted in memory** at that moment. Here's why this is a security feature, not a bug:

### The Security Model

#### 1. **Passwords Are Always Encrypted in Database**

```
Database Storage:
┌─────────────────────────────────────┐
│ Entry: google.com                   │
│ Username: user@gmail.com (plain)    │
│ Password: [AES-256 encrypted blob]  │ ← Not human-readable
│ Created: 2025-10-26 (plain)         │
└─────────────────────────────────────┘
```

- Passwords are encrypted with **AES-256-CBC** encryption
- Each password is encrypted with your **master password**
- Even if someone steals the database file, they can't read the passwords without your master password

#### 2. **Lazy Loading for Security**

When you open the password list, the application does **NOT** decrypt all passwords immediately:

```
What Loads on Startup:
✅ Website names (google.com, facebook.com, etc.)
✅ Usernames (user@gmail.com)
✅ Timestamps (created, modified dates)
✅ Favorites status
❌ Actual passwords (NOT decrypted)
```

**Why?**
- **Screen Privacy**: If someone walks behind you, they won't see all your passwords
- **Memory Safety**: Fewer passwords in memory = less exposure if computer is compromised
- **Performance**: Decrypting hundreds of passwords on startup is slow
- **Zero Trust**: Only decrypt what you actually need, when you need it

#### 3. **On-Demand Decryption**

Passwords are only decrypted when you perform these actions:

| Action | When Decryption Happens | Master Password Required |
|--------|------------------------|--------------------------|
| **View Password** (👁) | Click view → Prompt for master password → Decrypt → Show for 30 seconds | ✅ Yes |
| **Copy Password** (📋) | Click copy → Prompt for master password → Decrypt → Copy → Discard | ✅ Yes |
| **Edit Password** (✏️) | Open edit dialog → Password field empty → Click "View Original" → Prompt → Show | ✅ Yes |
| **Export/Backup** | Export operation → Prompt once → Decrypt all → Export file | ✅ Yes |

### How It Works - Technical Flow

#### Example: Copying a Password

```
User Action: Click Copy Button (📋)

Step 1: Check if password is in memory
        ├─ NO → Continue (security: don't cache passwords)
        └─ (Passwords are never pre-loaded in list view)

Step 2: Prompt for master password
        ├─ Show MasterPasswordPrompt dialog
        ├─ User enters master password
        └─ Verify against database (bcrypt hash check)

Step 3: If verification succeeds:
        ├─ Retrieve encrypted password from database
        ├─ Use master password to derive decryption key (PBKDF2)
        ├─ Decrypt password blob (AES-256-CBC)
        └─ Get plaintext password

Step 4: Copy to clipboard
        ├─ Use pyperclip.copy(plaintext_password)
        └─ Show success message

Step 5: Security cleanup
        ├─ Plaintext password discarded from memory
        ├─ NOT stored in the entry object
        └─ Next copy requires master password again
```

### Security Benefits

#### 1. **Defense in Depth**

```
Layer 1: Login Authentication
         ↓
Layer 2: Session Management (auto-logout)
         ↓
Layer 3: Master Password Re-verification (for sensitive operations)
         ↓
Layer 4: Encrypted Storage
         ↓
Layer 5: No Plaintext Caching
```

Even if someone bypasses one layer, others protect your passwords.

#### 2. **Shoulder Surfing Protection**

**Without lazy loading:**
```
[Your Screen - BAD DESIGN]
───────────────────────────────────
Google      user@gmail.com    MyPassword123!
Facebook    user@fb.com       SecretPass456!
GitHub      developer         GithubKey789!
───────────────────────────────────
                              ↑
                         Anyone walking by can see ALL passwords!
```

**With lazy loading (our design):**
```
[Your Screen - SECURE DESIGN]
───────────────────────────────────
Google      user@gmail.com    ************
Facebook    user@fb.com       ************
GitHub      developer         ************
───────────────────────────────────
                              ↑
                         Passwords hidden until explicitly viewed
```

#### 3. **Memory Dump Protection**

If malware dumps your computer's memory:

**Without lazy loading:**
- Attacker gets: 100+ plaintext passwords (all loaded in RAM)

**With lazy loading:**
- Attacker gets: 0-1 plaintext passwords (only what's currently viewed)
- Viewed password auto-hides after 30 seconds
- Password cleared from memory after use

### User Experience Trade-offs

#### What You Give Up:
- ❌ Instant copying (need to enter master password first)
- ❌ Quick view (need to verify each time)

#### What You Gain:
- ✅ **Superior Security**: Passwords never exposed in bulk
- ✅ **Compliance**: Meets industry best practices
- ✅ **Peace of Mind**: Safe even if screen is visible to others
- ✅ **Malware Resistance**: Minimal plaintext exposure

### Comparison with Other Password Managers

| Password Manager | Lazy Loading | Re-verification | Auto-hide |
|-----------------|--------------|-----------------|-----------|
| **Our App** | ✅ Yes | ✅ Yes | ✅ Yes (30s) |
| **LastPass** | ✅ Yes | ⚠️ Optional | ⚠️ Optional |
| **1Password** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Bitwarden** | ⚠️ Partial | ⚠️ Optional | ❌ No |
| **KeePass** | ✅ Yes | ✅ Yes | ⚠️ Manual |

Our security model matches **enterprise-grade** password managers like 1Password.

### Configuration Options (Future Enhancement)

Currently the security model is strict. Possible future settings:

```python
# Potential configuration (not yet implemented)
SECURITY_SETTINGS = {
    "require_master_password_for_copy": True,  # Current: Always True
    "require_master_password_for_view": True,  # Current: Always True
    "auto_hide_timeout": 30,                   # Current: 30 seconds
    "cache_master_password": False,            # Current: Always False
    "cache_duration": 0,                       # Current: No caching
}
```

You could add a "Convenience Mode" that caches the master password for 5 minutes, but this would reduce security.

### FAQ

**Q: Why do I need to enter my master password so often?**
A: This is **by design** for maximum security. Each sensitive operation verifies you're the authorized user.

**Q: Can I disable master password re-verification?**
A: Not currently. This is a core security feature. Adding an option would require careful consideration of security implications.

**Q: What if I'm working alone and don't need this level of security?**
A: The current implementation prioritizes security over convenience. Consider it insurance - you might not need it 99% of the time, but that 1% matters.

**Q: Does entering my master password multiple times weaken security?**
A: No. Each verification is independent. Your master password is:
- Hashed with bcrypt (very slow, resistant to brute force)
- Never stored in plaintext
- Only compared against stored hash
- Not logged or cached

**Q: How is this different from the edit dialog?**
A: The edit dialog also uses lazy loading:
- Password field starts **empty**
- Click "View Original" button to see current password
- Enter master password to decrypt and view
- Auto-hides after 30 seconds

### Technical Implementation

#### Database Schema
```sql
CREATE TABLE passwords (
    entry_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    website TEXT NOT NULL,
    username TEXT NOT NULL,
    password_encrypted BLOB NOT NULL,  -- AES-256 encrypted
    created_at TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    is_favorite BOOLEAN DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

#### Encryption Process
```python
# When storing a password
1. User enters password: "MySecretPassword123"
2. Derive key from master password: PBKDF2(master_password, salt, 100000 iterations)
3. Encrypt: AES-256-CBC(plaintext="MySecretPassword123", key=derived_key)
4. Store encrypted blob in database

# When retrieving a password
1. Prompt for master password
2. Verify master password (bcrypt hash check)
3. Derive same encryption key: PBKDF2(master_password, salt, 100000 iterations)
4. Decrypt: AES-256-CBC-decrypt(encrypted_blob, key=derived_key)
5. Return plaintext password
6. Discard from memory after use
```

### Summary

**"Password Not Loaded" is not an error - it's a security feature.**

Your passwords are:
- ✅ Always encrypted in the database
- ✅ Never decrypted unless you explicitly request it
- ✅ Protected by master password re-verification
- ✅ Auto-hidden after temporary viewing
- ✅ Never cached in memory unnecessarily

This design follows the **Principle of Least Privilege**: only decrypt what you need, when you need it, for as long as you need it.

---

*If you find the master password prompts too frequent for your use case, please open an issue to discuss adding a "Convenience Mode" setting. We'd need to carefully balance security and usability.*
