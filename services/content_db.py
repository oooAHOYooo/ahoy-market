"""Database-backed content queries for music, shows, artists, and podcasts.

Each function returns plain dicts/lists matching the exact JSON response shapes
from the original static files. Used by API routes in app.py as a drop-in
replacement for load_json_data().

All functions include a TTL-based in-memory cache to avoid hitting the DB
on every request (mirrors the old 600s JSON file cache).
"""
import os
import re
import logging
from time import time as _now

from db import get_session
from storage import read_json
from models import (
    Track, Show, ContentArtist, ContentArtistAlbum, ContentArtistAlbumTrack,
    ContentArtistShow, ContentArtistTrack, PodcastShow, PodcastEpisode,
    Event, ContentMerch, ContentVideo, WhatsNewItem,
)

logger = logging.getLogger(__name__)


def _db_err(label: str, e: Exception) -> None:
    """Log a compact DB error — strips the full SQL dump for expected local-dev cases."""
    msg = str(e)
    if "no such table" in msg or "UndefinedTable" in msg:
        logger.warning(f"DB table missing: {label} — using JSON fallback")
    elif isinstance(e, ValueError):
        logger.warning(f"DB: {msg} — using JSON fallback")
    else:
        # Keep first line only (strips the [SQL: ...] block)
        first_line = msg.splitlines()[0]
        logger.error(f"DB query for {label} failed: {first_line}")


def _load_fallback_json(filename, default=None):
    """Load JSON from legacy or static data folders as a fallback."""
    # Check migrated content first (dev/legacy_json/)
    migrated_path = f"dev/legacy_json/{filename}"
    if os.path.exists(migrated_path):
        return read_json(migrated_path, default or {})
    
    # Check static data
    static_path = f"static/data/{filename}"
    return read_json(static_path, default or {})

# ---------------------------------------------------------------------------
# In-memory cache (same pattern as the old _json_data_cache)
# ---------------------------------------------------------------------------
_cache = {}


def _cached(key, ttl, fn):
    """Return cached result or call fn() and cache it."""
    now = _now()
    if key in _cache:
        val, ts = _cache[key]
        if now - ts < ttl:
            return val
    val = fn()
    _cache[key] = (val, now)
    return val


def invalidate_cache(key=None):
    """Clear one key or the entire content cache."""
    if key:
        _cache.pop(key, None)
    else:
        _cache.clear()


# ---------------------------------------------------------------------------
# Serializers: DB row -> dict matching original JSON shape
# ---------------------------------------------------------------------------

def _serialize_track(t):
    """Convert a Track row to a dict matching music.json track objects."""
    d = {
        'id': t.track_id,
        'title': t.title,
        'artist': t.artist,
        'album': t.album,
        'genre': t.genre,
        'duration_seconds': t.duration_seconds,
        'audio_url': t.audio_url,
        'preview_url': t.preview_url,
        'cover_art': t.cover_art,
        'added_date': t.added_date,
        'tags': t.tags or [],
        'artist_slug': t.artist_slug,
        'track_slug': _slugify_podcast(t.title or ''),
        'play_count': t.play_count or 0,
    }
    # Optional fields: only include if truthy (matches original JSON where absent)
    if t.artist_url:
        d['artist_url'] = t.artist_url
    if t.background_image:
        d['background_image'] = t.background_image
    if t.featured:
        d['featured'] = True
    if t.is_new:
        d['new'] = True
    if t.date_added:
        d['date_added'] = t.date_added
    # Merge any extra fields from the catch-all column
    if t.extra_fields:
        d.update(t.extra_fields)
    return d


def _serialize_show(s):
    """Convert a Show row to a dict matching shows.json show objects."""
    d = {
        'id': s.show_id,
        'title': s.title,
        'host': s.host,
        'description': s.description,
        'duration_seconds': s.duration_seconds,
        'video_url': s.video_url,
        'thumbnail': s.thumbnail,
        'published_date': s.published_date,
        'views': s.views,
        'type': s.show_type,
        'is_live': s.is_live,
        'tags': s.tags or [],
        'host_slug': s.host_slug,
        'category': s.category,
    }
    if s.trailer_url:
        d['trailer_url'] = s.trailer_url
    if s.extra_fields:
        d.update(s.extra_fields)
    return d


def _video_as_show(v):
    """Convert a ContentVideo row to a show-like dict so it appears in /api/shows (Videos page)."""
    extra = v.extra_fields or {}
    return {
        'id': v.video_id,
        'title': v.title or '',
        'host': extra.get('host') or '',
        'description': v.description or '',
        'duration_seconds': None,
        'video_url': v.url or '',
        'thumbnail': v.thumbnail or '',
        'published_date': v.upload_date or '',
        'views': 0,
        'type': 'full_show',
        'is_live': False,
        'tags': [],
        'host_slug': extra.get('host_slug') or '',
        'category': 'events',
    }


def _serialize_artist(a, albums_map, shows_map, tracks_map):
    """Convert a ContentArtist row + nested data to a dict matching artists.json."""
    # Determine which fields were in the original JSON
    extra = a.extra_fields or {}
    orig_keys = set(extra.pop('_original_keys', []))
    artist_type = a.artist_type or ''
    if artist_type == 'skater':
        artist_type = 'athlete'

    d = {
        'id': a.artist_id,
        'name': a.name,
        'slug': a.slug,
        'type': artist_type,
        'image': a.image,
        'social_links': a.social_links or {},
        'genres': a.genres or [],
        'followers': a.followers,
        'verified': a.verified,
        'location': 'New Haven, CT',
    }
    # Only include these if they were in the original record
    if 'description' in orig_keys:
        d['description'] = a.description
    if 'created_at' in orig_keys:
        d['created_at'] = a.created_at_str
    if 'updated_at' in orig_keys:
        d['updated_at'] = a.updated_at_str
    if a.featured:
        d['featured'] = True

    # Only include nested arrays if present in original
    if 'albums' in orig_keys:
        d['albums'] = []
    if 'shows' in orig_keys:
        d['shows'] = []
    if 'tracks' in orig_keys:
        d['tracks'] = []

    # Albums
    if 'albums' in d:
        for alb in albums_map.get(a.artist_id, []):
            alb_dict = {
                'id': alb['album_id'],
                'title': alb['title'],
                'release_date': alb['release_date'],
                'cover_art': alb['cover_art'],
                'tags': alb['tags'] or [],
                'tracks': alb.get('tracks', []),
            }
            if alb.get('is_new'):
                alb_dict['new'] = True
            if alb.get('extra_fields'):
                alb_dict.update(alb['extra_fields'])
            d['albums'].append(alb_dict)

    # Shows
    if 'shows' in d:
        for sh in shows_map.get(a.artist_id, []):
            sh_dict = {
                'id': sh['show_ref_id'],
                'title': sh['title'],
                'type': sh['show_type'],
                'duration': sh['duration'],
                'category': sh['category'],
                'published_date': sh['published_date'],
            }
            d['shows'].append(sh_dict)

    # Tracks
    if 'tracks' in d:
        for tr in tracks_map.get(a.artist_id, []):
            tr_dict = {
                'id': tr['track_ref_id'],
                'title': tr['title'],
                'album': tr['album'],
                'duration': tr['duration'],
                'genre': tr['genre'],
                'added_date': tr['added_date'],
            }
            d['tracks'].append(tr_dict)

    # Merge extra fields (bio, avatar, cover_image, location, website, etc.)
    if a.extra_fields:
        d.update(a.extra_fields)

    return d


def _serialize_podcast_show(ps, episodes, episode_number_map=None):
    """Convert PodcastShow + episodes to dict matching podcasts.json."""
    episode_number_map = episode_number_map or {}
    episode_count = len(episodes)

    episodes_payload = []
    for ep in episodes:
        ep_id = str(ep.episode_id)
        ep_num = episode_number_map.get(ep_id)

        # If a show only has one episode (and it's missing explicit episode_number),
        # treat it as episode 1 so episode detail routes work.
        if ep_num is None and episode_count == 1:
            ep_num = 1

        ep_dict = {
            'id': ep.episode_id,
            'title': ep.title,
            'description': ep.description,
            'date': ep.date,
            'duration': ep.duration,
            'duration_seconds': ep.duration_seconds,
            'audio_url': ep.audio_url,
            'video_url': ep.video_url,
            'artwork': ep.artwork,
            'is_clip': ep.is_clip,
        }
        if ep_num is not None:
            ep_dict['episode_number'] = ep_num

        episodes_payload.append(ep_dict)

    return {
        'slug': ps.slug,
        'title': ps.title,
        'description': ps.description,
        'artwork': ps.artwork,
        'last_updated': ps.last_updated,
        'episodes': episodes_payload,
    }


def _serialize_event(e):
    """Convert Event row to dict matching events.json event objects."""
    d = {
        'id': e.event_id,
        'title': e.title,
        'date': e.date,
        'time': e.time,
        'venue': e.venue,
        'venue_address': e.venue_address,
        'event_type': e.event_type,
        'status': e.status,
        'description': e.description or '',
        'photos': e.photos if e.photos is not None else [],
        'image': e.image or '',
        'rsvp_external_url': e.rsvp_external_url,
        'rsvp_enabled': bool(e.rsvp_enabled),
        'rsvp_limit': e.rsvp_limit,
        'rsvps': [],
    }
    if e.extra_fields:
        d.update(e.extra_fields)
    return d


def _serialize_merch_item(m):
    """Convert ContentMerch row to dict matching data/merch.json item shape."""
    d = {
        'id': m.item_id,
        'name': m.name,
        'image_url': m.image_url or '',
        'price_usd': float(m.price_usd),
        'kind': m.kind or 'merch',
        'available': bool(m.available),
    }
    if m.image_url_back:
        d['image_url_back'] = m.image_url_back
    if m.extra_fields:
        d.update(m.extra_fields)
    return d


def _serialize_video(v):
    """Convert ContentVideo row to dict matching videos.json video objects."""
    d = {
        'id': v.video_id,
        'event_id': v.event_id,
        'title': v.title,
        'description': v.description,
        'url': v.url,
        'duration': v.duration,
        'file_size': v.file_size,
        'format': v.format,
        'status': v.status,
        'upload_date': v.upload_date,
        'thumbnail': v.thumbnail or '',
    }
    if v.extra_fields:
        d.update(v.extra_fields)
    return d


# ---------------------------------------------------------------------------
# Query functions (return dicts ready for jsonify)
# ---------------------------------------------------------------------------

def get_all_tracks(ttl=600):
    """Return {"tracks": [...]} matching /api/music response."""
    def _query():
        try:
            with get_session() as session:
                rows = session.query(Track).order_by(Track.position).all()
                if rows:
                    return {'tracks': [_serialize_track(t) for t in rows]}
        except Exception as e:
            _db_err("music", e)
        
        # Fallback
        return _load_fallback_json('music.json', {'tracks': []})
    return _cached('all_tracks', ttl, _query)


def get_all_shows(ttl=600):
    """Return {"shows": [...]} matching /api/shows response. Includes Show rows plus ContentVideo rows (e.g. full event recordings) so they appear on the Videos page."""
    def _query():
        try:
            with get_session() as session:
                show_rows = session.query(Show).order_by(Show.position).all()
                video_rows = session.query(ContentVideo).order_by(ContentVideo.position).all()
                if not show_rows and not video_rows:
                    raise ValueError("No show or video rows in DB")
                shows_list = [_serialize_show(s) for s in show_rows]
                for v in video_rows:
                    shows_list.append(_video_as_show(v))
                if shows_list:
                    return {'shows': shows_list}
        except Exception as e:
            _db_err("shows", e)

        # Fallback: shows.json + merge in videos.json so full event recordings (e.g. Poets & Friends #8) appear
        out = _load_fallback_json('shows.json', {'shows': []})
        shows_list = list(out.get('shows') or [])
        videos_data = _load_fallback_json('videos.json', {'videos': []})
        for v in (videos_data.get('videos') or []):
            vid = v.get('id')
            if not vid or any(s.get('id') == vid for s in shows_list):
                continue
            shows_list.append({
                'id': vid,
                'title': v.get('title', ''),
                'host': v.get('host', '') or '',
                'description': v.get('description', ''),
                'duration_seconds': None,
                'video_url': v.get('url', ''),
                'thumbnail': v.get('thumbnail', ''),
                'published_date': v.get('upload_date', ''),
                'views': 0,
                'type': 'full_show',
                'is_live': False,
                'tags': [],
                'host_slug': v.get('host_slug', '') or '',
                'category': 'events',
            })
        return {'shows': shows_list}
    return _cached('all_shows', ttl, _query)


def get_all_artists(ttl=600):
    """Return {"artists": [...], "total_count": N, "last_updated": "..."} matching /api/artists."""
    def _query():
        try:
            with get_session() as session:
                artists = session.query(ContentArtist).order_by(ContentArtist.position).all()
                if not artists:
                    raise ValueError("No artists in DB") # Trigger fallback if empty

                artist_ids = [a.artist_id for a in artists]

                # Load nested data in bulk
                albums_raw = session.query(ContentArtistAlbum).filter(
                    ContentArtistAlbum.artist_id_ref.in_(artist_ids)
                ).order_by(ContentArtistAlbum.position).all()

                album_ids = [alb.album_id for alb in albums_raw]
                album_tracks_raw = session.query(ContentArtistAlbumTrack).filter(
                    ContentArtistAlbumTrack.album_id_ref.in_(album_ids)
                ).order_by(ContentArtistAlbumTrack.position).all() if album_ids else []

                shows_raw = session.query(ContentArtistShow).filter(
                    ContentArtistShow.artist_id_ref.in_(artist_ids)
                ).order_by(ContentArtistShow.position).all()

                tracks_raw = session.query(ContentArtistTrack).filter(
                    ContentArtistTrack.artist_id_ref.in_(artist_ids)
                ).order_by(ContentArtistTrack.position).all()

                # Build lookup maps
                album_tracks_by_album = {}
                for at in album_tracks_raw:
                    album_tracks_by_album.setdefault(at.album_id_ref, []).append({
                        'id': at.track_id_ref, 'title': at.title,
                    })

                albums_map = {}
                for alb in albums_raw:
                    albums_map.setdefault(alb.artist_id_ref, []).append({
                        'album_id': alb.album_id,
                        'title': alb.title,
                        'release_date': alb.release_date,
                        'cover_art': alb.cover_art,
                        'tags': alb.tags,
                        'is_new': alb.is_new,
                        'extra_fields': alb.extra_fields,
                        'tracks': album_tracks_by_album.get(alb.album_id, []),
                    })

                shows_map = {}
                for sh in shows_raw:
                    shows_map.setdefault(sh.artist_id_ref, []).append({
                        'show_ref_id': sh.show_ref_id,
                        'title': sh.title,
                        'show_type': sh.show_type,
                        'duration': sh.duration,
                        'category': sh.category,
                        'published_date': sh.published_date,
                    })

                tracks_map = {}
                for tr in tracks_raw:
                    tracks_map.setdefault(tr.artist_id_ref, []).append({
                        'track_ref_id': tr.track_ref_id,
                        'title': tr.title,
                        'album': tr.album,
                        'duration': tr.duration,
                        'genre': tr.genre,
                        'added_date': tr.added_date,
                    })

                result_artists = [
                    _serialize_artist(a, albums_map, shows_map, tracks_map)
                    for a in artists
                ]

                return {
                    'artists': result_artists,
                    'total_count': len(result_artists),
                    'last_updated': artists[0].updated_at_str if artists else '',
                }
        except Exception as e:
            _db_err("artists", e)
            
        # Fallback
        return _load_fallback_json('artists.json', {'artists': [], 'total_count': 0, 'last_updated': ''})
    return _cached('all_artists', ttl, _query)


# ---------------------------------------------------------------------------
# Podcast collection fallback helpers
# ---------------------------------------------------------------------------
_PODCAST_SLUG_ALIASES = {
    'The Rob Show': 'the-rob-show',
    'Rob Meglio Show': 'the-rob-show',
    'Poets & Friends': 'poets-and-friends',
    'Tyler Needs a Break': 'tyler-needs-a-break',
    'Ahoy Live Shows': 'ahoy-live-shows',
}


def _slugify_podcast(s: str) -> str:
    s = (s or '').strip().lower()
    s = re.sub(r"['']", '', s)
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = re.sub(r'-{2,}', '-', s).strip('-')
    return s or 'show'


def _extract_podcast_show_name(title: str) -> str:
    t = (title or '').strip()
    lower = t.lower()
    if lower.startswith('the rob show'):    return 'The Rob Show'
    if lower.startswith('my friend'):       return 'My Friend'
    if lower.startswith('found cassettes'): return 'Found Cassettes'
    head = re.split(r'\s*[-–—]\s*', t, maxsplit=1)[0].strip()
    head = re.sub(r'\s*#\s*\d+.*$', '', head).strip()
    return head or 'Podcast'


def _load_podcast_collection_fallback() -> dict:
    """Convert flat podcastCollection.json into {'shows': [...]} matching get_all_podcasts() shape."""
    collection = read_json('static/data/podcastCollection.json', {'podcasts': []})
    shows_meta = collection.get('shows', {})
    items = [p for p in collection.get('podcasts', []) if p.get('active', True)]
    items.sort(
        key=lambda p: (str(p.get('date') or p.get('releaseDate') or ''), int(p.get('id') or 0)),
        reverse=True,
    )
    shows_by_slug: dict = {}
    for p in items:
        title = p.get('title') or 'Untitled Episode'
        # Check if episode explicitly specifies which show it belongs to
        if 'show_slug' in p:
            slug = p['show_slug']
            show_name = None
        else:
            # Infer from title
            show_name = _extract_podcast_show_name(title)
            slug = _PODCAST_SLUG_ALIASES.get(show_name) or _slugify_podcast(show_name)
        meta = shows_meta.get(slug, {})
        show = shows_by_slug.setdefault(slug, {
            'slug': slug,
            'title': meta.get('title') or show_name,
            'description': meta.get('description') or '',
            'artwork': meta.get('artwork') or p.get('thumbnail') or '/static/img/default-cover.jpg',
            'host': meta.get('host') or '',
            'host_slug': meta.get('host_slug') or '',
            'last_updated': p.get('date') or p.get('releaseDate') or '',
            'episodes': [],
        })
        ep = {
            'id': str(p.get('id') or title),
            'title': title,
            'description': p.get('description') or '',
            'date': p.get('date') or p.get('releaseDate') or '',
            'duration': '',
            'duration_seconds': 0,
            'audio_url': p.get('mp3url') or '',
            'artwork': p.get('thumbnail') or '/static/img/default-cover.jpg',
            'is_clip': bool(p.get('is_clip', False)),
            'video_url': p.get('video_url') or '',
        }
        if p.get('episode_number') is not None:
            ep['episode_number'] = p['episode_number']
        show['episodes'].append(ep)
    shows = sorted(shows_by_slug.values(), key=lambda s: str(s.get('last_updated') or ''), reverse=True)
    return {'shows': shows}


def _load_podcast_episode_number_map() -> dict:
    """Build episode_id -> episode_number map from podcastCollection.json."""
    collection = read_json('static/data/podcastCollection.json', {'podcasts': []})
    items = [p for p in collection.get('podcasts', []) if p.get('active', True)]
    mapping = {}
    for p in items:
        if p.get('episode_number') is None:
            continue
        ep_id = str(p.get('id') or p.get('title') or '')
        if not ep_id:
            continue
        mapping[ep_id] = p.get('episode_number')
    return mapping


def get_all_podcasts(ttl=600):
    """Return {"shows": [...]} from database with JSON fallback for local dev.

    Render DB is source of truth; podcastCollection.json is fallback for local dev without DATABASE_URL.
    """
    def _query():
        try:
            with get_session() as session:
                shows = session.query(PodcastShow).filter(
                    PodcastShow.is_hidden == False
                ).order_by(PodcastShow.position).all()

                slugs = [s.slug for s in shows]
                episodes = session.query(PodcastEpisode).filter(
                    PodcastEpisode.show_slug.in_(slugs),
                    PodcastEpisode.is_hidden == False,
                ).order_by(PodcastEpisode.position).all()
                eps_by_show = {}
                for ep in episodes:
                    eps_by_show.setdefault(ep.show_slug, []).append(ep)

                shows_list = [
                    _serialize_podcast_show(
                        s,
                        eps_by_show.get(s.slug, []),
                        episode_number_map=_load_podcast_episode_number_map(),
                    )
                    for s in shows
                ]
                if shows_list:
                    return {'shows': shows_list}
        except Exception as e:
            _db_err("podcasts", e)

        # Fallback: parse podcastCollection.json for local dev without DATABASE_URL
        return _load_podcast_collection_fallback()
    return _cached('all_podcasts', ttl, _query)


def get_tracks_list(ttl=600):
    """Return just the list of track dicts (for daily-playlist, radio, etc.)."""
    return get_all_tracks(ttl).get('tracks', [])


def get_shows_list(ttl=600):
    """Return just the list of show dicts."""
    return get_all_shows(ttl).get('shows', [])


def get_artists_list(ttl=600):
    """Return just the list of artist dicts."""
    return get_all_artists(ttl).get('artists', [])


def get_all_events(ttl=600):
    """Return {"events": [...]} matching events.json."""
    def _query():
        try:
            with get_session() as session:
                rows = session.query(Event).order_by(Event.position, Event.date.desc()).all()
                if rows:
                    return {'events': [_serialize_event(e) for e in rows]}
        except Exception as e:
            _db_err("events", e)
            
        # Fallback
        return _load_fallback_json('events.json', {'events': []})
    return _cached('all_events', ttl, _query)


def get_all_merch(ttl=600):
    """Return {"items": [...]} matching data/merch.json catalog."""
    def _query():
        try:
            with get_session() as session:
                rows = session.query(ContentMerch).order_by(ContentMerch.position).all()
                if rows:
                    return {'items': [_serialize_merch_item(m) for m in rows]}
        except Exception as e:
            _db_err("merch", e)
            
        # Fallback
        return _load_fallback_json('merch.json', {'items': []})
    return _cached('all_merch', ttl, _query)


def get_all_videos(ttl=600):
    """Return {"videos": [...]} matching videos.json."""
    def _query():
        try:
            with get_session() as session:
                rows = session.query(ContentVideo).order_by(ContentVideo.position).all()
                if rows:
                    return {'videos': [_serialize_video(v) for v in rows]}
        except Exception as e:
            _db_err("videos", e)
            
        # Fallback
        return _load_fallback_json('videos.json', {'videos': []})
    return _cached('all_videos', ttl, _query)


def get_all_whats_new(ttl=600):
    """Return whats_new data structured as {"updates": {year: {month: {section: ...}}}}."""
    def _query():
        with get_session() as session:
            rows = session.query(WhatsNewItem).order_by(
                WhatsNewItem.year.desc(), WhatsNewItem.month, WhatsNewItem.section, WhatsNewItem.position
            ).all()
            updates = {}
            for row in rows:
                yr = updates.setdefault(row.year, {})
                mn = yr.setdefault(row.month, {})
                section_titles = {
                    'music': 'Music Updates', 'videos': 'Video Updates',
                    'artists': 'Artist Updates', 'platform': 'Platform Updates',
                    'merch': 'Merch Updates', 'events': 'Events Updates',
                }
                if row.section not in mn:
                    mn[row.section] = {
                        'title': section_titles.get(row.section, f'{row.section.capitalize()} Updates'),
                        'items': [],
                    }
                item = {
                    'type': row.item_type,
                    'title': row.title,
                    'description': row.description,
                }
                if row.date:
                    item['date'] = row.date
                if row.link:
                    item['link'] = row.link
                if row.link_external:
                    item['link_external'] = row.link_external
                if row.thumbnail:
                    item['thumbnail'] = row.thumbnail
                if row.is_new:
                    item['is_new'] = row.is_new
                if row.skip_feature:
                    item['skip_feature'] = row.skip_feature
                if row.features:
                    item['features'] = row.features
                if row.extra_fields:
                    item.update(row.extra_fields)
                    if 'thumbnail_grid' in row.extra_fields and 'thumbnails' not in item:
                        item['thumbnails'] = row.extra_fields['thumbnail_grid']
                mn[row.section]['items'].append(item)
            return {'updates': updates}
    return _cached('all_whats_new', ttl, _query)
