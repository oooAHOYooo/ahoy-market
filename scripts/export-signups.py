#!/usr/bin/env python3
"""
Export production signup data to CSV for lightweight tracking.
Usage: DATABASE_URL=<prod_url> python scripts/export-signups.py
"""
import os
import sys
import csv
from datetime import datetime
from pathlib import Path

# Add parent dir to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text

def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    engine = create_engine(db_url)

    # Query production users
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, username, email, created_at
            FROM users
            ORDER BY created_at DESC
        """))
        rows = result.fetchall()

    # Export to CSV
    csv_path = Path(__file__).parent.parent / "signups.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Username", "Email", "Created At", "Export Date"])
        for row in rows:
            writer.writerow([row[0], row[1], row[2], row[3], datetime.now().isoformat()])

    # Print summary
    total = len(rows)
    today = datetime.now().date()
    today_count = sum(1 for row in rows if row[3].date() == today)
    week_count = sum(1 for row in rows if (today - row[3].date()).days < 7)

    print(f"✓ Exported {total} users to signups.csv")
    print(f"  Today: {today_count} | Last 7 days: {week_count}")

if __name__ == "__main__":
    main()
