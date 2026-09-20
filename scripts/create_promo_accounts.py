#!/usr/bin/env python3
"""
Create promo login accounts with strong temporary passwords.

Usage:
  python scripts/create_promo_accounts.py --count 25 --prefix nightmarket --output /tmp/ahoy-nightmarket-accounts.csv

The script creates new users only. It never deletes or resets existing accounts.
"""

import argparse
import csv
import os
import secrets
import string
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


PASSWORD_ALPHABET = string.ascii_letters + string.digits + "!@#$%+_-"


def make_password(length: int = 16) -> str:
    while True:
        password = "".join(secrets.choice(PASSWORD_ALPHABET) for _ in range(length))
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in "!@#$%+_-" for c in password)
        ):
            return password


def clean_prefix(raw: str) -> str:
    prefix = "".join(c.lower() for c in raw.strip() if c.isalnum() or c == "_").strip("_")
    return prefix or "promo"


def next_username(session, user_model, prefix: str, index: int) -> str:
    n = index
    while True:
        username = f"{prefix}{n:03d}"
        exists = session.query(user_model.id).filter(user_model.username == username).first()
        if not exists:
            return username
        n += 1


def parse_args():
    parser = argparse.ArgumentParser(description="Create Ahoy promo accounts with temporary passwords.")
    parser.add_argument("--count", type=int, required=True, help="Number of accounts to create.")
    parser.add_argument("--prefix", default="promo", help="Username prefix, for example nightmarket.")
    parser.add_argument("--email-domain", default="promo.ahoy.ooo", help="Placeholder email domain.")
    parser.add_argument("--display-prefix", default="Ahoy Guest", help="Display name prefix.")
    parser.add_argument("--login-url", default="https://app.ahoy.ooo/login", help="Login URL to include in the CSV.")
    parser.add_argument("--password-length", type=int, default=16, help="Temporary password length.")
    parser.add_argument("--output", required=True, help="CSV path for generated credentials.")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.count < 1:
        raise SystemExit("--count must be at least 1")
    if args.password_length < 12:
        raise SystemExit("--password-length must be at least 12")

    prefix = clean_prefix(args.prefix)[:21]
    email_domain = args.email_domain.strip().lower().lstrip("@")
    login_url = args.login_url.strip() or "https://app.ahoy.ooo/login"
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    from db import get_session
    from models import User
    from utils.security import hash_password

    rows = []
    with get_session() as session:
        for i in range(1, args.count + 1):
            username = next_username(session, User, prefix, i)
            password = make_password(args.password_length)
            email = f"{username}@{email_domain}"
            user = User(
                username=username,
                email=email,
                password_hash=hash_password(password),
                display_name=f"{args.display_prefix} {i}",
            )
            session.add(user)
            session.flush()
            rows.append({
                "id": user.id,
                "username": username,
                "email": email,
                "temporary_password": password,
                "login_url": login_url,
                "instructions": "Sign in, open Account, then change this temporary password.",
            })
        session.commit()

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "username", "email", "temporary_password", "login_url", "instructions"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Created {len(rows)} promo account(s).")
    print(f"Credential CSV: {output_path}")
    print("Users can sign in with username + temporary password, then change it on Account.")


if __name__ == "__main__":
    main()
