# How to Build a Browser Extension for Your Password Manager

## Overview

A browser extension allows users to auto-fill passwords directly on websites without copying/pasting from your desktop app.

---

## 🎯 What You'll Build

```
┌─────────────────────────────────────┐
│   Website (gmail.com)               │
│   [Email: ____________]             │
│   [Password: ________]              │  ← Extension auto-fills these
│   [  Login  ]                       │
└─────────────────────────────────────┘
         ↑
         │ (Clicks extension icon)
         │
┌─────────────────┐
│ Extension Popup │
│ ┌─────────────┐ │
│ │ Gmail       │ │ ← Shows matching passwords
│ │ work@gm...  │ │
│ │ [Fill]      │ │
│ └─────────────┘ │
└─────────────────┘
         ↓
┌─────────────────────────────┐
│  Your Desktop App (running) │
│  - Database                 │
│  - Encryption               │
│  - Authentication           │
└─────────────────────────────┘
```

---

## 🏗️ Architecture

### Option 1: Extension + Desktop App via Native Messaging (Recommended)

**How it works:**
1. Extension runs in browser
2. Communicates with desktop app via "Native Messaging"
3. Desktop app accesses encrypted database
4. Returns password to extension (after master password check)
5. Extension fills password fields

**Pros:** Most secure, desktop app controls everything
**Cons:** Desktop app must be running

### Option 2: Extension + Local API

**How it works:**
1. Your Flask web interface runs on http://localhost:5000
2. Extension makes HTTP requests to localhost
3. API returns passwords (with authentication)
4. Extension fills fields

**Pros:** Simpler, you already have Flask API!
**Cons:** Web interface must be running

---

## 📁 Extension File Structure

```
password-manager-extension/
├── manifest.json          # Extension configuration
├── background.js          # Background service worker
├── content.js             # Runs on web pages
├── popup/
│   ├── popup.html         # Extension popup UI
│   ├── popup.js           # Popup logic
│   └── popup.css          # Popup styles
├── icons/
│   ├── icon16.png         # 16x16 icon
│   ├── icon48.png         # 48x48 icon
│   └── icon128.png        # 128x128 icon
└── lib/
    └── api-client.js      # Communicate with desktop app
```

---

## 🚀 Step-by-Step Development

### Step 1: Create manifest.json

This tells Chrome about your extension:

```json
{
  "manifest_version": 3,
  "name": "Personal Password Manager",
  "version": "1.0.0",
  "description": "Auto-fill passwords from your local password manager",
  "permissions": [
    "activeTab",
    "storage",
    "tabs"
  ],
  "host_permissions": [
    "http://localhost:5000/*"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content.js"],
      "run_at": "document_idle"
    }
  ],
  "action": {
    "default_popup": "popup/popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  }
}
```

### Step 2: Create content.js (Runs on every webpage)

This detects password fields:

```javascript
// content.js - Detect password fields on page

function findPasswordFields() {
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    const usernameInputs = document.querySelectorAll(
        'input[type="email"], input[type="text"][name*="user"], input[type="text"][name*="email"]'
    );

    return {
        username: usernameInputs[0] || null,
        password: passwordInputs[0] || null,
        domain: window.location.hostname
    };
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'fillPassword') {
        const fields = findPasswordFields();

        if (fields.username) {
            fields.username.value = request.username;
        }
        if (fields.password) {
            fields.password.value = request.password;
        }

        sendResponse({ success: true });
    }
    return true;
});

// Detect when user types in password field
const fields = findPasswordFields();
if (fields.password) {
    // Show extension icon badge
    chrome.runtime.sendMessage({
        action: 'passwordFieldDetected',
        domain: fields.domain
    });
}
```

### Step 3: Create popup.html (Extension UI)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Password Manager</title>
    <style>
        body {
            width: 300px;
            padding: 10px;
            font-family: Arial, sans-serif;
        }
        .password-item {
            padding: 10px;
            border: 1px solid #ddd;
            margin-bottom: 5px;
            cursor: pointer;
        }
        .password-item:hover {
            background-color: #f0f0f0;
        }
        .status {
            padding: 10px;
            text-align: center;
        }
        .loading {
            color: #666;
        }
        .error {
            color: #d00;
        }
    </style>
</head>
<body>
    <div id="status" class="status loading">
        Loading passwords...
    </div>
    <div id="passwords-list"></div>
    <script src="popup.js"></script>
</body>
</html>
```

### Step 4: Create popup.js (Popup Logic)

```javascript
// popup.js - Extension popup logic

async function getPasswordsForCurrentSite() {
    // Get current tab's domain
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const url = new URL(tab.url);
    const domain = url.hostname;

    // Call your local API
    try {
        const response = await fetch(`http://localhost:5000/api/passwords?domain=${domain}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                // Add authentication token if needed
                'Authorization': 'Bearer ' + getStoredToken()
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch passwords');
        }

        const passwords = await response.json();
        return passwords;
    } catch (error) {
        console.error('Error fetching passwords:', error);
        return [];
    }
}

function getStoredToken() {
    // Get authentication token from storage
    return localStorage.getItem('auth_token') || '';
}

async function fillPassword(username, password) {
    // Send message to content script to fill fields
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    chrome.tabs.sendMessage(tab.id, {
        action: 'fillPassword',
        username: username,
        password: password
    }, (response) => {
        if (response && response.success) {
            window.close(); // Close popup after filling
        }
    });
}

function displayPasswords(passwords) {
    const container = document.getElementById('passwords-list');
    const statusDiv = document.getElementById('status');

    if (passwords.length === 0) {
        statusDiv.textContent = 'No passwords found for this site';
        statusDiv.className = 'status';
        return;
    }

    statusDiv.style.display = 'none';

    passwords.forEach(pwd => {
        const item = document.createElement('div');
        item.className = 'password-item';
        item.textContent = `${pwd.username} (${pwd.entry_name || 'Default'})`;

        item.addEventListener('click', () => {
            fillPassword(pwd.username, pwd.password);
        });

        container.appendChild(item);
    });
}

// Main execution
(async () => {
    try {
        const passwords = await getPasswordsForCurrentSite();
        displayPasswords(passwords);
    } catch (error) {
        const statusDiv = document.getElementById('status');
        statusDiv.textContent = 'Error: Desktop app not running?';
        statusDiv.className = 'status error';
    }
})();
```

### Step 5: Update Flask API (In your desktop app)

Add API endpoint for browser extension:

```python
# In src/web/app.py - Add this endpoint

@app.route('/api/passwords', methods=['GET'])
@requires_authentication
def get_passwords_for_domain():
    """Get passwords for specific domain (for browser extension)"""
    domain = request.args.get('domain', '')

    if not domain:
        return jsonify({'error': 'Domain required'}), 400

    user_id = session.get('user_id')

    try:
        # Get passwords matching domain
        passwords = password_manager.search_passwords(
            user_id=user_id,
            criteria=SearchCriteria(website=domain)
        )

        # Return as JSON (passwords already decrypted by password_manager)
        return jsonify({
            'passwords': [
                {
                    'entry_id': p.entry_id,
                    'username': p.username,
                    'password': p.password,  # Decrypted
                    'entry_name': p.entry_name,
                    'website': p.website
                }
                for p in passwords
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## 🧪 Testing Your Extension

### Load Unpacked Extension in Chrome:

1. Open Chrome
2. Go to `chrome://extensions/`
3. Enable "Developer mode" (top right)
4. Click "Load unpacked"
5. Select your extension folder
6. ✅ Extension loaded!

### Test It:

1. Start your Flask web interface (`python src/web/app.py`)
2. Log in at `http://localhost:5000`
3. Go to any website (e.g., gmail.com)
4. Click your extension icon
5. See if passwords appear
6. Click a password to auto-fill

---

## 🔒 Security Considerations

### 1. **Localhost Only**
- Extension only talks to localhost (your computer)
- No passwords sent over internet

### 2. **Authentication**
- Require authentication token
- Token expires after timeout

### 3. **HTTPS Only (Production)**
- When website uses HTTPS, only send passwords over HTTPS
- Prevent man-in-the-middle attacks

### 4. **Content Security Policy**
- Restrict what extension can do
- Prevent XSS attacks

### 5. **Minimal Permissions**
- Only request needed permissions
- Users trust extensions with fewer permissions

---

## 📦 Publishing to Chrome Web Store

### 1. Create Developer Account
- Go to: https://chrome.google.com/webstore/devconsole
- Pay $5 one-time fee
- Register as developer

### 2. Prepare Extension
- Create nice icons (16x16, 48x48, 128x128)
- Write good description
- Take screenshots
- Create promotional images

### 3. Upload
- Zip your extension folder
- Upload to Chrome Web Store
- Fill in metadata
- Submit for review

### 4. Review Process
- Usually takes 1-3 days
- Google reviews for policy violations
- Fix any issues and resubmit

### 5. Published!
- Users can install from Chrome Web Store
- Automatic updates when you release new versions

---

## 🎨 Making It Look Professional

### Add CSS Styling:
```css
/* popup.css */
:root {
    --primary-color: #4CAF50;
    --danger-color: #f44336;
}

body {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: #f5f5f5;
}

.header {
    background-color: var(--primary-color);
    color: white;
    padding: 15px;
    text-align: center;
}

.password-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    background-color: white;
    border-bottom: 1px solid #e0e0e0;
    cursor: pointer;
    transition: background-color 0.2s;
}

.password-item:hover {
    background-color: #f0f0f0;
}

.fill-button {
    background-color: var(--primary-color);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
}

.fill-button:hover {
    opacity: 0.9;
}
```

---

## ⏱️ Development Timeline

**Week 1-2:** Basic structure, detect password fields
**Week 3:** Connect to desktop app API
**Week 4:** Auto-fill functionality
**Week 5:** Polish UI, add features
**Week 6:** Testing, bug fixes
**Week 7:** Prepare for Chrome Web Store
**Week 8:** Submit and launch

**Total: 2 months** part-time

---

## 📚 Resources

- **Chrome Extension Docs:** https://developer.chrome.com/docs/extensions/
- **Tutorial:** "Build a Chrome Extension" (YouTube)
- **Examples:** https://github.com/GoogleChrome/chrome-extensions-samples
- **Testing:** chrome://extensions/ in Developer Mode

---

## 🎯 Quick Start

```bash
# Create extension structure
mkdir password-manager-extension
cd password-manager-extension

# Create files
touch manifest.json background.js content.js
mkdir popup && touch popup/popup.html popup/popup.js popup/popup.css
mkdir icons

# Add code from examples above

# Load in Chrome
# 1. Go to chrome://extensions/
# 2. Enable Developer Mode
# 3. Click "Load unpacked"
# 4. Select extension folder
```

---

## ✅ Checklist

- [ ] manifest.json created
- [ ] content.js detects password fields
- [ ] popup.html shows UI
- [ ] popup.js fetches passwords
- [ ] Desktop API endpoint added
- [ ] Auto-fill works
- [ ] Extension loads in Chrome
- [ ] Tested on real websites
- [ ] Icons created
- [ ] Ready for publishing

---

**Start small, test often, iterate quickly!** 🚀

Your browser extension will make your password manager **10x more convenient** for users!
