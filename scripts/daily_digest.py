#!/usr/bin/env python3
"""
Digest email — sent to alex@ahoy.ooo at 6am, 12pm, and 6pm UTC.

Each run shows stats from midnight UTC to now (running tally for the day):
  - Active users so far today
  - New signups (with names/emails)
  - Boosts received
  - Merch purchases
  - Running totals

Usage:
    python scripts/daily_digest.py
    python scripts/daily_digest.py --dry-run   # Print email without sending
"""
import os
import sys
import argparse
from decimal import Decimal
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_session
from models import User, Tip, Purchase
from services.emailer import send_email, can_send_email

DIGEST_TO = "alex@ahoy.ooo"


def _time_label(now: datetime) -> str:
    hour = now.hour
    if hour < 9:
        return "Morning Update"
    elif hour < 15:
        return "Midday Update"
    else:
        return "Evening Recap"


def build_digest(day_start: datetime, day_end: datetime) -> str:
    date_label = day_start.strftime("%A, %B %-d %Y")
    time_label = _time_label(day_end)

    with get_session() as db:
        # --- New signups ---
        new_users = (
            db.query(User)
            .filter(User.created_at >= day_start, User.created_at < day_end)
            .order_by(User.created_at)
            .all()
        )

        # --- Active users (last_active_at touched today) ---
        active_count = (
            db.query(User)
            .filter(User.last_active_at >= day_start, User.last_active_at < day_end)
            .count()
        )

        # --- Total users ever ---
        total_users = db.query(User).count()

        # --- Boosts today ---
        boosts_today = (
            db.query(Tip)
            .filter(Tip.created_at >= day_start, Tip.created_at < day_end)
            .all()
        )
        boost_count = len(boosts_today)
        boost_total = sum(t.total_paid or t.amount or Decimal("0") for t in boosts_today)

        # --- Merch purchases today ---
        merch_today = (
            db.query(Purchase)
            .filter(
                Purchase.created_at >= day_start,
                Purchase.created_at < day_end,
                Purchase.type == "merch",
            )
            .all()
        )
        merch_count = len(merch_today)
        merch_total = sum(getattr(p, "amount", None) or Decimal("0") for p in merch_today)

    # --- Build email ---
    window_label = f"midnight–{day_end.strftime('%-I:%M %p')} UTC"
    lines = [
        f"Ahoy {time_label} — {date_label}",
        "=" * 48,
        f"  ({window_label})",
        "",
        f"  Active users so far:  {active_count}",
        f"  New signups:          {len(new_users)}",
        f"  Total members:        {total_users}",
        "",
    ]

    if new_users:
        lines.append("New signups:")
        for u in new_users:
            ts = u.created_at.strftime("%H:%M UTC") if u.created_at else "?"
            lines.append(f"  {ts}  @{u.username or 'unknown'}  ({u.email})")
        lines.append("")

    lines += [
        "Activity:",
        f"  Boosts:   {boost_count}  (${boost_total:.2f} total)",
        f"  Merch:    {merch_count}  (${merch_total:.2f} total)",
        "",
    ]

    if not new_users and active_count == 0 and boost_count == 0 and merch_count == 0:
        lines.append("Quiet day — no activity recorded.")
        lines.append("")

    lines.append("— Ahoy bot")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print without sending")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = now

    body = build_digest(day_start, day_end)

    if args.dry_run:
        print(body)
        return

    if "no activity" in body:
        print("No activity since midnight — skipping email.")
        return

    if not can_send_email():
        print("ERROR: Email not configured (RESEND_API_KEY or SMTP required).")
        sys.exit(1)

    time_label = _time_label(now)
    date_label = now.strftime("%b %-d")
    subject = f"Ahoy {time_label} — {date_label}"

    result = send_email(DIGEST_TO, subject, body)
    if result.get("ok"):
        print(f"Digest sent to {DIGEST_TO}")
    else:
        print(f"Failed to send digest: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()
