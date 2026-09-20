# CODEX.md

Codex handoff notes for this repository.

## Android Bottom Deck

Before changing the mobile bottom deck, read:

- `docs/mobile/ANDROID_BOTTOM_DECK_SAFE_AREA.md`

Current understanding:

- Android Capacitor WebView does not reliably expose the bottom system navigation area through `env(safe-area-inset-bottom)`.
- Do not solve Android cutoff by adding external `margin-bottom` to `.bottom-deck`; that lifts the entire fixed widget and makes it float above the phone bottom.
- Keep `.bottom-deck` flush at `bottom: 0`.
- Add Android-only internal reserve on `.deck-frame`.
- Pin Deck 1 rows lower because `.mobile-dock` flex centering creates apparent hidden padding below the icons.
- Keep this scoped to `body.platform-android`; mobile web at `app.ahoy.ooo` and iOS should not inherit the Android reserve.

Primary files:

- `spa/src/assets/platform-android.css`
- `spa/src/assets/platform-ios.css`
- `spa/src/assets/mini-player-tune.css`
- `docs/mobile/ANDROID_BOTTOM_DECK_SAFE_AREA.md`
