#!/usr/bin/env python3
"""
List Master Users Utility
=========================

This utility script displays all master user accounts in the password manager database.
Useful for debugging and checking which users exist in the system.

Usage:
    python list_users.py [database_path]

    database_path: Optional path to database file (default: data/password_manager.db)

Author: Personal Password Manager
Version: 2.2.0
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def list_users(db_path: str = "data/password_manager.db") -> List[Dict[str, Any]]:
    """
    List all users in the database

    Args:
        db_path (str): Path to the database file

    Returns:
        List[Dict[str, Any]]: List of user information
    """
    db_file = Path(db_path)

    if not db_file.exists():
        print(f"[ERROR] Database not found at: {db_file.absolute()}")
        print("\nThe database file does not exist yet.")
        print("It will be created when you run the application for the first time.")
        return []

    try:
        # Connect to database
        conn = sqlite3.connect(str(db_file))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if users table exists
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='users'
        """
        )

        if not cursor.fetchone():
            print("[ERROR] Database exists but 'users' table not found.")
            print("This might be a corrupted or incompatible database file.")
            conn.close()
            return []

        # Get all users
        cursor.execute(
            """
            SELECT
                user_id,
                username,
                created_at,
                last_login,
                failed_attempts,
                locked_until,
                is_active
            FROM users
            ORDER BY created_at ASC
        """
        )

        users = []
        for row in cursor.fetchall():
            users.append(dict(row))

        conn.close()
        return users

    except sqlite3.Error as e:
        print(f"[ERROR] Database error: {e}")
        return []
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return []


def format_timestamp(timestamp_str: str) -> str:
    """Format timestamp for display"""
    if not timestamp_str:
        return "Never"

    try:
        # Parse ISO format timestamp
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return timestamp_str


def display_users(users: List[Dict[str, Any]]) -> None:
    """Display users in a formatted table"""
    if not users:
        print("\n" + "=" * 80)
        print("NO MASTER USERS FOUND")
        print("=" * 80)
        print("\nThe database exists but contains no user accounts.")
        print("\nTo create your first account:")
        print("  1. Run: python main.py")
        print("  2. Click the 'Create New Account' button (NOT 'Sign In')")
        print("  3. Enter your desired username and master password")
        print("  4. Click 'Create Account'")
        print("=" * 80)
        return

    print("\n" + "=" * 80)
    print(f"MASTER USERS IN DATABASE ({len(users)} total)")
    print("=" * 80)
    print()

    for i, user in enumerate(users, 1):
        print(f"User #{i}:")
        print(f"  - Username:       {user['username']}")
        print(f"  - User ID:        {user['user_id']}")
        print(f"  - Status:         {'Active' if user['is_active'] else 'Inactive'}")
        print(f"  - Created:        {format_timestamp(user['created_at'])}")
        print(f"  - Last Login:     {format_timestamp(user['last_login'])}")
        print(f"  - Failed Attempts: {user['failed_attempts']}")

        if user["locked_until"]:
            locked_until = datetime.fromisoformat(user["locked_until"])
            if datetime.now() < locked_until:
                print(
                    f"  - Status:         [LOCKED] until {format_timestamp(user['locked_until'])}"
                )
            else:
                print("  - Status:         [Lock expired - will be cleared on next login]")

        if i < len(users):
            print()

    print("=" * 80)


def get_password_counts(db_path: str, users: List[Dict[str, Any]]) -> Dict[int, int]:
    """Get password entry counts for each user"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        counts = {}
        for user in users:
            cursor.execute(
                """
                SELECT COUNT(*) as count FROM passwords
                WHERE user_id = ?
            """,
                (user["user_id"],),
            )

            result = cursor.fetchone()
            counts[user["user_id"]] = result[0] if result else 0

        conn.close()
        return counts

    except Exception:
        return {}


def main():
    """Main entry point"""
    print("\n" + "=" * 80)
    print("Personal Password Manager - List Master Users Utility")
    print("Version 2.2.0")
    print("=" * 80)

    # Get database path from command line or use default
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/password_manager.db"

    print(f"\nDatabase: {Path(db_path).absolute()}")

    # List users
    users = list_users(db_path)

    # Display users
    display_users(users)

    # Show password counts if users exist
    if users:
        print("\nPassword Entry Statistics:")
        print("-" * 80)

        counts = get_password_counts(db_path, users)
        for user in users:
            count = counts.get(user["user_id"], 0)
            print(f"  - {user['username']:20} : {count} password entries")

        print("-" * 80)

    print("\nDone!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
