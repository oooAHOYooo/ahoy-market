*Last Updated: 2026-03-25T07:42:27-04:00*

# AI Development Changelog

This file contains logs of changes made by AI agents to help maintain context across different sessions and agents.

## 2026-03-25: Video Podcast Routing Fix
**Agent/Session**: Routing & Data Fixes

### Issue Summary
When clicking a full video episode or video clip from the "Tyler Needs a Break" podcast section:
- The router correctly tried to navigate to a video id (`/player?id=tyler-needs-a-break-ep4-full&type=show`).
- However, `router.js` intercepts `/player` and automatically redirects it to `/now-playing`, which is the global audio player.
- Additionally, video podcast clips lacked the correct routing logic entirely and simply added themselves to the audio queue.

### Changes Made
1. **Routing Updates in `PodcastDetailView.vue`**:
   - `playLatest` and `playEpisode` now programmatically navigate correctly to `/videos/:id` instead of `/player?id=...`.
   - Replaced inline audio queuing logic (`playerStore.setQueue`) for individual "clips" with a dedicated `playClip(idx)` function.
   - The `playClip` function checks if the clip is part of a known video podcast (e.g. `tyler-needs-a-break`). If it is, the clip routes straight to its dedicated video page (`/videos/:id`).
   
2. **Data Availability (`videos.json` vs DB)**:
   - Investigated `content_db.py` backend logic (`get_all_shows` and `get_all_podcasts`).
   - The backend specifically merges `Show` records (which `seed_tyler_ep4_clips.py` seeds the Tyler Needs a Break clips into) with the events/videos dictionary, ensuring all these Tyler clips accurately show up in the central "Videos" (`/api/shows`) section on production safely, even if they aren't written natively into the fallback static `videos.json` schema.

3. **Rebuild & Git**:
   - Rebuilt the standard SPA bundle (`npm run build`).
   - Standardized and pushed the corrected source code and `spa-dist` compiled bundles to the `main` branch upstream.

### Validation Results
- Codebase changes manually checked.
- Routing paths verified against legacy aliases in `router.js`.
- Successfully built and pushed to remote origin.

_Note: The `/now-playing` app route is the core audio player route intended strictly for MP3 tracks, music streams, and audio-only podcasts._
