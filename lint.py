#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linting and Formatting Helper Script
Personal Password Manager - Code Quality Tools

This script provides convenient commands to run all linting and formatting tools.

Usage:
    python lint.py format          - Format code with black and isort
    python lint.py check           - Check code style (no changes)
    python lint.py fix             - Auto-fix what can be fixed
    python lint.py full            - Run all checks (format + lint + type check)
    python lint.py pre-commit      - Run pre-commit on all files
"""

import subprocess
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    try:
        import codecs

        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")
    except Exception:
        pass  # Fallback if encoding setup fails


class Colors:
    """ANSI color codes for terminal output"""

    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def run_command(cmd, description, check=True):
    """Run a command and print status"""
    print(f"\n{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{description}{Colors.END}")
    print(f"{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.CYAN}Running: {' '.join(cmd)}{Colors.END}\n")

    try:
        result = subprocess.run(cmd, check=check, capture_output=False)
        if result.returncode == 0:
            print(f"\n{Colors.GREEN}✓ {description} - SUCCESS{Colors.END}")
            return True
        else:
            print(f"\n{Colors.YELLOW}⚠ {description} - COMPLETED WITH WARNINGS{Colors.END}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"\n{Colors.RED}✗ {description} - FAILED{Colors.END}")
        return False
    except FileNotFoundError:
        print(f"\n{Colors.RED}✗ Tool not found. Make sure it's installed.{Colors.END}")
        return False


def format_code():
    """Format code with black and isort"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}FORMATTING CODE{Colors.END}\n")

    success = True

    # Run isort first (organize imports)
    success &= run_command(
        ["isort", "src", "tests", "main.py", "main_enhanced.py", "--profile", "black"],
        "Organizing imports with isort",
        check=False,
    )

    # Run black (format code)
    success &= run_command(
        ["black", "src", "tests", "main.py", "main_enhanced.py", "--line-length", "100"],
        "Formatting code with black",
        check=False,
    )

    return success


def check_code():
    """Check code style without making changes"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}CHECKING CODE STYLE{Colors.END}\n")

    success = True

    # Check with black (no changes)
    success &= run_command(
        ["black", "src", "tests", "--check", "--line-length", "100"],
        "Checking code formatting with black",
        check=False,
    )

    # Check with isort (no changes)
    success &= run_command(
        ["isort", "src", "tests", "--check", "--profile", "black"],
        "Checking import order with isort",
        check=False,
    )

    # Check with flake8
    success &= run_command(
        ["flake8", "src", "tests"], "Checking code style with flake8", check=False
    )

    return success


def fix_code():
    """Auto-fix issues where possible"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}AUTO-FIXING CODE ISSUES{Colors.END}\n")

    success = True

    # Format code (fixes formatting)
    success &= format_code()

    # Note: flake8 doesn't auto-fix, but we can suggest fixes
    print(f"\n{Colors.YELLOW}Note: Some issues may need manual fixing.{Colors.END}")
    print(f"{Colors.YELLOW}Run 'python lint.py check' to see remaining issues.{Colors.END}")

    return success


def full_check():
    """Run all checks"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}FULL CODE QUALITY CHECK{Colors.END}\n")

    success = True

    # 1. Format code
    print(f"\n{Colors.BOLD}Step 1: Formatting{Colors.END}")
    success &= format_code()

    # 2. Check style
    print(f"\n{Colors.BOLD}Step 2: Style Checks{Colors.END}")
    success &= run_command(
        ["flake8", "src", "tests"], "Checking code style with flake8", check=False
    )

    # 3. Type checking
    print(f"\n{Colors.BOLD}Step 3: Type Checking{Colors.END}")
    success &= run_command(
        ["mypy", "src", "--config-file", "mypy.ini"], "Checking types with mypy", check=False
    )

    # 4. Security check
    print(f"\n{Colors.BOLD}Step 4: Security Checks{Colors.END}")
    success &= run_command(
        ["bandit", "-r", "src", "-c", ".bandit.yaml"], "Checking security with bandit", check=False
    )

    return success


def run_pre_commit():
    """Run pre-commit on all files"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}RUNNING PRE-COMMIT HOOKS{Colors.END}\n")

    return run_command(
        ["pre-commit", "run", "--all-files"], "Running pre-commit hooks", check=False
    )


def print_usage():
    """Print usage information"""
    print(
        """
{Colors.HEADER}{Colors.BOLD}Password Manager - Code Quality Tools{Colors.END}

{Colors.BOLD}Usage:{Colors.END}
    python lint.py <command>

{Colors.BOLD}Commands:{Colors.END}
    {Colors.GREEN}format{Colors.END}          Format code with black and isort (modifies files)
    {Colors.GREEN}check{Colors.END}           Check code style without making changes
    {Colors.GREEN}fix{Colors.END}             Auto-fix issues where possible
    {Colors.GREEN}full{Colors.END}            Run all checks (format + lint + type + security)
    {Colors.GREEN}pre-commit{Colors.END}      Run pre-commit hooks on all files

{Colors.BOLD}Examples:{Colors.END}
    python lint.py format       # Format all code
    python lint.py check        # Just check, don't modify
    python lint.py full         # Run everything

{Colors.BOLD}Individual Tools:{Colors.END}
    black src/                  # Format with black
    isort src/                  # Sort imports
    flake8 src/                 # Check style
    mypy src/                   # Check types
    bandit -r src/              # Security check

{Colors.BOLD}Pre-commit:{Colors.END}
    The pre-commit hooks will run automatically before each git commit.
    To skip hooks (not recommended): git commit --no-verify
"""
    )


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print_usage()
        return 0

    command = sys.argv[1].lower()

    # Map commands to functions
    commands = {
        "format": format_code,
        "check": check_code,
        "fix": fix_code,
        "full": full_check,
        "pre-commit": run_pre_commit,
        "help": print_usage,
    }

    if command not in commands:
        print(f"{Colors.RED}Unknown command: {command}{Colors.END}")
        print_usage()
        return 1

    # Run the command
    success = commands[command]()

    # Print final status
    print(f"\n{Colors.BLUE}{'=' * 70}{Colors.END}")
    if success:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL CHECKS PASSED{Colors.END}")
        print(f"{Colors.BLUE}{'=' * 70}{Colors.END}\n")
        return 0
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠ SOME CHECKS FAILED OR HAD WARNINGS{Colors.END}")
        print(f"{Colors.YELLOW}Review the output above for details.{Colors.END}")
        print(f"{Colors.BLUE}{'=' * 70}{Colors.END}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
