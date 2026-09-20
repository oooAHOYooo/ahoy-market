# Media Startup Benchmark

This repo now has a simple benchmark for media speed that future releases can try to beat without changing playback behavior.

## Standard test setup

- Device: one real mobile phone, preferably the same one each release
- Network: throttled to `Fast 3G` or worse
- Browser state: cold tab, no cached page, no media already loaded
- Runs: 3 audio runs and 3 video runs
- Reported number: use the median, not the best run

## What to measure

- Audio start latency: `loadstart` to `canplay`
- Video readiness latency: `loadstart` to `loadedmetadata`
- Video first-frame latency: `play` to first `timeupdate` when available
- Stall rate: number of `waiting` or `stalled` events during the first 60 seconds
- Resume latency: time from tapping play to actual `play`

## One-number score

Use this release score so you have a single target to beat:

```text
Media Startup Score = round(median(audio loadstart -> canplay) / 100)
                    + round(median(video loadstart -> loadedmetadata) / 100)
                    + (2 x median(stall count in first 60s))
```

Lower is better.

## Why this is the right benchmark

- It measures the user-visible delay, not just whether a request succeeded.
- It works for both mobile and desktop.
- It uses the existing media diagnostics already emitted by the app, so you do not need a new tracking system.

## How to collect it

- Open the app on a slow mobile connection or throttle to "Fast 3G" in Chrome DevTools.
- Play one audio track and one video page from a cold tab.
- Read the app's existing `ahoy:audio-diagnostic` and `ahoy:video-diagnostic` events from the console or `localStorage`.
- Record the gap between `loadstart`, `loadedmetadata`, `canplay`, and the first `play`.

## Suggested release target

Use the first validated measurement as the baseline for that release line, then try to improve:

- Audio: lower `loadstart -> canplay`
- Video: lower `loadstart -> loadedmetadata`
- Reliability: reduce `waiting` and `stalled` events
- Overall: lower the `Media Startup Score`

Export shape for the CLI:

```json
{
  "audio": [],
  "video": []
}
```

You can generate that from the browser console with:

```js
JSON.stringify({
  audio: JSON.parse(localStorage.getItem('ahoy.audioDiagnostics') || '[]'),
  video: JSON.parse(localStorage.getItem('ahoy.videoDiagnostics') || '[]'),
}, null, 2)
```

If you only export one medium at a time, pass `--kind audio` or `--kind video` to `ahoy-cli benchmark`.

Example:

```bash
ahoy-cli benchmark media-benchmark.json --label v1.1.5 --device "iPhone 14" --network "Fast 3G"
```

## Practical rule

If a change improves the benchmark but adds visible layout jank or changes playback behavior, it is not worth it. Keep the benchmark tied to the same user flow, device class, and network profile across releases.

## Release scorecard

Record this in the release notes or PR:

| Release | Device | Network | Audio median | Video median | Stall median | Score |
| --- | --- | --- | --- | --- | --- | --- |
| baseline |  |  |  |  |  |  |
| current  |  |  |  |  |  |  |
