"""
Seed Kicker Pictures as a filmmaker artist, add the "Elvis" short film to the
videos catalog, tie their existing media (Youth XL music video) to the artist
page, and add a What's New entry.

Idempotent: safe to run multiple times (runs on every deploy via
scripts/migrate_and_start.sh, which is how the Render database gets updated).

Run locally with: python scripts/seed_kicker_pictures.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_session
from models import ContentArtist, ContentArtistShow, Show, WhatsNewItem

ARTIST_ID = 'kicker-pictures'
ARTIST_NAME = 'Kicker Pictures'
ARTIST_SLUG = 'kicker-pictures'
DATE_ADDED = '2026-07-02'

ELVIS_SHOW_ID = 'kicker-pictures-elvis-short-film'
ELVIS_TITLE = '[Short Film] - [Elvis] - [Kicker Pictures]'
ELVIS_VIDEO_URL = 'https://storage.googleapis.com/ahoy-videos/short-films/kicker-pictures/o9BApRX7-fQ.mp4'
ELVIS_THUMB = 'https://storage.googleapis.com/ahoy-videos/short-films/kicker-pictures/thumbnails/o9BApRX7-fQ.jpg'
ELVIS_DURATION = 947  # 15:47

YOUTHXL_SHOW_ID = 'youth-xl-text-your-friends'
YOUTHXL_TITLE = '[Music Video] - [Youth XL] - [Text Your Friends]'
YOUTHXL_VIDEO_URL = 'https://storage.googleapis.com/ahoy-videos/music-videos/youth-xl/Q7ipQC6kdFM.mp4'
YOUTHXL_THUMB = 'https://i.ytimg.com/vi/Q7ipQC6kdFM/maxresdefault.jpg'
YOUTHXL_DURATION = 204  # 3:24

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
            artist_type='filmmaker',
            description='Independent film production company. Short films and music videos.',
            image=ELVIS_THUMB,
            social_links={'youtube': 'https://www.youtube.com/@kickerpictures'},
            genres=['Filmmaker'],
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

    # --- Shows (videos page catalog) ---
    shows = [
        dict(
            show_id=ELVIS_SHOW_ID,
            title=ELVIS_TITLE,
            host=ARTIST_NAME,
            description='Elvis — a short film by Kicker Pictures.',
            duration_seconds=ELVIS_DURATION,
            video_url=ELVIS_VIDEO_URL,
            trailer_url=ELVIS_VIDEO_URL,
            thumbnail=ELVIS_THUMB,
            published_date=DATE_ADDED,
            views=0,
            show_type='short_film',
            is_live=False,
            tags=['short-film', 'elvis', 'kicker-pictures', 'drama'],
            host_slug=ARTIST_SLUG,
            category='Short Film',
            position=38,
            is_new=True,
            extra_fields={
                'youtube_id': 'o9BApRX7-fQ',
                'original_url': 'https://www.youtube.com/watch?v=o9BApRX7-fQ',
                'uploader': 'Kicker Pictures',
                'uploader_id': '@kickerpictures',
                'imported_from': 'youtube',
            },
        ),
        dict(
            show_id=YOUTHXL_SHOW_ID,
            title=YOUTHXL_TITLE,
            host='Youth XL',
            description='Official music video by Youth XL. A Kicker Pictures production.',
            duration_seconds=YOUTHXL_DURATION,
            video_url=YOUTHXL_VIDEO_URL,
            trailer_url=YOUTHXL_VIDEO_URL,
            thumbnail=YOUTHXL_THUMB,
            published_date='2026-06-15',
            views=0,
            show_type='music_video',
            is_live=False,
            tags=['music-video', 'youth-xl', 'kicker-pictures'],
            host_slug=ARTIST_SLUG,  # ties the video to the Kicker Pictures artist page
            category='Music Videos',
            position=39,
            is_new=True,
            extra_fields={
                'youtube_id': 'Q7ipQC6kdFM',
                'original_url': 'https://www.youtube.com/watch?v=Q7ipQC6kdFM',
                'uploader': 'Kicker Pictures',
                'uploader_id': '@kickerpictures',
                'bandcamp_url': 'https://youthxl.bandcamp.com/',
                'imported_from': 'youtube',
            },
        ),
    ]
    for data in shows:
        existing_show = session.query(Show).filter_by(show_id=data['show_id']).first()
        if existing_show:
            print(f"Show {data['show_id']} already exists, skipping.")
        else:
            session.add(Show(**data))
            print(f"Added show: {data['title']}")

    # --- Artist show cross-references ---
    refs = [
        (ELVIS_SHOW_ID, ELVIS_TITLE, 'short_film', ELVIS_DURATION, 'Short Film', DATE_ADDED, 1),
        (YOUTHXL_SHOW_ID, YOUTHXL_TITLE, 'music_video', YOUTHXL_DURATION, 'Music Videos', '2026-06-15', 2),
    ]
    for show_ref_id, title, show_type, duration, category, published_date, position in refs:
        existing_ref = session.query(ContentArtistShow).filter_by(
            artist_id_ref=ARTIST_ID, show_ref_id=show_ref_id
        ).first()
        if not existing_ref:
            session.add(ContentArtistShow(
                artist_id_ref=ARTIST_ID,
                show_ref_id=show_ref_id,
                title=title,
                show_type=show_type,
                duration=duration,
                category=category,
                published_date=published_date,
                position=position,
            ))
            print(f'Added artist show reference: {show_ref_id}')

    # --- What's New ---
    wn_title = 'New Short Film: Elvis — Kicker Pictures'
    existing_wn = session.query(WhatsNewItem).filter_by(
        year='2026', month='07', title=wn_title
    ).first()
    if existing_wn:
        print('WhatsNew entry already exists, skipping.')
    else:
        session.add(WhatsNewItem(
            year='2026',
            month='07',
            section='videos',
            item_type='content',
            title=wn_title,
            description='Kicker Pictures joins Ahoy with their short film "Elvis" — plus their music video for Youth XL\'s "Text Your Friends". Watch on the Videos page.',
            date=DATE_ADDED,
            link='/videos',
            link_external='https://www.youtube.com/@kickerpictures',
            thumbnail=ELVIS_THUMB,
            is_new=True,
            skip_feature=False,
            position=0,
            extra_fields={},
        ))
        print("Added What's New entry")

    session.commit()
    print('Done.')
