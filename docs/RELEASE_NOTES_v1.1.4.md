# Release Notes — v1.1.4

**Target platforms:** iOS (TestFlight), Android (Play Store), Web, Desktop
**Status:** Released 2026-05-22

> v1.1.4 ships a full Radio page redesign, profile editing, search page improvements, and Games Lab separation alongside a reliability pass that cleans up timer and event listener leaks across five components, plus a round of AHOY TV mobile polish.

---

## What's new in v1.1.4

- **Radio page redesign**: `/radio` rebuilt as a full-page live station. Shows album art (square hero with gradient veil overlay), track title + artist overlaid at bottom, a real-time progress bar synced to the deterministic station clock, elapsed/remaining timestamps, a prominent Tune In / Mute button, and an Up Next queue showing the next 3 tracks. Idle state uses cyan accents; active/audible state flips to pink with a pulsing LIVE dot. Desktop shows a full page header; mobile uses a compact inline header.

- **Profile editing**: Account page now supports in-place name editing, displays a "Member since" date, accepts PNG and WebP avatar uploads, and surfaces a Sign Out action in the quick-access section.

- **Search page improvements**: `/search` now opens with the Ahoy logo, pre-populated browse sections for quick discovery, and wider 16:9 video thumbnails so show art is visible without a tap.

- **Games Lab separated**: The hidden games collection has been moved to a nested item under Settings so it is accessible without polluting the main nav. Radio is now a standalone route.

- **Media Session API on radio**: Radio now registers track metadata with the browser's Media Session API so the current track title, artist, and artwork appear on lock screens, Bluetooth head units, and car infotainment (Safari/Chrome). Play/pause/stop map to tune-in and mute.

- **Screen Wake Lock on radio**: The display stays on while tuned in so the station page stays visible on car dashboards and countertop use. The lock re-requests automatically if the tab regains visibility.

- **CarPlay Swift fixes**: Added missing `whatsNewItems` property and `buildWhatsNewTab()` so the Swift file compiles cleanly. Per-track Now Playing updates fire as the radio queue advances (lock screen and Bluetooth metadata). All tabs now use SF Symbols tab images.

- **Radio browser tab title**: The browser tab title updates to `Track · Artist — Ahoy Radio` while on `/radio` and restores to the previous title on navigate away.

- **Radio art crossfade**: Album art now cross-fades between tracks (0.7 s opacity transition) instead of snapping. The outgoing image stays in place during the transition so both overlap cleanly.

- **Radio auto-resync on tab restore**: When the tab regains visibility after being backgrounded (browser may have throttled the station clock), the player immediately seeks to the correct live position to correct any drift.

---

## Changed

- **Bottom dock tools tray**: Replaced duplicate Boost shortcut with Search. Boost remains in the main dock nav; the tools tray now offers Search (routes to `/search`), Theme toggle, and Settings.

---

## Fixes

### Memory & timer cleanup (internal reliability)

- **CompactFooter — orphaned ticker timeout**: The 300 ms delayed ticker start on mount now stores its timer ID and cancels it in `onUnmounted`. Previously, if the user navigated away within that window the callback fired on a dismounted component.

- **Live TV schedule — stale interval guard**: The 15-second UI clock interval (`uiTimer`) in `useLiveTvSchedule` now clears any previous interval before reassigning. Without this guard, rapid mount/unmount cycles (e.g. navigating in and out of Live TV quickly) could accumulate multiple intervals all ticking in parallel, each updating reactive state unnecessarily.

- **GlobalTvPlayer — controls hide timer**: The controls auto-hide timer (`controlsTimer`, 1500 ms) now clears on `onUnmounted`. The component mounts and dismounts via `v-if` on player mode, so ejecting the TV player while the timer was mid-countdown previously left a dangling callback. The callback wrote to a local ref on a dead instance — Vue handles this silently, but it was wasted work on every eject.

- **Toast — duplicate global event listener**: The `ahoy:toast` window event listener was being added at component setup time with an anonymous function, meaning it was never removable and a fresh listener accumulated on every remount. Moved into `onMounted` with a named handler and paired with `removeEventListener` in `onUnmounted`. In normal use Toast is a singleton, but this closes the leak for hot reload cycles and any future multi-instance scenario.

- **Debug user endpoints — auth gate**: `/api/debug/users` and `/api/debug/data/users` are now protected by `@admin_required`; previously any unauthenticated visitor could retrieve user emails and IDs.

- **Debug user endpoints — unbounded DB query**: Both `/api/debug/users` and `/api/debug/data/users` previously called `.query(User).all()` with no limit, loading the entire user table into memory for serialization. Both now cap at 500 rows ordered by newest signup first. At current user counts this makes no practical difference, but the pattern was fragile as the platform grows.

- **Recently Played widget**: Fixed pill alignment, clear history button visibility, and stacked empty-state layout.

### AHOY TV mobile polish

- **Channel drawer — iPhone safe-area**: The channel list now uses `max(24px, env(safe-area-inset-bottom))` for bottom padding so the last channel item is no longer clipped by the home indicator on iPhone X+.
- **AHOY TV — excess bottom padding**: Mobile player section bottom padding reduced from 140 px to 20 px; the outer container already provides dock clearance, so the extra space was dead whitespace at the bottom of the page.
- **Channel selector trigger — icon**: The channel dropdown trigger now shows a colour swatch for the active channel, matching the visual language used in the channel drawer and channel list.
- **Channel dropdown height**: The inline channel menu max-height increased from 220 px to `min(320px, 50vh)` so more channels are visible before scrolling.
- **Channel drawer — active state**: The selected channel in the drawer now has a visible blue-tinted background and left border, distinguishing it clearly from the press/hover state.
- **Channel rows — touch feedback**: Mobile channel list rows now have a subtle `:active` press state so taps feel responsive.
- **"Pinned" label replaced with "Now Playing"**: The control panel chip below the player now correctly labels the current program as "Now Playing". When schedule data includes an upcoming slot, an "Up Next" line is shown beneath it (mirrors the desktop panel behaviour).
- **Channel dropdown icons**: The inline channel menu now shows a colour swatch next to each channel name, consistent with the drawer and the trigger button.
- **Program progress bar**: A thin bar appears between the video and the control panel while a channel is playing, showing how far into the current slot you are. Uses the same schedule data already computed for the guide.
- **Program details — bottom sheet on mobile**: The program details pop-up now slides up from the bottom on phones instead of appearing as a centered modal, which feels more native and leaves the video visible above it. Includes safe-area inset for iPhone home indicator.
- **"Now Playing" badge position**: The in-video badge was offset 56 px from the left with nothing beside it; it now sits 12 px from the edge for a tidier look.
- **Fullscreen button anchored to video frame**: Button moved inside the video frame so it always sits at the bottom-right corner of the video regardless of what is below it. Previously positioned relative to the whole player wrap, which broke after the progress bar was inserted between video and controls.
- **Mini TV player controls visible on touch**: Close, pin, and expand buttons on the floating mini player were hover-only, making them unreachable on phones. They now show persistently on touch devices.
- **Mini player safe-area**: The floating mini player bottom now uses `max(90px, calc(72px + env(safe-area-inset-bottom)))` so it clears the dock on iPhones with a home indicator.

### Cross-view mobile touch polish

- **Bottom nav bar — touch feedback**: Nav tabs in the mobile bottom bar now scale down on press (`:active` state), giving physical feedback that the tap registered.
- **Home search action buttons — touch target**: Expand, collapse, and clear buttons in the home page search bar are 36×36px on desktop but now expand to 44×44px on touch devices via `pointer: coarse`, meeting the minimum recommended tap target. All three also have an `:active` press state.
- **Home search result items — touch feedback**: Search result rows now have an `:active` state (scale down + brighten) on touch so taps feel immediate rather than silent.
- **Home recent search remove button — touch target and feedback**: The × button on recent search pills grows to 44×44px on touch and shows a red-tinted `:active` state when pressed.
- **Shows carousel arrows — touch target**: Featured carousel prev/next arrows bumped from 36→44px and now have an `:active` scale-down state.
- **Shows indicator dots — tap area**: Carousel indicator dots stay visually small (4px) but their hit area is expanded to 24px vertically via content-box padding, reducing missed taps when scrubbing through slides.
- **Podcast episode buttons — touch target**: Episode play/add/share buttons are now forced to 44×44px on the podcasts page with a visible `:active` press state.

---

## Version bumps

- `package.json`: `1.1.4`
- `android/app/build.gradle`: `versionName "1.1.4"`
- `ios/App/App.xcodeproj/project.pbxproj`: `MARKETING_VERSION = 1.1.4`

---

## Known gaps

- `useNotificationCenter` uses a 24-hour auto-dismiss timer that cannot be cancelled mid-flight if `clearAll()` is called — the orphaned timeouts fire harmlessly but accumulate for the session lifetime.

---

## Guest profile improvements

- **Show real local data**: Guest profile now reads from the same `localStorage` stores as the logged-in experience. If the guest has saved bookmarks, their actual cover art appears in the Saved strip (desaturated). If they've been listening, their real artwork and track titles appear in Recently Played — also desaturated. Both strips shimmer as empty skeletons if no local data exists.
- **Sections reordered**: Saved → Recently Played → Wallet. Content history leads; the wallet moves to third.
- **Ghost hero fields**: The profile hero now shows skeleton bars in place of the name, member-since date, and bio — mirroring the logged-in layout so the space reads as a real profile waiting to be filled.
- **Ghost avatar camera badge**: A dimmed camera badge sits on the guest avatar, hinting at the photo-upload affordance available after sign-in.
- **Staggered shimmer**: Shimmer tiles animate with a 120 ms delay per position, creating a left-to-right wave instead of all tiles pulsing together.
- **Playlists guest state**: The playlists page no longer shows a plain text wall. Guests now see ghost versions of the create row and playlist list rows (shimmer tiles matching the real layout), all linking to sign-in.
- **Boost auth gate**: Guests clicking Boost on an artist page, the Dashboard sidebar, or navigating to `/tip-artist` are now redirected to sign-in before any cart interaction. Guests who navigated directly to `/checkout` could also reach the payment form — `confirmCheckout` now gates on auth before any Stripe call.

## Boost page redesign

- **Artist emotional context**: The boost spotlight card now shows the artist's genre and description/bio beneath their name, so users connect with who they're about to support before choosing an amount.
- **$0.05 minimum boost**: The minimum boost amount is now five cents — lowered from $5 across the slider, checkout presets, cart defaults, and validation.
- **$0.05–$1,000 logarithmic slider**: The boost slider now covers a 20,000x range using 27 logarithmic steps ($0.05, $0.10, $0.25, $0.50, $0.75, $1, $2, $3, $5 … $500, $750, $1,000). The thumb starts at $0.05 so the default gesture is sliding up from the smallest possible amount.
