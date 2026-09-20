"""AHOY TV scheduler: pre-generates 96-slot daily schedules with prime-time promotion."""

import hashlib
import random
import logging
from datetime import datetime, date, timedelta
from sqlalchemy import cast, String
from db import get_session
from models import Show, LiveTVSchedule


def _tag_match(tag):
    """LIKE-filter a JSON array column for a tag. Quoted form avoids
    substring collisions (e.g., 'live' matching 'live-show')."""
    return cast(Show.tags, String).like(f'%"{tag}"%')

logger = logging.getLogger(__name__)

SLOTS_PER_DAY = 96  # 15-min slots, midnight-midnight UTC
SLOT_DURATION_SEC = 900  # 15 minutes
PRIME_TIME_START_SLOT = 80  # 8pm UTC (slot 80 = 80*15/60 = 20 hours)
PRIME_TIME_END_SLOT = 92  # 11pm UTC (slot 92 = 92*15/60 = 23 hours)

CHANNEL_IDS = ['misc', 'films', 'music-videos', 'live-shows']


def get_seed(schedule_date, channel_id, slot_id):
    """Deterministic seed per (date, channel, slot) for reproducible shuffles."""
    key = f"{schedule_date.isoformat()}{channel_id}{slot_id}"
    hash_digest = hashlib.sha256(key.encode()).hexdigest()
    return int(hash_digest, 16) % (2**31)


def shuffle_with_seed(items, seed):
    """Shuffle list reproducibly with given seed."""
    if not items:
        return []
    rng = random.Random(seed)
    shuffled = items.copy()
    rng.shuffle(shuffled)
    return shuffled


def get_shows_for_channel(session, channel_id, exclude_hidden=True):
    """Get all active shows for a channel (by tag/category)."""
    query = session.query(Show).filter(Show.is_hidden == False) if exclude_hidden else session.query(Show)

    if channel_id == 'misc':
        # Misc = everything not in other channels
        query = query.filter(
            ~_tag_match('short-film'),
            ~_tag_match('music-video'),
            ~_tag_match('live'),
        )
    elif channel_id == 'films':
        query = query.filter(_tag_match('short-film'))
    elif channel_id == 'music-videos':
        query = query.filter(_tag_match('music-video'))
    elif channel_id == 'live-shows':
        query = query.filter(_tag_match('live'))

    return query.all()


def get_related_shows(session, show, pool, limit=5):
    """Get shows with same category (for filler queue)."""
    related = [s for s in pool if s.category == show.category and s.id != show.id]
    return related[:limit] if related else []


def generate_schedule(schedule_date):
    """
    Generate full-day schedule for given date.
    Returns: dict mapping (slot_id, channel_id) -> {show_id, filler_queue, is_prime_time, weight_used}
    """
    with get_session() as session:
        try:
            schedule = {}
            today = date.today()
            is_today = schedule_date == today

            for channel_id in CHANNEL_IDS:
                # Get all active shows for this channel
                all_shows = get_shows_for_channel(session, channel_id, exclude_hidden=True)
                if not all_shows:
                    logger.warning(f"No shows found for channel {channel_id}")
                    continue

                # Track which shows we've already scheduled to avoid repeats (if desired)
                slot = 0
                while slot < SLOTS_PER_DAY:
                    is_prime = PRIME_TIME_START_SLOT <= slot <= PRIME_TIME_END_SLOT

                    # Determine weight for this slot
                    weight = 'new' if is_prime else 'random'

                    # Filter shows based on weight
                    if is_prime:
                        # 70% new shows, 30% random
                        new_shows = [s for s in all_shows if s.is_new and s.featured_until and s.featured_until >= schedule_date]
                        random_shows = [s for s in all_shows if not (s.is_new and s.featured_until and s.featured_until >= schedule_date)]

                        # Alternate between new (70%) and random (30%)
                        # Simple approach: use deterministic seed to decide
                        seed = get_seed(schedule_date, channel_id, slot)
                        rng = random.Random(seed)
                        if rng.random() < 0.7 and new_shows:
                            pool = new_shows
                            weight = 'new'
                        else:
                            pool = random_shows if random_shows else new_shows
                            weight = 'random'
                    else:
                        pool = all_shows
                        weight = 'random'

                    if not pool:
                        slot += 1
                        continue

                    # Pick show for this slot
                    seed = get_seed(schedule_date, channel_id, slot)
                    shuffled = shuffle_with_seed(pool, seed)
                    show = shuffled[0]

                    # Calculate slot times
                    duration_sec = show.duration_seconds or 300
                    duration_slots = max(1, (duration_sec + SLOT_DURATION_SEC - 1) // SLOT_DURATION_SEC)  # ceiling div

                    # Filler queue for short shows
                    filler_queue = []
                    if duration_sec < SLOT_DURATION_SEC:
                        related = get_related_shows(session, show, all_shows, limit=3)
                        if related:
                            seed_filler = get_seed(schedule_date, channel_id, slot + 1000)  # different seed for filler
                            filler_queue = [s.id for s in shuffle_with_seed(related, seed_filler)]

                    # Store entry
                    schedule[(slot, channel_id)] = {
                        'show_id': show.id,
                        'filler_queue': filler_queue,
                        'is_prime_time': is_prime,
                        'weight_used': weight,
                    }

                    slot += duration_slots

            # Save to DB
            session.query(LiveTVSchedule).filter(LiveTVSchedule.schedule_date == schedule_date).delete()
            for (slot_id, channel_id), data in schedule.items():
                entry = LiveTVSchedule(
                    schedule_date=schedule_date,
                    slot_id=slot_id,
                    channel_id=channel_id,
                    show_id=data['show_id'],
                    filler_queue=data['filler_queue'],
                    is_prime_time=data['is_prime_time'],
                    weight_used=data['weight_used'],
                )
                session.add(entry)
            session.commit()
            logger.info(f"Generated schedule for {schedule_date}: {len(schedule)} slots")
            return schedule

        except Exception as e:
            logger.error(f"Failed to generate schedule for {schedule_date}: {e}", exc_info=True)
            session.rollback()
            return {}


def get_today_schedule():
    """Get pre-generated schedule for today (or generate if missing)."""
    with get_session() as session:
        try:
            today = date.today()
            entries = session.query(LiveTVSchedule).filter(LiveTVSchedule.schedule_date == today).all()
            if entries:
                return {(e.slot_id, e.channel_id): {
                    'show_id': e.show_id,
                    'filler_queue': e.filler_queue or [],
                    'is_prime_time': e.is_prime_time,
                    'weight_used': e.weight_used,
                } for e in entries}
            else:
                logger.info(f"No schedule found for {today}, generating...")
                return generate_schedule(today)
        except Exception as e:
            logger.error(f"Failed to get today's schedule: {e}")
            return {}


def auto_expire_featured():
    """Mark shows as is_new=false if featured_until < today."""
    with get_session() as session:
        try:
            today = date.today()
            expired = session.query(Show).filter(
                Show.is_new == True,
                Show.featured_until < today
            ).all()
            for show in expired:
                show.is_new = False
                logger.info(f"Auto-expired: {show.title}")
            session.commit()
            logger.info(f"Expired {len(expired)} shows")
        except Exception as e:
            logger.error(f"Failed to expire featured shows: {e}", exc_info=True)
            session.rollback()
