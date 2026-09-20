# Ahoy App Overview

This document is the baseline product and architecture overview for Ahoy. It is intentionally broad and grounded in the current `app.py` entrypoint and route surface so it can expand as features stabilize.

## How To Use This Document

This file is meant to be the first-stop context file for future work sessions.

The intended workflow is:

- read this file first at the start of a new conversation
- use it to understand product intent before diving into code
- expand it whenever a bug fix or feature changes behavior, architecture, or product scope

This should stay concise enough to scan quickly, while linking conceptually to deeper docs elsewhere in `docs/`.

## What Ahoy Is

Ahoy is an indie media platform built around direct artist support.

At a high level, the app combines:

- music discovery
- artist profiles
- shows, podcasts, videos, and live programming
- user accounts, bookmarks, playlists, and listening history
- direct artist support through boosts/tips
- wallet, checkout, merch, and payout flows
- admin and operational tooling
- web, mobile, and desktop distribution

The current stack is a Flask backend plus a Vue 3 SPA frontend, with Capacitor and Electron projects for native/mobile packaging.

**Repository:** Private on GitHub (`oooAHOYooo/ahoy-little-platform`) as of 2026-04-22. Render deploys from `main` on push via authorized GitHub App — unaffected by private visibility.

## Current Product Shape

Reading `app.py` suggests the platform is trying to operate as a single product with three overlapping modes:

1. A consumer media app for listeners.
2. A commerce layer for supporting artists and buying merch.
3. An internal/admin control surface for moderation, analytics, fulfillment, and payment operations.

That same backend also serves health checks, diagnostics, search, and deployment-friendly SPA routing.

A fourth mode is emerging: **ambient play**. The `/radio` page has been simplified back to a station-first surface with live tune-in and mute controls, while the arcade/game ideas have been parked for a future hidden entry point instead of living on the radio route. Native car-mode radio now skips bad stream items instead of stalling on them, and the player prebuffers the next item or two when it can.

Native mobile and installed PWA wrappers now keep the same shell in portrait and landscape. Phones still get the mobile layout in both orientations, but landscape uses a tighter density scale so the chrome does not eat the whole viewport. The iOS and Android shells no longer force portrait, so the simulator and device can rotate freely.

The responsive SPA shell uses width plus runtime platform detection: normal desktop browsers get sidebar chrome from 1024px up, smaller widths use the mobile bottom-bar shell, and iPad/iPhone/Android/native mobile surfaces force the mobile shell even when their CSS viewport is wider than 1024px.

The desktop sidebar (`AppSidebar.vue`) is grouped into three labeled sections — **Discover** (Explore, Search, What's New), **Play** (Music, Podcasts, AHOY TV, Videos, Poems, Radio, Saved), **Community** (Artists, Studio) — plus a footer with Settings and an Account row (avatar, name, chevron). It supports a collapsible rail mode (208px expanded / 68px collapsed, toggled via the header button) persisted in `localStorage` through `useSidebarCollapse.js`; collapsed mode hides labels/group headers and falls back to icon-only rows with native `title` tooltips. Active rows get a tinted background plus a highlighted icon "chip". Because Settings and Account now live in the sidebar footer, the desktop top bar (`AppNavbar.vue`) no longer duplicates them — its right-side cluster is notifications-only.

The mobile bottom bar now uses a two-row frame with a shared mode switcher and a single fixed content stage across nav, player, and utility modes so the shell does not jump when the mode changes; the utility mode is intentionally compact and centers on a What's New teaser plus a small set of utility pills instead of a larger launcher grid. Platform-specific safe-area reserves are still applied inside that frame.

The theme system now defaults to `default` on first load. Saved explicit themes still apply, but the old random first-paint fallback is no longer used.

The delivery/cache system is intentionally conservative on the entry shell and aggressive on hashed assets: HTML is treated as `no-store`, SPA bundles use versioned filenames and long cache lifetimes, the service worker keeps a `/refresh` escape hatch, and only selected read-only API data uses client-side TTL caches. The goal is a fast mobile experience that still updates cleanly after deploys without asking users to do manual cache clears most of the time.

## Release history (short)

| Version | Highlight |
|---|---|
| 1.1.5 (current) | Boost/Support page enhancements: artist bio/genre, expandable media preview with inline bookmarking, artist media tags (tracks, albums, shows), $0.05–$1000 slider — see `docs/RELEASE_NOTES_v1.1.5.md` |
| 1.1.4 | Radio full-page redesign with Media Session + Wake Lock, profile editing, search browse sections, Games Lab separated, timer/memory cleanup, AHOY TV mobile polish — see `docs/RELEASE_NOTES_v1.1.4.md` |
| 1.1.2 | Radio mini-games (Three.js CMYK), Support Hub marketplace, glassmorphism consolidation, video library grouping, PostHog analytics — see `docs/RELEASE_NOTES_v1.1.2.md` |
| 1.1.0 | Cross-platform release line with mobile shell polish, podcast browse compacting, and car-mode playback stability — see `docs/RELEASE_NOTES_v1.1.0.md` |
| 1.0.9 | Cross-platform release line after Google Play v1.0.8, with AHOY TV pause stability and aligned native/web version metadata — see `docs/RELEASE_NOTES_v1.0.9.md` |
| 1.0.8 | Android deck safe-area fix, iPhone deck tightening, show-first podcasts, portrait-only mobile wrappers, GCS audio compatibility, and `/radio` tiny-skipper polish — see `docs/RELEASE_NOTES_v1.0.8.md` |
| 1.0.7.6 | Notification center and related release polish — see `docs/RELEASE_NOTES_v1.0.7.6.md` |
| 1.0.7 | First store release with public playlists and radio foundation — see `docs/RELEASE_NOTES_v1.0.7.md` |
| 1.0.5 | Mobile UI: MiniPlayer timeline hidden, 8-column icon nav |
| 1.0.4 | ContentHeader component, CarPlay/Android Auto radio, icon regen |
| 1.0.3 | UI glitch fixes |
| 1.0.0–1.0.2 | Initial Play Store + TestFlight launch |

Future upgrade ideas live in [`docs/FUTURE_UPGRADES.md`](\/Users\/agworkywork\/ahoy-little-platform\/docs\/FUTURE_UPGRADES.md).

## Core User Flows

### 1. Discover and play content

Users can browse music, shows, artists, podcasts, events, studio collections, and a "what's new" feed. There are also routes for daily playlists, now playing, and search/suggestions.

The home hero search is an instant client-side preview over music, artists, shows, podcast shows, podcast episodes, and events. It accepts both array-shaped API payloads and object-keyed JSON fallbacks so offline/static fallback data still produces matches while typing. Home search and the `/search` route share the same client search helpers for payload normalization, in-memory catalog caching, relevance ranking, match highlighting, readable result labels, and result URL routing. Home search supports keyboard selection, a loading state while the catalog hydrates, a no-results state, a view-all handoff to `/search?q=...`, and pressing Enter opens the top current match.

The now-playing overlay now includes podcast skip controls, playback speed cycling, sleep timer access, and podcast resume state, while the Podcasts page uses a horizontal show strip on mobile to keep show switching dense and touch-friendly. The podcast browse surface now favors "newest" wording over repeated "latest" badges so the freshness cues are cleaner without changing the episode ordering, and video-backed podcast episodes now expose obvious `Listen audio` / `Watch video` actions that stay on one row on mobile and send the user to the dedicated video page when a show has a matching video entry. Episodes can also fall back to a direct `video_url`/`url` when a matching internal video page is not mapped yet, which keeps newer Poets & Friends video entries reachable without waiting on a slug table update.

The Podcasts page now uses a show-first layout: featured show cards are entry points, and the main feed is grouped by show so individual series like The Rob Show stay reachable. Video-first series such as G-Dub Disc Golf belong in the video catalog and are hidden from the podcast API if they appear in the content database.

The Videos page now groups the library by content type first, using buckets like music videos, live shows, and films/shorts before falling back to an everything-else section. Those section shelves now sort by the newest item they contain, and each section header shows a small recency label so fresh uploads are obvious without opening the section. The Podcasts page uses the same recency-label pattern on each show section and orders the show sections by the newest episode inside them, while still keeping the show-first browse structure intact. The show catalog endpoint is read fresh so newly imported videos appear without waiting on stale cache windows. Individual video detail pages can surface both a type-based rail and the existing "More from [artist]" rail when enough matching videos exist, and their fullscreen mode keeps the same shell while the video stage takes over the screen. They also use a smaller transparent `u_ahoy23.png` watermark that stays in the top-right corner and fades down when fullscreen controls settle, instead of a square placeholder, so the brand mark stays visible over the player. Video detail URLs also emit server-side Open Graph and Twitter metadata using the thumbnail, title, and description so shared links preview the specific video art instead of the default app icon.

The Music page now leans on reusable filter controls: the artist selector is a dropdown, the track list defaults to newest-first sorting, and the shared footer, desktop now-playing transport, and mobile deck player show seekable timelines for finite-duration tracks so playback progress stays visible in the global shell.

Individual artist pages now group music by album when album metadata exists. They prefer the artist's own album list, then infer album sections from track metadata, and still render any remaining tracks in an "Other Tracks" section so the full catalog stays visible.

Artist-page video cards now link to the internal video detail route using a stable video slug, and the video detail view resolves those slugs back to the matching show when the data does not already expose one directly.

Explore widgets and the video detail "More" rails follow the same rule so video thumbnails stay inside the app until the user explicitly starts playback.

The Account page now keeps security controls in a collapsed disclosure so password changes, sign out, and account deletion do not dominate the page by default.

The repo also includes a small repair script, `scripts/convert_podcast_videos_to_audio.py`, for podcast rows that still point at video files. It detects video-backed podcast entries, converts them with `ffmpeg`, and can upload the resulting MP3s to GCS before the podcast URLs are rewritten.

The What's New surface borrows the mobile media-library pattern: phones get a compact archive summary hero, thumbnail-aware latest strip, section-hinted month rows, compact tappable month-feed rows, a simplified detail page with previous/next month-item navigation, route-specific empty-notification suppression, and bottom-safe action pills so updates stay scannable above the bottom deck instead of using the larger desktop cards. Month-view featured art now sits in a square frame and uses contained artwork so update imagery is not clipped.

The Poems surface now gives the Poets & Friends community a dedicated reading view for original work, with poet profile links, a compact dark reading mode with fullscreen support, and a lightweight archive that slots into the same month-driven content system as What's New.

The homepage "What's New at Ahoy" widget surfaces the seven newest updates from `/api/whats-new`, with the newest item promoted as the spotlight and the next six shown as compact secondary entries.

Individual video pages do not show a generic "Related" rail. When the current video has other videos from the same `host_slug`, `host_id`, or host name, the detail page shows "More from [artist]" with those videos; otherwise the rail is omitted.

Shareable detail URLs are now SEO-aware at both layers: the Flask shell rewrites Open Graph, Twitter, and canonical tags from the current route, and the SPA updates the same tags again after route/content loads so shares and crawlers both see the specific page rather than the default homepage shell.

AHOY TV is treated as its own video surface: desktop keeps a persistent channel rail and playback controls visible, while mobile uses a drawer-first channel browser with quick channel pills so channel switching does not depend on hover. The AHOY TV schedule is anchored to a stable guide timeline, paused live playback must stay paused through slot refreshes and the route handoff into the global video player, the TV route uses the compact footer as a fixed bottom anchor so the guide remains the scroll stop, and fullscreen playback is allowed to break out of the phone portrait guard while keeping the small top-right watermark visible before it fades.

Relevant API areas in `app.py`:

- `/api/music`
- `/api/shows`
- `/api/artists`
- `/api/podcasts`
- `/api/events`
- `/api/studio`
- `/api/whats-new`
- `/api/now-playing`
- `POST /api/media/resolve` — batch-resolve playlist item IDs to metadata
- `/api/daily-playlist`
- `/api/search`
- `/api/suggest`

Analytics ownership is split across two layers:

- Public web analytics now flow through PostHog in the SPA shell, with pageviews, autocapture, and authenticated identity stitching handled client-side.
- The Flask SPA response injects PostHog runtime config from environment variables so the same build can be enabled without editing the frontend bundle.
- Video playback now emits `video_watch_start`, `video_watch_progress`, `video_watch_stop`, and `video_watch_complete` so watch counts and watch duration can be measured from the native player surfaces.
- Owner stats now expose a watch funnel and top watched videos in `/ops/stats` plus the `ahoy-cli stats` / `handoff` output.
- First-party product analytics still live in the app's PostgreSQL `analytics_events` table and power the admin analytics endpoint.
- Anonymous playback now maps to a dedicated internal guest account so guest listening can count without changing the listening session schema.
- The `/ops/stats` page now includes a compact daily trend view, and `ahoy-cli posthog-import <file>` can seed PostHog exports into the same first-party analytics table later.
- `ahoy-cli posthog-env-check`, `ahoy-cli posthog-mirror-check`, and `ahoy-cli posthog-sync-check` now split PostHog env parity from PostHog mirror checks, while the `/ops/stats` sync panel shows both together and Flask logs only env drift at startup.
- The sibling `ahoy-mgmt` repo reads the same live database to produce operator-facing daily snapshots and traffic trackers.
- A repo-local `ahoy-cli` entry point now exposes `status`, `stats`, and `handoff` commands so future agents and the owner can get a quick source-of-truth summary from the repo root.
- `ahoy-cli benchmark` scores media startup from exported diagnostics so release notes can track a repeatable mobile performance baseline.
- `ahoy-cli backfill` can seed recoverable historical analytics into `analytics_events` from users, purchases, tips, and wallet transactions so the stats pages have meaningful history.
- The internal `/ops/stats` page is owner-only and reuses the same analytics snapshot data for a browser view of active users, signups, listening hours, and top pages/content.

Studio collections are DB-backed via `StudioCollection` in `models.py`. Use the idempotent scripts in `scripts/add_*_studio.py` for one-off photo drops; the current Poets & Friends #10 BTS drop lives in `scripts/add_poets10_studio.py` and mirrors to `static/data/studio.json` for packaged fallback content.

### 2. Create an account and personalize the experience

The app supports authenticated users, guest behavior, profile updates, password reset/change flows, playlists, bookmarks, follows, and listening stats/history.

Password recovery is available through the SPA routes `/auth/forgot` and `/auth/reset`, backed by `/api/auth/password-reset/request` and `/api/auth/password-reset/confirm`. Email delivery requires production email configuration (`RESEND_API_KEY` + `SUPPORT_EMAIL`, or the SMTP env vars). Logged-in users can change a temporary password from the Account and Settings pages via `/api/auth/change-password`, which verifies the current password before writing a new hash. For in-person promos, `scripts/create_promo_accounts.py` creates database users with unique usernames and strong temporary passwords and exports a print-ready credential CSV with login URL and change-password instructions.

**Playlists** are stored in Postgres (`playlists` + `playlist_items` tables). Each playlist has a `visibility` field: `private` (default, owner-only), `public` (listed in discovery feed, readable by anyone), or `unlisted` (accessible by link, not listed). Public and unlisted playlists are readable by unauthenticated guests at `/playlists/:id`. The detail view resolves raw `media_id` values to titles/artwork/duration via `POST /api/media/resolve` (a batch endpoint, avoids fetching full catalogs). Guest users see a sign-up CTA. Only the owner can write. The `description` field is optional. Migrations `a3f1b2c4d5e6` + `b4g2c3d5e6f7` add these columns — run `alembic upgrade head` before deploying. See `memory/feature_public_playlists.md` for full implementation notes.

Relevant areas:

- `blueprints/api/auth.py`
- `blueprints/api/playlists.py`
- `blueprints/api/bookmarks.py`
- `scripts/create_promo_accounts.py`
- `/api/user/profile`
- `/api/user/stats`
- `/api/guest-data`
- `/artists/<artist_id>/follow`
- `/api/artists/follow`
- `/api/artists/unfollow`
- `/api/listening/start`
- `/api/listening/end`
- `/api/listening/stats`

### 3. Support artists financially

Ahoy is not only a streaming/discovery app. A major part of the product is direct money movement between fans and artists.

This currently includes:

- boosts/tips
- a dedicated `/support` marketplace that leads with artist boosts, puts the artist spotlight above the browse controls, uses an artist-page-style circular spotlight thumbnail, keeps the browse and portfolio sections compact, adds browse sorting and marketplace stats, gives the Ahoy support card amount-aware copy, collapses the artist CTA into the card footer, and keeps a separate Ahoy support card below the directory as an optional second line item
- the desktop app sidebar no longer shows a cart shortcut; boost checkout still exists through the artist and support flows
- the experimental `/marketplace` digital catalog supports a local “save for later” list; digital releases do not enter boost checkout because a digital-order, payment, and fulfillment contract is not implemented yet
- wallet funding and wallet-based purchases
- Stripe checkout integration
- merch purchases
- payout support and transaction tracking

Relevant areas:

- `blueprints/payments.py`
- `blueprints/api/tips.py`
- `routes/boost_stripe.py`
- `routes/stripe_webhooks.py`
- `/checkout`
- `/checkout/process`
- `/success`
- `/api/config/stripe`

### 4. Operate the platform

The app contains explicit operational routes for health, readiness, payment debugging, webhook monitoring, analytics, order handling, and admin user management.

Relevant areas:

- `/healthz`
- `/readyz`
- `/ops/debug/payments`
- `/ops/debug/checkout`
- `/ops/status/api`
- `/ops/webhooks/monitor`
- `/api/admin/stats`
- `/api/admin/analytics`
- `/api/admin/users`
- `/api/admin/orders`
- `blueprints/admin.py`

## Architecture Summary

### Backend

- `app.py` is the main Flask application entrypoint and still owns a large amount of route logic.
- Blueprints are already used for auth, playlists, bookmarks, tips, feedback, admin, activity, payments, and Stripe-related flows.
- Security and operational concerns are initialized early: sessions, login management, rate limiting, CORS, compression, CSRF, security headers, request logging, and Sentry wiring.

### Frontend

- `spa/` is the primary frontend application.
- `spa-dist/` is the built frontend served by Flask.
- `templates/` still exists for legacy/server-rendered pages and some admin/auth surfaces.
- Unknown frontend routes fall back to the SPA index so the client router can own the main app experience.

### Data

Content appears to be in a transition model:

- runtime prefers the database
- JSON files still exist as editable/source content in parts of the workflow
- import/sync scripts move local content into the runtime database

Key hints from the codebase:

- `services/content_db.py` is a central content access layer
- `search_indexer.py` builds a search index from DB data first, then JSON fallback
- the app can run locally with SQLite when `DATABASE_URL` is absent
- Alembic migrations are present for schema evolution

### Delivery Targets

This is not just a website repository.

The codebase includes:

- web app
- PWA assets
- Capacitor Android project
- Capacitor iOS project
- Electron desktop app for direct macOS/Windows/Linux downloads
- Mac Catalyst archive path for App Store Connect distribution
- release and packaging scripts

That implies the product goal is a unified media platform shipped across browser, phone, and desktop.

The current Electron macOS path is a direct-distribution desktop app flow, not a Mac App Store flow. The Mac App Store path now runs through the Capacitor iOS target as a Mac Catalyst archive, which is a separate signing/package shape from the current DMG/ZIP release path.

### Release Workflow

The repo also contains developer-operated release orchestration for mobile distribution.

`fire.py` is a human-in-the-loop mobile release helper that:

- reads the app version from `package.json`
- performs preflight checks for expected tools and project paths
- runs Capacitor sync for iOS and Android
- boots an iOS simulator and Android emulator
- tries to build and launch the app on both targets for manual testing
- pauses until the operator explicitly approves the release
- builds an iOS archive and Android AAB for store submission
- supports scoped runs such as iOS-only, Android-only, test-only, and build-only

This is a strong signal that the intended release process is not fully automated CI-only publishing. The product currently expects a manual QA gate before shipping mobile builds to TestFlight and Google Play.

## Local Runtime Note

Running `python app.py` in the current repo confirms the direct app entrypoint works locally.

In this environment it:

- starts the Flask app without `DATABASE_URL`
- falls back to local SQLite
- enables filesystem-backed sessions
- warns when DB-backed content is missing and falls back to JSON for at least some content paths

## Product Rules And Recent Decisions

Use this section to capture rules that should survive individual conversations and PRs.

Keep entries short and practical. Add to this section when a bug fix or feature introduces a rule that future work should preserve.

Suggested entry format:

- 2026-04-26: For public S3/GCS media playback, do not force `crossOrigin = 'anonymous'` on `<audio>` elements unless the bucket CORS policy is verified to return the needed `Access-Control-Allow-Origin` headers. See `docs/troubleshooting/GCS_AUDIO_DELIVERY.md`.

- `YYYY-MM-DD` - short rule or decision
- Impact: what future changes should respect

Current rules:

- `2026-04-21` - `docs/APP_OVERVIEW.md` is the default product-memory anchor for new work sessions in this repo.
- Impact: read this file before making product or architecture assumptions, and update it when behavior or scope changes.

- `2026-04-21` - Documentation should be updated in the same task as meaningful behavior, feature, architecture, setup, or deployment changes.
- Impact: avoid treating docs as deferred cleanup; keep the repo itself as the durable source of project memory.

- `2026-05-22` - Radio is a standalone full-page station (`/radio`). Games Lab lives under Settings as a nested item, not on the radio route.
- Impact: do not re-merge games into the radio route; radio should stay focused on the live station experience.

- `2026-05-26` - Desktop sidebar and mobile dock should stay in parity for all primary content sections.
- Impact: when adding a new primary nav section, add it to both surfaces. Events is intentionally desktop-only for now (planned as a What's New subpage on mobile in a future cycle). Theme toggle lives in both the desktop top bar and mobile Deck 3.

- `2026-07-06` - Desktop sidebar redesigned into grouped sections (Discover / Play / Community) with a collapsible rail mode; current desktop sidebar order: Explore, Search, What's New, Music, Podcasts, AHOY TV, Videos, Poems, Radio, Saved, Artists, Studio, then a footer with Settings and Account. Desktop top bar right cluster is now notifications-only — Account and Settings moved to the sidebar footer and were removed from `AppNavbar.vue` to avoid duplication.
- Impact: when adding a new primary nav section, add it to the correct sidebar group (and to the mobile dock for parity). Don't re-add Account/Settings to the desktop top bar — the sidebar footer owns them app-wide now.

- `2026-04-28` - Electron desktop releases and Mac App Store releases are separate paths.
- Impact: keep DMG/ZIP GitHub-release packaging distinct from any sandboxed App Store Connect target and do not assume one can upload to the other unchanged.

- `2026-04-21` - Mobile releases currently use a human approval gate between emulator testing and store-build generation.
- Impact: preserve the manual validation step unless the release process is intentionally redesigned and documented.

- `2026-04-21` - `fire.py` is structured as a phased release helper with preflight validation and optional scoped modes, not just a one-off script.
- Impact: future release automation should extend the existing phases and flags rather than reintroducing more hardcoded ad hoc flow.

## What `app.py` Reveals About Intent

`app.py` makes the product intent unusually visible because it contains both core API routes and operational wiring.

From that file alone, the intended platform seems to be:

- media-rich rather than music-only
- commerce-enabled rather than content-only
- creator-support oriented rather than ad-driven
- SPA-first on the frontend
- operationally self-hosted enough to need health/debug/admin endpoints

In other words: Ahoy is trying to be a direct-to-artist media and commerce platform, not just a content catalog.

## Important Code Areas To Expand Later

This document should eventually grow dedicated sections for:

- authentication and account model
- content model and ingestion pipeline
- search indexing and discovery logic
- listening/session tracking
- playlists, bookmarks, and personalization
- wallet, boosts, merch, and payout architecture
- admin and analytics surfaces
- SPA frontend structure
- mobile and desktop packaging
- deployment environments and required services

## Practical Starting Points

If you are trying to understand or extend the app, start here:

- `app.py` for runtime wiring and top-level routes
- `blueprints/` for modular backend features
- `services/content_db.py` for content access patterns
- `models.py` for the core data model
- `spa/src/` for the main user-facing frontend
- `docs/setup/` and `docs/deployment/` for environment-specific setup

## Mobile Layout System (as of v1.0.9)

### Gold standard: StudioView
Studio is the reference implementation for mobile page layout. All nav pages should match its pattern.

### How it works
All main nav pages use `flush-content` in `App.vue` — this zeroes out the outer `app-content` shell padding on mobile/tablet (`≤1024px`) so iPad uses the bottom-dock shell instead of the fixed desktop sidebar. Each page's top-level container then manages its own spacing via CSS tokens:

```css
/* Mobile page container — the pattern every nav page uses */
padding: var(--mobile-top-offset, 36px) var(--mobile-gutter, 4px) var(--mobile-bottom-clear, 100px);
```

### Tokens (defined in `static/css/main.css` `:root` at `@media (max-width: 1024px)`)
| Token | Value | Purpose |
|---|---|---|
| `--mobile-gutter` | `4px` | Side padding on all page containers |
| `--mobile-top-offset` | `36px` | Top padding below the fixed topbar |
| `--mobile-bottom-clear` | `100px` | Bottom clearance above the dock |
| `--gutter` | `0px` | Outer shell padding — always 0 on mobile |

**To adjust all mobile side padding at once:** change `--mobile-gutter` in `main.css`. Desktop is unaffected.

### flush-content pages (outer shell = 0 on mobile)
`home`, `artists`, `support`, `events`, `videos`, `merch`, `music`, `podcasts`, `live-tv`, `radio`, `saved`, `account`, `studio`, `artist-detail`, `whats-new`, `wallet`, `tip-artist`, `performances`, `studio-collection`

Desktop layout starts at `1025px` on the web, but native iOS is platform-driven rather than width-driven: `body.platform-ios` forces the phone-style touch shell on both iPhone and iPad. That keeps iPad on the bottom-dock experience even when the iPad Pro viewport is wider than 1024 CSS pixels.

## Notification Center (as of v1.0.7.6)

The app collects system notifications (new content alerts, connectivity status) into a persistent notification center instead of ephemeral toasts.

### Architecture

- **`useNotificationCenter()`** — Composable managing notification state. Notifications auto-dismiss after 24 hours.
- **`NotificationOverlay.vue`** — Global UI component (mounted in `App.vue`). Shows as a right-sliding panel on mobile, dropdown on desktop.
- **Trigger points** — `useContentDropDetector()` (new videos/podcasts/music/events), app reconnect (back online).

### UI

- **Mobile:** Bell icon in minimal top-right nav bar. Clicking opens slide-in panel from right showing notification history.
- **Desktop:** Bell icon is the only element in the top-right navbar cluster (Account/Settings now live in the sidebar footer). Clicking opens dropdown panel.
- **Badge:** Red count badge on bell pulses when notifications are present.
- **Panel:** Each notification shows message, timestamp ("5m ago", "2h ago"), and dismiss button. "Clear all" button at bottom.
- **Mobile deck 3:** A compact What's New summary card opens the notification center, with utility pills kept to Boosts, Settings, and Theme so the surface stays short and does not crowd the dock.

### Adding New Notifications

```javascript
import { useNotificationCenter } from '@/composables/useNotificationCenter'

const { addNotification } = useNotificationCenter()
addNotification('New music added', 'music', 8000)  // 8 second auto-dismiss
addNotification('Something important', 'success')   // 24 hour default auto-dismiss
addNotification('Sticky alert', 'error', false)     // Never auto-dismiss
```

## Suggested Next Documentation Passes

The next high-value docs to write after this one are:

1. A feature map that groups routes, services, models, and UI screens by product area.
2. A data flow document covering JSON, DB, import scripts, and search indexing.
3. A payments document covering wallet, Stripe, boosts, merch, webhooks, and payouts.
4. A frontend architecture document for the SPA and native wrappers.

## Source Basis

This overview is based primarily on:

- `app.py`
- `README.md`
- `docs/README.md`
- the current repository structure

It should be treated as a living overview, not a final specification.
