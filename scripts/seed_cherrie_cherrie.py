"""
Seed Cherrie Cherrie as a new artist, add their track, and add a What's New entry.
Run with: python scripts/seed_cherrie_cherrie.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_session
from models import ContentArtist, ContentArtistTrack, Track, WhatsNewItem

ARTIST_ID = 'cherrie-cherrie'
ARTIST_NAME = 'Cherrie Cherrie'
ARTIST_SLUG = 'cherrie-cherrie'

TRACK_ID = 'cherrie-cherrie-waiting-for-the-long-days'
TRACK_TITLE = 'Waiting for the Long Days...'
AUDIO_URL = 'https://storage.googleapis.com/ahoy-song-collection/cherrie%20cherrie/Waiting%20for%20the%20Long%20Days...%20-%20Cherrie%20Cherrie.m4a'
COVER_ART = 'https://storage.googleapis.com/ahoy-song-collection/cherrie%20cherrie/cherrie%20cherrie%20-%20waiting%20for%20the%20long%20days.jpeg'
DATE_ADDED = '2026-06-22'

with get_session() as session:
    # --- Artist ---
    existing_artist = session.query(ContentArtist).filter_by(slug=ARTIST_SLUG).first()
    if existing_artist:
        print(f'Artist {ARTIST_SLUG} already exists, skipping.')
    else:
        artist = ContentArtist(
            artist_id=ARTIST_ID,
            name=ARTIST_NAME,
            slug=ARTIST_SLUG,
            artist_type='musician',
            description='',
            image=COVER_ART,
            social_links={},
            genres=['Indie'],
            followers=0,
            verified=False,
            featured=False,
            created_at_str=DATE_ADDED,
            updated_at_str=DATE_ADDED,
            position=0,
            extra_fields={},
        )
        session.add(artist)
        print(f'Added artist: {ARTIST_NAME}')

    # --- Track (global music catalog) ---
    existing_track = session.query(Track).filter_by(track_id=TRACK_ID).first()
    if existing_track:
        print(f'Track {TRACK_ID} already exists, skipping.')
    else:
        track = Track(
            track_id=TRACK_ID,
            title=TRACK_TITLE,
            artist=ARTIST_NAME,
            album='',
            genre='Indie',
            duration_seconds=0,
            audio_url=AUDIO_URL,
            preview_url=AUDIO_URL,
            cover_art=COVER_ART,
            added_date=DATE_ADDED,
            tags=['cherrie-cherrie', 'indie', 'new'],
            artist_slug=ARTIST_SLUG,
            artist_url=f'/artists/{ARTIST_SLUG}',
            featured=False,
            is_new=True,
            date_added=DATE_ADDED,
            position=83,
            extra_fields={},
        )
        session.add(track)
        print(f'Added track: {TRACK_TITLE}')

    # --- Artist track cross-reference ---
    existing_artist_track = session.query(ContentArtistTrack).filter_by(track_ref_id=TRACK_ID).first()
    if not existing_artist_track:
        artist_track = ContentArtistTrack(
            artist_id_ref=ARTIST_ID,
            track_ref_id=TRACK_ID,
            title=TRACK_TITLE,
            album='',
            duration=0,
            genre='Indie',
            added_date=DATE_ADDED,
            position=1,
        )
        session.add(artist_track)
        print(f'Added artist track reference')

    # --- What's New ---
    existing_wn = session.query(WhatsNewItem).filter_by(
        year='2026', month='06', title=f'New Music: {ARTIST_NAME} — {TRACK_TITLE}'
    ).first()
    if existing_wn:
        print(f'WhatsNew entry already exists, skipping.')
    else:
        wn = WhatsNewItem(
            year='2026',
            month='06',
            section='music',
            item_type='content',
            title=f'New Music: {ARTIST_NAME} — {TRACK_TITLE}',
            description=f'{ARTIST_NAME} joins Ahoy with their debut track "{TRACK_TITLE}".',
            date=DATE_ADDED,
            link=f'/artists/{ARTIST_SLUG}',
            thumbnail=COVER_ART,
            is_new=True,
            skip_feature=False,
            position=1,
            extra_fields={},
        )
        session.add(wn)
        print(f'Added What\'s New entry')

    session.commit()
    print('Done.')
