# AHOY TV Refactor

Updated for `v1.0.6`.

## Goals

- Keep the mobile AHOY TV experience simpler than desktop.
- Make schedule state authoritative instead of rebuilding playback state ad hoc in the view.
- Make playback transitions deterministic at slot boundaries.
- Preserve desktop layout while improving mobile controls and standby behavior.

## Structure

The AHOY TV page is now split into three layers:

1. `LiveTVView.vue`
   - Owns page layout, desktop guide rendering, mobile-specific controls, and modal state.
   - Consumes derived schedule and playback state instead of building it inline.

2. `useLiveTvSchedule()`
   - Normalizes channel and item payloads from `/api/live-tv/channels`.
   - Fills empty channels with placeholder schedule items so the guide stays coherent.
   - Owns:
     - selected channel
     - current slot
     - next slot
     - guide timeline rows
     - current/next boundary timing
     - lightweight thumbnail generation/caching
   - Uses a slot-boundary timeout plus a low-frequency UI timer instead of a full-page 1-second engine loop.

3. `useLiveTvPlayback()`
   - Owns hero video lifecycle and track synchronization.
   - Explicitly handles:
     - `idle`
     - `loading`
     - `preview`
     - `playing`
     - `error`
   - Keeps hero video updates scoped to actual slot transitions.
   - Records lightweight video diagnostics in `localStorage` under `ahoy.videoDiagnostics`.

## Mobile-specific components

- `LiveTvStandbyState.vue`
  - Branded standby state for idle/error/no-video situations.
  - Mobile standby now uses a taller hero treatment so empty-state copy and actions fit without clipping.

- `LiveTvChannelDrawer.vue`
  - Mobile channel selection drawer extracted from the main view.

- `LiveTVView.vue` mobile idle actions
  - Idle mobile state now exposes a direct `Open Channels` CTA and a small quick-pick row under the hero so the screen keeps a next-step action visible even when the desktop guide is hidden.
  - Idle mobile state no longer renders playback controls. Phone transport controls now appear only after a playable stream is active.

## Playback behavior

- Slot changes no longer depend on a 1-second `tick()` loop.
- The current slot is derived from normalized schedule state.
- Playback transitions now go through one sync path:
  - no playable slot -> standby
  - same source / new slot -> reseek
  - new source -> reload video

## Release note

For release-oriented AHOY TV changes:

- update `CHANGELOG.md`
- update `release-notes/android/internal-beta.txt`
- document the architectural change in `docs/`
