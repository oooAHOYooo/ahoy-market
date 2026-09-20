#!/usr/bin/env python3
"""Upsert the Poets & Friends #8 BTS photo collection into studio_collections.

Usage:
    DATABASE_URL=<render_postgres_url> python scripts/add_poets8_studio.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_session
from models import StudioCollection

COLLECTION = {
    'collection_id': 'poets-and-friends-8-bts',
    'title': "Poets & Friends #8 — Behind the Scenes",
    'date': '2026-03-11',
    'tag': 'Live Event',
    'description': 'Photography by Ellen Martin from Poets & Friends #8.',
    'cover': 'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets8_BTS/Studio_Poets%238_EllenMartin_%202026-03-11%20at%2021.37.17.jpeg',
    'photos': [
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets8_BTS/Studio_Poets%238_EllenMartin_%202026-03-11%20at%2021.37.17.jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets8_BTS/Studio_Poets%238_EllenMartin_%202026-03-11%20at%2021.37.17%20(1).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets8_BTS/Studio_Poets%238_EllenMartin_%202026-03-11%20at%2021.37.17%20(2).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets8_BTS/Studio_Poets%238_EllenMartin_%202026-03-11%20at%2021.37.17%20(3).jpeg',
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
