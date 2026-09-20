#!/usr/bin/env python3
"""Sync Youth XL - Text Your Friends video to database and What's New."""
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db import get_session
from models import ContentVideo, WhatsNewItem

def sync_youth_xl_video():
    """Add Youth XL video to content_videos and WhatsNewItem."""

    video_data = {
        "video_id": "youth-xl-text-your-friends",
        "title": "Youth XL - Text Your Friends (Official Music Video)",
        "description": "Official music video by Youth XL. Kicker Pictures production.",
        "url": "https://storage.googleapis.com/ahoy-videos/music-videos/youth-xl/Q7ipQC6kdFM.mp4",
        "duration": "3:24",
        "thumbnail": "https://i.ytimg.com/vi/Q7ipQC6kdFM/maxresdefault.jpg",
        "status": "available",
        "upload_date": "20201128",
        "extra_fields": {
            "youtube_id": "Q7ipQC6kdFM",
            "original_url": "https://www.youtube.com/watch?v=Q7ipQC6kdFM",
            "uploader": "Kicker Pictures",
            "uploader_id": "@kickerpictures",
            "view_count": 60,
            "like_count": 2,
            "bandcamp_url": "https://youthxl.bandcamp.com/",
            "gcs_bucket": "ahoy-videos",
            "gcs_path": "music-videos/youth-xl/Q7ipQC6kdFM.mp4",
            "imported_from": "youtube",
            "import_date": datetime.utcnow().isoformat(),
        }
    }

    whats_new_data = {
        "year": "2026",
        "month": "06",
        "section": "videos",
        "item_type": "content",
        "title": "Youth XL - Text Your Friends",
        "description": "New music video now available. Official video by Youth XL / Kicker Pictures. Watch on Ahoy and support the artist at youthxl.bandcamp.com",
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "link": "/videos",  # Link to videos page
        "link_external": "https://youthxl.bandcamp.com/",
        "thumbnail": "https://i.ytimg.com/vi/Q7ipQC6kdFM/maxresdefault.jpg",
        "is_new": True,
        "skip_feature": False,
        "position": 0,
    }

    with get_session() as session:
        # Check if video already exists
        existing = session.query(ContentVideo).filter(
            ContentVideo.video_id == video_data["video_id"]
        ).first()

        if existing:
            print(f"Video already exists: {existing.video_id}")
            # Update it
            for key, value in video_data.items():
                setattr(existing, key, value)
            session.commit()
            print("Updated existing video")
        else:
            # Create new
            video = ContentVideo(**video_data)
            session.add(video)
            session.commit()
            print(f"Added new video: {video.video_id}")

        # Check if whats new item already exists
        existing_news = session.query(WhatsNewItem).filter(
            WhatsNewItem.title == whats_new_data["title"],
            WhatsNewItem.year == whats_new_data["year"],
            WhatsNewItem.month == whats_new_data["month"],
        ).first()

        if existing_news:
            print(f"What's New item already exists: {existing_news.title}")
            # Update it
            for key, value in whats_new_data.items():
                setattr(existing_news, key, value)
            session.commit()
            print("Updated existing What's New item")
        else:
            # Create new
            news = WhatsNewItem(**whats_new_data)
            session.add(news)
            session.commit()
            print(f"Added new What's New item: {news.title}")

        print("\nSummary:")
        print(f"  Video: {video_data['title']}")
        print(f"  URL: {video_data['url']}")
        print(f"  Status: Available")
        print(f"  What's New: Featured (June 2026)")
        print(f"  External link: {whats_new_data['link_external']}")

if __name__ == "__main__":
    try:
        sync_youth_xl_video()
        print("\nSync complete!")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
