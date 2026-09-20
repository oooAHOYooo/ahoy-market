# Release Notes — v1.1.0.1

**Target platforms:** Android (Play Store)
**Status:** In progress

> v1.1.0.1 is a narrow repack of v1.1.0 for fresh Play Console testing after the Android Auto refactor.

---

## What's new in v1.1.0.1

- **Android Auto radio queue fix**: The radio root now exposes a real queue instead of a single playable item, so the car host can move forward through tracks.
- **Android Auto runtime logging**: Added service logs for radio queue resolution and content fetch counts to make Play Console and device testing easier to inspect.
- **Mobile music library polish**: The Music page now uses a denser, more transparent liquid-glass mobile library layout with simplified song rows, a compact control rail, and a bottom-sheet action menu.
- **Mobile podcast library polish**: The Podcasts page now matches the transparent liquid-glass mobile library treatment with a compact hero, useful quick actions, denser show browsing, play-on-art episode rows, and ten visible episodes per show with incremental expansion.
- **Mobile library easy wins**: Saved Songs and New Music now start playback directly, Podcasts can surface a Continue action from saved episode progress, active artwork gets a subtle now-playing pulse, mobile heroes compact while scrolling, and the bottom deck is lighter and shorter.
- **Default theme bootstrap**: First load now uses the `default` theme instead of randomly picking a theme when no explicit preference is saved.
- **Mobile subpage chrome cleanup**: Removed the stray blue progress strip that could appear across mobile subpages.
- **Mobile bottom deck fix**: Deck 2 and Deck 3 now render in the same fixed deck frame as Deck 1, and the toggle avoids double-advancing on pointer devices.
- **Mobile playlist shortcut**: Deck 3 now includes a Playlists action next to What's New.
- **Mobile deck toggle polish**: The deck switcher now shows clearer state icons and tiny position dots for nav, player, and utility.
- **Mobile notification drawer polish**: Deck 3 notifications now open as a full-width top sheet on mobile, with fixed-width icon and dismiss columns, a dismiss handle, swipe-up close, and clamped deck text so messages do not crowd the utility deck.
- **Tablet shell breakpoint fix**: Normal desktop browsers now return to desktop chrome at 1024px, while iPad/iPhone/Android/native mobile surfaces force the mobile bottom-deck shell even when their viewport is wider.
- **Desktop web blank-page fix**: Fixed the navbar mobile-shell CSS so desktop-width browsers no longer receive a generated `body { display: none; }` rule.

---

## Version bumps

- `package.json`: `1.1.0.1`
- `android/app/build.gradle`: `versionName "1.1.0.1"`, `versionCode 1772056503`
