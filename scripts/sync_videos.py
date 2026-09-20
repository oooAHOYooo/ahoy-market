#!/usr/bin/env python3
"""Sync videos from static/data/videos.json to content_videos table.

Usage:
    python scripts/sync_videos.py
"""
import json
import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from db import get_session, engine
from models import ContentVideo, Base

def load_videos():
    path = os.path.join('static', 'data', 'videos.json')
    if not os.path.exists(path):
        print(f"Error: {path} not found")
        sys.exit(1)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f).get('videos', [])

def upsert_videos(session, videos):
    if not videos:
        return 0
    
    dialect = engine.dialect.name
    count = 0
    
    for v in videos:
        video_id = v.get('id')
        if not video_id:
            continue
            
        # Extract known fields
        known_data = {
            'video_id': video_id,
            'event_id': v.get('event_id'),
            'title': v.get('title', ''),
            'description': v.get('description', ''),
            'url': v.get('url'),
            'duration': str(v.get('duration')) if v.get('duration') else None,
            'file_size': str(v.get('file_size')) if v.get('file_size') else None,
            'format': v.get('format'),
            'status': v.get('status', 'available'),
            'upload_date': v.get('upload_date'),
            'thumbnail': v.get('thumbnail', ''),
            'position': count,
        }
        
        # Everything else goes to extra_fields
        extra = {k: v for k, v in v.items() if k not in {
            'id', 'event_id', 'title', 'description', 'url', 'duration', 
            'file_size', 'format', 'status', 'upload_date', 'thumbnail'
        }}
        if extra:
            known_data['extra_fields'] = extra

        if dialect == 'sqlite':
            stmt = sqlite_insert(ContentVideo.__table__).values(**known_data)
            stmt = stmt.on_conflict_do_update(
                index_elements=['video_id'],
                set_={k: v for k, v in known_data.items() if k != 'video_id'}
            )
            session.execute(stmt)
        else:
            # PostgreSQL
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            stmt = pg_insert(ContentVideo.__table__).values(**known_data)
            stmt = stmt.on_conflict_do_update(
                index_elements=['video_id'],
                set_={k: v for k, v in known_data.items() if k != 'video_id'}
            )
            session.execute(stmt)
        count += 1
    
    return count

def main():
    print("Syncing videos: JSON -> Database...")
    videos = load_videos()
    
    with get_session() as session:
        n = upsert_videos(session, videos)
        session.commit()
        print(f"Successfully upserted {n} videos to database.")

if __name__ == '__main__':
    main()
