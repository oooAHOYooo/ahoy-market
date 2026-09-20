import json
import os

filepath = 'static/data/music.json'
with open(filepath, 'r') as f:
    data = json.load(f)

updated_count = 0
for track in data['tracks']:
    if track.get('artist') == 'Jake Custer':
        track['is_new'] = True
        if 'tags' not in track:
            track['tags'] = []
        if 'new' not in track['tags']:
            track['tags'].append('new')
        if 'new music' not in track['tags']:
            track['tags'].append('new music')
        updated_count += 1

with open(filepath, 'w') as f:
    json.dump(data, f, indent=2)

print(f"Updated {updated_count} tracks for Jake Custer")
