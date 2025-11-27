# How to Build a Mobile App for Your Password Manager

## Overview

A mobile app lets users access passwords on their phones/tablets with the same security as your desktop app.

---

## 🎯 What You'll Build

```
┌─────────────────────────┐
│  📱 Mobile App          │
│                         │
│  🔐 Login               │
│  Master Password: ***   │
│  [   Unlock   ]         │
│                         │
│  ────────────────       │
│                         │
│  📋 Passwords           │
│  ┌─────────────────┐   │
│  │ Gmail ⭐        │   │
│  │ work@gmail.com  │   │
│  └─────────────────┘   │
│  ┌─────────────────┐   │
│  │ Facebook        │   │
│  │ john@fb.com     │   │
│  └─────────────────┘   │
│                         │
│  [+] Add Password       │
└─────────────────────────┘
```

---

## 🏗️ Framework Choices

### Option 1: React Native (Recommended) ⭐

**Pros:**
- ✅ One codebase for iOS + Android
- ✅ JavaScript/TypeScript (familiar)
- ✅ Large community
- ✅ Fast development
- ✅ Hot reload (see changes instantly)

**Cons:**
- ⚠️ Slightly larger app size
- ⚠️ Some native code needed for encryption

**Best for:** Most developers, fastest to market

### Option 2: Flutter

**Pros:**
- ✅ One codebase for iOS + Android
- ✅ Beautiful UI out-of-the-box
- ✅ Fast performance
- ✅ Hot reload

**Cons:**
- ⚠️ Learn Dart language
- ⚠️ Smaller community than React Native

**Best for:** If you like Dart or want beautiful UI easily

### Option 3: Native (Swift + Kotlin)

**Pros:**
- ✅ Best performance
- ✅ Full platform capabilities
- ✅ Native look and feel

**Cons:**
- ❌ Two separate codebases
- ❌ 2x development time
- ❌ Requires Mac for iOS

**Best for:** If you need maximum performance or already know Swift/Kotlin

---

## 📱 Recommended: React Native Setup

### Prerequisites

```bash
# Install Node.js (https://nodejs.org)
# Install Expo CLI (easier React Native setup)
npm install -g expo-cli

# For iOS (Mac only):
# - Install Xcode from App Store
# - Install Xcode Command Line Tools

# For Android:
# - Install Android Studio
# - Set up Android SDK
```

### Create New Project

```bash
# Create new Expo project
expo init PasswordManagerMobile

# Choose template: "blank (TypeScript)"

cd PasswordManagerMobile

# Install dependencies
npm install react-navigation @react-navigation/native @react-navigation/stack
npm install react-native-crypto-js  # For AES encryption
npm install expo-secure-store        # For secure storage
npm install expo-local-authentication # For biometrics
```

---

## 📁 Project Structure

```
PasswordManagerMobile/
├── src/
│   ├── screens/
│   │   ├── LoginScreen.tsx        # Login/create account
│   │   ├── PasswordListScreen.tsx # List of passwords
│   │   ├── PasswordViewScreen.tsx # View single password
│   │   ├── AddPasswordScreen.tsx  # Add new password
│   │   └── SettingsScreen.tsx     # App settings
│   ├── components/
│   │   ├── PasswordItem.tsx       # Password list item
│   │   ├── PasswordGenerator.tsx  # Generate passwords
│   │   └── SearchBar.tsx          # Search component
│   ├── services/
│   │   ├── DatabaseService.ts     # Local database (SQLite)
│   │   ├── EncryptionService.ts   # AES-256 encryption
│   │   ├── AuthService.ts         # Authentication
│   │   └── SyncService.ts         # Sync with desktop (optional)
│   ├── utils/
│   │   ├── crypto.ts              # Encryption helpers
│   │   └── storage.ts             # Secure storage
│   └── types/
│       └── index.ts               # TypeScript types
├── App.tsx                        # Main app entry
└── package.json                   # Dependencies
```

---

## 🔐 Core Implementation

### 1. Encryption Service (Same as Desktop!)

```typescript
// src/services/EncryptionService.ts

import CryptoJS from 'react-native-crypto-js';
import * as SecureStore from 'expo-secure-store';

export class EncryptionService {
    // Derive key from master password (same as desktop)
    private static deriveKey(password: string, salt: string): string {
        return CryptoJS.PBKDF2(password, salt, {
            keySize: 256 / 32,
            iterations: 100000,
            hasher: CryptoJS.algo.SHA256
        }).toString();
    }

    // Encrypt password (AES-256-CBC)
    static encrypt(plaintext: string, masterPassword: string, salt: string): string {
        const key = this.deriveKey(masterPassword, salt);
        const iv = CryptoJS.lib.WordArray.random(16);

        const encrypted = CryptoJS.AES.encrypt(plaintext, key, {
            iv: iv,
            mode: CryptoJS.mode.CBC,
            padding: CryptoJS.pad.Pkcs7
        });

        // Return: iv + encrypted data
        return iv.toString() + ':' + encrypted.toString();
    }

    // Decrypt password
    static decrypt(ciphertext: string, masterPassword: string, salt: string): string {
        const key = this.deriveKey(masterPassword, salt);
        const parts = ciphertext.split(':');
        const iv = CryptoJS.enc.Hex.parse(parts[0]);
        const encrypted = parts[1];

        const decrypted = CryptoJS.AES.decrypt(encrypted, key, {
            iv: iv,
            mode: CryptoJS.mode.CBC,
            padding: CryptoJS.pad.Pkcs7
        });

        return decrypted.toString(CryptoJS.enc.Utf8);
    }
}
```

### 2. Secure Storage

```typescript
// src/utils/storage.ts

import * as SecureStore from 'expo-secure-store';

export class SecureStorage {
    // Store master password hash securely
    static async storeMasterPasswordHash(hash: string): Promise<void> {
        await SecureStore.setItemAsync('master_password_hash', hash);
    }

    // Get master password hash
    static async getMasterPasswordHash(): Promise<string | null> {
        return await SecureStore.getItemAsync('master_password_hash');
    }

    // Store session token
    static async storeSessionToken(token: string): Promise<void> {
        await SecureStore.setItemAsync('session_token', token);
    }

    // Clear all secure data (logout)
    static async clearAll(): Promise<void> {
        await SecureStore.deleteItemAsync('master_password_hash');
        await SecureStore.deleteItemAsync('session_token');
    }
}
```

### 3. Biometric Authentication

```typescript
// src/services/AuthService.ts

import * as LocalAuthentication from 'expo-local-authentication';
import { SecureStorage } from '../utils/storage';

export class AuthService {
    // Check if biometrics available
    static async isBiometricsAvailable(): Promise<boolean> {
        const compatible = await LocalAuthentication.hasHardwareAsync();
        const enrolled = await LocalAuthentication.isEnrolledAsync();
        return compatible && enrolled;
    }

    // Authenticate with biometrics
    static async authenticateWithBiometrics(): Promise<boolean> {
        const result = await LocalAuthentication.authenticateAsync({
            promptMessage: 'Unlock Password Manager',
            fallbackLabel: 'Use Master Password',
            disableDeviceFallback: false,
        });

        return result.success;
    }

    // Authenticate with master password
    static async authenticateWithPassword(password: string): Promise<boolean> {
        const storedHash = await SecureStorage.getMasterPasswordHash();
        if (!storedHash) return false;

        // Hash entered password and compare
        const enteredHash = this.hashPassword(password);
        return enteredHash === storedHash;
    }

    private static hashPassword(password: string): string {
        // Use bcrypt or similar (same as desktop)
        // Simplified example:
        return CryptoJS.SHA256(password).toString();
    }
}
```

### 4. Login Screen

```typescript
// src/screens/LoginScreen.tsx

import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, Button, TouchableOpacity } from 'react-native';
import * as LocalAuthentication from 'expo-local-authentication';
import { AuthService } from '../services/AuthService';

export function LoginScreen({ navigation }) {
    const [masterPassword, setMasterPassword] = useState('');
    const [biometricsAvailable, setBiometricsAvailable] = useState(false);

    useEffect(() => {
        checkBiometrics();
    }, []);

    async function checkBiometrics() {
        const available = await AuthService.isBiometricsAvailable();
        setBiometricsAvailable(available);
    }

    async function handleLogin() {
        const success = await AuthService.authenticateWithPassword(masterPassword);
        if (success) {
            navigation.navigate('PasswordList');
        } else {
            alert('Incorrect master password');
        }
    }

    async function handleBiometricLogin() {
        const success = await AuthService.authenticateWithBiometrics();
        if (success) {
            navigation.navigate('PasswordList');
        }
    }

    return (
        <View style={styles.container}>
            <Text style={styles.title}>🔐 Password Manager</Text>

            <TextInput
                style={styles.input}
                placeholder="Master Password"
                secureTextEntry
                value={masterPassword}
                onChangeText={setMasterPassword}
            />

            <Button title="Unlock" onPress={handleLogin} />

            {biometricsAvailable && (
                <TouchableOpacity onPress={handleBiometricLogin} style={styles.biometricButton}>
                    <Text>🔑 Use Biometric</Text>
                </TouchableOpacity>
            )}
        </View>
    );
}
```

### 5. Password List Screen

```typescript
// src/screens/PasswordListScreen.tsx

import React, { useState, useEffect } from 'react';
import { View, FlatList, TextInput, Button } from 'react-native';
import { PasswordItem } from '../components/PasswordItem';
import { DatabaseService } from '../services/DatabaseService';

export function PasswordListScreen({ navigation }) {
    const [passwords, setPasswords] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        loadPasswords();
    }, []);

    async function loadPasswords() {
        const allPasswords = await DatabaseService.getAllPasswords();
        setPasswords(allPasswords);
    }

    const filteredPasswords = passwords.filter(pwd =>
        pwd.website.toLowerCase().includes(searchQuery.toLowerCase()) ||
        pwd.username.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <View style={styles.container}>
            <TextInput
                style={styles.searchBar}
                placeholder="Search passwords..."
                value={searchQuery}
                onChangeText={setSearchQuery}
            />

            <FlatList
                data={filteredPasswords}
                keyExtractor={item => item.id.toString()}
                renderItem={({ item }) => (
                    <PasswordItem
                        password={item}
                        onPress={() => navigation.navigate('PasswordView', { password: item })}
                    />
                )}
            />

            <Button
                title="+ Add Password"
                onPress={() => navigation.navigate('AddPassword')}
            />
        </View>
    );
}
```

---

## 🔄 Syncing with Desktop App

### Option 1: WiFi Direct Sync (Recommended for Privacy)

```typescript
// src/services/SyncService.ts

export class SyncService {
    // Discover desktop app on local network
    static async discoverDesktopApp(): Promise<string | null> {
        // Scan local network for your app
        // Desktop app broadcasts on port 9090
        // Return IP address if found
    }

    // Sync with desktop
    static async syncWithDesktop(desktopIP: string) {
        // 1. Establish encrypted connection
        // 2. Compare database versions
        // 3. Download newer passwords
        // 4. Upload new passwords from mobile
        // 5. Resolve conflicts
    }
}
```

### Option 2: File-based Sync (Simplest)

```typescript
// Export encrypted database from desktop
// User transfers file to phone (USB, email, etc.)
// Import on mobile app

export class FileImportService {
    static async importFromFile(filePath: string, masterPassword: string) {
        // 1. Read encrypted database file
        // 2. Decrypt with master password
        // 3. Import passwords into mobile database
    }
}
```

### Option 3: QR Code Sync (Cool!)

```typescript
// Desktop shows QR code with encrypted data
// Mobile scans QR code and imports

export class QRSyncService {
    static async syncViaQRCode(qrData: string) {
        // 1. Parse QR code data
        // 2. Decrypt passwords
        // 3. Import into mobile database
    }
}
```

---

## 📦 Building and Deploying

### For iOS (Requires Mac):

```bash
# Build standalone app
expo build:ios

# Upload to App Store
# 1. Create App Store Connect account ($99/year)
# 2. Configure app in App Store Connect
# 3. Use Xcode to upload
# 4. Submit for review
# 5. Wait 1-3 days for approval
```

### For Android:

```bash
# Build APK (for testing)
expo build:android -t apk

# Build AAB (for Play Store)
expo build:android -t app-bundle

# Upload to Play Store
# 1. Create Play Console account ($25 one-time)
# 2. Create app listing
# 3. Upload AAB
# 4. Submit for review
# 5. Usually approved within 24-48 hours
```

---

## 🎨 Making It Beautiful

```typescript
// Use React Native Paper for Material Design
npm install react-native-paper

// Or React Native Elements
npm install react-native-elements

// Example with Paper:
import { Button, Card, TextInput } from 'react-native-paper';

<Card style={styles.card}>
    <Card.Content>
        <Text>Gmail</Text>
        <Text>work@gmail.com</Text>
    </Card.Content>
    <Card.Actions>
        <Button onPress={handleView}>View</Button>
        <Button onPress={handleCopy}>Copy</Button>
    </Card.Actions>
</Card>
```

---

## ⏱️ Development Timeline

### Phase 1: Setup & Learning (2 weeks)
- Install React Native / Expo
- Learn basics
- Set up project structure

### Phase 2: Core UI (3 weeks)
- Login screen
- Password list
- Add/Edit screens
- Settings

### Phase 3: Encryption (2 weeks)
- Implement AES-256
- Secure storage
- Master password hashing

### Phase 4: Features (3 weeks)
- Search
- Password generator
- Biometrics
- Auto-lock

### Phase 5: Sync (3 weeks)
- Choose sync method
- Implement sync
- Test thoroughly

### Phase 6: Polish (2 weeks)
- Beautiful UI
- Smooth animations
- Onboarding
- Help screens

### Phase 7: Testing (2 weeks)
- Test on real devices
- Beta testers
- Bug fixes

### Phase 8: Deployment (1 week)
- App Store submission
- Play Store submission
- Wait for approval

**Total: 4-5 months** part-time

---

## 💰 Costs

- **React Native:** Free
- **Expo:** Free
- **iOS Developer Account:** $99/year
- **Android Developer Account:** $25 one-time
- **Mac (for iOS development):** $1000+
- **Test devices:** $500-1000
- **Total First Year:** ~$1,600+

---

## 🎯 Quick Start

```bash
# Install Expo
npm install -g expo-cli

# Create project
expo init PasswordManagerMobile
cd PasswordManagerMobile

# Install dependencies
npm install @react-navigation/native @react-navigation/stack
npm install react-native-crypto-js expo-secure-store expo-local-authentication
npm install expo-sqlite  # For local database

# Start development
expo start

# Scan QR code with Expo Go app on phone
# App runs on your phone in real-time!
```

---

## 📱 Testing on Real Devices

### Android:
1. Install "Expo Go" from Play Store
2. Scan QR code from `expo start`
3. App runs on your phone!

### iOS:
1. Install "Expo Go" from App Store
2. Scan QR code (or same WiFi network)
3. App runs on your phone!

**Hot Reload:** Edit code → Changes appear instantly on phone!

---

## 🔒 Security Best Practices

1. **Never Store Master Password**
   - Only store hash
   - Use bcrypt or Argon2

2. **Use Secure Storage**
   - Use expo-secure-store or Keychain (iOS) / Keystore (Android)
   - Never use AsyncStorage for sensitive data

3. **Implement Auto-Lock**
   - Lock after 5 minutes inactivity
   - Require biometric/password to unlock

4. **Clear Clipboard**
   - Auto-clear password from clipboard after 30 seconds

5. **No Screenshots**
   ```typescript
   // Prevent screenshots on sensitive screens
   import { preventScreenCapture } from 'expo-screen-capture';
   preventScreenCapture();
   ```

---

## ✅ Checklist

- [ ] React Native / Expo set up
- [ ] Login screen with master password
- [ ] Biometric authentication
- [ ] Password list view
- [ ] Add password screen
- [ ] Edit password screen
- [ ] Password generator
- [ ] Search functionality
- [ ] Secure encryption (AES-256)
- [ ] Secure storage
- [ ] Auto-lock feature
- [ ] Sync with desktop (optional)
- [ ] Beautiful UI
- [ ] Tested on real devices
- [ ] App Store submission
- [ ] Play Store submission

---

## 📚 Resources

- **Expo Docs:** https://docs.expo.dev/
- **React Native Docs:** https://reactnative.dev/
- **Tutorial:** "The Complete React Native + Hooks Course" (Udemy)
- **UI Libraries:** React Native Paper, React Native Elements
- **Crypto:** react-native-crypto-js

---

## 🎯 Summary

**Framework:** React Native with Expo (easiest)
**Time:** 4-5 months part-time
**Cost:** ~$1,600 first year
**Difficulty:** Medium-High
**Result:** Professional mobile app on iOS + Android!

**Start with Android (easier), then port to iOS!** 📱✨

Your mobile app will make your password manager **accessible anywhere**!
