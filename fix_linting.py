#!/usr/bin/env python3
"""
Automated Linting Fix Script
============================
This script automatically fixes common Flake8 issues.
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def remove_unused_imports(file_path: Path, unused_imports: List[str]) -> None:
    """Remove unused imports from a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    modified = False
    new_lines = []

    for line in lines:
        skip_line = False
        for unused in unused_imports:
            # Check if this line contains the unused import
            if f"import {unused}" in line or f"from {unused}" in line:
                # Check if it's a single import or part of multi-import
                if "import" in line and "," not in line:
                    skip_line = True
                    modified = True
                    break

        if not skip_line:
            new_lines.append(line)

    if modified:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"[+] Fixed unused imports in {file_path}")


def fix_f_strings(file_path: Path) -> None:
    """Remove f-string prefix when there are no placeholders."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Match f-strings without placeholders
    pattern = r'f(["\'])([^\1]*?)\1'

    def replace_if_no_placeholder(match):
        quote = match.group(1)
        string_content = match.group(2)
        # If no { } placeholders, remove the f prefix
        if "{" not in string_content:
            return f"{quote}{string_content}{quote}"
        return match.group(0)

    new_content = re.sub(pattern, replace_if_no_placeholder, content)

    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"[+] Fixed f-strings in {file_path}")


def fix_bare_except(file_path: Path) -> None:
    """Fix bare except clauses."""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    modified = False
    new_lines = []

    for line in lines:
        # Match bare except with optional comment
        if re.match(r"^\s+except:\s*(?:#.*)?$", line):
            indent = len(line) - len(line.lstrip())
            comment = ""
            if "#" in line:
                comment = " " + line[line.index("#") :]
            else:
                comment = "\n"
            new_line = " " * indent + "except Exception:" + comment
            new_lines.append(new_line)
            modified = True
        else:
            new_lines.append(line)

    if modified:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"[+] Fixed bare except in {file_path}")


def fix_unused_variables(file_path: Path, unused_vars: List[Tuple[int, str]]) -> None:
    """Prefix unused variables with underscore."""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    modified = False

    for line_no, var_name in unused_vars:
        if 0 < line_no <= len(lines):
            line = lines[line_no - 1]
            # Simple replacement for assignment
            if f"{var_name} =" in line and not line.strip().startswith("#"):
                new_line = line.replace(f"{var_name} =", f"_{var_name} =", 1)
                if new_line != line:
                    lines[line_no - 1] = new_line
                    modified = True

    if modified:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"[+] Fixed unused variables in {file_path}")


def get_flake8_issues() -> dict:
    """Run flake8 and parse the output."""
    try:
        result = subprocess.run(
            ["flake8", "--max-line-length=100", "--extend-ignore=E203,W503"],
            capture_output=True,
            text=True,
        )

        issues = {}
        for line in result.stdout.splitlines():
            if not line.strip():
                continue

            # Parse flake8 output: path:line:col: error_code message
            parts = line.split(":", 3)
            if len(parts) >= 4:
                file_path = parts[0]
                line_no = int(parts[1])
                error_code = parts[3].strip().split()[0]
                message = parts[3].strip()

                if file_path not in issues:
                    issues[file_path] = []
                issues[file_path].append((line_no, error_code, message))

        return issues

    except FileNotFoundError:
        print("Error: flake8 not found. Please install it: pip install flake8")
        sys.exit(1)


def main():
    """Main function to fix linting issues."""
    print("[*] Automated Linting Fix Script")
    print("=" * 50)

    # Get all Python files
    python_files = list(Path(".").rglob("*.py"))
    python_files = [f for f in python_files if "venv" not in str(f) and ".venv" not in str(f)]

    print(f"\nFound {len(python_files)} Python files to check.")
    print("\nFixing issues...\n")

    # Fix f-strings in all files
    for file_path in python_files:
        try:
            fix_f_strings(file_path)
        except Exception as e:
            print(f"[\\!] Error fixing f-strings in {file_path}: {e}")

    # Fix bare except in all files
    for file_path in python_files:
        try:
            fix_bare_except(file_path)
        except Exception as e:
            print(f"[\\!] Error fixing bare except in {file_path}: {e}")

    print("\n[OK] Automated fixes completed!")
    print("\nNote: Some issues require manual review:")
    print("  - Unused imports with multiple imports on one line")
    print("  - Unused variables in complex contexts")
    print("  - Duplicate function/import redefinitions")
    print("  - Code complexity issues")
    print("\nRun 'flake8' again to see remaining issues.")


if __name__ == "__main__":
    main()
