@echo off
REM Build script for Personal Password Manager
REM This script creates a standalone executable for Windows

echo ================================================================
echo   Personal Password Manager - Executable Builder
echo   Version 2.2.0
echo ================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

echo [1/5] Checking Python installation...
python --version
echo.

REM Install PyInstaller if not already installed
echo [2/5] Installing PyInstaller...
python -m pip install pyinstaller --quiet --upgrade
if errorlevel 1 (
    echo [ERROR] Failed to install PyInstaller
    pause
    exit /b 1
)
echo [OK] PyInstaller is ready
echo.

REM Install all dependencies
echo [3/5] Installing dependencies...
echo This may take a few minutes...
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [WARNING] Some dependencies may have failed to install
    echo The build will continue, but the executable may not work properly
)
echo [OK] Dependencies installed
echo.

REM Clean previous builds
echo [4/5] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist distribution rmdir /s /q distribution
if exist Personal_Password_Manager.exe del /q Personal_Password_Manager.exe
echo [OK] Cleanup complete
echo.

REM Build the executable
echo [5/5] Building executable...
echo This may take several minutes, please wait...
echo.
python -m PyInstaller --clean password_manager.spec
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    echo Please check the errors above and try again.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   BUILD COMPLETED SUCCESSFULLY!
echo ================================================================
echo.
echo Your executable has been created:
echo   Location: dist\Personal_Password_Manager.exe
echo.
echo To create a distribution package:
echo   1. Create a new folder (e.g., "Password_Manager_v2.2.0")
echo   2. Copy the executable from dist\ folder
echo   3. Create a "data" folder next to the executable
echo   4. Include README.txt with usage instructions
echo.
echo To test the executable:
echo   1. Navigate to the dist folder
echo   2. Double-click Personal_Password_Manager.exe
echo.
echo Press any key to open the dist folder...
pause >nul
start dist
