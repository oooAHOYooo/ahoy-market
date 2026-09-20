#!/usr/bin/env python3
"""
Remove unwanted podcast shows and their episodes from the database.
Run after import_podcast_collection.py so these shows stay removed on deploy.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_session
from models import PodcastShow, PodcastEpisode

# Shows to remove from the live catalog (slug must match exactly).
UNWANTED_SHOW_SLUGS = ["my-friend", "tylers-show", "tyler-broadcast", "g-dub-disc-golf"]

# Specific episodes to remove (episode_id, show_slug).
UNWANTED_EPISODES = [("10", "the-rob-show")]  # The Rob Show #21 - Tony Rick and Andrew August


def main():
    with get_session() as session:
        n_ep = (
            session.query(PodcastEpisode)
            .filter(PodcastEpisode.show_slug.in_(UNWANTED_SHOW_SLUGS))
            .delete(synchronize_session=False)
        )
        n_show = (
            session.query(PodcastShow)
            .filter(PodcastShow.slug.in_(UNWANTED_SHOW_SLUGS))
            .delete(synchronize_session=False)
        )
        for ep_id, show_slug in UNWANTED_EPISODES:
            n_ep += (
                session.query(PodcastEpisode)
                .filter(
                    PodcastEpisode.episode_id == ep_id,
                    PodcastEpisode.show_slug == show_slug,
                )
                .delete(synchronize_session=False)
            )
        session.commit()
    if n_ep or n_show:
        print(f"Removed {n_ep} episodes and {n_show} shows: {UNWANTED_SHOW_SLUGS}")


if __name__ == "__main__":
    main()
