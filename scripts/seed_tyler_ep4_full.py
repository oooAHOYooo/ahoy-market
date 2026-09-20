"""
Seed Tyler Needs a Break Episode 4 (Sam Carlson) full show into content_shows,
and remove any duplicate podcast episode entry.
Run with: DATABASE_URL=<prod_url> python scripts/seed_tyler_ep4_full.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_session
from models import Show, PodcastEpisode

FULL_SHOW = {
    'show_id': 'tyler-needs-a-break-ep4-full',
    'title': 'Tyler Needs a Break — Episode 4: Sam Carlson (Full Show)',
    'description': (
        'Tyler talks with Sam Carlson about booking shows, naming projects, '
        'basement venues, and going on tour. Full episode of Tyler Needs a Break, Episode 4.'
    ),
    'video_url': 'https://storage.googleapis.com/ahoy-videos/series/tyler%20needs%20a%20break/ep4/Tyler%20Needs%20a%20Break%20-%20Ep4%20-%20Sam%20Carlson%20-%20full%20-%20d1.mp4',
    'thumbnail': '/static/thumbnails/tyler-needs-a-break-ep4-full_sam-carlson_8646f844c333.jpg',
    'tags': ['tyler-needs-a-break', 'episode', 'full-show', 'sam-carlson'],
    'position': 36,
}

with get_session() as session:
    # 1. Add full show entry to content_shows (for video player)
    existing = session.query(Show).filter_by(show_id=FULL_SHOW['show_id']).first()
    if existing:
        print(f'Already exists: {FULL_SHOW["show_id"]}, skipping.')
    else:
        show = Show(
            show_id=FULL_SHOW['show_id'],
            title=FULL_SHOW['title'],
            host='Tyler Mirando',
            host_slug='tyler-mirando',
            description=FULL_SHOW['description'],
            duration_seconds=None,
            video_url=FULL_SHOW['video_url'],
            thumbnail=FULL_SHOW['thumbnail'],
            published_date='2026-03-22',
            views=0,
            show_type='broadcast',
            is_live=False,
            tags=FULL_SHOW['tags'],
            category='Tyler Needs a Break',
            position=FULL_SHOW['position'],
            is_hidden=False,
        )
        session.add(show)
        print(f'Added full show: {FULL_SHOW["title"]}')

    # 2. Find and remove duplicate podcast episodes for EP4
    # Keep only the canonical entry (id=42, title="Episode #04: Sam Carlson")
    ep4_dupes = session.query(PodcastEpisode).filter(
        PodcastEpisode.show_slug == 'tyler-needs-a-break',
        PodcastEpisode.is_clip == False,
        PodcastEpisode.episode_id != '42',
        PodcastEpisode.title.like('%Episode%4%Sam Carlson%'),
    ).all()

    for dupe in ep4_dupes:
        print(f'Removing duplicate: id={dupe.episode_id}, title="{dupe.title}"')
        session.delete(dupe)

    if not ep4_dupes:
        print('No duplicate EP4 podcast episodes found.')

    session.commit()
    print('Done.')
