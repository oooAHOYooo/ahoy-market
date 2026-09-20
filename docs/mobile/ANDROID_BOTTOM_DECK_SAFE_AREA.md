# Android Bottom Deck Safe-Area Investigation

Date: 2026-04-26

## Problem

On real Android phones, the mobile bottom deck can be cut off or visually displaced by the system navigation area. The issue was seen with both deck states:

- Deck 1: two-row navigation dock.
- Deck 2: now-playing/player controls.

The visible symptom changed across attempted fixes:

- Original state: lower deck content could sit under Android system navigation.
- `margin-bottom: 48px` state: controls moved above system navigation, but the whole widget floated too high and page content showed underneath.
- Deck 1 also showed its icons riding upward inside the deck, even when the full widget position was adjusted.

## What Was Really Happening

There are two separate layout problems that look similar:

1. **System navigation reserve**
   Android Capacitor WebView does not reliably expose the bottom system navigation area through `env(safe-area-inset-bottom)`. In practice, CSS sees `0px`, even when the phone has a visible system navigation strip.

2. **Deck 1 internal flex centering**
   Deck 1 inherits `.mobile-dock { min-height: var(--np-mobile-dock-height); justify-content: center; }`. The two rows require less height than the deck frame, so Flexbox centers the row stack inside the extra vertical space. This creates the feeling of hidden or magical padding below the icons.

The previous `margin-bottom: 48px` attempt solved the safety problem in the wrong layer: it moved the entire fixed `.bottom-deck` upward. The correct model is to keep the visual deck flush to the bottom of the phone and reserve space inside the deck.

## Current Model

Android only:

- Keep `.bottom-deck` fixed at `bottom: 0`.
- Do not use external `margin-bottom` to avoid system navigation.
- Add an internal Android reserve using `--android-nav-reserve`.
- Make `.deck-frame` visually taller by that reserve.
- Put reserve into `padding-bottom`, so deck glass reaches the physical bottom while controls stay above the system navigation area.
- For Deck 1, pin `.mobile-dock` rows lower with `justify-content: flex-end` instead of centered.

Current starting reserve:

```css
body.platform-android {
  --android-nav-reserve: 32px;
}
```

Why `32px` instead of `48px`: screenshots showed the `48px` external lift was too aggressive visually. In an isolated headless layout fixture, `32px` reduced the over-lift while keeping a bottom reserve. Real-device testing should decide whether this should become `28px`, `32px`, or another value.

## Scope

The fix is intentionally scoped to:

```css
body.platform-android ...
```

Expected impact:

- Android Capacitor app: affected.
- Web app at `app.ahoy.ooo`: not affected, because normal browsers do not receive `body.platform-android`.
- iOS Capacitor app: not affected by these Android rules; iOS remains under `body.platform-ios` and uses native safe-area behavior.

Headless CSS scope check loaded the actual app CSS and compared body classes:

```text
web
bottom-deck margin-bottom: 0px
deck-frame height: 164px
deck-frame padding-bottom: 0px
dock justify-content: center

ios
bottom-deck margin-bottom: 0px
deck-frame height: 164px
deck-frame padding-bottom: 0px
dock justify-content: flex-start

android
bottom-deck margin-bottom: 0px
deck-frame height: 196px
deck-frame padding-bottom: 32px
dock justify-content: flex-end
```

## Test Checklist

- Test Deck 1 on a real Android phone: icons should sit lower, and the glass deck should stay flush to the phone bottom.
- Test Deck 2 on a real Android phone: player controls should not sit under system navigation, and the whole widget should not float high with page content underneath.
- Check both Android three-button navigation and gesture navigation if possible.
- Smoke test iOS after any related change; Android-only CSS should not affect iOS, but visual regression testing is still required.
- Smoke test mobile web; Android-only CSS should not affect `app.ahoy.ooo`.

## Files

- `spa/src/assets/platform-android.css`: Android-only override and reserve.
- `spa/src/assets/platform-ios.css`: iOS-only safe-area behavior.
- `spa/src/assets/mini-player-tune.css`: source of the mobile dock flex behavior that Deck 1 inherits.
