#!/usr/bin/env python3
"""
Regenerate AHOY TV schedule for today.
Run daily at midnight UTC via cron or scheduler.

Usage:
  python scripts/regenerate_live_tv_schedule.py

Exit codes:
  0 = success
  1 = error
"""

import sys
import os
import logging
from datetime import date
from pathlib import Path

# Add parent directory to path so imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger(__name__)

try:
    from services.live_tv_scheduler import generate_schedule, auto_expire_featured
    from db import get_session
    from models import Show

    logger.info("🎬 Regenerating AHOY TV schedule...")

    # Step 1: Auto-expire featured shows
    try:
        auto_expire_featured()
        logger.info("✓ Expired old featured shows")
    except Exception as e:
        logger.warning(f"Failed to auto-expire featured shows: {e}")

    # Step 2: Generate new schedule
    schedule = generate_schedule(date.today())
    logger.info(f"✓ Generated schedule for {date.today()}: {len(schedule)} slots")

    # Step 3: Report stats
    prime_slots = [d for d in schedule.values() if d.get('is_prime_time')]
    new_slots = [d for d in prime_slots if d.get('weight_used') == 'new']
    random_slots = [d for d in prime_slots if d.get('weight_used') == 'random']

    logger.info(f"Prime-time slots: {len(prime_slots)} (new: {len(new_slots)}, random: {len(random_slots)})")

    sys.exit(0)

except Exception as e:
    logger.error(f"✗ Failed to regenerate schedule: {e}", exc_info=True)
    sys.exit(1)
