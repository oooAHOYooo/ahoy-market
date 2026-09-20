#!/usr/bin/env python3
"""
Quick Twilio setup tester.

Tests:
1. Credentials are set
2. Connection works
3. Can send a test SMS
"""

import os
import sys

def check_credentials():
    """Check if Twilio credentials are set."""
    print("1. Checking Twilio credentials...\n")

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    phone_from = os.getenv("TWILIO_PHONE_NUMBER")

    if not account_sid:
        print("   ✗ TWILIO_ACCOUNT_SID not set")
        return False

    if not auth_token:
        print("   ✗ TWILIO_AUTH_TOKEN not set")
        return False

    if not phone_from:
        print("   ✗ TWILIO_PHONE_NUMBER not set")
        return False

    print(f"   ✓ TWILIO_ACCOUNT_SID: {account_sid[:20]}...")
    print(f"   ✓ TWILIO_AUTH_TOKEN: {auth_token[:20]}...")
    print(f"   ✓ TWILIO_PHONE_NUMBER: {phone_from}")

    return True


def test_connection():
    """Test connection to Twilio."""
    print("\n2. Testing Twilio connection...\n")

    try:
        from twilio.rest import Client

        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")

        client = Client(account_sid, auth_token)
        account = client.api.accounts(account_sid).fetch()

        print(f"   ✓ Connected to Twilio")
        print(f"   ✓ Account: {account.friendly_name}")
        print(f"   ✓ Status: {account.status}")

        return True
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        return False


def test_sms(to_phone):
    """Test sending SMS."""
    print(f"\n3. Sending test SMS to {to_phone}...\n")

    try:
        from twilio.rest import Client

        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        phone_from = os.getenv("TWILIO_PHONE_NUMBER")

        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body="⚓ AHOY ⚓\nTest SMS from Twilio\nEverything works!",
            from_=phone_from,
            to=to_phone,
        )

        print(f"   ✓ SMS sent!")
        print(f"   ✓ Message SID: {message.sid}")
        print(f"   ✓ Status: {message.status}")
        print(f"\n   The recipient should receive this SMS shortly.")
        print(f"   (Make sure their number is verified in Twilio!)")

        return True
    except Exception as e:
        error_msg = str(e)
        print(f"   ✗ SMS failed: {e}")

        if "unverified" in error_msg.lower():
            print(f"\n   💡 Hint: The number {to_phone} is not verified.")
            print(f"   Go to: https://www.twilio.com/console/phone-numbers/verified")
            print(f"   Add this number and have them confirm the code.")

        return False


def main():
    print("=" * 60)
    print("Twilio Setup Tester")
    print("=" * 60)

    # Check credentials
    if not check_credentials():
        print("\n✗ Missing credentials!")
        print("\nSet them with:")
        print('  export TWILIO_ACCOUNT_SID="AC..."')
        print('  export TWILIO_AUTH_TOKEN="..."')
        print('  export TWILIO_PHONE_NUMBER="+1..."')
        sys.exit(1)

    # Test connection
    if not test_connection():
        print("\n✗ Could not connect to Twilio")
        print("Check your credentials and try again")
        sys.exit(1)

    # Test SMS
    if len(sys.argv) > 1:
        to_phone = sys.argv[1]
        if not to_phone.startswith("+"):
            print(f"\nError: Phone number must start with + (e.g., +15551234567)")
            sys.exit(1)

        test_sms(to_phone)
    else:
        print("\n3. Send test SMS?\n")
        print("   Run: python scripts/test_twilio.py +15551234567")
        print("   (Use a verified phone number)")

    print("\n" + "=" * 60)
    print("Setup looks good! ✓")
    print("=" * 60)


if __name__ == "__main__":
    main()
