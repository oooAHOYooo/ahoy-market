#!/usr/bin/env python3
"""Convert Poets & Friends #8 videos to MP3. Sources list from DB (content_shows + content_videos).
Requires: ffmpeg, DATABASE_URL or local.db. Usage: poets08_to_mp3.py [--full-only] [--upload] [--output-dir DIR]
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from db import get_session
from models import Show, ContentVideo

OUT_DIR = Path(__file__).resolve().parent / "poets08_mp3_output"
GCS_MP3 = "gs://ahoy-videos/live/poets/poets-08-mp3"
GCS_URL = "https://storage.googleapis.com/ahoy-videos/live/poets/poets-08-mp3"


def items_from_db(full_only: bool):
    """Yield (output_basename, video_url) from DB. Full show first, then chapters by position."""
    with get_session() as session:
        # Full show: content_videos.video_id == poets-and-friends-8 → poets-and-friends-8-full.mp3
        cv = session.query(ContentVideo).filter(
            ContentVideo.video_id == "poets-and-friends-8",
            ContentVideo.url.isnot(None),
        ).first()
        if cv and cv.url:
            yield "poets-and-friends-8-full", cv.url
        if full_only:
            return
        # Chapters: content_shows category poets-and-friends, show_id like poets-and-friends-8%
        shows = session.query(Show).filter(
            Show.category == "poets-and-friends",
            Show.show_id.like("poets-and-friends-8%"),
            Show.video_url != "",
        ).order_by(Show.position, Show.show_id).all()
        for s in shows:
            yield s.show_id, s.video_url


def ffmpeg_to_mp3(url: str, out: Path, timeout: int = 600) -> bool:
    out.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["ffmpeg", "-i", url, "-vn", "-acodec", "libmp3lame", "-q:a", "2", "-y", str(out)],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.returncode == 0 and out.exists() and out.stat().st_size > 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--full-only", action="store_true")
    ap.add_argument("--upload", action="store_true")
    args = ap.parse_args()

    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Need ffmpeg on PATH"); sys.exit(1)

    items = list(items_from_db(args.full_only))
    if not items:
        print("No Poets #8 videos in DB. Run: DATABASE_URL=... python scripts/add_poets08.py"); sys.exit(1)

    failed = []
    for basename, url in items:
        out_mp3 = out_dir / f"{basename}.mp3"
        print(f"\n{basename} ...")
        ok = ffmpeg_to_mp3(url, out_mp3, timeout=3600 if "full" in basename else 600)
        if ok:
            print(f"  OK ({out_mp3.stat().st_size // 1024} KB)")
        else:
            failed.append(basename)
            print("  FAILED")

    if failed:
        print(f"\nFailed: {failed}"); sys.exit(1)
    print(f"\nWrote {len(items)} MP3s to {out_dir}")

    if args.upload:
        mp3s = list(out_dir.glob("*.mp3"))
        if not mp3s: sys.exit(1)
        try:
            subprocess.run(["gsutil", "-m", "cp", "-n"] + [str(f) for f in mp3s] + [f"{GCS_MP3}/"], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"Upload: gsutil -m cp -n {out_dir}/*.mp3 {GCS_MP3}/"); sys.exit(1)
        print(f"Done. e.g. {GCS_URL}/poets-and-friends-8-full.mp3")
    else:
        print(f"Upload: gsutil -m cp -n {out_dir}/*.mp3 {GCS_MP3}/")
        print(f"Then set podcast mp3url/audio_url to {GCS_URL}/<basename>.mp3")


if __name__ == "__main__":
    main()
