#!/usr/bin/env python3
"""
Assign phone numbers to existing users for SMS testing.

Usage:
    # Interactively add phone numbers
    python scripts/assign_phone_numbers.py

    # Add from CSV (username,phone format)
    python scripts/assign_phone_numbers.py --csv users.csv

    # Query users with/without phone numbers
    python scripts/assign_phone_numbers.py --list
    python scripts/assign_phone_numbers.py --list-no-phone
"""

import sys
import os
import argparse
import csv
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import get_session
from models import User


def list_users_with_phone():
    """List all users that have phone numbers."""
    with get_session() as session:
        users = session.query(User.id, User.username, User.email, User.phone_number).filter(
            User.phone_number.isnot(None)
        ).order_by(User.created_at.desc()).all()

        if not users:
            print("No users with phone numbers yet")
            return

        print(f"\n{len(users)} users with phone numbers:\n")
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Phone':<15}")
        print("-" * 70)
        for user_id, username, email, phone in users:
            print(f"{user_id:<5} {username:<20} {email:<30} {phone:<15}")


def list_users_without_phone():
    """List all users that don't have phone numbers."""
    with get_session() as session:
        users = session.query(User.id, User.username, User.email).filter(
            User.phone_number.isnull()
        ).order_by(User.created_at.desc()).all()

        if not users:
            print("All users have phone numbers!")
            return

        print(f"\n{len(users)} users without phone numbers:\n")
        print(f"{'ID':<5} {'Username':<20} {'Email':<30}")
        print("-" * 55)
        for user_id, username, email in users:
            print(f"{user_id:<5} {username:<20} {email:<30}")


def assign_phone_interactive():
    """Interactively assign phone numbers to users."""
    print("\n=== Assign Phone Numbers to Users ===\n")
    print("Enter username and phone number. Leave username blank to quit.\n")

    assignments = []

    while True:
        username = input("Username (or 'quit'): ").strip()
        if not username or username.lower() == 'quit':
            break

        phone = input("Phone number (e.g., +15551234567): ").strip()
        if not phone:
            print("  Skipped (no phone number)\n")
            continue

        assignments.append((username, phone))
        print(f"  Added: {username} -> {phone}\n")

    if not assignments:
        print("No assignments made")
        return

    # Confirm before applying
    print(f"\nReady to assign {len(assignments)} phone numbers:")
    for username, phone in assignments:
        print(f"  {username}: {phone}")

    confirm = input("\nApply changes? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Cancelled")
        return

    # Apply to database
    with get_session() as session:
        for username, phone in assignments:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                print(f"  ERROR: User '{username}' not found")
                continue

            user.phone_number = phone
            session.commit()
            print(f"  OK: {username}")

    print(f"\n✓ Assigned {len(assignments)} phone numbers")


def assign_from_csv(csv_path):
    """Assign phone numbers from CSV file (username,phone)."""
    if not os.path.exists(csv_path):
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)

    assignments = []
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        for row_num, row in enumerate(reader, start=1):
            if len(row) < 2:
                print(f"Warning: Row {row_num} has fewer than 2 columns, skipping")
                continue

            username = row[0].strip()
            phone = row[1].strip()

            if not username or not phone:
                print(f"Warning: Row {row_num} has empty fields, skipping")
                continue

            assignments.append((username, phone))

    if not assignments:
        print("No valid assignments found in CSV")
        sys.exit(1)

    print(f"\nFound {len(assignments)} assignments:")
    for username, phone in assignments[:5]:
        print(f"  {username}: {phone}")
    if len(assignments) > 5:
        print(f"  ... and {len(assignments) - 5} more")

    confirm = input("\nApply these assignments? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Cancelled")
        sys.exit(0)

    # Apply to database
    applied = 0
    errors = 0

    with get_session() as session:
        for username, phone in assignments:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                print(f"  ERROR: User '{username}' not found")
                errors += 1
                continue

            user.phone_number = phone
            session.commit()
            applied += 1

    print(f"\n✓ Applied {applied} assignments")
    if errors:
        print(f"✗ {errors} errors")


def main():
    parser = argparse.ArgumentParser(
        description="Assign phone numbers to existing users"
    )
    parser.add_argument("--list", action="store_true", help="List users with phone numbers")
    parser.add_argument("--list-no-phone", action="store_true", help="List users without phone numbers")
    parser.add_argument("--csv", help="CSV file with username,phone pairs")

    args = parser.parse_args()

    if args.list:
        list_users_with_phone()
    elif args.list_no_phone:
        list_users_without_phone()
    elif args.csv:
        assign_from_csv(args.csv)
    else:
        assign_phone_interactive()


if __name__ == "__main__":
    main()
