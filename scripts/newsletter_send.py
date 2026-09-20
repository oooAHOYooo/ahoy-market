#!/usr/bin/env python3
"""
newsletter_send.py — Send a newsletter HTML file to subscribers via Resend.

Usage:
  python scripts/newsletter_send.py newsletters/2026-may.html
  python scripts/newsletter_send.py newsletters/2026-may.html --to alex@ahoy.ooo
  python scripts/newsletter_send.py newsletters/2026-may.html --dry-run
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-16"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from services.emailer import send_email, can_send_email

REPO_ROOT        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBSCRIBERS_JSON = os.path.join(REPO_ROOT, "static", "data", "newsletter_subscribers.json")


def extract_subject(html: str) -> str:
    # Strip HTML comments first so we don't match <title> text inside them
    no_comments = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    m = re.search(r"<title[^>]*>(.*?)</title>", no_comments, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else "What's New at Ahoy"


def html_to_text(html: str) -> str:
    # Strip style/script blocks
    text = re.sub(r"<(style|script)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Replace block elements with newlines
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?(p|div|tr|td|li|h[1-6])[^>]*>", "\n", text, flags=re.IGNORECASE)
    # Strip all remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode common entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">") \
               .replace("&mdash;", "—").replace("&ndash;", "–") \
               .replace("&middot;", "·").replace("&rarr;", "→") \
               .replace("&nbsp;", " ").replace("&#8594;", "→") \
               .replace("&#9875;", "⚓").replace("&#8226;", "•")
    # Collapse whitespace
    lines = [ln.strip() for ln in text.splitlines()]
    # Remove consecutive blank lines
    out = []
    prev_blank = False
    for ln in lines:
        if not ln:
            if not prev_blank:
                out.append("")
            prev_blank = True
        else:
            out.append(ln)
            prev_blank = False
    return "\n".join(out).strip()


def load_subscribers():
    import json
    try:
        with open(SUBSCRIBERS_JSON, encoding="utf-8") as f:
            data = json.load(f)
        return [s for s in data.get("subscribers", []) if s.get("status") == "active"]
    except FileNotFoundError:
        return []


def main():
    parser = argparse.ArgumentParser(
        description="Send a newsletter HTML file to subscribers"
    )
    parser.add_argument("file", help="Path to the newsletter HTML file")
    parser.add_argument("--to", default=None,
                        help="Comma-separated emails (overrides subscriber list)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be sent without actually sending")
    args = parser.parse_args()

    # Read the HTML file
    if not os.path.isabs(args.file):
        html_path = os.path.join(REPO_ROOT, args.file)
    else:
        html_path = args.file

    if not os.path.exists(html_path):
        print(f"ERROR: File not found: {html_path}")
        sys.exit(1)

    with open(html_path, encoding="utf-8") as f:
        html = f.read()

    subject = extract_subject(html)
    text    = html_to_text(html)

    # Recipients
    if args.to:
        recipients = [{"email": e.strip(), "name": ""} for e in args.to.split(",") if e.strip()]
    else:
        recipients = load_subscribers()

    print(f"\n  File     : {os.path.basename(html_path)}")
    print(f"  Subject  : {subject}")
    print(f"  To       : {len(recipients)} recipient(s)")

    if not recipients:
        print(f"\nNo active subscribers. Add emails to: {SUBSCRIBERS_JSON}")
        print("Or use: --to someone@example.com")
        sys.exit(1)

    for r in recipients:
        print(f"           • {r['email']}")

    if args.dry_run:
        print("\n  [dry-run] Nothing sent.\n")
        return

    if not can_send_email():
        print("\nEmail not configured — set RESEND_API_KEY in your .env file.")
        sys.exit(1)

    confirm = input(f"\nSend to {len(recipients)} subscriber(s)? [y/N] ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    print()
    ok_count = fail_count = 0
    for r in recipients:
        result = send_email(r["email"], subject, text, html)
        if result.get("ok"):
            print(f"  ✓ {r['email']}")
            ok_count += 1
        else:
            print(f"  ✗ {r['email']}  ({result.get('detail')})")
            fail_count += 1

    print(f"\n  Done — {ok_count} sent, {fail_count} failed.\n")


if __name__ == "__main__":
    main()
