#!/usr/bin/env python3
"""
Database Viewer Script
======================
This script allows you to view and verify data in the password manager database.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from tabulate import tabulate

DB_PATH = "data/password_manager.db"

def connect_db():
    """Connect to the database"""
    if not Path(DB_PATH).exists():
        print(f"❌ Database not found at: {DB_PATH}")
        return None

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def show_tables():
    """Show all tables in the database"""
    conn = connect_db()
    if not conn:
        return

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    print("\n" + "="*60)
    print("📊 AVAILABLE TABLES")
    print("="*60)
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table['name']}")
        count = cursor.fetchone()[0]
        print(f"  • {table['name']:<20} ({count} rows)")

    conn.close()

def show_table_schema(table_name):
    """Show schema of a specific table"""
    conn = connect_db()
    if not conn:
        return

    cursor = conn.cursor()

    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        print(f"\n" + "="*60)
        print(f"📋 SCHEMA: {table_name}")
        print("="*60)

        schema_data = []
        for col in columns:
            schema_data.append([
                col['cid'],
                col['name'],
                col['type'],
                "NOT NULL" if col['notnull'] else "NULL",
                col['pk'] if col['pk'] else ""
            ])

        print(tabulate(schema_data,
                      headers=['ID', 'Column', 'Type', 'Constraint', 'Primary Key'],
                      tablefmt='grid'))

    except sqlite3.Error as e:
        print(f"❌ Error: {e}")

    conn.close()

def show_users():
    """Show all users"""
    conn = connect_db()
    if not conn:
        return

    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, username, email, created_at, last_login, is_active
        FROM users
        ORDER BY user_id
    """)
    users = cursor.fetchall()

    print(f"\n" + "="*80)
    print("👥 USERS")
    print("="*80)

    if not users:
        print("  No users found.")
    else:
        user_data = []
        for user in users:
            user_data.append([
                user['user_id'],
                user['username'],
                user['email'] or 'N/A',
                user['created_at'][:19] if user['created_at'] else 'N/A',
                user['last_login'][:19] if user['last_login'] else 'Never',
                '✓' if user['is_active'] else '✗'
            ])

        print(tabulate(user_data,
                      headers=['ID', 'Username', 'Email', 'Created', 'Last Login', 'Active'],
                      tablefmt='grid'))

    conn.close()

def show_passwords(user_id=None, show_encrypted=False):
    """Show password entries (encrypted by default)"""
    conn = connect_db()
    if not conn:
        return

    cursor = conn.cursor()

    if user_id:
        cursor.execute("""
            SELECT entry_id, user_id, website, username,
                   password_encrypted, remarks, is_favorite,
                   created_at, modified_at
            FROM passwords
            WHERE user_id = ?
            ORDER BY website, username
        """, (user_id,))
    else:
        cursor.execute("""
            SELECT entry_id, user_id, website, username,
                   password_encrypted, remarks, is_favorite,
                   created_at, modified_at
            FROM passwords
            ORDER BY user_id, website, username
        """)

    passwords = cursor.fetchall()

    print(f"\n" + "="*120)
    print(f"🔐 PASSWORD ENTRIES" + (f" (User ID: {user_id})" if user_id else " (All Users)"))
    print("="*120)

    if not passwords:
        print("  No password entries found.")
    else:
        password_data = []
        for pwd in passwords:
            encrypted_preview = pwd['password_encrypted'][:20] + "..." if show_encrypted else "[ENCRYPTED]"
            password_data.append([
                pwd['entry_id'],
                pwd['user_id'],
                pwd['website'][:30],
                pwd['username'][:20],
                encrypted_preview if show_encrypted else "[ENCRYPTED]",
                '⭐' if pwd['is_favorite'] else '',
                pwd['created_at'][:19] if pwd['created_at'] else 'N/A'
            ])

        print(tabulate(password_data,
                      headers=['Entry ID', 'User ID', 'Website', 'Username', 'Password', 'Fav', 'Created'],
                      tablefmt='grid'))

        print(f"\nTotal entries: {len(passwords)}")

        if not show_encrypted:
            print("\n💡 Tip: Passwords are encrypted. To see encrypted values, run with --show-encrypted flag")

    conn.close()

def show_metadata():
    """Show database metadata"""
    conn = connect_db()
    if not conn:
        return

    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM database_metadata ORDER BY key")
        metadata = cursor.fetchall()

        print(f"\n" + "="*60)
        print("ℹ️  DATABASE METADATA")
        print("="*60)

        if not metadata:
            print("  No metadata found.")
        else:
            metadata_data = []
            for item in metadata:
                metadata_data.append([
                    item['key'],
                    item['value']
                ])

            print(tabulate(metadata_data,
                          headers=['Key', 'Value'],
                          tablefmt='grid'))

    except sqlite3.Error as e:
        print(f"  ℹ️  No metadata table found (this is normal for older databases)")

    conn.close()

def show_statistics():
    """Show database statistics"""
    conn = connect_db()
    if not conn:
        return

    cursor = conn.cursor()

    print(f"\n" + "="*60)
    print("📈 DATABASE STATISTICS")
    print("="*60)

    # Total users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    # Active users
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
    active_users = cursor.fetchone()[0]

    # Total passwords
    cursor.execute("SELECT COUNT(*) FROM passwords")
    total_passwords = cursor.fetchone()[0]

    # Favorites
    cursor.execute("SELECT COUNT(*) FROM passwords WHERE is_favorite = 1")
    total_favorites = cursor.fetchone()[0]

    # Passwords per user
    cursor.execute("""
        SELECT u.username, COUNT(p.entry_id) as count
        FROM users u
        LEFT JOIN passwords p ON u.user_id = p.user_id
        GROUP BY u.user_id
        ORDER BY count DESC
    """)
    pwd_per_user = cursor.fetchall()

    stats_data = [
        ['Total Users', total_users],
        ['Active Users', active_users],
        ['Total Password Entries', total_passwords],
        ['Favorite Entries', total_favorites]
    ]

    print(tabulate(stats_data, headers=['Metric', 'Count'], tablefmt='grid'))

    if pwd_per_user:
        print(f"\n📊 Passwords per User:")
        user_stats = []
        for row in pwd_per_user:
            user_stats.append([row['username'], row['count']])
        print(tabulate(user_stats, headers=['Username', 'Password Count'], tablefmt='grid'))

    conn.close()

def verify_data_integrity():
    """Verify database integrity"""
    conn = connect_db()
    if not conn:
        return

    cursor = conn.cursor()

    print(f"\n" + "="*60)
    print("🔍 DATA INTEGRITY CHECK")
    print("="*60)

    issues = []

    # Check for orphaned passwords (passwords without users)
    cursor.execute("""
        SELECT COUNT(*) FROM passwords p
        LEFT JOIN users u ON p.user_id = u.user_id
        WHERE u.user_id IS NULL
    """)
    orphaned = cursor.fetchone()[0]
    if orphaned > 0:
        issues.append(f"⚠️  {orphaned} password entries with missing users")

    # Check for NULL encrypted passwords
    cursor.execute("SELECT COUNT(*) FROM passwords WHERE password_encrypted IS NULL OR password_encrypted = ''")
    null_passwords = cursor.fetchone()[0]
    if null_passwords > 0:
        issues.append(f"⚠️  {null_passwords} entries with NULL/empty encrypted passwords")

    # Check database integrity
    cursor.execute("PRAGMA integrity_check")
    integrity = cursor.fetchone()[0]

    if issues:
        print("\n❌ Issues Found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ No data integrity issues found")

    print(f"\n✅ SQLite Integrity Check: {integrity}")

    conn.close()

def interactive_menu():
    """Interactive menu"""
    while True:
        print("\n" + "="*60)
        print("🔐 PASSWORD MANAGER DATABASE VIEWER")
        print("="*60)
        print("\n1. Show all tables")
        print("2. Show table schema")
        print("3. Show users")
        print("4. Show password entries")
        print("5. Show password entries (with encrypted data)")
        print("6. Show database metadata")
        print("7. Show statistics")
        print("8. Verify data integrity")
        print("9. Exit")

        choice = input("\nEnter your choice (1-9): ").strip()

        if choice == '1':
            show_tables()
        elif choice == '2':
            table = input("Enter table name: ").strip()
            show_table_schema(table)
        elif choice == '3':
            show_users()
        elif choice == '4':
            user_id = input("Enter user ID (or press Enter for all): ").strip()
            show_passwords(int(user_id) if user_id else None, show_encrypted=False)
        elif choice == '5':
            user_id = input("Enter user ID (or press Enter for all): ").strip()
            show_passwords(int(user_id) if user_id else None, show_encrypted=True)
        elif choice == '6':
            show_metadata()
        elif choice == '7':
            show_statistics()
        elif choice == '8':
            verify_data_integrity()
        elif choice == '9':
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    import sys

    # Check if tabulate is installed
    try:
        from tabulate import tabulate
    except ImportError:
        print("❌ Error: 'tabulate' module not found.")
        print("Install it with: pip install tabulate")
        sys.exit(1)

    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--tables':
            show_tables()
        elif sys.argv[1] == '--users':
            show_users()
        elif sys.argv[1] == '--passwords':
            show_encrypted = '--show-encrypted' in sys.argv
            show_passwords(show_encrypted=show_encrypted)
        elif sys.argv[1] == '--metadata':
            show_metadata()
        elif sys.argv[1] == '--stats':
            show_statistics()
        elif sys.argv[1] == '--verify':
            verify_data_integrity()
        elif sys.argv[1] == '--help':
            print("\nUsage:")
            print("  python view_database.py              # Interactive mode")
            print("  python view_database.py --tables     # Show all tables")
            print("  python view_database.py --users      # Show users")
            print("  python view_database.py --passwords  # Show passwords")
            print("  python view_database.py --metadata   # Show database metadata")
            print("  python view_database.py --stats      # Show statistics")
            print("  python view_database.py --verify     # Verify integrity")
        else:
            print(f"❌ Unknown option: {sys.argv[1]}")
            print("Run with --help for usage information")
    else:
        # Interactive mode
        interactive_menu()
