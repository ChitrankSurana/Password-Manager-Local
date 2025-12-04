Deployment
==========

Guide for packaging and distributing the Password Manager application.

Packaging Overview
------------------

Distribution Formats
~~~~~~~~~~~~~~~~~~~~

* **Standalone Executable**: Single-file application (Windows .exe, macOS .app)
* **Installer**: Platform-specific installer (NSIS for Windows, DMG for macOS)
* **Python Package**: Distributed via pip (for developers)

Tools Used
~~~~~~~~~~

* **PyInstaller**: Create standalone executables
* **NSIS**: Windows installer
* **DMG Canvas**: macOS disk images
* **setuptools**: Python package distribution

Building Executables
--------------------

Using PyInstaller
~~~~~~~~~~~~~~~~~

**Installation:**

.. code-block:: bash

   pip install pyinstaller

**Basic Build:**

.. code-block:: bash

   pyinstaller main.py \\
       --name="Password Manager" \\
       --onefile \\
       --windowed \\
       --icon=assets/icon.ico

**Advanced Build Spec:**

Create ``build_spec.py``:

.. code-block:: python

   # -*- mode: python ; coding: utf-8 -*-

   block_cipher = None

   a = Analysis(
       ['main.py'],
       pathex=[],
       binaries=[],
       datas=[
           ('assets', 'assets'),
           ('README.md', '.'),
       ],
       hiddenimports=[
           'customtkinter',
           'PIL._tkinter_finder',
       ],
       hookspath=[],
       hooksconfig={},
       runtime_hooks=[],
       excludes=[],
       win_no_prefer_redirects=False,
       win_private_assemblies=False,
       cipher=block_cipher,
       noarchive=False,
   )

   pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

   exe = EXE(
       pyz,
       a.scripts,
       a.binaries,
       a.zipfiles,
       a.datas,
       [],
       name='PasswordManager',
       debug=False,
       bootloader_ignore_signals=False,
       strip=False,
       upx=True,
       upx_exclude=[],
       runtime_tmpdir=None,
       console=False,
       disable_windowed_traceback=False,
       argv_emulation=False,
       target_arch=None,
       codesign_identity=None,
       entitlements_file=None,
       icon='assets/icon.ico',
   )

Build:

.. code-block:: bash

   pyinstaller build_spec.py

Platform-Specific Builds
-------------------------

Windows
~~~~~~~

**Build Executable:**

.. code-block:: bash

   pyinstaller --onefile --windowed \\
       --icon=assets/icon.ico \\
       --name="Password Manager" \\
       --add-data="assets;assets" \\
       main.py

**Create Installer with NSIS:**

``installer.nsi``:

.. code-block:: nsis

   !define APP_NAME "Password Manager"
   !define APP_VERSION "2.2.0"
   !define APP_PUBLISHER "Password Manager Team"
   !define APP_EXE "PasswordManager.exe"

   Name "${APP_NAME}"
   OutFile "PasswordManager-Setup-${APP_VERSION}.exe"
   InstallDir "$PROGRAMFILES\\${APP_NAME}"

   Section "Install"
       SetOutPath "$INSTDIR"
       File "dist\\${APP_EXE}"
       File /r "assets"

       CreateDirectory "$SMPROGRAMS\\${APP_NAME}"
       CreateShortcut "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXE}"
       CreateShortcut "$DESKTOP\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXE}"

       WriteUninstaller "$INSTDIR\\Uninstall.exe"
       WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayName" "${APP_NAME}"
       WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "UninstallString" "$INSTDIR\\Uninstall.exe"
   SectionEnd

   Section "Uninstall"
       Delete "$INSTDIR\\${APP_EXE}"
       Delete "$INSTDIR\\Uninstall.exe"
       RMDir /r "$INSTDIR\\assets"
       RMDir "$INSTDIR"

       Delete "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk"
       RMDir "$SMPROGRAMS\\${APP_NAME}"
       Delete "$DESKTOP\\${APP_NAME}.lnk"

       DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}"
   SectionEnd

Build installer:

.. code-block:: bash

   makensis installer.nsi

macOS
~~~~~

**Build .app Bundle:**

.. code-block:: bash

   pyinstaller --onefile --windowed \\
       --icon=assets/icon.icns \\
       --name="Password Manager" \\
       --osx-bundle-identifier=com.passwordmanager.app \\
       main.py

**Create DMG:**

``create_dmg.sh``:

.. code-block:: bash

   #!/bin/bash

   APP_NAME="Password Manager"
   VERSION="2.2.0"
   DMG_NAME="${APP_NAME}-${VERSION}.dmg"

   # Create DMG
   hdiutil create -volname "${APP_NAME}" -srcfolder dist/"${APP_NAME}.app" -ov -format UDZO "${DMG_NAME}"

**Code Signing (macOS):**

.. code-block:: bash

   # Sign the app
   codesign --force --deep --sign "Developer ID Application: Your Name" \\
       dist/"Password Manager.app"

   # Verify signature
   codesign --verify --verbose dist/"Password Manager.app"

   # Notarize (required for macOS 10.15+)
   xcrun notarytool submit "Password Manager-2.2.0.dmg" \\
       --apple-id "your@email.com" \\
       --team-id "TEAM_ID" \\
       --password "app-specific-password"

Linux
~~~~~

**Build Executable:**

.. code-block:: bash

   pyinstaller --onefile \\
       --name="password-manager" \\
       --add-data="assets:assets" \\
       main.py

**Create .deb Package:**

``DEBIAN/control``:

.. code-block:: text

   Package: password-manager
   Version: 2.2.0
   Section: utils
   Priority: optional
   Architecture: amd64
   Maintainer: Password Manager Team <team@passwordmanager.dev>
   Description: Secure local password manager
    A secure, local-first password management application with
    strong encryption and modern features.

Build:

.. code-block:: bash

   mkdir -p password-manager_2.2.0/DEBIAN
   mkdir -p password-manager_2.2.0/usr/bin
   mkdir -p password-manager_2.2.0/usr/share/applications
   mkdir -p password-manager_2.2.0/usr/share/icons/hicolor/256x256/apps

   cp dist/password-manager password-manager_2.2.0/usr/bin/
   cp assets/icon.png password-manager_2.2.0/usr/share/icons/hicolor/256x256/apps/password-manager.png

   dpkg-deb --build password-manager_2.2.0

**Create .rpm Package:**

``password-manager.spec``:

.. code-block:: spec

   Name:           password-manager
   Version:        2.2.0
   Release:        1%{?dist}
   Summary:        Secure local password manager

   License:        MIT
   URL:            https://github.com/yourusername/password-manager
   Source0:        %{name}-%{version}.tar.gz

   %description
   A secure, local-first password management application.

   %install
   mkdir -p %{buildroot}%{_bindir}
   install -m 755 dist/password-manager %{buildroot}%{_bindir}/password-manager

   %files
   %{_bindir}/password-manager

Build:

.. code-block:: bash

   rpmbuild -ba password-manager.spec

Continuous Deployment
---------------------

GitHub Actions
~~~~~~~~~~~~~~

``.github/workflows/build.yml``:

.. code-block:: yaml

   name: Build and Release

   on:
     push:
       tags:
         - 'v*'

   jobs:
     build-windows:
       runs-on: windows-latest
       steps:
         - uses: actions/checkout@v3

         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.10'

         - name: Install dependencies
           run: |
             pip install -r requirements.txt
             pip install pyinstaller

         - name: Build executable
           run: pyinstaller build_spec.py

         - name: Upload artifact
           uses: actions/upload-artifact@v3
           with:
             name: windows-exe
             path: dist/PasswordManager.exe

     build-macos:
       runs-on: macos-latest
       steps:
         - uses: actions/checkout@v3

         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.10'

         - name: Install dependencies
           run: |
             pip install -r requirements.txt
             pip install pyinstaller

         - name: Build app
           run: pyinstaller build_spec.py

         - name: Create DMG
           run: ./scripts/create_dmg.sh

         - name: Upload artifact
           uses: actions/upload-artifact@v3
           with:
             name: macos-dmg
             path: "*.dmg"

     release:
       needs: [build-windows, build-macos]
       runs-on: ubuntu-latest
       steps:
         - name: Download artifacts
           uses: actions/download-artifact@v3

         - name: Create Release
           uses: softprops/action-gh-release@v1
           with:
             files: |
               windows-exe/*
               macos-dmg/*
           env:
             GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

Versioning
----------

Semantic Versioning
~~~~~~~~~~~~~~~~~~~

Follow SemVer: ``MAJOR.MINOR.PATCH``

* **MAJOR**: Breaking changes
* **MINOR**: New features (backwards compatible)
* **PATCH**: Bug fixes

**Examples:**

* ``2.0.0`` → ``2.1.0``: Added browser extension (new feature)
* ``2.1.0`` → ``2.1.1``: Fixed encryption bug (bug fix)
* ``2.1.1`` → ``3.0.0``: Changed API structure (breaking change)

Version Management
~~~~~~~~~~~~~~~~~~

``src/version.py``:

.. code-block:: python

   __version__ = "2.2.0"
   __version_info__ = (2, 2, 0)

Update version:

.. code-block:: bash

   # Update version in all places
   python scripts/update_version.py 2.3.0

Release Process
---------------

Pre-Release Checklist
~~~~~~~~~~~~~~~~~~~~~

- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version number bumped
- [ ] No critical bugs
- [ ] Security audit completed
- [ ] Performance tested

Creating a Release
~~~~~~~~~~~~~~~~~~

1. **Update Version:**

   .. code-block:: bash

      python scripts/update_version.py 2.3.0

2. **Update CHANGELOG:**

   Add release notes:

   .. code-block:: markdown

      ## [2.3.0] - 2025-12-04

      ### Added
      - Password health monitoring
      - Import/Export functionality
      - Performance optimizations

      ### Fixed
      - Session timeout issues
      - UI rendering bugs

3. **Commit and Tag:**

   .. code-block:: bash

      git add .
      git commit -m "Release v2.3.0"
      git tag -a v2.3.0 -m "Version 2.3.0"
      git push origin main
      git push origin v2.3.0

4. **Build Releases:**

   CI/CD automatically builds and uploads artifacts.

5. **Create GitHub Release:**

   * Go to GitHub Releases
   * Draft new release
   * Select tag v2.3.0
   * Copy CHANGELOG content
   * Attach binaries
   * Publish

Post-Release
~~~~~~~~~~~~

- [ ] Verify downloads work
- [ ] Test on clean systems
- [ ] Monitor issue tracker
- [ ] Announce release (blog, social media)
- [ ] Update download links on website

Distribution
------------

GitHub Releases
~~~~~~~~~~~~~~~

Primary distribution channel:

* Latest release always available
* Historical versions accessible
* Automatic download counters
* Release notes with each version

Website Downloads
~~~~~~~~~~~~~~~~~

Host on project website:

* Direct download links
* Version selector
* Platform detection
* Installation instructions

Python Package Index (PyPI)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For developers:

``setup.py``:

.. code-block:: python

   from setuptools import setup, find_packages
   from src.version import __version__

   setup(
       name="password-manager-local",
       version=__version__,
       packages=find_packages(),
       install_requires=[
           "customtkinter>=5.2.0",
           "cryptography>=41.0.0",
           "argon2-cffi>=23.1.0",
           "pillow>=10.0.0",
       ],
       entry_points={
           "console_scripts": [
               "password-manager=src.main:main",
           ],
       },
   )

Publish:

.. code-block:: bash

   python setup.py sdist bdist_wheel
   twine upload dist/*

Update Mechanism
----------------

Auto-Update System
~~~~~~~~~~~~~~~~~~

``src/core/updater.py``:

.. code-block:: python

   class UpdateChecker:
       def check_for_updates(self) -> Optional[UpdateInfo]:
           \"\"\"Check if newer version is available.\"\"\"
           current = __version__
           latest = self._fetch_latest_version()

           if self._is_newer(latest, current):
               return UpdateInfo(
                   version=latest,
                   download_url=self._get_download_url(latest),
                   release_notes=self._get_release_notes(latest)
               )
           return None

       def download_and_install(self, update_info: UpdateInfo):
           \"\"\"Download and install update.\"\"\"
           # Download update
           update_file = self._download_update(update_info.download_url)

           # Verify signature
           if not self._verify_signature(update_file):
               raise SecurityError("Invalid update signature")

           # Install
           self._install_update(update_file)

           # Restart application
           self._restart_application()

Manual Update Check
~~~~~~~~~~~~~~~~~~~

Add to Help menu:

.. code-block:: python

   def on_check_for_updates(self):
       \"\"\"Check for updates manually.\"\"\"
       checker = UpdateChecker()
       update = checker.check_for_updates()

       if update:
           response = messagebox.askyesno(
               "Update Available",
               f"Version {update.version} is available.\\n\\n"
               f"Release Notes:\\n{update.release_notes}\\n\\n"
               f"Would you like to download and install it?"
           )
           if response:
               checker.download_and_install(update)
       else:
           messagebox.showinfo(
               "Up to Date",
               "You are running the latest version."
           )

Monitoring
----------

Crash Reporting
~~~~~~~~~~~~~~~

Integrate Sentry for error tracking:

.. code-block:: python

   import sentry_sdk

   sentry_sdk.init(
       dsn="your-dsn-here",
       traces_sample_rate=1.0,
       release=f"password-manager@{__version__}",
   )

Analytics
~~~~~~~~~

Track usage (with user consent):

* Installation/update events
* Feature usage
* Error rates
* Performance metrics

Security
--------

Code Signing
~~~~~~~~~~~~

**Windows:**

.. code-block:: bash

   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com PasswordManager.exe

**macOS:**

See code signing section above.

Supply Chain Security
~~~~~~~~~~~~~~~~~~~~~

* Pin dependency versions in ``requirements.txt``
* Use ``pip-audit`` to check for vulnerabilities
* Regularly update dependencies
* Review third-party code changes

Secure Distribution
~~~~~~~~~~~~~~~~~~~

* HTTPS for downloads
* SHA256 checksums published
* GPG signatures for releases
* Official channels only

Troubleshooting
---------------

Common Build Issues
~~~~~~~~~~~~~~~~~~~

**Issue: "Module not found" errors**

Solution: Add to ``hiddenimports`` in spec file.

**Issue: Application crashes on startup**

Solution: Check for missing data files, add to ``datas``.

**Issue: Large executable size**

Solution: Use ``--exclude-module`` for unused packages.

Testing Builds
~~~~~~~~~~~~~~

Test on clean systems:

* Fresh OS install (VM)
* No Python installed
* No dependencies installed
* Different user accounts

Resources
---------

* PyInstaller documentation: https://pyinstaller.org/
* NSIS documentation: https://nsis.sourceforge.io/
* GitHub Actions: https://docs.github.com/actions
* Semantic Versioning: https://semver.org/
