import hashlib
from datetime import datetime, timezone

from services.content_db import get_tracks_list

DEFAULT_STATION_EPOCH_MS = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)


def _stable_item_key(item, station_key: str) -> str:
    item_id = str(
        item.get('id')
        or item.get('track_id')
        or item.get('slug')
        or item.get('key')
        or item.get('title')
        or ''
    ).strip()
    return hashlib.sha256(f"{station_key}:{item_id}".encode('utf-8')).hexdigest()


def normalize_radio_item(item, default_kind: str = 'track'):
    """Convert a source record into a radio station item.

    The shape intentionally stays flexible so plugs, bumpers, and future
    radio-only content can live in the same schedule without changing the
    consumer code.
    """
    duration_seconds = int(item.get('duration_seconds') or item.get('duration') or 180)
    audio_url = item.get('audio_url') or item.get('preview_url') or item.get('url') or ''
    return {
        'id': str(item.get('id') or item.get('track_id') or item.get('slug') or item.get('key') or item.get('title') or '').strip(),
        'kind': item.get('kind') or item.get('type') or default_kind,
        'title': item.get('title') or item.get('name') or 'Untitled',
        'artist': item.get('artist') or item.get('host') or item.get('author') or 'Ahoy Artist',
        'audio_url': audio_url,
        'cover_art': item.get('cover_art') or item.get('artwork') or item.get('thumbnail') or '',
        'duration_seconds': max(1, duration_seconds),
        'source_type': item.get('source_type') or default_kind,
        'playable': bool(audio_url),
    }


def build_station_state(items, station_clock_seconds: int, up_next_count: int = 3):
    """Compute the current item and upcoming window from a deterministic clock."""
    if not items:
        return {
            'current_index': -1,
            'current_item': None,
            'elapsed_seconds': 0,
            'total_duration_seconds': 0,
            'up_next': [],
        }

    total_duration = sum(item.get('duration_seconds', 180) for item in items)
    if total_duration <= 0:
        total_duration = len(items) * 180

    clock = ((station_clock_seconds % total_duration) + total_duration) % total_duration
    cursor = 0
    for index, item in enumerate(items):
        duration = int(item.get('duration_seconds') or 180)
        if clock < cursor + duration:
            up_next = [
                items[(index + offset) % len(items)]
                for offset in range(1, min(up_next_count, len(items) - 1) + 1)
            ]
            return {
                'current_index': index,
                'current_item': item,
                'elapsed_seconds': clock - cursor,
                'total_duration_seconds': total_duration,
                'up_next': up_next,
            }
        cursor += duration

    return {
        'current_index': 0,
        'current_item': items[0],
        'elapsed_seconds': 0,
        'total_duration_seconds': total_duration,
        'up_next': items[1:1 + up_next_count],
    }


def build_radio_manifest(tracks=None, extra_items=None, station_key='ahoy-radio-main', station_name='Ahoy Radio'):
    """Build the deterministic radio station manifest.

    `tracks` may be passed in by callers that already fetched the catalog.
    `extra_items` lets the station mix in future plugs or radio-only content
    without changing the consumer API.
    """
    if tracks is None:
        tracks = get_tracks_list(ttl=600)

    source_items = []
    seen = set()

    for track in tracks or []:
        normalized = normalize_radio_item(track, 'track')
        if not normalized['id'] or normalized['id'] in seen:
            continue
        if not normalized['audio_url']:
            continue
        seen.add(normalized['id'])
        source_items.append(normalized)

    for item in extra_items or []:
        normalized = normalize_radio_item(item, item.get('kind') or 'radio_item')
        if not normalized['id'] or normalized['id'] in seen:
            continue
        if not normalized['audio_url']:
            continue
        seen.add(normalized['id'])
        source_items.append(normalized)

    ordered_items = sorted(source_items, key=lambda item: _stable_item_key(item, station_key))

    server_time_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    station_clock_seconds = int((server_time_ms - DEFAULT_STATION_EPOCH_MS) / 1000)
    station_state = build_station_state(ordered_items, station_clock_seconds)

    return {
        'station': {
            'key': station_key,
            'name': station_name,
            'epoch_ms': DEFAULT_STATION_EPOCH_MS,
            'computed_locally': True,
            'track_count': len(ordered_items),
            'manifest_version': 2,
        },
        'server_time_ms': server_time_ms,
        'items': ordered_items,
        'tracks': ordered_items,
        'current_index': station_state['current_index'],
        'current_item': station_state['current_item'],
        'current': station_state,
        'up_next': station_state['up_next'],
    }
