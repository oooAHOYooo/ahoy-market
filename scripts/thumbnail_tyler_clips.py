"""
Extract thumbnails for Tyler Needs a Break EP2 clips from their video URLs,
save to static/thumbnails/, and update the DB records.

Run with: python scripts/thumbnail_tyler_clips.py
"""
import sys, os, subprocess, hashlib
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_session
from models import Show

PROJECT_ROOT = Path(__file__).parent.parent
THUMBNAILS_DIR = PROJECT_ROOT / 'static' / 'thumbnails'
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

CLIP_IDS = [
    'tyler-needs-a-break-ep2-ct-skating',
    'tyler-needs-a-break-ep2-philly-connection',
    'tyler-needs-a-break-ep2-skating-metaphor',
    'tyler-needs-a-break-ep2-basement-project',
]

SEEK_SECONDS = 5


def extract_thumbnail(video_url, output_path, seek=SEEK_SECONDS):
    cmd = [
        'ffmpeg',
        '-ss', str(seek),
        '-i', video_url,
        '-vframes', '1',
        '-q:v', '2',
        '-vf', 'scale=1280:-1',
        '-y',
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
        print(f'  ✓ {output_path.name} ({output_path.stat().st_size // 1024}KB)')
        return True
    print(f'  ✗ ffmpeg failed: {result.stderr[:200]}')
    return False


with get_session() as session:
    clips = session.query(Show).filter(Show.show_id.in_(CLIP_IDS)).all()
    if not clips:
        print('No clips found in DB. Have you run seed_tyler_mirando.py and seed_tyler_ep2_clips.py?')
        sys.exit(1)

    for clip in clips:
        print(f'\n{clip.title}')
        if not clip.video_url:
            print('  ⊘ No video_url, skipping')
            continue

        url_hash = hashlib.md5(clip.video_url.encode()).hexdigest()[:12]
        filename = f'{clip.show_id}_{url_hash}.jpg'
        thumb_path = THUMBNAILS_DIR / filename
        relative = f'/static/thumbnails/{filename}'

        if thumb_path.exists():
            print(f'  ⊘ Already exists: {filename}')
            if clip.thumbnail != relative:
                clip.thumbnail = relative
                print(f'  → Updated DB path')
            continue

        if extract_thumbnail(clip.video_url, thumb_path):
            clip.thumbnail = relative
        else:
            print(f'  Retrying at 2s...')
            if extract_thumbnail(clip.video_url, thumb_path, seek=2):
                clip.thumbnail = relative

    session.commit()
    print('\nDone. Thumbnails saved to static/thumbnails/')
    print('Commit + push static/thumbnails/ and run this script on Render to update prod DB.')
