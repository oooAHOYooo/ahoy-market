# Release Notes — v1.0.7

**Target platforms:** iOS (TestFlight), Android (Play Store internal), Web, Desktop
**Release date:** 2026-04-24
**Status:** In progress — SPA built, `cap sync ios` complete. Pending: `python fire.py` → iOS archive upload + Android AAB upload.

> v1.0.7 is the first store release to carry the v1.0.6 radio and public-playlist work. v1.0.6 was tagged in git (2026-04-22) but never shipped to TestFlight/Play Console; both releases are bundled into this upload. See **Rolled up from v1.0.6** below.

---

## What's new in v1.0.7

### Mobile layout system unified

The key UX fix of this release. All main nav pages now use the same flush-content pattern introduced in Studio, with one CSS variable controlling mobile side padding across the app.

**What changed:**
- `--mobile-gutter: 4px` defined once in `static/css/main.css` at `@media (max-width: 768px)` — one line now controls every nav page's mobile side padding
- `flush-content` class applied to `artists`, `events`, `videos`, `merch` outer shells (previously had `20px` double-padding)
- `HomeView` switched from hardcoded `8px` to `var(--mobile-gutter, 4px)`
- `EventsView` switched from hardcoded `1rem` to `var(--mobile-gutter, 4px)`
- Cards now sit flush to the edges with a consistent 4px breathing room; desktop layouts unaffected
- StudioView is the reference implementation — see `docs/APP_OVERVIEW.md` → "Mobile Layout System"

**Why:** cards on nav pages were getting ~24px combined padding (outer shell + inner container) vs Studio's flush look. Inconsistent per page, felt cramped on narrow phones.

---

### iOS bottom deck flush

Bottom dock now sits flush against the home indicator area instead of floating with a visible gap. Dock height and dock spacing retuned for the new flush look. `spa/src/assets/platform-ios.css` carries the iOS-specific dock tokens.

---

### AHOY TV — architecture refactor + mobile UX

Schedule state and playback state are now split into `useLiveTvSchedule()` and `useLiveTvPlayback()` composables instead of being rebuilt inline in `LiveTVView.vue`. Mobile gets a dedicated control surface, a branded standby state, and an extracted channel drawer; desktop keeps the wider guide-oriented layout.

**Specifics:**
- Mobile idle state: taller hero, direct `Open Channels` CTA, quick-pick channel pills (no more dead empty screen)
- Mobile controls split into idle vs playback states — idle only shows channel-picking actions, playback controls appear after a live stream starts
- Slot transitions now driven by boundary-based refreshes rather than a 1-second full-page playback-engine loop
- Hero playback records lightweight video diagnostics in `ahoy.videoDiagnostics` (source classification + load timing)

---

### Audio load times optimized

- Metadata preload on track mount
- Next-track prefetch
- Lazy restore for queue rehydration on cold start

Perceptible win on first-tap-to-play latency, especially on mobile Safari.

---

### Radio / owl runner refactor

The owl scene behind the radio page is being built into a runner minigame. Input handling, lane transitions, and particle systems were refactored; controls split from rendering. GDD added at `docs/` with the artist-bird mechanic locked in as the emotional core. Home exit button added for easier escape.

**Not in this release:** server-authoritative scheduling, finished gameplay loop, social features. Gameplay is still ambient/experimental.

### Radio gameplay tuning + now-playing HUD card

- Radio game controls are now one-touch/click-first: tap or click a lane to steer, with tap-pop tricks, and no drag requirement
- Gameplay feel was flattened toward 2D platforming by locking vertical steering and softening camera depth dynamics
- Particle bloom and spray brightness were reduced for calmer visuals while listening
- Added a top-right glass now-playing widget on `/radio` that shows live track art/title/artist and doubles as a quick radio mute/unmute control

---

### Settings — accent color slider + cleaner UI section

- **Accent color** is now a hipster-gradient slider (terracotta → mustard → sage → teal → indigo → plum → dusty rose) with a live preview swatch instead of six fixed chips. Position is stored as `accentPos` (0–100) and interpolates between curated stops.
- **Compact mode** toggle removed from Settings — was a dead control with no consumers in the SPA.
- **Fractal Glass** is now a first-class option in the Theme dropdown; the floating `FX` button is gone.

---

### Mobile deck polish

Deck spacing tuned across mobile nav states; behavior refined in relation to AHOY TV mobile controls so there is no overlap or floating gap between the dock and the playback surface.

---

### Themes — Fractal Glass added (test layer)

Themes now include a new "Fractal Glass" (Vitrium Opus) layer sitting alongside the existing four. Fractal is implemented as a strictly-scoped overlay — it activates only when `data-theme="fractal"` is set on `<html>` and leaves every other theme's CSS untouched. As of 2026-04-24, Fractal Glass is selectable directly from **Settings → Appearance → Theme**; the standalone `FX` toggle pill has been retired. Existing `ahoyFractalTheme` storage migrates into the unified `ahoyTheme` key on next load.

#### Existing theme palette (unchanged)

| Theme | Trigger | Primary | Secondary | Accent | Background gradient | Text |
|---|---|---|---|---|---|---|
| **Deep Blue** | `body.theme-deep-blue` | `#00a2ff` electric blue | `#0066ff` deep blue | `#00ffff` cyan glow | `radial-gradient(#0a1f44 → #040810)` | `#ffffff` |
| **After Dark** | `body.theme-after-dark` | `#ff4d00` orange-red | `#9d00ff` vivid purple | `#ff9100` amber/gold | `linear-gradient(#120b1f → #2a0e36)` | `#ffffff` |
| **Alien Tundra** | `body.theme-alien-tundra` | `#ff2a75` vivid pink | `#00d4ff` ice cyan | `#ff85a2` lighter pink | `linear-gradient(#0a1118 → #1a2a3a)` | `#ffffff` |
| **Mint** | `body.theme-mint` | `#4ecdc4` mint teal | `#81BFB7` wintergreen | `#a8edea` ice mint | `radial-gradient(#0d2b20 → #061a14 → #030e09)` | `#e8f8f5` |

Cycle key: **`L`** cycles `default → deep-blue → after-dark → alien-tundra → mint → random`. Persisted in `localStorage` under `ahoyTheme`. Source: `spa/src/composables/useTheme.js`, definitions in `spa/src/assets/main.css` (lines 879–1138).

#### New: Fractal Glass (Vitrium Opus)

Deep navy with sunset-peach + crimson accents, mimicking light through anamorphic glass.

| Token | Value | Role |
|---|---|---|
| `--color-bg-base` | `#101E2E` | Page background (deep navy) |
| `--color-bg-surface` | `#242F49` | Cards, navbars, mini-player, sidebar |
| `--color-accent-peach` | `#FFA586` | Primary buttons, active links, highlights |
| `--color-accent-crimson` | `#B51A2B` | Secondary / destructive buttons, alerts |
| `--color-glass-border` | `rgba(56, 67, 88, 0.5)` | Surface borders |
| `--color-text-primary` | `#F2F4F7` | High-contrast off-white body text |
| `--fractal-blur` | `16px` | `backdrop-filter` on every surface |

**Implementation:**
- `spa/src/assets/themes/fractal.css` — every selector is prefixed with `:root[data-theme='fractal']`, so removing the attribute restores the previous theme without lingering styles
- `spa/src/components/ThemeTestToggle.vue` — fixed-position toggle pill (top-right, `z-index: 9999`), persists state in `localStorage` under `ahoyFractalTheme`
- Mounted globally in `App.vue`; CSS imported once in `main.js`
- `useTheme.js` is **not** modified — Fractal layers on top of any existing body-class theme by setting `<html data-theme="fractal">`
- `@supports` fallback fills surfaces with solid `#2A3654` on browsers without `backdrop-filter`

**Constraint honoured:** no other theme touched. Existing `body.theme-*` rules, `useTheme.js`, the `L` cycle, and the Settings theme picker are unchanged.

---

## Fixes

- **Portrait-only mobile shell**: Reversed the mobile wrapper orientation policy so iOS, Android, and installed PWA builds stay in portrait on phones. Added a phone-landscape guard in the SPA so the layout does not snap into the desktop-style landscape arrangement on browsers that ignore the native lock.
- **iOS launch**: fix to restore clean iOS launch for the v1.0.6 build; carried forward into v1.0.7
- **Playlist `updated_at`**: `onupdate` now properly stamps rows on edit; partial index added for public-discovery queries (performance)
- **Playlist CSRF**: exempt playlists blueprint from CSRF (API consumers were getting 400s)
- **Alembic head merge**: resolved divergent heads (playlist visibility + match tips) into a single upgrade path
- **Auth logo consistency**: Login/Sign Up screen now uses the same new Ahoy logo asset as Home (`u_ahoy23.png`)
- **Global logo consistency**: Sidebar, top navbar logo slot, and footer brand logo now use `u_ahoy23.png` instead of the legacy `ahoy_logo.png`.
- **Merch checkout on web**: fixed a production routing conflict where `/checkout` could be intercepted by SPA fallback, and restored the server checkout/success template paths so merch purchases can reach Stripe checkout reliably.
- **Settings cleanup**: removed the `UI Styling` section (corner style + glow intensity) to simplify the Settings screen.
- **Settings cleanup**: removed the `User Interface` card (System theme / match OS toggle) to keep appearance controls focused in one place.
- **Profile layout order**: moved `Personal Dashboard` above `Time Spent` on the Profile page for a clearer top-to-bottom flow.

---

## Rolled up from v1.0.6 (first store ship)

All shipping to TestFlight / Play for the first time in this upload. See `docs/RELEASE_NOTES_v1.0.6.md` for full detail.

- **Radio — live station architecture**: one manifest-backed source of truth (`GET /api/radio/live`), tune-in joins live offset, shared across home + `/radio`
- **Compact radio hero**: `/radio` no longer full-screen takeover; bottom dock stays visible
- **Public playlist sharing**: `private` / `unlisted` / `public` visibility; guests can view non-private links
- **Community Playlists row** on Music page
- **`POST /api/media/resolve`** batch endpoint for playlist metadata
- **`GET /api/playlists/public`** discovery feed (no auth)
- **Playlist detail**: real metadata, play queue integration, share button, guest CTA
- **Create form**: description + visibility fields
- **`AddToPlaylistModal`** mounted globally in `App.vue`
- **Podcast "Add to playlist"** in `PodcastDetailView`

---

## Version bumps (done)

- `package.json`: `1.0.7`
- `android/app/build.gradle`: `versionName "1.0.7+${buildTimestampName}"`
- `ios/App/App.xcodeproj/project.pbxproj`: `MARKETING_VERSION = 1.0.7`, `CURRENT_PROJECT_VERSION = 7`

---

## Commits since v1.0.6

```
4587f67 Prepare v1.0.7 release
94b4e54 Unify mobile layout system: --mobile-gutter token + flush-content for all nav pages
31b3057 Bump to v1.0.7: flush home cards on mobile
3cde9e1 Make iOS bottom deck flush for v1.0.7
2ccc7cd Tune iOS bottom dock spacing for v1.0.7
2edf7b1 Fix iOS launch for v1.0.6 release
a7152d5 GDD: artist-bird mechanic — the emotional core of the owl game
df65d35 Expand owl game GDD with locked design direction
1694464 Add owl game GDD and update APP_OVERVIEW
66ce3a9 Refactor owl game controls, particles, and add home exit button
58892f3 Refactor AHOY TV schedule and playback
b2189b4 Refactor mobile AHOY TV experience
7eaa118 Refine mobile deck spacing
6bc17f7 Polish mobile deck and ahoy tv behavior
c2c6deb Ignore OpenClaw workspace metadata
7698b09 Optimize audio load times: metadata preload, prefetch, lazy restore
3cfd328 Tune owl runner feel
65e60a4 Split owl runner input and soften lane transitions
7a76763 Refactor radio into endless owl runner
75a9f17 Fix: playlist updated_at onupdate + partial index for public discovery
e65a16a Fix: exempt playlists blueprint from CSRF
fa33546 Merge alembic heads: playlist visibility + match tips
ac62a05 v1.0.6: Radio in changelog/release notes, podcast playlist wiring
f81a6ae Security: make repo private, gitignore OpenClaw runtime files
429f872 v1.0.6: Public playlists, media resolve endpoint, community discovery
```

---

## Deploy checklist

- [x] SPA built (`cd spa && npm run build`)
- [x] `npx cap sync ios`
- [ ] `npx cap sync android`
- [ ] Commit any stragglers on `main` (check `git status`; `spa/src/components/NowPlayingOverlay.vue` token refactor is on-theme if kept)
- [ ] `alembic upgrade head` on production (migrations from v1.0.6 still pending on store builds)
- [ ] `python fire.py` from repo root — preflight + iOS archive + Android AAB
- [ ] iOS archive → Xcode Organizer → TestFlight
- [ ] Android AAB → Play Console Internal Testing track
- [ ] Smoke test on device: mobile layout flush on Home / Artists / Events / Videos / Merch
- [ ] Smoke test: iOS bottom dock flush against home indicator
- [ ] Smoke test: AHOY TV mobile idle → channel pill → playback → control surface swap
- [ ] Smoke test: first-tap audio latency (metadata preload + prefetch)
- [ ] Smoke test: radio tune-in joins at live offset
- [ ] Smoke test: public playlist shareable link opens as guest

---

## Known gaps / next release candidates

- **Owl runner gameplay loop** — still ambient/experimental; not a shippable mini-game yet
- **Podcast list view "Add to playlist"** — `PodcastsView` episode rows still missing the button (only `PodcastDetailView` and Music view have it)
- **Playlist cover art** — no cover image; could auto-generate from first track artwork
- **CHANGELOG hygiene** — current `CHANGELOG.md` has a malformed bullet near the `AddToPlaylistModal was never mounted` entry and skips v1.0.6; worth a cleanup pass separate from release

---

## Build identity

- **App name:** Ahoy Indie Media App
- **Bundle ID / Package:** `ooo.ahoy.app`
- **Marketing version:** `1.0.7`
- **iOS build number:** `7`
- **Android versionName:** `1.0.7+<buildTimestamp>`
- **Android versionCode:** sequential (see `memory/android_version_code_strategy.md`)
