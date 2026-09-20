# Release Notes — v1.1.3

**Target platforms:** iOS (TestFlight), Android (Play Store), Web, Desktop
**Status:** In progress

> v1.1.3 tightens shareable links and page previews so content URLs carry the right SEO metadata instead of falling back to the generic app shell.

---

## What's new in v1.1.3

- **Android Auto — full queue playback**: Radio, music, podcast episodes, and What's New items now expand into proper playable queues in Android Auto, so selecting any item plays through the full catalog rather than stopping after one track.
- **Android Auto — search**: Voice and text search in Android Auto now returns matching tracks and podcast episodes across the full catalog.
- **Android Auto — fresh catalog on reconnect**: The media catalog is re-fetched every time Android Auto connects, so content added since the last session is available immediately.
- **Volume sound cues**: Adjusting volume now plays a short audio cue — slide whistle going up, sad trombone going down.

- **Dynamic share previews**: Content pages now update Open Graph, Twitter, and canonical tags from the active route and loaded content so shared links preview the actual artist, track, video, podcast, or event.
- **Origin-aware sharing**: Share buttons now build URLs from the current public site origin instead of hardcoding the previous host, which keeps share links aligned with the deployed site.
- **Podcast audio/video split**: Podcast shows and episodes now surface separate `Listen audio` and `Watch video` actions when a matching video page exists, so listeners can choose the format without an extra picker.

---

## Changed

- **Now Playing — play button**: Play button now reads as the primary action with a brighter white-glass treatment, separating it visually from the secondary controls without adding color.
- **Now Playing — action labels**: Save, Boost, and Share buttons now show small uppercase labels below their icons so first-time users can identify each action. "Save" toggles to "Saved" when the track is bookmarked.
- **Now Playing — seek drag**: The seek bar now supports touch drag — tap and scrub to any position, with the thumb tracking your finger live. Playback pauses during drag and resumes on release. Hit area expanded to 28 px tall for easier targeting.
- **Podcast browse copy**: The podcast surfaces now use "newest" wording instead of repeated "latest" labels, and the show page now leads with the newest episode actions in a cleaner, denser row.

## Fixes

- **Podcast mobile action row**: The podcast video/audio choice now stays on one line on mobile, and the video badge was softened further so it reads like a subtle state marker instead of a loud callout.
- **Podcast video/audio split**: Podcast cards and show detail pages now show explicit `Listen audio` and `Watch video` actions for episodes that have a video version, and the video choice lands on the dedicated video page instead of opening an inline player.
- **Podcast label cleanup**: The podcast browse and show pages now use "Newest" wording for the freshness CTA and remove the extra `Latest` badge from the hero so the page reads cleaner without changing the show order.
- **Desktop cart shortcut removal**: The desktop app sidebar no longer shows the cart entry, while boost checkout still works through the existing artist and support flows.
- **Mobile deck toggle attachment**: The toggle now clips into the top edge of the bottom deck instead of floating as a separate badge, so it reads like part of the bar.
- **Mobile deck toggle attachment**: The deck toggle now has a small visual bridge into the bottom shell so it feels mounted above the menu instead of floating separately.
- **Mobile deck toggle placement**: The deck toggle now sits slightly above the mobile menu instead of overlapping the row content, which keeps the control attached without covering icons.
- **Ahoy support copy**: The Ahoy support card now changes its short description as you move through the dollar amounts, so the CTA reads more like a tiered support choice.
- **Boost filter highlight**: The active creator filter now uses a darker non-white accent so the selected chip stays readable without turning the row into a bright block.
- **Boost directory ordering**: The Boosts page now leads with the artist spotlight before the search and sort controls, and the selected artist card is wider on desktop so the artist selection reads first.
- **Mobile bottom deck sizing**: The mobile deck now uses a single shared frame height across the nav, player, and utility slots, so the bottom shell no longer feels like it changes size when you switch deck modes.
- **Default shell preview drift**: The SPA shell now includes a canonical link tag, and the server rewrites it for direct content visits so crawlers and social scrapers see the specific page URL rather than the homepage default.
- **Stale SPA asset fallback**: The Flask asset handler now rewrites `index.html` entrypoint links and falls back to the current `index-*.js` and `index-*.css` bundles when a stale hash is requested, which prevents a blank white screen if Render and the HTML shell drift out of sync.
- **Deploy self-heal**: The Render start path now verifies the built SPA bundle and rebuilds `spa-dist` before gunicorn starts when the hashed entrypoint assets are missing or stale, which closes the gap if the separate build step is skipped.
- **Render SPA dependency fix**: The SPA rebuild path now installs dev dependencies explicitly so `vite` is present during Render startup rebuilds.
- **Render SPA heap bump**: The SPA build now gives Vite a larger Node heap so Render does not abort with an out-of-memory crash during large production transforms.
- **Fresh SPA rebuild marker**: The SPA entrypoint now includes a harmless build stamp so a redeploy produces a new frontend bundle and avoids reusing an older cached build during rollout verification.
