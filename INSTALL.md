# Installation Guide - Personal Password Manager

This guide provides detailed installation instructions for the Personal Password Manager on Windows, macOS, and Linux systems.

## System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **RAM**: 512 MB available
- **Storage**: 100 MB free space
- **Display**: 1024x768 resolution

### Recommended Requirements
- **Python**: 3.9 or higher
- **RAM**: 1 GB available
- **Storage**: 500 MB free space (for backups)
- **Display**: 1920x1080 resolution

## Installation Methods

### Method 1: Automatic Installation (Recommended)

1. **Download the project files**
   - Download and extract the ZIP file, or
   - Clone with Git: `git clone <repository-url>`

2. **Navigate to the project directory**
   ```bash
   cd Password-Manager-Local
   ```

3. **Run the dependency checker**
   ```bash
   python check_dependencies.py
   ```
   
   This script will:
   - Check your Python version
   - Verify all required packages
   - Automatically install missing dependencies
   - Provide colored status updates
   - Create necessary directories

4. **Launch the application**
   ```bash
   python main.py
   ```

### Method 2: Manual Installation

If you prefer to install dependencies manually:

1. **Verify Python installation**
   ```bash
   python --version
   # Should show Python 3.8 or higher
   ```

2. **Install required packages**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**
   ```bash
   python -c "import customtkinter; print('GUI framework: OK')"
   python -c "import cryptography; print('Encryption: OK')"
   python -c "import bcrypt; print('Password hashing: OK')"
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

## Platform-Specific Instructions

### Windows Installation

#### Using Command Prompt
```cmd
# Navigate to the project directory
cd C:\path\to\Password-Manager-Local

# Run dependency checker
python check_dependencies.py

# Launch application
python main.py
```

#### Using PowerShell
```powershell
# Navigate to the project directory
Set-Location "C:\path\to\Password-Manager-Local"

# Run dependency checker
python check_dependencies.py

# Launch application
python main.py
```

#### Creating a Desktop Shortcut
1. Create a new batch file `launch.bat`:
   ```batch
   @echo off
   cd /d "C:\path\to\Password-Manager-Local"
   python main.py
   pause
   ```

2. Create a shortcut to this batch file on your desktop

### macOS Installation

#### Using Terminal
```bash
# Navigate to the project directory
cd ~/Downloads/Password-Manager-Local

# Run dependency checker
python3 check_dependencies.py

# Launch application
python3 main.py
```

#### Creating an Application Bundle (Optional)
1. Create a shell script `launch.sh`:
   ```bash
   #!/bin/bash
   cd "$(dirname "$0")"
   python3 main.py
   ```

2. Make it executable: `chmod +x launch.sh`

### Linux Installation

#### Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install Python and pip (if not installed)
sudo apt install python3 python3-pip

# Navigate to project directory
cd ~/Downloads/Password-Manager-Local

# Run dependency checker
python3 check_dependencies.py

# Launch application
python3 main.py
```

#### CentOS/RHEL/Fedora
```bash
# Install Python and pip
sudo dnf install python3 python3-pip

# Navigate to project directory
cd ~/Downloads/Password-Manager-Local

# Run dependency checker
python3 check_dependencies.py

# Launch application
python3 main.py
```

#### Arch Linux
```bash
# Install Python
sudo pacman -S python python-pip

# Navigate to project directory
cd ~/Downloads/Password-Manager-Local

# Run dependency checker
python3 check_dependencies.py

# Launch application
python3 main.py
```

## Virtual Environment Setup (Recommended for Advanced Users)

Using a virtual environment isolates the application dependencies:

### Create Virtual Environment
```bash
# Create virtual environment
python -m venv password_manager_env

# Activate virtual environment
# Windows:
password_manager_env\Scripts\activate
# macOS/Linux:
source password_manager_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

### Deactivating Virtual Environment
```bash
deactivate
```

## Dependency Details

The application requires these Python packages:

### Core Dependencies
- **customtkinter** (5.2.0+): Modern GUI framework
- **cryptography** (41.0.0+): Encryption and security
- **bcrypt** (4.0.0+): Password hashing
- **pyperclip** (1.8.0+): Clipboard operations

### Optional Dependencies
- **requests** (2.31.0+): For future cloud sync features
- **pillow** (10.0.0+): Image processing for GUI

All dependencies are automatically managed by the `check_dependencies.py` script.

## Troubleshooting Installation

### Common Issues

#### Python Not Found
**Error**: `'python' is not recognized as an internal or external command`

**Solutions**:
- **Windows**: Add Python to PATH or use `python.exe` with full path
- **macOS/Linux**: Try `python3` instead of `python`
- Reinstall Python with "Add to PATH" option enabled

#### Permission Denied
**Error**: `Permission denied` when installing packages

**Solutions**:
- **Windows**: Run Command Prompt as Administrator
- **macOS/Linux**: Use `sudo` with pip commands or install in user directory:
  ```bash
  pip install --user -r requirements.txt
  ```

#### Package Installation Fails
**Error**: Various pip installation errors

**Solutions**:
1. Update pip: `python -m pip install --upgrade pip`
2. Clear pip cache: `pip cache purge`
3. Install packages individually:
   ```bash
   pip install customtkinter
   pip install cryptography
   pip install bcrypt
   pip install pyperclip
   ```

#### GUI Framework Issues
**Error**: CustomTkinter not displaying properly

**Solutions**:
- Update graphics drivers
- Try different appearance modes (light/dark)
- Check display scaling settings

#### Encryption Library Issues
**Error**: Cryptography package compilation errors

**Solutions**:
- **Windows**: Install Microsoft Visual C++ Build Tools
- **Linux**: Install development packages:
  ```bash
  # Ubuntu/Debian
  sudo apt install build-essential libffi-dev python3-dev
  
  # CentOS/RHEL
  sudo dnf install gcc openssl-devel libffi-devel python3-devel
  ```
- **macOS**: Install Xcode command line tools: `xcode-select --install`

### Advanced Troubleshooting

#### Check Python Installation
```bash
python --version
python -c "import sys; print(sys.executable)"
python -c "import sys; print(sys.path)"
```

#### Verify Package Installation
```bash
pip list | grep customtkinter
pip list | grep cryptography
pip list | grep bcrypt
```

#### Test Core Functionality
```bash
# Test database creation
python -c "from src.core.database import DatabaseManager; print('Database: OK')"

# Test encryption
python -c "from src.core.encryption import EncryptionManager; print('Encryption: OK')"

# Test GUI
python -c "import customtkinter; print('GUI: OK')"
```

## First Run Setup

### Initial Application Launch

1. **First launch**: Run `python main.py`
2. **Login window appears**: The application starts with the login interface
3. **Create account**: Click "Create Account" for first-time setup
4. **Set credentials**: Choose a username and strong master password
5. **Main interface**: After login, the main password management interface opens

### Directory Structure Creation

On first run, the application creates:
- **Database directory**: Stores the encrypted password database
- **Backup directory**: For automatic backups
- **Config directory**: For application settings
- **Log directory**: For debugging and error logs

### Security Initialization

The application automatically:
- Generates encryption keys
- Creates secure database schema
- Sets up session management
- Initializes security logging

## Performance Optimization

### For Better Performance

1. **SSD Storage**: Store the database on an SSD for faster access
2. **Adequate RAM**: Ensure sufficient memory for encryption operations
3. **Updated Python**: Use the latest Python 3.x version
4. **Graphics Drivers**: Keep graphics drivers updated for smooth GUI

### Resource Usage
- **Memory**: Typically uses 50-100 MB RAM
- **CPU**: Low usage except during encryption operations
- **Disk**: Database grows with stored passwords (typically <10 MB)

## Uninstallation

### Complete Removal

1. **Delete application files**: Remove the entire project directory
2. **Remove user data** (optional):
   - **Windows**: Delete `%APPDATA%\PasswordManager\`
   - **macOS**: Delete `~/Library/Application Support/PasswordManager/`
   - **Linux**: Delete `~/.local/share/PasswordManager/`

3. **Remove Python packages** (if installed globally):
   ```bash
   pip uninstall customtkinter cryptography bcrypt pyperclip
   ```

### Backup Before Uninstall
Always backup your password database before uninstalling:
1. Use the built-in Backup Manager
2. Create encrypted exports
3. Save to external storage or cloud

## Getting Help

If you encounter issues during installation:

1. **Run diagnostics**: Use `python check_dependencies.py --verbose`
2. **Check logs**: Review error messages carefully
3. **Platform support**: The application is tested on Windows 10/11, macOS 12+, and Ubuntu 20.04+
4. **Documentation**: Review the main README.md and technical documentation

Remember: The installation process is designed to be simple and automated. Most users can get started by just running `python check_dependencies.py` followed by `python main.py`.