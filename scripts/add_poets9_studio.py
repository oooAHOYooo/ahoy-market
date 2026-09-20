#!/usr/bin/env python3
"""Upsert the Poets & Friends #9 BTS photo collection into studio_collections.

Usage:
    DATABASE_URL=<render_postgres_url> python scripts/add_poets9_studio.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_session
from models import StudioCollection

COLLECTION = {
    'collection_id': 'poets-and-friends-9-bts',
    'title': "Poets & Friends #9 — Behind the Scenes",
    'date': '2026-03-26',
    'tag': 'Live Event',
    'description': 'Photography by various photographers from Poets & Friends #9.',
    'cover': 'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_ELLENMARTIN_%202026-03-27%20at%2017.19.13%20(1).jpeg',
    'photos': [
        # Ellen Martin photos
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_ELLENMARTIN_%202026-03-27%20at%2017.19.13%20(1).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_ELLENMARTIN_%202026-03-27%20at%2017.19.13%20(2).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_ELLENMARTIN_%202026-03-27%20at%2017.19.13%20(3).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_ELLENMARTIN_%202026-03-27%20at%2017.19.13.jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_ELLENMARTIN_%202026-03-27%20at%2017.19.14%20(1).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_ELLENMARTIN_%202026-03-27%20at%2017.19.14.jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_ELLENMARTIN_%202026-03-27%20at%2017.19.15%20(1).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_ELLENMARTIN_%202026-03-27%20at%2017.19.15%20(2).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_ELLENMARTIN_%202026-03-27%20at%2017.19.15.jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_ELLENMARTIN_%202026-03-27%20at%2017.19.16%20(1).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_ELLENMARTIN_%202026-03-27%20at%2017.19.16%20(2).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_ELLENMARTIN_%202026-03-27%20at%2017.19.16%20(3).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_ELLENMARTIN_%202026-03-27%20at%2017.19.16.jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_ELLENMARTIN_%202026-03-27%20at%2017.19.17%20(1).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_ELLENMARTIN_%202026-03-27%20at%2017.19.17%20(2).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_ELLENMARTIN_%202026-03-27%20at%2017.19.17%20(3).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_ELLENMARTIN_%202026-03-27%20at%2017.19.17.jpeg',
        # Alex Gonzalez photos
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_AlexGonzalez_%202026-03-27%20at%2007.31.37.jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_AlexGonzalez_%202026-03-27%20at%2007.31.37%20(1).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_AlexGonzalez_%202026-03-27%20at%2007.31.37%20(2).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_AlexGonzalez_%202026-03-27%20at%2007.31.38%20(1).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_AlexGonzalez_%202026-03-27%20at%2007.31.38%20(2).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_AlexGonzalez_%202026-03-27%20at%2007.31.38.jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_AlexGonzalez_%202026-03-27%20at%2007.31.39%20(1).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_AlexGonzalez_%202026-03-27%20at%2007.31.39%20(2).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_AlexGonzalez_%202026-03-27%20at%2007.31.39.jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_AlexGonzalez_%202026-03-27%20at%2007.31.40%20(1).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_AlexGonzalez_%202026-03-27%20at%2007.31.40%20(2).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_AlexGonzalez_%202026-03-27%20at%2007.31.40%20(3).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_AlexGonzalez_%202026-03-27%20at%2007.31.40%20(4).jpeg',
        'https://storage.googleapis.com/ahoy-dynamic-content/studio/poets09_BTS/Studio_Poets%239_AlexGonzalez_%202026-03-27%20at%2007.31.40.jpeg',
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
