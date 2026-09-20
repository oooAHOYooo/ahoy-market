#!/usr/bin/env python3
"""
Quick phone number assignment for testing SMS.
Pre-configured for production database.

Usage:
    python scripts/quick_assign_phones.py alex_g +15551234567
    python scripts/quick_assign_phones.py --list
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Production database
DB_URL = "postgresql://ahoy_postgres_user:mw42b5fByJtur3kTyjXR8quN6xEdkDpd@dpg-d5l90n75r7bs73cjtoh0-a.ohio-postgres.render.com/ahoy_postgres"
os.environ['DATABASE_URL'] = DB_URL

from db import get_session
from models import User


def list_users():
    """Show all users."""
    with get_session() as session:
        users = session.query(User).order_by(User.created_at.desc()).all()

        if not users:
            print("No users found")
            return

        print(f"\n{len(users)} users in database:\n")
        print(f"{'#':<3} {'Username':<20} {'Email':<35} {'Phone':<15}")
        print("-" * 73)

        for i, user in enumerate(users, 1):
            phone = user.phone_number or "[empty]"
            username = user.username or "[unnamed]"
            email = user.email or "[no email]"
            print(f"{i:<3} {username:<20} {email:<35} {phone:<15}")


def assign_phone(username, phone_number):
    """Assign a phone number to a user."""
    with get_session() as session:
        user = session.query(User).filter(User.username == username).first()

        if not user:
            print(f"Error: User '@{username}' not found")
            print("\nRun 'python scripts/quick_assign_phones.py --list' to see available users")
            return False

        user.phone_number = phone_number
        session.commit()

        print(f"✓ Assigned {phone_number} to @{username}")
        return True


def main():
    if len(sys.argv) < 2:
        print("Quick Phone Number Assignment\n")
        print("Usage:")
        print("  python scripts/quick_assign_phones.py USERNAME +1XXXXXXXXXX")
        print("  python scripts/quick_assign_phones.py --list\n")
        print("Examples:")
        print("  python scripts/quick_assign_phones.py conmanrogster01 +15551234567")
        print("  python scripts/quick_assign_phones.py --list")
        sys.exit(1)

    if sys.argv[1] == '--list':
        list_users()
        return

    if len(sys.argv) < 3:
        print("Error: Please provide both username and phone number")
        print("Usage: python scripts/quick_assign_phones.py USERNAME +1XXXXXXXXXX")
        sys.exit(1)

    username = sys.argv[1]
    phone = sys.argv[2]

    # Validate phone format
    if not phone.startswith('+'):
        print("Error: Phone number should start with '+' (e.g., +15551234567)")
        sys.exit(1)

    if not phone[1:].isdigit():
        print("Error: Phone number should contain only digits after '+'")
        sys.exit(1)

    assign_phone(username, phone)


if __name__ == "__main__":
    main()
