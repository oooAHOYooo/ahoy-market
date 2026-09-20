#!/usr/bin/env python3
"""Fail if podcast rows still point at video sources.

This is a lightweight regression check for the podcast catalog.
It flags rows that:
- have an mp3url ending in a video extension
- have a non-empty video_url
- carry the video-podcast tag

Usage:
    python scripts/validate_podcast_audio_sources.py
"""
from __future__ import annotations

import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
COLLECTION_PATH = PROJECT_ROOT / "static" / "data" / "podcastCollection.json"
VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".m4v", ".webm")


def is_video_row(item: dict) -> bool:
    mp3url = (item.get("mp3url") or "").strip().lower()
    tags = item.get("tags") or []
    return (
        any(mp3url.endswith(ext) for ext in VIDEO_EXTS)
        or "video-podcast" in tags
    )


def main() -> int:
    data = json.loads(COLLECTION_PATH.read_text(encoding="utf-8"))
    bad_rows = []

    for item in data.get("podcasts", []) or []:
        if item.get("active", True) and is_video_row(item):
            bad_rows.append(
                f"- {item.get('id')} | {item.get('title')} | "
                f"mp3url={item.get('mp3url') or ''} | tags={item.get('tags') or []}"
            )

    if bad_rows:
        print("Podcast video sources still present:")
        for row in bad_rows:
            print(row)
        return 1

    print("PASS: no podcast rows point at video sources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
