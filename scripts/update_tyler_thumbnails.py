"""
Update thumbnail paths for all Tyler Needs a Break shows in the DB.
Thumbnails must already exist in static/thumbnails/ (committed to git).

Run with: python scripts/update_tyler_thumbnails.py
"""
import sys, os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_session
from models import Show

# show_id -> explicit thumbnail path (relative to static root)
THUMBNAIL_MAP = {
    # Full episodes (seeded by seed_tyler_mirando.py)
    'tyler-needs-a-break-ep1': '/static/thumbnails/tyler-needs-a-break-ep1_01918dfa58dd.jpg',
    'tyler-needs-a-break-ep2': '/static/thumbnails/tyler-needs-a-break-ep2_aee78832fc65.jpg',
    # Full episodes (imported from legacy JSON, different show_id)
    'tyler-needs-a-break-ep1-full': '/static/thumbnails/tyler-needs-a-break-ep1_01918dfa58dd.jpg',
    'tyler-needs-a-break-ep2-full': '/static/thumbnails/tyler-needs-a-break-ep2_aee78832fc65.jpg',
    # EP1 clips
    'tyler-needs-a-break-ep1-truth-over-ease': '/static/thumbnails/tyler-needs-a-break-ep1-truth-over-ease_835bf7dcedbd.jpg',
    'tyler-needs-a-break-ep1-healing-music':   '/static/thumbnails/tyler-needs-a-break-ep1-healing-music_02486df62ca3.jpg',
    # EP2 clips
    'tyler-needs-a-break-ep2-ct-skating':        '/static/thumbnails/tyler-needs-a-break-ep2-ct-skating_aec66b4c0fb0.jpg',
    'tyler-needs-a-break-ep2-philly-connection': '/static/thumbnails/tyler-needs-a-break-ep2-philly-connection_8afd9bee9e22.jpg',
    'tyler-needs-a-break-ep2-skating-metaphor':  '/static/thumbnails/tyler-needs-a-break-ep2-skating-metaphor_6acd1eb1ae8c.jpg',
    'tyler-needs-a-break-ep2-basement-project':  '/static/thumbnails/tyler-needs-a-break-ep2-basement-project_58b534ce5f69.jpg',
}

PROJECT_ROOT = Path(__file__).parent.parent

with get_session() as session:
    updated = 0
    skipped = 0
    not_found = 0

    for show_id, thumb_path in THUMBNAIL_MAP.items():
        abs_path = PROJECT_ROOT / thumb_path.lstrip('/')
        if not abs_path.exists():
            print(f'  ✗ File missing on disk: {abs_path.name}')
            continue

        show = session.query(Show).filter_by(show_id=show_id).first()
        if not show:
            not_found += 1
            continue

        if show.thumbnail == thumb_path:
            skipped += 1
        else:
            show.thumbnail = thumb_path
            print(f'  → {show_id}')
            updated += 1

    session.commit()
    print(f'\nDone. updated={updated} already_set={skipped} not_in_db={not_found}')
