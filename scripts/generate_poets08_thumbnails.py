#!/usr/bin/env python3
"""
Generate unique thumbnails for ALL Poets & Friends #8 videos and update database/JSON.
Extracts a frame from each video at 10 seconds.
"""

import os
import sys
import subprocess
import hashlib
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from db import get_session
from models import Show, ContentVideo, PodcastEpisode, PodcastShow

THUMBNAILS_DIR = PROJECT_ROOT / "static" / "thumbnails"
VIDEOS_JSON = PROJECT_ROOT / "static" / "data" / "videos.json"

def ensure_thumbnails_dir():
    THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

def get_video_hash(video_url):
    return hashlib.md5(video_url.encode()).hexdigest()[:12]

def extract_thumbnail(video_url, output_path, seek_seconds=10):
    try:
        cmd = [
            "ffmpeg",
            "-ss", str(seek_seconds),
            "-i", video_url,
            "-vframes", "1",
            "-q:v", "2",
            "-vf", "scale=1280:-1",
            "-y",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0
    except Exception as e:
        print(f"Error extracting thumbnail from {video_url}: {e}")
        return False

def update_videos_json(video_id, thumbnail_path_rel):
    if not VIDEOS_JSON.exists():
        return
    try:
        with open(VIDEOS_JSON, 'r') as f:
            data = json.load(f)
        
        updated = False
        for video in data.get('videos', []):
            if video.get('id') == video_id:
                video['thumbnail'] = thumbnail_path_rel
                updated = True
        
        if updated:
            with open(VIDEOS_JSON, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  ✓ Updated videos.json for {video_id}")
    except Exception as e:
        print(f"  ✗ Error updating videos.json: {e}")

def main():
    ensure_thumbnails_dir()
    print("Generating thumbnails for Poets & Friends #8...")
    
    with get_session() as session:
        # 1. Process Show chapters
        shows = session.query(Show).filter(Show.category == "poets-and-friends", Show.show_id.like("poets-and-friends-8%")).all()
        print(f"Found {len(shows)} chapter shows.")
        for s in shows:
            if not s.video_url: continue
            
            v_hash = get_video_hash(s.video_url)
            filename = f"{s.show_id}_{v_hash}.jpg"
            out_path = THUMBNAILS_DIR / filename
            rel_path = f"/static/thumbnails/{filename}"
            
            print(f"Processing show: {s.title}...")
            if extract_thumbnail(s.video_url, out_path):
                s.thumbnail = rel_path
                print(f"  ✓ Created: {filename}")
                # Also update videos.json (many chapters might be shared)
                update_videos_json(s.show_id, rel_path)
            else:
                print(f"  ✗ Failed: {s.title}")

        # 2. Process ContentVideo (Full show)
        content_videos = session.query(ContentVideo).filter(ContentVideo.video_id == "poets-and-friends-8").all()
        for cv in content_videos:
            if not cv.url: continue
            
            v_hash = get_video_hash(cv.url)
            filename = f"{cv.video_id}_{v_hash}.jpg"
            out_path = THUMBNAILS_DIR / filename
            rel_path = f"/static/thumbnails/{filename}"
            
            print(f"Processing content video: {cv.title}...")
            if extract_thumbnail(cv.url, out_path):
                cv.thumbnail = rel_path
                update_videos_json(cv.video_id, rel_path)
                print(f"  ✓ Created: {filename}")
            else:
                print(f"  ✗ Failed: {cv.title}")

        # 3. Process PodcastEpisode
        episodes = session.query(PodcastEpisode).filter(PodcastEpisode.episode_id == "poets-and-friends-8-full").all()
        for ep in episodes:
            if not ep.audio_url: continue # audio_url is video URL for video podcasts
            
            v_hash = get_video_hash(ep.audio_url)
            filename = f"{ep.episode_id}_{v_hash}.jpg"
            out_path = THUMBNAILS_DIR / filename
            rel_path = f"/static/thumbnails/{filename}"
            
            print(f"Processing podcast episode: {ep.title}...")
            if extract_thumbnail(ep.audio_url, out_path):
                ep.artwork = rel_path
                print(f"  ✓ Created: {filename}")
            else:
                print(f"  ✗ Failed: {ep.title}")

        # 4. Update PodcastShow artwork if it's using the old one
        podcast_show = session.query(PodcastShow).filter(PodcastShow.slug == "poets-and-friends").first()
        if podcast_show and "thumbnails/poets-and-friends-4" in podcast_show.artwork:
            # use the full show thumbnail
            full_show_cv = session.query(ContentVideo).filter(ContentVideo.video_id == "poets-and-friends-8").first()
            if full_show_cv and full_show_cv.thumbnail:
                podcast_show.artwork = full_show_cv.thumbnail
                print(f"Updated PodcastShow '{podcast_show.title}' artwork.")

        session.commit()

    print("Done.")

if __name__ == "__main__":
    main()
