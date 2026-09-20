"""
Seed Tyler Mirando as an artist and add Tyler Needs a Break video episodes to the DB.
Run with: python scripts/seed_tyler_mirando.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_session
from models import ContentArtist, Show

ARTIST_ID = 'artist_23'
ARTIST_NAME = 'Tyler Mirando'
ARTIST_SLUG = 'tyler-mirando'
THUMBNAIL = 'https://ahoy.ooo/images/Ahoy-Indie-Media-DEFAULT-COVER-A-8.jpg'

SHOWS = [
    {
        'show_id': 'tyler-needs-a-break-ep1',
        'title': 'Tyler Needs a Break — Episode 1',
        'position': 1,
    },
    {
        'show_id': 'tyler-needs-a-break-ep2',
        'title': 'Tyler Needs a Break — Episode 2',
        'position': 2,
    },
    {
        'show_id': 'tyler-needs-a-break-ep3',
        'title': 'Tyler Needs a Break — Episode 3',
        'position': 3,
    },
]

with get_session() as session:
    # --- Artist ---
    existing = session.query(ContentArtist).filter_by(slug=ARTIST_SLUG).first()
    if existing:
        print(f'Artist {ARTIST_SLUG} already exists (id={existing.artist_id}), skipping.')
    else:
        artist = ContentArtist(
            artist_id=ARTIST_ID,
            name=ARTIST_NAME,
            slug=ARTIST_SLUG,
            artist_type='host',
            description='',
            image=THUMBNAIL,
            social_links={},
            genres=['Podcast'],
            followers=0,
            verified=False,
            featured=False,
            created_at_str='2026-03-14',
            updated_at_str='2026-03-14',
            position=23,
            extra_fields={'_original_keys': ['description', 'created_at', 'updated_at', 'shows', 'tracks']},
        )
        session.add(artist)
        print(f'Added artist: {ARTIST_NAME} ({ARTIST_SLUG})')

    # --- Shows ---
    for s in SHOWS:
        existing_show = session.query(Show).filter_by(show_id=s['show_id']).first()
        if existing_show:
            print(f'Show {s["show_id"]} already exists, skipping.')
            continue
        show = Show(
            show_id=s['show_id'],
            title=s['title'],
            host=ARTIST_NAME,
            host_slug=ARTIST_SLUG,
            description='',
            duration_seconds=None,
            video_url='',
            thumbnail=THUMBNAIL,
            published_date='2026-03-14',
            views=0,
            show_type='episode',
            is_live=False,
            tags=['tyler-needs-a-break', 'podcast', 'video'],
            category='Podcast',
            position=s['position'],
            is_hidden=False,
            extra_fields={'podcast_slug': 'tyler-needs-a-break', 'episode_number': s['position']},
        )
        session.add(show)
        print(f'Added show: {s["title"]}')

    session.commit()
    print('Done.')
