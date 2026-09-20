#!/usr/bin/env python3
"""
Send SMS notifications for a new "what's new" item.

Usage:
    python scripts/send_whats_new_sms.py --title "New Video" --description "Check out..." --link "https://..."
    python scripts/send_whats_new_sms.py --title "New Video" --description "Check out..."
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import get_session
from models import User
from services.sms import notify_whats_new_sms, can_send_sms


def get_sms_subscribers() -> list[tuple[str, str]]:
    """Get all users with phone numbers who have opted in for notifications."""
    with get_session() as session:
        # Get all users with phone numbers
        users = session.query(User.username, User.phone_number).filter(
            User.phone_number.isnot(None),
            User.disabled == False
        ).all()
        return [(username, phone) for username, phone in users if phone]


def main():
    parser = argparse.ArgumentParser(
        description="Send SMS notifications for a new what's new item"
    )
    parser.add_argument("--title", required=True, help="Title of the new item")
    parser.add_argument("--description", required=True, help="Description of the item")
    parser.add_argument("--link", help="Link to view the item (defaults to ahoy.ooo/whats-new)")
    parser.add_argument("--test-phone", help="Send only to this test phone number (for testing)")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually send, just show what would be sent")
    parser.add_argument("--no-art", action="store_true", help="Don't include ASCII art header")

    args = parser.parse_args()

    # Default link to what's new page
    link = args.link or "https://ahoy.ooo/whats-new"
    use_art = not args.no_art

    if not can_send_sms():
        print("Error: SMS not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER")
        sys.exit(1)

    # Get recipients
    if args.test_phone:
        recipients = [args.test_phone]
        print(f"Test mode: sending to {args.test_phone}")
    else:
        subscribers = get_sms_subscribers()
        recipients = [phone for _, phone in subscribers]
        print(f"Found {len(recipients)} users with phone numbers")

    if not recipients:
        print("No recipients found")
        sys.exit(0)

    # Show preview
    if use_art:
        message = "⚓ AHOY ⚓\n"
    else:
        message = ""

    message += f"{args.title}\n{args.description[:50]}..."
    if link:
        message += f"\n{link}"

    print(f"\nMessage preview ({len(message)} chars):")
    print("-" * 40)
    print(message)
    print("-" * 40)

    if args.dry_run:
        print(f"\nDry run: would send to {len(recipients)} recipients")
        sys.exit(0)

    # Confirm
    if not args.test_phone:
        response = input(f"\nSend to {len(recipients)} recipients? (yes/no): ").strip().lower()
        if response != "yes":
            print("Cancelled")
            sys.exit(0)

    # Send
    print("\nSending...")
    result = notify_whats_new_sms(
        item_title=args.title,
        item_description=args.description,
        recipients=recipients,
        link=link,
        use_art=use_art
    )

    print(f"\nResult:")
    print(f"  Sent: {result['sent']}")
    print(f"  Failed: {result['failed']}")
    if result['errors']:
        print(f"  Errors: {result['errors'][:5]}")  # Show first 5 errors

    sys.exit(0 if result['failed'] == 0 else 1)


if __name__ == "__main__":
    main()
