# Release Notes — v1.0.7.6

**Target platforms:** iOS (TestFlight), Android (Play Store Internal), Web, Desktop
**Release date:** 2026-04-27
**Status:** Preparing store builds

> v1.0.7.6 is a minor feature release adding a global notification center to replace toast spam on first load. The notification bell collects new content alerts ("new videos", "new podcasts", etc.) into a persistent history panel that users can check on demand.

---

## What's new in v1.0.7.6

### Notification center + history panel

Replaces ephemeral toast notifications with a proper notification center.

**What changed:**
- Added notification bell icon to top-right navbar (both mobile and desktop)
- Mobile: Tiny bell in new minimal top nav bar (icon-only, no text)
- Desktop: Bell next to account icon in main navbar
- Clicking the bell opens a slide-in panel (mobile) or dropdown (desktop) showing notification history
- Each notification shows message, timestamp ("5m ago", "2h ago", etc.), and individual dismiss button
- Unread count badge on the bell (red badge showing number of notifications)
- Pulsing animation on the badge draws attention when new notifications arrive
- Auto-dismiss notifications after 24 hours (prevents list from growing unbounded)
- "Clear all" button at the bottom of the panel
- "Back online" message now uses the notification center instead of ephemeral toast

**Why:** First load used to spam 1-2 toasts ("New videos just dropped", "New podcast episodes available") that disappear after 2.5 seconds. Users miss them or find them disruptive. Notification center makes updates discoverable but not intrusive.

**Technical details:**
- `useNotificationCenter()` composable manages notification state (add, remove, clear)
- `NotificationOverlay.vue` handles the UI panel + history display
- `useContentDropDetector()` now adds to notification center instead of dispatching toasts
- Mobile top nav refactored to be self-contained (no reliance on global `.mobile-only` utility class) to prevent CSS conflicts
- Notification panel uses Teleport to render at body level for correct z-index layering

### AHOY TV control surface redesign

Refactors `/live-tv` channel selection into a clearer browsing model.

**What changed:**
- Desktop now keeps a persistent channel rail visible instead of hiding controls behind hover
- Mobile now uses the drawer as the primary channel browser, with quick channel pills and a larger tap target for the current channel
- Playback controls remain visible as a separate surface so channel switching and player actions do not compete for the same chrome
- The current channel now feels anchored with stronger active styling and a cleaner now-playing hierarchy

**Why:** The old AHOY TV chrome mixed channel browsing and playback into one hover-sensitive bar. This made desktop feel transient and mobile feel overloaded. The new split keeps the player calm while making channel switching obvious on both form factors.

**Technical details:**
- `LiveTvControlPanel.vue` owns the desktop rail and mobile action surface
- `LiveTVView.vue` now passes channel selection and playback callbacks into the shared panel rather than hand-rolling two separate control layouts
- The mobile channel drawer remains the full-list fallback for deeper browsing

---

## Mobile UI refinements

- **Mobile top nav fully refactored:** Removed old logo, hamburger, tabs, and breadcrumbs code. Mobile now has a minimal top bar with just the notification bell. All navigation lives in the bottom deck.
- **Mobile-specific CSS:** Mobile-top-nav uses explicit scoped styles instead of relying on global `.mobile-only` class, preventing specificity conflicts and making the component more portable.
- **Music filter drawer polish:** Reworked the Saved Songs / New Music action drawer so the play and exit controls are right-aligned and compact on mobile. The split buttons also got a tighter mobile proportion pass.
- **New Music catalog entry:** Added Jake Custer's `I Think We're Lost` album to the music catalog and tagged it as hidden `new music` so it appears in the New Music drawer without a visible badge.

---

## Version bumps

- `package.json`: `1.0.7.6`
- `android/app/build.gradle`: `versionName "1.0.7.6+${buildTimestamp}"`, `versionCode 1772056496`
- `ios/App/App.xcodeproj/project.pbxproj`: `MARKETING_VERSION = 1.0.7.6`, `CURRENT_PROJECT_VERSION = 8`

---

## Build identity

- **App name:** Ahoy Indie Media App
- **Bundle ID / Package:** `ooo.ahoy.app`
- **Marketing version:** `1.0.7.6`
- **Android versionName:** `1.0.7.6+<buildTimestamp>`
- **Android versionCode:** `1772056496`
- **iOS version:** `1.0.7.6` (`CURRENT_PROJECT_VERSION = 8`)

---

## Deploy checklist

- [ ] SPA built (`cd spa && npm run build`)
- [ ] `npx cap sync` (iOS + Android)
- [ ] Android: `cd android && ./gradlew bundleRelease` → upload AAB to Play Console
- [ ] iOS: `cd ios && xcodebuild ...` → archive for TestFlight
- [ ] Mobile smoke test: Music drawer buttons are right-aligned and compact on mobile
- [ ] Mobile smoke test: Jake Custer appears in New Music
- [ ] Verify the new archive/AAB version metadata matches `1.0.7.6`

---

## Known gaps

None — this is a stable feature release.
