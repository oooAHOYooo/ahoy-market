#!/usr/bin/env python3
"""Add Poets & Friends #8 (Feb 22, 2026) content to the database.

- 11 chapter videos → content_shows        (video library at /shows)
- Full show entry   → content_videos        (live recordings at /events)
- Full show podcast → content_podcast_episodes  (podcast section)

Idempotent: safe to run multiple times.

Usage:
    python scripts/add_poets08.py

    # Against Render prod DB:
    DATABASE_URL=postgresql://... python scripts/add_poets08.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_session, engine
from models import Show, ContentVideo, PodcastShow, PodcastEpisode

GCS_BASE = "https://storage.googleapis.com/ahoy-videos/live/poets/poets-08-chapters"

CHAPTERS = [
    (1,  "Micky Vampiro",   "Micky+Vampiro"),
    (2,  "Paul Wildly",     "Paul+Wildly"),
    (3,  "Aidan Bauer",     "Aidan+Bauer"),
    (4,  "Layne Boles",     "Layne+Boles"),
    (5,  "Alex Gonzalez",   "Alex+Gonzalez"),
    (6,  "Miranda Copps",   "Miranda+Copps"),
    (7,  "Katie Myerscough","Katie+Myerscough"),
    (8,  "Pat Clendenen",   "Pat+Clendenen"),
    (9,  "Ellen Martin",    "Ellen+Martin"),
    (10, "Samuel Chen",     "Samuel+Chen"),
    (11, "Sasha",           "Sasha"),
    (12, "CJ",              "CJ"),
    (13, "Dan Carbonella",  "Dan+Carbonella"),
    (14, "Allison Luekens", "Allison+Luekens"),
    (15, "Micky Outro",     "Micky+Outro"),
]

THUMBNAIL = "/static/thumbnails/poets-and-friends-4_24ec074f1c38.jpg"  # reuse until #8 thumb exists


def _video_url(n, name_encoded):
    fname = f"Poets+and+Friends+%238+-+Part+{n}+-+{name_encoded}.mp4"
    return f"{GCS_BASE}/{fname}".replace("+", "%20").replace("%23", "%23")


def _show_id(n, name):
    slug = name.lower().replace(" ", "-").replace("'", "")
    return f"poets-and-friends-8-part-{n}-{slug}"


def _upsert(session, model, unique_col, records):
    dialect = engine.dialect.name
    for rec in records:
        if dialect == "sqlite":
            from sqlalchemy.dialects.sqlite import insert as _ins
            stmt = _ins(model.__table__).values(**rec)
            stmt = stmt.on_conflict_do_update(
                index_elements=[unique_col],
                set_={k: v for k, v in rec.items() if k != unique_col},
            )
        else:
            from sqlalchemy.dialects.postgresql import insert as _ins
            stmt = _ins(model.__table__).values(**rec)
            stmt = stmt.on_conflict_do_update(
                index_elements=[unique_col],
                set_={k: v for k, v in rec.items() if k != unique_col},
            )
        session.execute(stmt)
    return len(records)


def add_chapter_shows():
    """Insert 11 chapter clips into content_shows (feeds /api/shows → video library)."""
    records = []
    for i, (n, name, name_enc) in enumerate(CHAPTERS):
        url = f"{GCS_BASE}/Poets%20and%20Friends%20%238%20-%20Part%20{n}%20-%20{name_enc.replace('+', '%20')}.mp4"
        records.append({
            "show_id":        _show_id(n, name),
            "title":          f"Poets & Friends #8 — {name}",
            "host":           name,
            "host_slug":      name.lower().replace(" ", "-").replace("'", ""),
            "description":    f"{name} performs at Poets & Friends #8, recorded live on February 26, 2026.",
            "video_url":      url,
            "trailer_url":    None,
            "thumbnail":      THUMBNAIL,
            "published_date": "2026-02-26",
            "views":          0,
            "show_type":      "live_performance",
            "is_live":        False,
            "tags":           ["poets-and-friends", "live", "poetry", "performance"],
            "category":       "poets-and-friends",
            "position":       200 + i,  # after existing shows
            "is_hidden":      False,
            "extra_fields":   {"event": "Poets & Friends #8", "event_date": "2026-02-26"},
        })

    with get_session() as session:
        n = _upsert(session, Show, "show_id", records)
        print(f"  content_shows: {n} chapter videos upserted")


def add_full_show_video():
    """Insert Poets & Friends #8 full show into content_videos (feeds /events)."""
    records = [{
        "video_id":    "poets-and-friends-8",
        "event_id":    "2026-02-26T18:30:00",
        "title":       "Poets & Friends #8 — Full Show Recording",
        "description": "Full unedited recording of Poets & Friends #8, live on February 26, 2026. Featuring Micky Vampiro, Paul Wildly, Aidan Bauer, Layne Boles, Alex Gonzalez, Miranda Copps, Katie Myerscough, Pat Clendenen, Ellen Martin, Samuel Chen, and Sasha.",
        "url":         "https://storage.googleapis.com/ahoy-videos/live/poets/Poets%20and%20Friends%20%238%20-%20Draft%203.mp4",
        "duration":    None,
        "file_size":   None,
        "format":      "MP4",
        "status":      "available",
        "upload_date": "2026-02-26",
        "thumbnail":   THUMBNAIL,
        "position":    0,
        "is_hidden":   False,
        "extra_fields": None,
    }]

    with get_session() as session:
        n = _upsert(session, ContentVideo, "video_id", records)
        print(f"  content_videos: {n} full-show entry upserted")


FULL_VIDEO_URL = "https://storage.googleapis.com/ahoy-videos/live/poets/Poets%20and%20Friends%20%238%20-%20Draft%203.mp4"
POETS_SHOW_SLUG = "poets-and-friends"


def ensure_podcast_show():
    """Make sure the 'poets-and-friends' podcast show exists."""
    record = {
        "slug":         POETS_SHOW_SLUG,
        "title":        "Poets & Friends",
        "description":  "Live poetry and performance events from Ahoy Indie Media. Each episode features a full show recording from the Poets & Friends series.",
        "artwork":      THUMBNAIL,
        "last_updated": "2026-03-10",
        "position":     10,
        "is_hidden":    False,
    }
    with get_session() as session:
        _upsert(session, PodcastShow, "slug", [record])
        print(f"  podcast show '{POETS_SHOW_SLUG}' ensured")


def add_podcast_episode():
    """Insert Poets & Friends #8 as a podcast episode (video podcast)."""
    records = [{
        "episode_id":       "poets-and-friends-8-full",
        "show_slug":        POETS_SHOW_SLUG,
        "title":            "Poets & Friends #8 — Full Show (Feb 26, 2026)",
        "description":      "Full recording of Poets & Friends #8. Featuring Micky Vampiro, Paul Wildly, Aidan Bauer, Layne Boles, Alex Gonzalez, Miranda Copps, Katie Myerscough, Pat Clendenen, Ellen Martin, Samuel Chen, and Sasha. Recorded live on February 26, 2026.",
        "date":             "2026-02-26",
        "duration":         "",
        "duration_seconds": 0,
        "audio_url":        FULL_VIDEO_URL,
        "artwork":          THUMBNAIL,
        "position":         0,
        "is_hidden":        False,
    }]

    with get_session() as session:
        n = _upsert(session, PodcastEpisode, "episode_id", records)
        print(f"  content_podcast_episodes: {n} episode upserted")


if __name__ == "__main__":
    print("Adding Poets & Friends #8 content...")
    add_chapter_shows()
    add_full_show_video()
    ensure_podcast_show()
    add_podcast_episode()
    print("Done.")
