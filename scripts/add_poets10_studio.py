#!/usr/bin/env python3
"""Upsert the Poets & Friends #10 BTS photo collection into studio_collections.

Usage:
    DATABASE_URL=<render_postgres_url> python scripts/add_poets10_studio.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_session
from models import StudioCollection

COLLECTION = {
    'collection_id': 'poets-and-friends-10-bts',
    'title': "Poets & Friends #10 — Behind the Scenes",
    'date': '2026-05-02',
    'tag': 'Live Event',
    'description': 'Behind-the-scenes photos from Poets & Friends #10.',
    'cover': 'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets10_Bts/WhatsApp%20Image%202026-05-02%20at%2017.26.08%20(1).jpeg',
    'photos': [
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets10_Bts/WhatsApp%20Image%202026-05-02%20at%2017.26.08%20(1).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets10_Bts/WhatsApp%20Image%202026-05-02%20at%2017.26.08%20(2).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets10_Bts/WhatsApp%20Image%202026-05-02%20at%2017.26.08%20(3).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets10_Bts/WhatsApp%20Image%202026-05-02%20at%2017.26.08%20(4).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets10_Bts/WhatsApp%20Image%202026-05-02%20at%2017.26.08.jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets10_Bts/WhatsApp%20Image%202026-05-02%20at%2017.26.09%20(1).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets10_Bts/WhatsApp%20Image%202026-05-02%20at%2017.26.09.jpeg',
    ],
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
