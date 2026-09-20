#!/usr/bin/env python3
"""
Sync Claude Code memory for this project (pull + commit + push).

Memory lives at:
  ~/.claude/projects/-Users-agworkywork-ahoy-little-platform/memory/

This wraps the existing sync-memory.sh script and prints a clear
timestamp confirmation so you can tell at a glance when the last
sync happened on this machine.

Usage:
    python sync.py
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MEMORY_DIR = Path.home() / ".claude" / "projects" / "-Users-agworkywork-ahoy-little-platform" / "memory"
SYNC_SCRIPT = MEMORY_DIR / "sync-memory.sh"
STAMP_FILE = MEMORY_DIR / "LAST_SYNC.txt"


def main() -> int:
    if not MEMORY_DIR.exists():
        print(f"✗ Memory directory not found: {MEMORY_DIR}")
        print("  On a new machine, clone it first:")
        print(f"    git clone git@github.com:oooAHOYooo/ahoy-memory.git {MEMORY_DIR}")
        return 1

    if not SYNC_SCRIPT.exists():
        print(f"✗ sync-memory.sh missing at {SYNC_SCRIPT}")
        return 1

    host = socket.gethostname().split(".")[0]
    started_at = datetime.now(timezone.utc).astimezone()

    STAMP_FILE.write_text(
        f"last_sync_started: {started_at.isoformat(timespec='seconds')}\n"
        f"host: {host}\n"
    )

    result = subprocess.run(
        ["bash", str(SYNC_SCRIPT)],
        cwd=str(MEMORY_DIR),
    )

    if result.returncode != 0:
        print(f"\n✗ sync failed (exit {result.returncode})")
        return result.returncode

    finished_at = datetime.now(timezone.utc).astimezone()
    STAMP_FILE.write_text(
        f"last_sync: {finished_at.isoformat(timespec='seconds')}\n"
        f"host: {host}\n"
    )

    print()
    print("─" * 48)
    print(f"  Memory synced at {finished_at.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"  Host: {host}")
    print(f"  Remote: github.com/oooAHOYooo/ahoy-memory")
    print("─" * 48)
    return 0


if __name__ == "__main__":
    sys.exit(main())
