#!/usr/bin/env python3
"""
Re-extract thumbnails at 40 seconds for CJ, Samuel Chen, Ellen Martin, Dan Carbonella.
Overwrites the existing thumbnail files in-place (DB paths unchanged).
"""
import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from db import get_session
from models import Show

THUMBNAILS_DIR = PROJECT_ROOT / "static" / "thumbnails"
SEEK_SECONDS = 40

TARGET_SHOW_IDS = [
    "poets-and-friends-8-part-9-ellen-martin",
    "poets-and-friends-8-part-10-samuel-chen",
    "poets-and-friends-8-part-12-cj",
    "poets-and-friends-8-part-13-dan-carbonella",
]


def extract_frame(video_url, output_path, seek=SEEK_SECONDS):
    cmd = [
        "ffmpeg",
        "-ss", str(seek),
        "-i", video_url,
        "-vframes", "1",
        "-q:v", "2",
        "-vf", "scale=1280:-1",
        "-y",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    return result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0


def main():
    with get_session() as session:
        shows = session.query(Show).filter(Show.show_id.in_(TARGET_SHOW_IDS)).all()
        found = {s.show_id: s for s in shows}

        for sid in TARGET_SHOW_IDS:
            s = found.get(sid)
            if not s:
                print(f"  NOT FOUND: {sid}")
                continue
            if not s.video_url:
                print(f"  NO URL: {s.title}")
                continue
            if not s.thumbnail:
                print(f"  NO THUMBNAIL PATH: {s.title}")
                continue

            # Thumbnail path is like /static/thumbnails/foo.jpg
            filename = Path(s.thumbnail).name
            out_path = THUMBNAILS_DIR / filename

            print(f"Processing: {s.title} (seek={SEEK_SECONDS}s) → {filename}")
            if extract_frame(s.video_url, out_path):
                print(f"  ✓ Updated: {filename}")
            else:
                print(f"  ✗ Failed — check video URL: {s.video_url[:80]}")

    print("Done.")


if __name__ == "__main__":
    main()
