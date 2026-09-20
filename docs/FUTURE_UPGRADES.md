# Future Upgrades

This file tracks higher-risk or later-release improvements that should not block the current ship.

## Frontend refactors

- Split `spa/src/views/MusicView.vue` into smaller music-specific components so the table, mobile row, and grid card are easier to maintain.
- Extract the repeated music action controls into a shared component so play, queue, and save behavior stays consistent across layouts.
- Revisit music-page table styling and remove any remaining dead play-count UI or CSS if the count stays hidden.
- Consolidate shell breakpoints so navigation chrome has one policy everywhere: normal desktop browsers use sidebar chrome from 1024px, while iPad/native mobile force the bottom-deck shell independent of width.
- Audit legacy `.mobile-only`, `.desktop-only`, and `.hidden-mobile` rules in `spa/src/assets/main.css`, `spa/src/assets/combined.css`, and `spa/src/assets/mini-player-tune.css`; remove or narrow the old `769px` utility rules that can conflict with the shell.
- Keep route-specific content breakpoints allowed for layout density, but stop route CSS from deciding global nav/sidebar visibility.
- Review tablet widths on high-risk routes after the cleanup: `/music`, `/podcasts`, `/live-tv`, `/videos`, `/whats-new`, `/playlists`, and `/radio`.

## Android car playback

- Migrate Android Auto radio playback from `MediaPlayer` to Media3 `ExoPlayer`.
- Use a preload manager or playlist buffering so the next item is already warm before the current one ends.
- Keep the existing `MediaBrowserServiceCompat` and media-session surface if possible; the goal is a playback-engine swap, not a full UX rewrite.

## Follow-up ideas

- Expand radio prefetch beyond the next 2 items only if real-device testing shows it materially improves handoff latency.
- Consider whether CarPlay needs deeper queue management if stall rates remain high after forward buffering.
- Revisit any other stream-heavy surfaces that would benefit from the same preload pattern.
