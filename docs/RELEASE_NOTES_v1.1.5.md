# Release Notes — v1.1.5

**Target platforms:** iOS, Android, Web, Desktop
**Status:** In progress — branched from v1.1.4 on May 22, 2026

---

## Changelog by Day

### May 22, 2026

| Commit | Feature |
|--------|---------|
| `a87bdd1d` | **Search page redesign** — Ahoy logo header, browse sections for artists/podcasts/videos, wide video thumbnails |
| `f3ad1548` | **Games Lab** moved to a nested item under Settings (no longer top-level nav) |
| `7f14ff96` | **Profile editing** — editable display name, member-since date, PNG/WebP avatar upload, sign out in quick access |
| `c940c1ba` | **Radio** split from hidden games section — now always visible without toggling games |
| `acb99a8a` | **Boost/Support flow polish** — SupportView improvements; `ahoy-cli` benchmark script added; old release notes docs archived |
| `cd2a6cac` | **AHOY TV mobile polish** |
| `5e86053f` | **Mobile touch polish** — larger tap targets and `:active` press states across nav, home, shows, podcasts |
| `85d2b2f1` | **Mobile deck** — Deck 3 now shows Saved instead of Search |
| `b67fce76` | **Podcasts mobile** — removed hero play button from podcast mobile header |
| `293a12d8` | **Mobile browse deck** — Saved removed from browse deck (now lives in Deck 3) |

---

### May 23, 2026

| Commit | Feature |
|--------|---------|
| `512cbf81` *(3:34 PM)* | **Mobile bottom bar** — fixed grid from 7 columns to 6 after deck swap |
| `b62fca09` *(3:46 PM)* | **What's New detail** — glass-morphism CTA button redesign (frosted, dark, backdrop blur); **Search input** — larger border radius, bigger font size, refined padding |

---

### May 25, 2026

| Commit | Feature |
|--------|---------|
| `185ffc3c` | **Boost page — artist bio/genre** — artist bio and genre tags appear above boost controls for emotional context; **amount slider** — $0.05–$1000 range replaces typed input |
| `459d5b04` | **Boost spotlight — media tags** — artist's tracks, albums, and shows surface as quick-reference tags in the spotlight panel |
| `aca4ad00` | **Boost spotlight — expandable preview** — media items expand in-place with inline bookmarking so fans can save without leaving the support flow |

---

### May 26, 2026

| Commit | Feature |
|--------|---------|
| `1bed90b9` *(9:08 AM)* | **Search UX** — catalog loads lazily on focus (not on page mount); recent searches redesigned as pill chips with individual remove buttons; search hint text shown when query is empty |
| `47928276` | **Performance benchmarking** — `ahoy-cli benchmark` for media startup baselines; `k6` OSS for API/load checks; documented in `docs/performance/` |
| `fe606dfe` | **Version bump to 1.1.5**; **Desktop top bar** — Account button shows user-circle icon + username; Search icon added; theme toggle (moon icon, lights up in accent color on Ayu Night); order: Account → Search → Theme → Bell → Settings |
| `88d86da7` *(12:14 PM)* | **Nav cleanup** — Events removed from left sidebar; Events feature card added to the bottom of the What's New archive instead |

---

### May 27, 2026

| Commit | Feature |
|--------|---------|
| `b8a6c383` | **Boost page — removed Support Ahoy section** — simplified boost flow to focus on direct artist support only; removed matching buttons and related math |
| `e3481f60` | **Video detail page — gallery heading** — renamed "Screenshots" to "Stills" across all video/film pages |

---

## Summary

### What's New

- **What's New detail** — thumbnail grid + lightbox browsing for gallery-backed updates, with keyboard and swipe navigation
- **Poems** — new experimental beta `/poems` surface for original work from the Poets & Friends community, with typeset reading and poet-profile links
- **Boost page** — artist bio, genre, $0.05–$1000 slider, media tag spotlight, expandable inline preview with bookmarking; Support Ahoy section removed for simplified flow
- **Search page** — redesigned with Ahoy logo, browse sections, pill-chip recent history, lazy catalog load
- **Profile** — editable name, avatar (PNG/WebP), member-since date
- **Desktop top bar** — account button, search icon, theme toggle

### Changed

- Games Lab nested under Settings
- Radio split from hidden games toggle
- Mobile Deck 3: Search → Saved
- Events moved from sidebar nav → What's New feature card
- Podcast mobile hero: play button removed
- Video detail page — gallery section renamed "Screenshots" → "Stills"
- **What's New detail hero** — thumbnail is now clickable, navigating directly to related video

### Performance

- `ahoy-cli benchmark` for media startup regression checks
- `k6` OSS for repeatable API/load testing (`/api/music`, `/api/search`, auth flows)
- Cache policy notes: keep the mobile fast path through hashed SPA assets, short-lived client caches where they help, and the `/refresh` escape hatch for deploy-sensitive content.

---

### June 2, 2026

| Commit | Feature |
|--------|---------|
| *(pending)* | **Global footer app nav** — synced the footer navigation with the desktop left rail so the shared footer now reflects the same route set and ordering, including Search, What's New, Studio, and Settings |
| *(pending)* | **Poems** — new experimental beta page at `/poems`; original poems from the Poets & Friends community with compact dark reading view, fullscreen toggle, handwritten scan toggle, and poet links to artist profiles. DB-backed via `poems` table on Render. Admin CRUD at `POST/PUT/DELETE /api/admin/poems`. Added Kyle Middleton's "The words in my head" and "Where do your best thoughts come from" from Poets & Friends #9 and #10, plus a linked Kyle Middleton poet profile. |
| *(pending)* | **Platform systems** — documented the current cache posture for fast mobile loads: HTML stays `no-store`, versioned SPA assets stay long-lived, and deploy-sensitive API data should favor freshness over broad browser caching so pushes do not get stuck behind old client state. |
| *(pending)* | **PostHog sync quality pass** — split env parity from analytics mirror checks, added `ahoy-cli posthog-env-check`, `ahoy-cli posthog-mirror-check`, and `ahoy-cli posthog-sync-check`, surfaced sync status in `/ops/stats`, and made Flask startup validation log only env drift |
| *(pending)* | **AHOY TV desktop scroll fix** — kept a footer visible on `/live-tv` while pinning the compact footer to the viewport so scrolling stops at the guide instead of jumping to the bottom footer |
| *(pending)* | **Podcasts video routing** — `Watch video` now maps Poets & Friends #10, falls back to `video_url`/`url` when a mapping is missing, and keeps the episode action row aligned in the two-column layout |

---

### June 3, 2026

| Commit | Feature |
|--------|---------|
| *(pending)* | **Breakpoint cleanup** — normalized the SPA shell so mobile/tablet rules hold through `1024px` and desktop chrome begins at `1025px`, removing the broken in-between sizing state in the header/sidebar/player shell |

---

### June 15, 2026

| Commit | Feature |
|--------|---------|
| *(pending)* | **What's New announcement** — Poets & Friends #12 event announced for Thursday, June 25th at 6:30 PM at Koffee?, New Haven, CT with Partiful RSVP link and event thumbnail |
| *(pending)* | **New music video** — Youth XL "Text Your Friends" (Official Music Video) by Kicker Pictures now available; imported from YouTube, hosted on GCS, and featured in What's New; links to https://youthxl.bandcamp.com/ for direct support |

---

### June 22, 2026

| Commit | Feature |
|--------|---------|
| *(pending)* | **New artist & track** — Cherrie Cherrie joins Ahoy with debut track "Waiting for the Long Days..."; artist profile at `/artists/cherrie-cherrie`, track available in music catalog, featured in What's New (June 2026) |

---

### July 2, 2026

| Commit | Feature |
|--------|---------|
| *(pending)* | **Poets & Friends #12 — Behind the Scenes** — behind-the-scenes photo gallery from Poets & Friends #12 (June 28, 2026); 7 photos by Spider in Stereo now available on `/studio/poets-and-friends-12-bts` and featured in What's New (June 2026 videos section). Photos captured the day after the event and hosted on GCS. |
| *(pending)* | **New short film & artist** — Kicker Pictures joins Ahoy as a filmmaker with their short film "Elvis" (15:47); imported from YouTube via `tools/youtube_to_bucket.py`, hosted on GCS (`short-films/kicker-pictures/`), on the Videos page with a NEW tag, and featured in What's New (July 2026). Artist page at `/artists/kicker-pictures` ties together the Elvis short film and the Youth XL "Text Your Friends" music video (now also on the Videos page). Seeded on deploy via `scripts/seed_kicker_pictures.py` in `migrate_and_start.sh` |

---

### July 6, 2026

| Commit | Feature |
|--------|---------|
| *(pending)* | **Left sidebar redesign** — grouped into Discover / Play / Community sections with a collapsible rail mode (208px ↔ 68px, persisted across sessions), tinted active-row + icon-chip highlighting, a scroll fade mask, and a footer Account row (avatar, name) alongside Settings. Desktop top bar simplified to notifications-only since Account/Settings now live in the sidebar. |
| *(pending)* | **Video detail screen polish** — rounded glass player frame with restyled transport controls (glass rewind/forward, solid magenta play button, monospace time pill), a slimmer indigo→magenta scrubber, and a restructured details panel (eyebrow meta row, byline, and pill-style Boost/Share/Save actions) on desktop. Same playback behavior as before — visual only. |

## Version Bumps

- `package.json`: `1.1.5`
- `android/app/build.gradle`: `versionName "1.1.5"` *(pending)*
- `ios/App/App.xcodeproj/project.pbxproj`: `MARKETING_VERSION = 1.1.5` *(pending)*
