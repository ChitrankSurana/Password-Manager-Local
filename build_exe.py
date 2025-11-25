#!/usr/bin/env python3
"""
Build script for Personal Password Manager executable
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def print_step(step_name):
    print(f"\n{'='*50}")
    print(f"[BUILD] {step_name}")
    print(f"{'='*50}")

def cleanup_build_files():
    """Clean up previous build files"""
    print_step("Cleaning up previous builds")
    
    dirs_to_remove = ['build', 'dist', '__pycache__']
    files_to_remove = ['*.pyc']
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            print(f"Removing directory: {dir_name}")
            shutil.rmtree(dir_name)
    
    # Remove .pyc files
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))
                print(f"Removed: {os.path.join(root, file)}")
    
    print("[OK] Cleanup completed")

def ensure_dependencies():
    """Ensure all required dependencies are installed"""
    print_step("Checking dependencies")
    
    # Run the dependency checker
    try:
        result = subprocess.run([sys.executable, 'check_dependencies.py'], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print("[ERROR] Dependency check failed. Please install missing dependencies.")
            print(result.stdout)
            print(result.stderr)
            return False
        print("[OK] All dependencies are available")
        return True
    except Exception as e:
        print(f"[ERROR] Error checking dependencies: {e}")
        return False

def create_executable():
    """Create the executable using PyInstaller"""
    print_step("Building executable with PyInstaller")
    
    try:
        # Build using the spec file
        cmd = [sys.executable, '-m', 'PyInstaller', '--clean', 'password_manager.spec']
        print(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, check=True)
        
        if result.returncode == 0:
            print("✅ Executable created successfully!")
            return True
        else:
            print("❌ Build failed!")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller failed with error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def create_distribution():
    """Create a distribution folder with all necessary files"""
    print_step("Creating distribution package")
    
    dist_dir = Path("distribution")
    exe_name = "Personal_Password_Manager.exe"
    
    try:
        # Create distribution directory
        if dist_dir.exists():
            shutil.rmtree(dist_dir)
        dist_dir.mkdir()
        
        # Copy executable
        exe_source = Path("dist") / exe_name
        exe_dest = dist_dir / exe_name
        
        if exe_source.exists():
            shutil.copy2(exe_source, exe_dest)
            print(f"✅ Copied executable to {exe_dest}")
        else:
            print(f"❌ Executable not found at {exe_source}")
            return False
        
        # Create README for distribution
        readme_content = f"""# Personal Password Manager v2.2.0

## Installation
1. Extract all files to a folder of your choice
2. Run `{exe_name}` to start the application

## Features
- Secure AES-256 encryption for all passwords
- Local SQLite database - no cloud dependency
- Modern GUI with dark/light theme support
- CSV import from other password managers
- Password generator with customizable options
- Grouped password entries by website
- Session-based authentication

## Security Notes
- All passwords are encrypted locally with your master password
- Master password is never stored on disk
- Database files are stored in the 'data' folder
- Backup your 'data' folder regularly to prevent data loss

## Requirements
- Windows 10/11 (64-bit)
- No additional software installation required

## Support
For issues or questions, refer to the documentation or contact support.

## License
Personal Password Manager v2.2.0
Copyright © 2024
"""
        
        readme_path = dist_dir / "README.txt"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"✅ Created README.txt")
        
        # Create a sample data directory
        data_dir = dist_dir / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Create a .gitkeep file to preserve the directory
        gitkeep_path = data_dir / ".gitkeep"
        gitkeep_path.write_text("This directory stores your encrypted password database.")
        
        print("✅ Distribution package created successfully!")
        print(f"📁 Location: {dist_dir.absolute()}")
        print(f"🚀 Run: {exe_dest}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating distribution: {e}")
        return False

def main():
    """Main build process"""
    print("Personal Password Manager - Executable Builder")
    print("=" * 60)
    
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    # Build process
    steps = [
        ("Cleanup", cleanup_build_files),
        ("Dependencies", ensure_dependencies),
        ("Build", create_executable),
        ("Package", create_distribution),
    ]
    
    for step_name, step_func in steps:
        if not step_func():
            print(f"\n[ERROR] Build process failed at: {step_name}")
            print("Please check the errors above and try again.")
            return 1
    
    print("\n" + "=" * 60)
    print("BUILD COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("Your executable is ready in the 'distribution' folder.")
    print("You can now distribute the entire 'distribution' folder to users.")
    print("\nTo test the executable:")
    print("1. Navigate to the distribution folder")
    print("2. Run Personal_Password_Manager.exe")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())