"""Seed full Poets & Friends videos into content_videos so they appear on Videos page (Render DB + live).

Revision ID: 0028_seed_pnf_videos
Revises: 0027_audit_logs
Create Date: 2026-03-18

Inserts full-show recordings from static/data/videos.json into content_videos so /api/shows
includes them and the Videos section shows them. Idempotent: safe to run on every deploy.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision = '0028_seed_pnf_videos'
down_revision = '0027_audit_logs'
branch_labels = None
depends_on = None


# Full Poets & Friends (and similar) full-show videos to ensure are in content_videos
FULL_VIDEOS = [
    {
        "video_id": "poets-and-friends-8",
        "event_id": "2026-02-26T18:30:00",
        "title": "Poets & Friends #8 — Full Show Recording",
        "description": "Full unedited recording of Poets & Friends #8, originally recorded live on February 26, 2026 at Koffee?, New Haven CT. Featuring Micky Vampiro, Paul Wildly, Aidan Bauer, Layne Boles, Alex Gonzalez, Miranda Copps, Katie Myerscough, Pat Clendenen, Ellen Martin, Samuel Chen, and Sasha.",
        "url": "https://storage.googleapis.com/ahoy-videos/live/poets/Poets%20and%20Friends%20%238%20-%20Draft%203.mp4",
        "thumbnail": "/static/thumbnails/poets-and-friends-8_b1908116a7c8.jpg",
        "upload_date": "2026-02-26",
        "status": "available",
        "format": "MP4",
    },
    {
        "video_id": "poets-and-friends-4",
        "event_id": "2025-10-30T18:30:00",
        "title": "Poets & Friends #4: Spooky Edition - Live Show Recording",
        "description": "Full recording of the Spooky Edition poetry and performance event",
        "url": "https://storage.googleapis.com/ahoy-videos/live/poets/Poets4Total.mp4",
        "thumbnail": "/static/thumbnails/poets-and-friends-4_24ec074f1c38.jpg",
        "upload_date": "2025-11-18",
        "status": "available",
        "format": "MP4",
    },
    {
        "video_id": "poets-and-friends-3",
        "event_id": "2025-09-24T19:00:00",
        "title": "Poets and Friends #3 - Live Show Recording",
        "description": "Full recording of the live poetry and performance event",
        "url": "https://storage.googleapis.com/ahoy-videos/live/poets/Ahoy_poets%20and%20friends%20-%203%20-%20ready.mov",
        "thumbnail": "/static/thumbnails/poets-and-friends-3_a0e72c328dba.jpg",
        "upload_date": "2025-10-01",
        "status": "available",
        "format": "MOV",
    },
]


def upgrade():
    conn = op.get_bind()
    dialect = conn.dialect.name
    for v in FULL_VIDEOS:
        vid, eid = v["video_id"], v.get("event_id")
        title = (v.get("title") or "").replace("'", "''")
        desc = (v.get("description") or "").replace("'", "''")
        url = (v.get("url") or "").replace("'", "''")
        thumb = (v.get("thumbnail") or "").replace("'", "''")
        udate = v.get("upload_date") or ""
        status = v.get("status") or "available"
        fmt = v.get("format") or ""

        if dialect == "postgresql":
            conn.execute(text("""
                INSERT INTO content_videos (video_id, event_id, title, description, url, thumbnail, upload_date, status, format, position, is_hidden)
                VALUES (:vid, :eid, :title, :desc, :url, :thumb, :udate, :status, :fmt, 0, false)
                ON CONFLICT (video_id) DO UPDATE SET
                    event_id = EXCLUDED.event_id,
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    url = EXCLUDED.url,
                    thumbnail = EXCLUDED.thumbnail,
                    upload_date = EXCLUDED.upload_date,
                    status = EXCLUDED.status,
                    format = EXCLUDED.format
            """), {"vid": vid, "eid": eid, "title": title, "desc": desc, "url": url, "thumb": thumb, "udate": udate, "status": status, "fmt": fmt})
        else:
            # SQLite: insert if not exists (idempotent for local dev)
            conn.execute(text("""
                INSERT OR IGNORE INTO content_videos (video_id, event_id, title, description, url, thumbnail, upload_date, status, format, position, is_hidden)
                VALUES (:vid, :eid, :title, :desc, :url, :thumb, :udate, :status, :fmt, 0, 0)
            """), {"vid": vid, "eid": eid, "title": title, "desc": desc, "url": url, "thumb": thumb, "udate": udate, "status": status, "fmt": fmt})


def downgrade():
    # Optional: remove only these seeded rows so we don't wipe user-added videos
    conn = op.get_bind()
    for v in FULL_VIDEOS:
        conn.execute(text("DELETE FROM content_videos WHERE video_id = :vid"), {"vid": v["video_id"]})
