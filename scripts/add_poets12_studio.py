#!/usr/bin/env python3
"""Upsert the Poets & Friends #12 BTS photo collection into studio_collections.

Usage:
    DATABASE_URL=<render_postgres_url> python scripts/add_poets12_studio.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_session
from models import StudioCollection

COLLECTION = {
    'collection_id': 'poets-and-friends-12-bts',
    'title': "Poets & Friends #12 — Behind the Scenes",
    'date': '2026-06-28',
    'tag': 'Live Event',
    'description': 'Behind-the-scenes photos from Poets & Friends #12. Photography by Spider in Stereo.',
    'cover': 'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets_12_BTS/WhatsApp%20Image%202026-07-01%20at%2021.37.57%20(1).jpeg',
    'photos': [
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets_12_BTS/WhatsApp%20Image%202026-07-01%20at%2021.37.57%20(1).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets_12_BTS/WhatsApp%20Image%202026-07-01%20at%2021.37.57%20(4).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets_12_BTS/WhatsApp%20Image%202026-07-01%20at%2021.37.57.jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets_12_BTS/WhatsApp%20Image%202026-07-01%20at%2021.37.58%20(2).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets_12_BTS/WhatsApp%20Image%202026-07-01%20at%2021.37.58%20(5).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets_12_BTS/WhatsApp%20Image%202026-07-01%20at%2021.37.58%20(6).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets_12_BTS/WhatsApp%20Image%202026-07-01%20at%2021.37.58.jpeg',
    ],
    'photographer_slug': 'spider-in-stereo',
    'is_hidden': False,
    'position': 0,
}

with get_session() as session:
    existing = session.query(StudioCollection).filter_by(
        collection_id=COLLECTION['collection_id']
    ).first()

    if existing:
        for k, v in COLLECTION.items():
            setattr(existing, k, v)
        print(f"Updated existing collection: {COLLECTION['collection_id']}")
    else:
        session.add(StudioCollection(**COLLECTION))
        print(f"Inserted new collection: {COLLECTION['collection_id']}")

    session.commit()

print("Done.")
