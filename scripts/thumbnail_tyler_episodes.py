"""
Extract thumbnails for Tyler Needs a Break full episodes from GCS video URLs,
save to static/thumbnails/, and update podcastCollection.json.

Run with: python scripts/thumbnail_tyler_episodes.py
"""
import sys, os, subprocess, hashlib, json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
THUMBNAILS_DIR = PROJECT_ROOT / 'static' / 'thumbnails'
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

PODCAST_JSON = PROJECT_ROOT / 'static' / 'data' / 'podcastCollection.json'

SEEK_SECONDS = 5

EPISODES = [
    {
        'id': 38,
        'slug': 'tyler-needs-a-break-ep1',
        'video_url': 'https://storage.googleapis.com/ahoy-videos/series/tyler%20needs%20a%20break/ep1/Ready%20-%20Tyler%20Show%20Ep%201%20-%20d1.mp4',
    },
    {
        'id': 39,
        'slug': 'tyler-needs-a-break-ep2',
        'video_url': 'https://storage.googleapis.com/ahoy-videos/series/tyler%20needs%20a%20break/ep2/ready_TmoneyEp2%20-d3.mp4',
    },
]


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
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
        print(f'  ✓ {output_path.name} ({output_path.stat().st_size // 1024}KB)')
        return True
    print(f'  ✗ ffmpeg failed: {result.stderr[-300:]}')
    return False


# Load JSON
with open(PODCAST_JSON) as f:
    data = json.load(f)

updated = []

for ep in EPISODES:
    print(f'\n{ep["slug"]}')
    url_hash = hashlib.md5(ep['video_url'].encode()).hexdigest()[:12]
    filename = f'{ep["slug"]}_{url_hash}.jpg'
    thumb_path = THUMBNAILS_DIR / filename
    relative = f'/static/thumbnails/{filename}'

    if thumb_path.exists() and thumb_path.stat().st_size > 0:
        print(f'  ⊘ Already exists: {filename}')
        success = True
    else:
        success = extract_thumbnail(ep['video_url'], thumb_path)
        if not success:
            print(f'  Retrying at 2s...')
            success = extract_thumbnail(ep['video_url'], thumb_path, seek=2)

    if success:
        updated.append((ep['id'], relative))

# Update podcastCollection.json
if updated:
    for ep_id, thumb_path in updated:
        for podcast in data['podcasts']:
            if podcast.get('id') == ep_id:
                podcast['artwork'] = thumb_path
                print(f'  → Updated JSON id={ep_id} artwork → {thumb_path}')
                break

    with open(PODCAST_JSON, 'w') as f:
        json.dump(data, f, indent=2)
    print('\nUpdated podcastCollection.json')

print('\nDone. Thumbnails saved to static/thumbnails/')
