# Changelog

All notable changes to the Ahoy Indie Media platform will be documented in this file.

## [1.1.4] - 2026-05-22

### Added
- **Radio page redesign**: `/radio` rebuilt as a full-page live station. Album art hero with gradient veil, overlaid track/artist, real-time progress bar synced to the deterministic station clock, elapsed/remaining timestamps, Tune In / Mute button, and Up Next queue (3 tracks). Cyan accents at idle, pink + pulsing LIVE dot when audible. Full-page header on desktop, compact inline header on mobile.
- **Radio blurred art backdrop**: Current track's album art blurs and color-shifts behind the entire radio page for an immersive now-playing atmosphere; updates automatically as tracks change.
- **Media Session API on radio**: Radio registers track metadata (title, artist, artwork) with the browser Media Session API so the current track appears on lock screens, Bluetooth head units, and car infotainment. Play/pause/stop map to tune-in and mute; seek and next/previous disabled (live station).
- **Screen Wake Lock on radio**: Display stays on while tuned in; lock re-requests automatically if the tab regains visibility.
- **Profile editing**: In-place name editing, "Member since" date, PNG/WebP avatar uploads, and Sign Out in quick-access section on the Account page.
- **Search page browse sections**: `/search` opens with the Ahoy logo, pre-populated browse sections, and wider 16:9 video thumbnails.
- **Games Lab nested in Settings**: Hidden games collection moved under Settings so Radio is a clean standalone route.
- **CarPlay Swift fixes**: Added missing `whatsNewItems` property and `buildWhatsNewTab()` so the Swift file compiles; per-track Now Playing updates as the radio queue advances; remote command center (play/pause/stop) wired to the radio queue player; all tabs now use SF Symbols tab images.
- **Radio browser tab title**: Tab updates to `Track · Artist — Ahoy Radio` while on `/radio` and restores on navigate away.
- **Radio art crossfade**: Album art cross-fades between tracks (0.7 s) instead of snapping; outgoing image stays in place during the transition.
- **Radio auto-resync on tab restore**: Player immediately seeks to the correct live position when the tab regains visibility after being backgrounded.

### Changed
- **Bottom dock tools tray**: Replaced duplicate Boost shortcut with Search. The tools tray now offers Search, Theme toggle, and Settings.

### Fixed
- **CompactFooter — orphaned ticker timeout**: 300 ms delayed ticker start now cancels on `onUnmounted` to prevent callbacks firing on dismounted components.
- **Live TV schedule — stale interval guard**: `useLiveTvSchedule` clears any previous 15-second UI clock interval before reassigning, preventing accumulated parallel intervals on rapid mount/unmount.
- **GlobalTvPlayer — controls hide timer**: 1500 ms controls auto-hide timer now clears on `onUnmounted`; ejecting the TV player mid-countdown no longer leaves a dangling callback.
- **Toast — duplicate global event listener**: `ahoy:toast` window listener moved into `onMounted` with a named handler and paired `removeEventListener` in `onUnmounted`; previously accumulated a fresh anonymous listener on every remount.
- **Debug endpoints — auth gate**: `/api/debug/users` and `/api/debug/data/users` now require `@admin_required`; previously any unauthenticated visitor could retrieve user emails and IDs.
- **Debug endpoints — unbounded DB query**: Both debug user endpoints now cap at 500 rows ordered by newest signup; previously loaded the full user table on every call.
- **Recently Played widget**: Fixed pill alignment, clear history button, and stacked empty state layout.
- **AHOY TV mobile — channel drawer safe-area**: Bottom padding now uses `max(24px, env(safe-area-inset-bottom))` so the last channel item is not clipped on iPhone X+.
- **AHOY TV mobile — excess bottom padding**: Mobile player section bottom padding reduced from 140 px to 20 px.
- **AHOY TV — "Now Playing" label**: Control panel chip now reads "Now Playing" and shows "Up Next" when schedule data includes an upcoming slot.
- **AHOY TV — program progress bar**: Thin bar between video and control panel shows progress through the current slot.
- **AHOY TV — program details bottom sheet**: Program details pop-up now slides up from the bottom on phones instead of appearing as a centered modal.
- **AHOY TV — fullscreen button anchored to video frame**: Button now sits at the video's bottom-right corner regardless of what's below it; previously broke when the progress bar was inserted between video and controls.
- **AHOY TV — mini player controls on touch**: Close, pin, and expand buttons were hover-only; now show persistently on touch devices.
- **AHOY TV — mini player safe-area**: Floating mini player bottom clears the dock on iPhones with a home indicator.

## [1.0.7.6] - 2026-04-27

### Changed
- **AHOY TV channel controls**: Reworked `/live-tv` into a persistent desktop channel rail plus a mobile drawer/quick-actions surface. Channel browsing is now separate from playback controls, which stay visible without hover gating.

## [1.0.8] - 2026-04-25

### Added
- **Jake Custer album in Music**: Added `I Think We're Lost` to the catalog and tagged it as hidden `new music` so it shows up in the New Music drawer without needing a visible badge.

### Changed
- **Music drawer alignment on mobile**: Reworked the Saved Songs and New Music filter UI into a shared drawer with right-aligned `Play all` and `Exit` controls. The same SPA build now serves web, iOS, and Android.
- **Mobile AHOY TV startup channel**: `/live-tv` on mobile now jumps to the first playable channel after the schedule loads if the default `Misc` row is off-air. That keeps the inline player visible instead of landing on the idle standby state.
- **AHOY TV backend session handling**: Fixed `/api/live-tv/channels` to use the SQLAlchemy session context manager correctly so the Render endpoint can build channels instead of throwing while loading the schedule.

## [1.0.7] - 2026-04-24

### Added
- **Radio architecture rewrite**: Radio is now a real app-wide live station. One manifest-backed source of truth, shared live timeline across home and `/radio`, tune-in joins the current song at its live offset.
- **Compact radio hero**: `/radio` redesigned as a compact station header with current song info and ambient owl scene. No longer a full-screen takeover — bottom dock stays visible.
- **Radio controls simplified**: Mute/unmute only. Queue-style transport controls (next, previous, shuffle, repeat) removed from radio mode. Mini-player no longer shows radio navigation.
- **AHOY TV diagnostics**: Hero playback now records lightweight video diagnostics with source classification and load timing in `ahoy.videoDiagnostics`.
- **`GET /api/radio/live`**: New endpoint serving the live station manifest.
- **Public playlist sharing**: Playlists now have three visibility states — `private` (default), `unlisted` (accessible by link), and `public` (listed in discovery feed). Public and unlisted playlists are viewable by guests without login.
- **Community Playlists row on Music page**: Horizontally-scrollable widget showing recently-updated public playlists. Hidden when empty.
- **`POST /api/media/resolve`**: Batch endpoint to resolve playlist item IDs to full track/episode metadata without downloading the full catalog.
- **`GET /api/playlists/public`**: Discovery feed endpoint for public playlists, no auth required.
- **Playlist detail — real metadata**: Track titles, artist names, artwork, and durations now load in the playlist detail view (previously showed raw IDs).
- **Playlist detail — play queue**: Clicking a track or "Play all" loads the playlist into the player queue via `playerStore.setQueue()`.
- **Share button**: Copies playlist URL to clipboard; shown on public/unlisted playlists for the owner.
- **Create form fields**: Playlist creation now includes optional description and visibility selector.
- **Guest CTA**: Guests viewing a shared playlist see a "Sign up free / Log in" banner inline with the track list.

### Fixed
- **`AddToPlaylistModal` was never mounted**
- **Podcast "Add to playlist"**: Episodes and clips in `PodcastDetailView` now have an "Add to playlist" button, matching Music view.: The component existed but was not imported in `App.vue`. Now mounted globally.
- **MusicView overlay button mismatch**: The track overlay button had class `add-to-playlist-btn`, title "Add to queue", and called `addToQueue()`. Now correctly opens the playlist modal.
- **Media type inconsistency**: Podcast episodes stored as `clip` in playlist items were not resolving because resolution code checked for `podcast`. Normalised throughout.
- **Duplicate item error message**: Adding a track already in a playlist now shows "Already in this playlist" instead of a generic error (409 handling in `AddToPlaylistModal`).

### Changed
- **AHOY TV architecture**: Schedule state and playback state are now split into `useLiveTvSchedule()` and `useLiveTvPlayback()` instead of being rebuilt inline in `LiveTVView.vue`.
- **AHOY TV mobile UX**: Mobile now uses a dedicated control surface, branded standby state, and extracted channel drawer while desktop keeps the wider guide-oriented layout.
- **AHOY TV mobile idle state**: The phone standby view now uses a taller hero, a direct `Open Channels` CTA, and quick channel pills so the screen does not fall into a dead empty state.
- **AHOY TV mobile control states**: Idle and playback controls are now separated on phone. Idle shows channel-picking actions only, while playback-only controls appear after a live stream is active.
- **AHOY TV timing**: Slot transitions now follow boundary-based refreshes instead of a full-page 1-second playback engine loop.
- **AHOY TV guide polish**: Program cards now show time ranges, the control panel surfaces an `Up next` line, the standby state has a retry action, and the program modal save button now bookmarks the selected item.
- `Playlist` model: `is_public` (boolean) replaced by `visibility` (varchar: `private`|`public`|`unlisted`); `description` field added.
- `blueprints/api/playlists.py`: Full rewrite. `is_owner` returned in all playlist responses. Read endpoints open to guests for non-private playlists.
- `usePlaylists.js`: `create()` accepts `{description, visibility}`; `update()` replaces `rename()`; `listPublic()` and `resolveMedia()` added.

### Migrations
- `a3f1b2c4d5e6`: Adds `description` and `is_public` to `playlists`
- `b4g2c3d5e6f7`: Replaces `is_public` with `visibility` enum string

---

## [1.0.5] - 2026-04-19

### Changed
- Hidden MiniPlayer timeline on mobile for cleaner compact layout.
- Compacted bottom nav to 8-column icon-only tabs.

---

## [1.0.4] - 2026-04-16

### Added
- **Android Auto Radio Tab**: New dedicated "Radio" root category and "Start Ahoy Radio" action for continuous shuffled playback.
- **CarPlay Radio Tab**: New "Radio" tab bar item with deep integration for on-the-go music discovery.
- **Media Session Enhancements**:
    - Absolute artwork URL resolution for car dash displays.
    - Full transport control support (Seek Forward/Backward) mapped to steering wheel controls.
    - Synchronized playback state reporting for native car UIs.
- **`ContentHeader.vue`**: A new, reusable, and responsive header component inspired by the high-end "Studio" design.
- **Subpage Refactor**: Unified the look and feel across 10 major subpages by inserting the new header.
    - Studio
    - Podcasts
    - Music
    - Videos (Shows)
    - Radio (Ahoy FM)
    - Saved (Bookmarks & History)
    - Events
    - Artists
    - What's New
    - Playlists
- **Context-Aware Headers**: Applied section-specific kickers (e.g., "Your Library", "Live Stream") to every subpage.
- **Responsive Layout**: Headers are centered on mobile for a clean editorial feel and left-aligned on desktop for grid consistency.

### Removed
- **Double Headers**: Removed redundant legacy titles and subtitles from the Radio and Artists views.
- **Legacy Heroes**: Replaced the complex profile-style hero on the Saved page with the clean new header.

### Changed
- **Radio CTA**: Repositioned the principal "Listen Now" action button into the header's direct visual hierarchy.

---

## [0.2.4] - 2026-03-30

### Added
- **Poets & Friends #9 Recap**: Full video recording and behind-the-scenes photography.
- **Tyler Needs a Break**: New podcast series episodes 1-4.
- **Linux Desktop App**: Native support via universal AppImage and AUR.

### Improved
- **Video Slugs**: Transitioned to human-readable video IDs for better sharing.
- **Mobile Performance**: Optimized asset delivery and local SQLite caching.
