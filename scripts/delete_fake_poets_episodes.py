#!/usr/bin/env python3
"""
Delete specific fake Poets & Friends episodes: Episode 1 and Episode 2
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_session
from models import PodcastEpisode

FAKE_TITLES = [
    "Episode 2 — The Craft of a Line",
    "Episode 1 — Open Mic Night",
]

def cleanup():
    print("Deleting fake Poets & Friends episodes...")

    with get_session() as session:
        # Find and delete episodes with fake titles
        episodes_deleted = 0
        for title in FAKE_TITLES:
            count = session.query(PodcastEpisode).filter(
                PodcastEpisode.title == title,
                PodcastEpisode.show_slug == "poets-and-friends"
            ).delete(synchronize_session=False)
            episodes_deleted += count
            if count > 0:
                print(f"  Deleted '{title}': {count} episode(s)")

        session.commit()

        print(f"\nTotal deleted: {episodes_deleted} episodes.")
        print("Cleanup complete.")

if __name__ == "__main__":
    cleanup()
