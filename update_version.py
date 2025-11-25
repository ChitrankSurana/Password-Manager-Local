#!/usr/bin/env python3
"""
Script to update version from 2.2.0 to 2.2.0 across all files
"""

import os
from pathlib import Path

def update_version_in_file(file_path):
    """Replace 2.2.0 with 2.2.0 in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if '2.2.0' in content:
            new_content = content.replace('2.2.0', '2.2.0')

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            print(f"[OK] Updated: {file_path}")
            return True
        else:
            return False

    except Exception as e:
        print(f"[ERROR] Error updating {file_path}: {e}")
        return False

def main():
    """Main function to update all files"""
    base_dir = Path(__file__).parent

    # File patterns to update
    patterns = ['**/*.py', '**/*.md']

    total_files = 0
    updated_files = 0

    print("Updating version from 2.2.0 to 2.2.0...")
    print("=" * 60)

    for pattern in patterns:
        for file_path in base_dir.glob(pattern):
            # Skip certain directories
            if any(skip in str(file_path) for skip in ['.git', '__pycache__', 'venv', 'env', 'node_modules']):
                continue

            total_files += 1
            if update_version_in_file(file_path):
                updated_files += 1

    print("=" * 60)
    print(f"Processed: {total_files} files")
    print(f"Updated: {updated_files} files")
    print("[COMPLETE] Version update complete!")

if __name__ == '__main__':
    main()
