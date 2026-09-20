"""
Seed Tyler Needs a Break Episode 4 (Sam Carlson) clips into content_shows.
Run with: DATABASE_URL=<prod_url> python scripts/seed_tyler_ep4_clips.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_session
from models import Show

BASE_URL = 'https://storage.googleapis.com/ahoy-videos/series/tyler%20needs%20a%20break/ep4'
THUMB_BASE = '/static/thumbnails'

CLIPS = [
    {
        'show_id': 'tyler-needs-a-break-ep4-release-and-tour',
        'title': 'Release and Tour — Tyler Needs a Break',
        'description': (
            'Sam Carlson on releasing music and hitting the road. '
            'What it takes to put out a record and take it on tour. '
            'A clip from Tyler Needs a Break, Episode 4.'
        ),
        'video_url': f'{BASE_URL}/01_Sam%20Carlson%20Release%20and%20Tour.mp4',
        'thumbnail': f'{THUMB_BASE}/tyler-needs-a-break-ep4-release-and-tour_87e1782cdf98.jpg',
        'tags': ['tyler-needs-a-break', 'clip', 'sam-carlson', 'music', 'tour'],
        'position': 14,
    },
    {
        'show_id': 'tyler-needs-a-break-ep4-booking-local-shows',
        'title': 'Booking Local Shows — Tyler Needs a Break',
        'description': (
            'Sam Carlson on booking local shows and navigating the scene. '
            'How to get your foot in the door and build a local following. '
            'A clip from Tyler Needs a Break, Episode 4.'
        ),
        'video_url': f'{BASE_URL}/2_SC_Booking%20Local%20Shows.mp4',
        'thumbnail': f'{THUMB_BASE}/tyler-needs-a-break-ep4-booking-local-shows_542c179e335d.jpg',
        'tags': ['tyler-needs-a-break', 'clip', 'sam-carlson', 'music', 'shows'],
        'position': 15,
    },
    {
        'show_id': 'tyler-needs-a-break-ep4-sweltering-basement-show',
        'title': 'Sweltering Basement Show — Tyler Needs a Break',
        'description': (
            'Sam Carlson on playing a sweltering basement show — '
            'the heat, the crowd, and what makes a basement set unforgettable. '
            'A clip from Tyler Needs a Break, Episode 4.'
        ),
        'video_url': f'{BASE_URL}/03_SC_Sweltering%20Basement%20Show.mp4',
        'thumbnail': f'{THUMB_BASE}/tyler-needs-a-break-ep4-sweltering-basement-show_7d4bb9bf95b9.jpg',
        'tags': ['tyler-needs-a-break', 'clip', 'sam-carlson', 'music', 'live'],
        'position': 16,
    },
    {
        'show_id': 'tyler-needs-a-break-ep4-naming-project-breaks',
        'title': 'Naming the Project and Breaks — Tyler Needs a Break',
        'description': (
            'Sam Carlson on naming the project and the importance of taking breaks. '
            'How stepping back leads to better work. '
            'A clip from Tyler Needs a Break, Episode 4.'
        ),
        'video_url': f'{BASE_URL}/04_SC_Naming%20the%20Project%20and%20Breaks.mp4',
        'thumbnail': f'{THUMB_BASE}/tyler-needs-a-break-ep4-naming-project-breaks_1be1987a53c0.jpg',
        'tags': ['tyler-needs-a-break', 'clip', 'sam-carlson', 'music'],
        'position': 17,
    },
]

with get_session() as session:
    for c in CLIPS:
        existing = session.query(Show).filter_by(show_id=c['show_id']).first()
        if existing:
            print(f'Already exists: {c["show_id"]}, skipping.')
            continue
        show = Show(
            show_id=c['show_id'],
            title=c['title'],
            host='Tyler Mirando',
            host_slug='tyler-mirando',
            description=c['description'],
            duration_seconds=None,
            video_url=c['video_url'],
            thumbnail=c['thumbnail'],
            published_date='2026-03-19',
            views=0,
            show_type='clip',
            is_live=False,
            tags=c['tags'],
            category='Tyler Needs a Break',
            position=c['position'],
            is_hidden=False,
            extra_fields={'episode_number': 4, 'podcast_slug': 'tyler-needs-a-break'},
        )
        session.add(show)
        print(f'Added: {c["title"]}')
    session.commit()
    print('Done.')
