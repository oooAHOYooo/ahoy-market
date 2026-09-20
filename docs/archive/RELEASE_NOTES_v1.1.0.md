# Release Notes — v1.1.0

**Target platforms:** iOS (TestFlight), Android (Play Store), Web, Desktop
**Status:** In progress

> v1.1.0 focuses on mobile playback stability and native car-mode enhancements, specifically migrating Android Auto to Media3 ExoPlayer and aligning the brand identity across CarPlay/Android Auto.

---

## What's new in v1.1.0

- **ExoPlayer Migration (Android Auto)**: Moving from legacy `MediaPlayer` to Media3 `ExoPlayer` for improved buffering, HLS support, and seamless handoffs.
- **Brand Alignment (#ff0060)**: Native car interfaces (CarPlay/Android Auto) now use the Ahoy signature pink (#ff0060) for highlight colors and active states.
- **Enhanced Car Playback**: Improved prebuffering and queue management to match standard music app expectations.
- **Podcast Listening Polish**: Now Playing adds podcast skip controls, playback-speed cycling, and sleep timer access, while podcast progress resumes from the last saved position.
- **Mobile Podcast Browse**: The Podcasts page uses a horizontal show strip on mobile so show switching is faster and denser.
- **Podcast Video-to-Audio Conversion**: Video-backed podcast clips were transcoded to MP3, uploaded to GCS, and rewired so the podcast surface now plays audio instead of video sources for those episodes.
- **Shared Search UX**: Home search and `/search` now share the same ranked catalog, match highlighting, and cached catalog loading.
- **Mobile Shell Polish**: Episode rows and sub-menu filters now compress better on phones, the deck toggle gives haptic feedback, and tap targets animate a little more cleanly on mobile.
- **Playlist UX Cleanup**: The add-to-playlist modal now closes reliably, supports quick playlist creation from the track modal, and lets listeners rename playlists inline from the Playlists page.
- **Music Row Action Visibility**: The music page now shows a clearer yellow `+` add-to-playlist button so the playlist action is obvious in both row and overlay layouts.
- **Music Library Default Sort**: The music list now opens newest-first by default, using each track's added date so the latest uploads appear before older tracks.
- **Spotify-style Music List**: Track number column shows animated cyan bars when a song is playing, album art moved into the title column, playing track title highlights in cyan, and a `···` dropdown replaces inline queue/playlist buttons so the row stays clean at rest. Clicking a track opens the full-screen player.
- **Video Detail Artist Rails**: Individual video pages now replace the generic "Related" rail with "More from [artist]" when the artist has additional videos; if there are no other videos from that artist, the rail is omitted.
- **Landscape-Friendly Shell**: Phones now keep the same shell in portrait and landscape. The layout stays consistent, while landscape uses a tighter density scale instead of switching modes.
- **Video Watermark Polish**: The player watermark is smaller, stays top-right on Live TV, and fades into a subtle overlay after fullscreen settles.

---

## Fixes

- Desktop header now keeps breadcrumbs left-aligned while the guest label, notifications, and account icon stay grouped on the right with matched controls and safer username truncation.
- Website visitors now get a web-only notification that Ahoy is available on Google Play Store, with theme-aware desktop unread states that clear after the notification panel is opened.
- What's New month cards now keep featured artwork inside a square frame so the image is not cropped into a wide banner.
- Prototype mobile Deck 3 utility mode adds notifications, What's New, settings, theme cycling, and reload shortcuts to the bottom deck cycle.
- Podcasts episode rows now collapse into a denser two-column mobile layout with a compact action row, and the sub-menu filter stays sticky on small screens.
- The mobile deck toggle now fires a light haptic tick when switching modes.
- Removed the stale app-version update banner so old version prompts no longer appear over the mobile shell.
- Now Playing and podcast playback now recognize the same podcast episode type coming from search results, keeping resume and skip controls aligned.
- Add-to-playlist is now a teleported modal with an explicit close path, an inline new-playlist creator, and the current track auto-added when creating a playlist from the modal.
- Playlist library cards now support inline rename/save without leaving the page.

---

## Version bumps

- `package.json`: `1.1.0`
- `android/app/build.gradle`: `versionName "1.1.0"`, `versionCode 1772056502`
- `ios/App/App.xcodeproj/project.pbxproj`: `MARKETING_VERSION = 1.1.0`, `CURRENT_PROJECT_VERSION = 10`

---

## Gameplan

1. Swap Android Auto engine to ExoPlayer.
2. Apply #ff0060 branding to CarPlay and Android Auto.
3. Implement pre-loading for the next track in car modes.
4. Verify playback stability on simulator/emulator.
