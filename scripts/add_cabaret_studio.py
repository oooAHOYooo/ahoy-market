#!/usr/bin/env python3
"""Upsert the Ahoy Cabaret BTS photo collection into studio_collections.

Usage:
    DATABASE_URL=<render_postgres_url> python scripts/add_cabaret_studio.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_session
from models import StudioCollection

COLLECTION = {
    'collection_id': 'ahoy-cabaret-bts',
    'title': "Ahoy Cabaret at Best Video — Behind the Scenes",
    'date': '2025-02-22',
    'tag': 'Live Event',
    'description': 'Photography by multiple cameras from Ahoy Cabaret at Best Video.',
    'cover': 'https://storage.googleapis.com/ahoy-dynamic-content/studio/cabaret_BTS/Ahoy%20Indie%20Media%20-%20Cabaret%20Best%20Video%202025%20-%20Pat%20Clendenen.jpeg',
    'photos': [
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/cabaret_BTS/Ahoy%20Indie%20Media%20-%20Cabaret%20Best%20Video%202025%20-%20Pat%20Clendenen.jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/news/ahoyCaba-ep2/%5BAHOY%20CABA%20BTS%20EP2%5D13.jpg',
        'https://storage.googleapis.com/ahoy-dynamic-content/news/ahoyCaba-ep2/%5BAHOY%20CABA%20BTS%20EP2%5D14.jpg',
        'https://storage.googleapis.com/ahoy-dynamic-content/news/ahoyCaba-ep2/%5BAHOY%20CABA%20BTS%20EP2%5D15.jpg',
        'https://storage.googleapis.com/ahoy-dynamic-content/news/ahoyCaba-ep2/%5BAHOY%20CABA%20BTS%20EP2%5D16.jpg',
        'https://storage.googleapis.com/ahoy-dynamic-content/news/ahoyCaba-ep2/%5BAHOY%20CABA%20BTS%20EP2%5D17.jpg',
        'https://storage.googleapis.com/ahoy-dynamic-content/news/ahoyCaba-ep2/%5BAHOY%20CABA%20BTS%20EP2%5D19.jpg',
        'https://storage.googleapis.com/ahoy-dynamic-content/news/ahoyCaba-ep2/%5BAHOY%20CABA%20BTS%20EP2%5D21.jpg',
        'https://storage.googleapis.com/ahoy-dynamic-content/news/ahoyCaba-ep2/%5BAHOY%20CABA%20BTS%20EP2%5D24.jpg',
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
