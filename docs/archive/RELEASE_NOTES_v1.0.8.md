# Release Notes — v1.0.8

**Target platforms:** iOS (TestFlight), Android (Play Store), Web, Desktop
**Release date:** 2026-04-25
**Status:** Ready to build and upload

> v1.0.8 is a patch release investigating and fixing the Android deck (bottom player widget) safe-area/navigation positioning bug discovered in internal testing.

---

## What's new in v1.0.8

None — patch release only.

> **Note:** The notification center (collects "new content" alerts into a persistent panel) shipped in v1.0.7.6 before this release.

---

## Fixes

- **Mobile podcasts show access**: The podcasts page now uses a show-first layout with featured cards plus per-show episode sections, instead of only the top four featured shows. The mobile show picker is visible again, so The Rob Show and other non-top-card shows stay reachable on mobile `/podcasts`.
- **Artist card overlay design**: Refactored artist cards to use an overlay design with name and type badge positioned over the bottom of the image with a gradient overlay. Eliminates empty space below the image and creates a more compact, premium visual treatment.
- **Music drawer alignment on mobile**: Reworked the Saved Songs and New Music drawer into a shared action panel with right-aligned `Play all` and `Exit` controls so the mobile music filter UI stays consistent across web, iOS, and Android.
- **Jake Custer new music entry**: Added Jake Custer's `I Think We're Lost` album to the music catalog and tagged it as `new music` so it appears in the New Music drawer without needing a visible badge.
- **Mobile AHOY TV startup channel**: On `/live-tv`, mobile now jumps to the first playable channel after the schedule loads if the default row is `Misc` or otherwise off-air. That keeps the inline player visible instead of landing users on the idle state with no video.
- **AHOY TV backend session handling**: Fixed `/api/live-tv/channels` so it uses the SQLAlchemy session context manager correctly and can build the channel response without crashing in Render logs.
- **Android bottom deck navigation reserve**: Updated the deck fix after real-device testing showed that `env(safe-area-inset-bottom)` is not reliable in the bundled Android Capacitor WebView and that an external `margin-bottom` lifts the whole widget too far. The current model keeps `.bottom-deck` flush at `bottom: 0`, adds an Android-only internal reserve on `.deck-frame`, and pins Deck 1 rows lower so the icons do not drift upward inside the deck.
- Added investigation notes in `docs/mobile/ANDROID_BOTTOM_DECK_SAFE_AREA.md`.
- **iPhone bottom deck tightening**: Trimmed the iOS-only bottom reserve so the mobile deck sits closer to the content on iPhone without changing Android or web spacing. The change stays scoped to `body.platform-ios`.
- **Portrait-only mobile shell**: Locked the shipped iOS, Android, and installed PWA wrappers to portrait so phones stay out of the desktop-style landscape layout. The SPA also shows a mobile-landscape guard for browsers that ignore the native lock.
- **iOS runtime portrait enforcement**: Added a native app-delegate orientation override so the iOS shell cannot rotate into the desktop-style landscape layout even if the simulator or device tries to flip orientation.
- **Radio page refactor**: Reworked `/radio` into a tiny skipper game instead of the heavier WebGL owl/cloud prototype. The new surface keeps the illusion-of-live-radio feel with a little boat on a waveform-water ribbon, uses drag/tap/hold controls, and leaves the mobile bottom deck visible on the route.
- **Tiny skipper polish**: Added audio-reactive water motion, a quiet session summary card, and a slimmer mobile HUD so the skipper reads more like a companion than a full-screen game.
- **GCS audio playback compatibility**: Removed forced `crossOrigin = 'anonymous'` from the Vue player audio elements. Legacy `static/js/player.js` already avoided this because anonymous CORS mode can make otherwise-public S3/GCS media fail when the bucket does not return `Access-Control-Allow-Origin`. The player still records `ahoy.audioDiagnostics` entries in localStorage and console logs for load/error/waiting/canplay events.
- **GCS bucket CORS for app/mobile origins**: Updated `gs://ahoy-song-collection` and `gs://ahoy-podcast-collection` CORS policy to include `https://app.ahoy.ooo`, `capacitor://localhost`, and `http://localhost`, while preserving the existing Render, `https://ahoy.ooo`, and dev localhost origins. The deployed policy is tracked in `docs/deployment/gcs-audio-cors.json`.
- **Android v1.0.7.5 test AAB**: Prepared a Play Console test bundle from the v1.0.8 audio/storage fix set using Android `versionName "1.0.7.5+<buildTimestamp>"` and `versionCode 1772056493`, so the GCS CORS/playback fix can be validated before final v1.0.8 release packaging.
- **Car mode radio fallback**: Hardened the Android Auto / CarPlay radio queues so broken or malformed stream items are skipped instead of stalling playback. The native car players now normalize stream URLs and advance to the next playable item on failure.
- **Radio prebuffering**: Web radio now preloads the next couple of tracks earlier, Android Auto keeps one hidden next-item player warm, and CarPlay buffers the next item with a forward buffer window so transitions are less likely to stall on slow streams.
- **Android release bundle compile fix**: Fixed a Java lambda-capture issue in `AhoyMediaService` so the release AAB builds cleanly again without changing the prebuffer behavior.

---

## Storage investigation log — GCS / S3 audio

**Date:** 2026-04-26
**Symptom:** GCS-hosted audio does not play reliably; S3-hosted audio does.

### Code findings

- `app.py` `/proxy/audio` allows `https://storage.googleapis.com/...`, S3 URLs, and `ahoycollection` URLs. It fetches with `requests.get(..., stream=True)` and returns `Content-Type: audio/mpeg`. This route only helps localhost because the legacy player proxies external URLs only on `localhost` / `127.0.0.1`.
- `static/js/player.js` explicitly avoids `crossOrigin` on the audio element because it previously caused S3/CORS issues.
- `spa/src/stores/player.js` still forced `crossOrigin = 'anonymous'` on both the main audio element and the prefetch audio element. That makes the browser require successful CORS headers even for media that could otherwise play as a plain `<audio src>`.
- Fix applied in this release: remove those two `crossOrigin` assignments in `spa/src/stores/player.js`.

### Public header checks

Checked sample GCS object:

`https://storage.googleapis.com/ahoy-song-collection/Jake%20Custer%20-%20Better%20Halves.mp3`

Results:

- Plain HEAD: `HTTP/2 200`, `content-type: audio/mpeg`, `accept-ranges: bytes`, `content-length: 8683481`, `vary: Origin`.
- Range HEAD with `Range: bytes=0-1`: `HTTP/2 206`, `content-range: bytes 0-1/8683481`, `accept-ranges: bytes`.
- Origin HEAD with `Origin: https://app.ahoy.ooo`: still returned `HTTP/2 200`, but did **not** return `Access-Control-Allow-Origin`.
- Origin HEAD with `Origin: capacitor://localhost` and `Origin: http://localhost`: also did **not** return `Access-Control-Allow-Origin`.

Interpretation: the object is publicly reachable and supports byte ranges, so raw storage delivery looks healthy. The missing CORS response makes forced anonymous CORS mode the likely browser-side failure path.

S3 comparison sample:

`https://ahoycollection.s3.us-east-2.amazonaws.com/01%20I%27ve%20Seen%20Better%20Days.mp3`

Results:

- Origin HEAD: `HTTP/1.1 200`, `Content-Type: audio/mp3`, `Accept-Ranges: bytes`, `Content-Length: 6086239`.
- Range HEAD: `HTTP/1.1 206`, `Content-Range: bytes 0-1/6086239`.
- Also did not return `Access-Control-Allow-Origin` in the sampled response, which explains why S3 works only when the app does not force CORS mode.

### Google CLI account check and bucket fix

- `gcloud auth list` initially showed only `alex@littlemarket.org` as active.
- User corrected that the relevant GCS data is under `alex@ahoy.ooo`.
- `gcloud auth login alex@ahoy.ooo --no-launch-browser` completed successfully on 2026-04-26.
- `gcloud config set account alex@ahoy.ooo` made `alex@ahoy.ooo` active for the current local CLI config.
- Before the fix, both buckets had CORS for `https://ahoy.ooo`, Render, and two localhost ports, but not `https://app.ahoy.ooo` or `capacitor://localhost`.
- Updated both buckets with `gcloud storage buckets update ... --cors-file=docs/deployment/gcs-audio-cors.json`.
- `gs://ahoy-song-collection` moved to metageneration `5`; `gs://ahoy-podcast-collection` moved to metageneration `4`.
- Object checks confirmed `Jake Custer - Better Halves.mp3` and `mintea - 7eleven.mp3` are `audio/mpeg` objects in `gs://ahoy-song-collection`.

Current deployed CORS policy:

```json
[
  {
    "origin": [
      "https://ahoy-indie-media.onrender.com",
      "https://ahoy.ooo",
      "https://app.ahoy.ooo",
      "capacitor://localhost",
      "http://localhost",
      "http://localhost:5001",
      "http://localhost:3000"
    ],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type", "Content-Length", "Content-Range", "Accept-Ranges", "Authorization"],
    "maxAgeSeconds": 3600
  }
]
```

### Post-fix header verification

- `Origin: https://app.ahoy.ooo` against `ahoy-song-collection` now returns `access-control-allow-origin: https://app.ahoy.ooo`.
- `Origin: capacitor://localhost` against `ahoy-song-collection` now returns `access-control-allow-origin: capacitor://localhost`.
- `Origin: https://app.ahoy.ooo` plus `Range: bytes=0-1` now returns `HTTP/2 206` and exposes `Accept-Ranges`, `Content-Length`, `Content-Range`, and `Content-Type`.
- `Origin: https://app.ahoy.ooo` against `ahoy-podcast-collection` now returns `access-control-allow-origin: https://app.ahoy.ooo`.

---

## Version bumps (done)

- `package.json`: `1.0.8`
- `android/app/build.gradle`: `versionName "1.0.8+${buildTimestampName}"`, `versionCode 1772056500`
- Android test backport AAB: `versionName "1.0.7.5+${buildTimestampName}"`, `versionCode 1772056493`

---

## Build identity

- **App name:** Ahoy Indie Media App
- **Bundle ID / Package:** `ooo.ahoy.app`
- **Marketing version:** `1.0.8`
- **Android versionName:** `1.0.8+<buildTimestamp>`
- **Android versionCode:** `1772056500`

---

## Deploy checklist

- [ ] SPA built (`cd spa && npm run build`)
- [ ] `npx cap sync` (iOS + Android)
- [ ] Android: `cd android && ./gradlew assembleDebug` → test on device/emulator
- [ ] iOS: `cd ios && xcodebuild ...` → test on device/simulator (if possible)
- [ ] `python fire.py` from repo root — preflight + iOS archive + Android AAB
- [ ] iOS archive → Xcode Organizer → TestFlight
- [ ] Android AAB → Play Console Internal Testing track
- [ ] Smoke test on device: Deck 1 and Deck 2 stay flush to the phone bottom, controls avoid Android system navigation, and Deck 1 icons sit lower inside the deck

---

## Known gaps

Android WebView still does not expose a trustworthy CSS `env(safe-area-inset-bottom)` value for this case. The Android fix is intentionally scoped to `body.platform-android`; iOS and mobile web should be checked separately but are not expected to inherit the Android reserve.

GCS bucket CORS is now verified for `https://app.ahoy.ooo` and `capacitor://localhost`. The app-side audio fix and bucket CORS change should still be retested in the built mobile apps after Capacitor sync.

Legacy Cast is now marked as an outdated feature and is not part of the v1.0.8 or v1.0.7.7 shipment.
