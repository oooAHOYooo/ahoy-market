# Release Notes — v1.0.9

**Target platforms:** iOS (TestFlight), Android (Play Store), Web, Desktop
**Release date:** 2026-04-29
**Status:** In progress

> v1.0.9 is the next cross-platform release after the Google Play v1.0.8 submission. It is not treated as a hidden hotfix line; iOS, Android, web, and desktop should all move forward under the same version label.

---

## What's new in v1.0.9

- **Unified post-v1.0.8 release line**: Moves the app metadata, native wrappers, and bundled SPA version to v1.0.9 so TestFlight and Google Play can converge on the same release label after the v1.0.8 Google submission.
- **Back button on detail pages**: All content detail pages (artists, tracks, podcasts, shows, playlists, events) now have a prominent back button in the top-left to return to the parent list. Routes explicitly to the parent page (not browser history) for reliable navigation.
- **Radio arcade playfield**: `/radio` now centers the player ship in the visible mobile playfield, adds a darker arcade shooter-style grid/starfield, and keeps radio controls in the game surface instead of launching the full now-playing overlay.

---

## Fixes

- **Production boot fix**: Removed duplicate Flask `robots.txt` and `sitemap.xml` route registrations so Gunicorn can import the app cleanly on Render.
- **AHOY TV pause stability**: AHOY TV now keeps the guide schedule anchored to a stable timeline and honors the paused state during channel reloads, slot refreshes, and route handoff to the global video player. A paused live stream should no longer randomly restart with sound after navigating elsewhere.
- **Podcast catalog cleanup**: G-Dub Disc Golf is hidden from `/api/podcasts` so that video-first series stay in the video catalog and The Rob Show returns to the main podcast card set.
- **Content drop notifications disabled**: Removed persistent "New content just dropped" notifications that appeared in the notification center. The app still monitors for content updates but no longer displays pop-up notifications to users.
- **Radio HUD overlap fixed**: Session summary and audio orb no longer stack on top of each other on desktop. Audio orb moved to bottom-center; session summary stays bottom-right.
- **Radio trick feedback**: BURST and PULSE actions now show distinct icons (⚡ bolt vs signal wave) when triggered.
- **iOS signing entitlement cleanup**: The iOS release target now signs with the iOS app entitlement file while Mac Catalyst keeps the macOS sandbox entitlement file through an SDK-specific build setting. The pending CarPlay entitlement is excluded from the App Store build until Apple grants that capability for the App ID.

---

## Version bumps

- `package.json`: `1.0.9`
- `android/app/build.gradle`: `versionName "1.0.9+${buildTimestampName}"`, `versionCode 1772056501`
- `ios/App/App.xcodeproj/project.pbxproj`: `MARKETING_VERSION = 1.0.9`, `CURRENT_PROJECT_VERSION = 9`
- iOS release entitlements: `App/App.entitlements`; Mac Catalyst release entitlements: `App/MacCatalyst.entitlements`
- SPA bundled version fallback: `1.0.9`

---

## Build identity

- **App name:** Ahoy Indie Media App
- **Bundle ID / Package:** `ooo.ahoy.app`
- **Marketing version:** `1.0.9`
- **Android versionName:** `1.0.9+<buildTimestamp>`
- **Android versionCode:** `1772056501`

---

## Deploy checklist

- [x] SPA built (`cd spa && npm run build`)
- [x] iOS synced (`npx cap sync ios`)
- [x] iOS simulator build installed and launched
- [ ] Manual iOS smoke test: AHOY TV pause stays paused after navigating away
- [x] Android sync/build
- [ ] Android smoke test
- [ ] iOS archive for TestFlight
- [x] Android AAB for Google Play
- [ ] Push release commit/tag when QA passes

---

## Gameplan

Keep v1.0.9 focused enough to release confidently:

1. Lock in the AHOY TV playback fix.
2. Verify iOS first in the simulator and, if possible, TestFlight.
3. Verify Android with a fresh AAB.
4. Only add artist-card UI polish if it is small, easy to visually inspect, and does not touch playback, routing, or native config.
5. Defer broader UI cleanup to the next release if it threatens the release window.

---

## Known gaps

Artist-card UI polish is a candidate for v1.0.9 only if it stays low risk. Otherwise, keep it as the first v1.0.10 item so the AHOY TV playback fix is not delayed.
