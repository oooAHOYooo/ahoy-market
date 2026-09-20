#!/usr/bin/env python3
"""Convert video-backed podcast items to MP3 and optionally upload to GCS.

This script is intentionally conservative:
- It detects podcast rows whose source URL is a video file or that carry a
  `video_url` / `video-podcast` marker.
- It extracts audio with ffmpeg.
- It uploads the MP3s to Google Cloud Storage when requested.
- It does not rewrite podcastCollection.json unless --write-json is passed.

Default GCS target:
    gs://ahoy-podcast-collection/podcasts/converted

Usage:
    python scripts/convert_podcast_videos_to_audio.py --dry-run
    python scripts/convert_podcast_videos_to_audio.py --upload
    python scripts/convert_podcast_videos_to_audio.py --upload --write-json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
COLLECTION_PATH = PROJECT_ROOT / "static" / "data" / "podcastCollection.json"
DEFAULT_BUCKET = "ahoy-podcast-collection"
DEFAULT_PREFIX = "podcasts/converted"
VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".m4v", ".webm")


def slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"['’]", "", value)
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "episode"


def load_collection() -> dict:
    with COLLECTION_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_collection(data: dict) -> None:
    with COLLECTION_PATH.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def is_video_source(item: dict) -> bool:
    mp3url = (item.get("mp3url") or "").strip().lower()
    video_url = (item.get("video_url") or "").strip()
    tags = item.get("tags") or []
    return (
        any(mp3url.endswith(ext) for ext in VIDEO_EXTS)
        or bool(video_url)
        or "video-podcast" in tags
    )


def detect_candidates(collection: dict) -> list[dict]:
    candidates = []
    for item in collection.get("podcasts", []) or []:
        if not item.get("active", True):
            continue
        if is_video_source(item):
            candidates.append(item)
    return candidates


def output_name(item: dict) -> str:
    show_slug = item.get("show_slug") or "podcast"
    episode_id = item.get("id") or item.get("title") or "episode"
    return f"{slugify(show_slug)}-{slugify(str(episode_id))}.mp3"


def ffmpeg_extract_audio(source_url: str, out_path: Path, timeout: int = 3600) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        source_url,
        "-vn",
        "-acodec",
        "libmp3lame",
        "-q:a",
        "2",
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0 or not out_path.exists() or out_path.stat().st_size == 0:
        stderr = (result.stderr or "").strip()
        raise RuntimeError(f"ffmpeg failed for {source_url}\n{stderr[-2000:]}")


def gcs_upload(local_file: Path, bucket: str, prefix: str) -> str:
    if shutil.which("gsutil") is None and shutil.which("gcloud") is None:
        raise RuntimeError("Need gsutil or gcloud on PATH for upload")

    prefix = prefix.strip("/")
    remote = f"gs://{bucket}/{prefix}/{local_file.name}"

    if shutil.which("gsutil") is not None:
        subprocess.run(["gsutil", "cp", str(local_file), remote], check=True)
    else:
        subprocess.run(["gcloud", "storage", "cp", str(local_file), remote], check=True)

    return f"https://storage.googleapis.com/{bucket}/{prefix}/{local_file.name}"


def build_source_url(item: dict) -> str:
    return (item.get("video_url") or item.get("mp3url") or "").strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Print candidates without converting")
    ap.add_argument("--upload", action="store_true", help="Upload MP3s to GCS after conversion")
    ap.add_argument("--write-json", action="store_true", help="Rewrite static/data/podcastCollection.json with new mp3url values")
    ap.add_argument("--bucket", default=os.getenv("AHOY_PODCAST_GCS_BUCKET", DEFAULT_BUCKET))
    ap.add_argument("--prefix", default=os.getenv("AHOY_PODCAST_GCS_PREFIX", DEFAULT_PREFIX))
    ap.add_argument("--temp-dir", type=Path, default=None)
    args = ap.parse_args()

    collection = load_collection()
    candidates = detect_candidates(collection)

    print(f"Podcast rows in file: {len(collection.get('podcasts', []) or [])}")
    print(f"Video-backed candidates: {len(candidates)}")
    for item in candidates:
        source = build_source_url(item)
        print(f"- {item.get('id')} | {item.get('title')} | {source}")

    if args.dry_run:
        return 0

    if not candidates:
        return 0

    temp_dir_ctx = tempfile.TemporaryDirectory(dir=str(args.temp_dir) if args.temp_dir else None)
    temp_dir = Path(temp_dir_ctx.name)
    updated_map: dict[str, str] = {}

    try:
        for item in candidates:
            source = build_source_url(item)
            if not source:
                print(f"Skipping {item.get('id')}: no usable source URL")
                continue

            out_path = temp_dir / output_name(item)
            print(f"Converting {item.get('id')} -> {out_path.name}")
            ffmpeg_extract_audio(source, out_path)

            if args.upload:
                public_url = gcs_upload(out_path, args.bucket, args.prefix)
                updated_map[str(item.get("id"))] = public_url
                print(f"  uploaded: {public_url}")
            else:
                print(f"  wrote: {out_path}")

        if args.write_json and updated_map:
            for item in collection.get("podcasts", []) or []:
                item_id = str(item.get("id"))
                if item_id in updated_map:
                    item["mp3url"] = updated_map[item_id]
                    tags = item.get("tags") or []
                    if "video-podcast" in tags:
                        item["tags"] = [t for t in tags if t != "video-podcast"]
            save_collection(collection)
            print(f"Updated {len(updated_map)} rows in {COLLECTION_PATH}")
        elif args.write_json:
            print("No uploaded URLs to write back; did upload fail?")
            return 1
    finally:
        temp_dir_ctx.cleanup()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
