DELETE FROM content_podcast_episodes
WHERE show_slug = 'poets-and-friends'
AND title IN ('Episode 2 — The Craft of a Line', 'Episode 1 — Open Mic Night');

SELECT 'Deleted fake Poets & Friends episodes' AS status;
SELECT COUNT(*) as remaining_episodes FROM content_podcast_episodes WHERE show_slug = 'poets-and-friends';
