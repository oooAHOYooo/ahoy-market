"""
Seed Tyler Needs a Break Episode 2 clips into content_shows.
Run with: python scripts/seed_tyler_ep2_clips.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_session
from models import Show

THUMBNAIL = 'https://ahoy.ooo/images/Ahoy-Indie-Media-DEFAULT-COVER-A-8.jpg'
BASE_URL = 'https://storage.googleapis.com/ahoy-videos/series/tyler%20needs%20a%20break/ep2'

CLIPS = [
    {
        'show_id': 'tyler-needs-a-break-ep2-ct-skating',
        'title': 'Roots of Connecticut Skating — Tyler Needs a Break',
        'description': (
            'Tyler Mirando traces the origins and culture of skateboarding in Connecticut. '
            'Where it started, who built it, and what keeps it alive. '
            'A clip from Tyler Needs a Break, Episode 2.'
        ),
        'video_url': f'{BASE_URL}/Roots%20of%20Conneticut%20Skating.mp4',
        'tags': ['tyler-needs-a-break', 'clip', 'skating', 'connecticut'],
        'position': 10,
    },
    {
        'show_id': 'tyler-needs-a-break-ep2-philly-connection',
        'title': 'The Philly Connection — Tyler Needs a Break',
        'description': (
            'Tyler Mirando on the deep ties between Connecticut and the Philadelphia skating scene — '
            'the crews, the spots, and the culture that crossed state lines. '
            'A clip from Tyler Needs a Break, Episode 2.'
        ),
        'video_url': f'{BASE_URL}/Roots%20of%20Philly%20Connection.mp4',
        'tags': ['tyler-needs-a-break', 'clip', 'skating', 'philadelphia'],
        'position': 11,
    },
    {
        'show_id': 'tyler-needs-a-break-ep2-skating-metaphor',
        'title': 'Skating as a Metaphor — Tyler Needs a Break',
        'description': (
            'What does skateboarding really mean? Tyler Mirando reflects on skating as a lens for life — '
            'persistence, creativity, and finding your own line. '
            'A clip from Tyler Needs a Break, Episode 2.'
        ),
        'video_url': f'{BASE_URL}/Skating%20as%20a%20Metaphor.mp4',
        'tags': ['tyler-needs-a-break', 'clip', 'skating'],
        'position': 12,
    },
    {
        'show_id': 'tyler-needs-a-break-ep2-basement-project',
        'title': 'The Basement Project — Tyler Needs a Break',
        'description': (
            'Tyler Mirando talks about the basement project — '
            'what gets built in the margins, away from the spotlight. '
            'A clip from Tyler Needs a Break, Episode 2.'
        ),
        'video_url': f'{BASE_URL}/The%20Basement%20Project.mp4',
        'tags': ['tyler-needs-a-break', 'clip'],
        'position': 13,
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
            thumbnail=THUMBNAIL,
            published_date='2026-03-14',
            views=0,
            show_type='clip',
            is_live=False,
            tags=c['tags'],
            category='Tyler Needs a Break',
            position=c['position'],
            is_hidden=False,
            extra_fields={'episode_number': 2, 'podcast_slug': 'tyler-needs-a-break'},
        )
        session.add(show)
        print(f'Added: {c["title"]}')
    session.commit()
    print('Done.')
