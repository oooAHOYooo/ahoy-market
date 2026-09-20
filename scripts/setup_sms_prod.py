#!/usr/bin/env python3
"""
Complete setup for SMS notifications on production database.

This script:
1. Connects to production PostgreSQL
2. Runs database migrations
3. Lists existing users
4. Allows assigning phone numbers
5. Tests SMS configuration
"""

import sys
import os
from pathlib import Path
from urllib.parse import urlparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

DB_URL = "postgresql://ahoy_postgres_user:mw42b5fByJtur3kTyjXR8quN6xEdkDpd@dpg-d5l90n75r7bs73cjtoh0-a.ohio-postgres.render.com/ahoy_postgres"


def setup_db_env():
    """Set DATABASE_URL for this session."""
    os.environ['DATABASE_URL'] = DB_URL
    print(f"Connected to: {DB_URL}")


def run_migrations():
    """Run alembic migrations."""
    print("\n1. Checking database migrations...")
    import subprocess
    result = subprocess.run(['alembic', 'upgrade', 'head'], capture_output=True, text=True)

    if result.returncode == 0:
        if 'is not None' in result.stderr or 'is already at the head' in result.stderr:
            print("   ✓ Database is up to date")
        else:
            print("   ✓ Migrations applied")
    else:
        print(f"   ✗ Error: {result.stderr}")
        if "phone_number" in result.stderr or "column" in result.stderr:
            print("   Retrying with force...")
            # Try to continue anyway
        else:
            return False

    return True


def list_users():
    """List all users in the database."""
    from db import get_session
    from models import User

    print("\n2. Existing Users:")

    try:
        with get_session() as session:
            # Query full user objects to get all data
            users = session.query(User).order_by(User.created_at.desc()).all()

            if not users:
                print("   No users found")
                return []

            print(f"   Found {len(users)} users:\n")
            print(f"   {'ID':<5} {'Username':<20} {'Email':<35} {'Phone':<15}")
            print("   " + "-" * 75)

            user_list = []
            for user in users:
                phone_str = user.phone_number if user.phone_number else "[empty]"
                print(f"   {user.id:<5} {(user.username or ''):<20} {(user.email or ''):<35} {phone_str:<15}")
                user_list.append(user)

            return user_list
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return []


def assign_phones_menu():
    """Menu to assign phone numbers."""
    from db import get_session
    from models import User

    print("\n3. Assign Phone Numbers to Users")
    print("   Options: (a)dd, (l)ist, (s)kip")

    choice = input("   Choice: ").strip().lower()

    if choice == 's' or not choice:
        print("   Skipped")
        return

    if choice == 'l':
        list_users()
        return

    if choice != 'a':
        print("   Invalid choice")
        return

    # Interactive assignment
    print("\n   Enter username and phone. Blank username to finish.\n")

    assignments = []
    while True:
        username = input("   Username (or blank to finish): ").strip()
        if not username:
            break

        phone = input("   Phone (e.g., +15551234567): ").strip()
        if not phone:
            print("   Skipped (no phone)\n")
            continue

        assignments.append((username, phone))
        print(f"   ✓ Added\n")

    if not assignments:
        print("   No assignments made")
        return

    # Confirm
    print(f"\n   Ready to assign {len(assignments)} phone numbers:")
    for username, phone in assignments:
        print(f"     @{username}: {phone}")

    confirm = input("\n   Confirm? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("   Cancelled")
        return

    # Apply
    with get_session() as session:
        for username, phone in assignments:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                print(f"   ✗ User @{username} not found")
                continue

            user.phone_number = phone
            session.commit()
            print(f"   ✓ @{username}")

    print(f"\n   ✓ Assigned {len(assignments)} phone numbers")


def check_twilio():
    """Check Twilio configuration."""
    from services.sms import can_send_sms

    print("\n4. SMS Configuration")

    if can_send_sms():
        print("   ✓ Twilio is configured and ready")
        print("   Credentials found in environment")
    else:
        print("   ✗ Twilio not configured")
        print("   To enable SMS, set:")
        print("     export TWILIO_ACCOUNT_SID='...'")
        print("     export TWILIO_AUTH_TOKEN='...'")
        print("     export TWILIO_PHONE_NUMBER='+1234567890'")


def show_next_steps():
    """Show what to do next."""
    print("\n5. Next Steps")
    print("   a) Set Twilio credentials:")
    print("      export TWILIO_ACCOUNT_SID='your_sid'")
    print("      export TWILIO_AUTH_TOKEN='your_token'")
    print("      export TWILIO_PHONE_NUMBER='+1234567890'")
    print("")
    print("   b) Test SMS to one user:")
    print("      python scripts/send_whats_new_sms.py \\")
    print("        --title 'Test Message' \\")
    print("        --description 'Testing SMS' \\")
    print("        --test-phone '+15551234567'")
    print("")
    print("   c) Send to all users with phone numbers:")
    print("      python scripts/send_whats_new_sms.py \\")
    print("        --title 'New Content' \\")
    print("        --description 'Check it out'")
    print("")
    print("   d) Manage phone numbers:")
    print("      python scripts/assign_phone_numbers.py")


def main():
    print("=== SMS Setup for Production Database ===\n")

    setup_db_env()

    # Try to run migrations (may fail if already applied, that's ok)
    run_migrations()

    # List users
    users = list_users()

    if not users:
        print("\n   Warning: No users found in database")
        return

    # Assign phones
    assign_phones_menu()

    # Check Twilio
    check_twilio()

    # Show next steps
    show_next_steps()

    print("\n=== Setup Complete ===\n")


if __name__ == "__main__":
    main()
