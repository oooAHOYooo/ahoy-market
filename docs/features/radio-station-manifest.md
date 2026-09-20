# Radio Station Manifest

## Goal

Keep radio cheap and simple without letting each client invent its own station.

This is the current `v1.0.6` radio contract.

The current approach is a middle ground:

- The server publishes a tiny manifest at `GET /api/radio/live`
- The client computes the live song position locally from that manifest
- The station clock keeps moving even when the user is not listening
- Tuning in joins the current song at its live offset
- Muting/unmuting affects only the local listener, not the station timeline

## What shipped in v1.0.6

- `/radio` and the home radio card now consume the same manifest-driven station state
- The radio page no longer takes over the viewport; it stays inside the normal app shell
- The bottom dock stays visible on the radio page
- Radio joins the live point in the current song instead of starting from the top
- Radio mode uses `tune in / mute / unmute`, not normal queue transport controls
- On-demand playback can still override radio, but the radio page exposes `Back To Live Radio`
- The mini-player no longer includes radio-specific navigation buttons; the dock remains the navigation surface

## Current UI shape

The `/radio` page now reads as a simple station surface:

- a clear `Now Playing` card for the live station
- a single tune-in / mute control
- no embedded game launcher

That keeps the active station obvious without making `/radio` feel like a separate mode.

## Why this approach

Pure client-side radio is cheap, but it becomes fragile because every page can end up reimplementing station logic.

Pure server-driven radio gives stronger control, but it is more work and more operationally expensive than this product needs right now.

The manifest model keeps the important part centralized:

- track order
- track durations
- station epoch
- station identity
- server time for clock offset correction

while leaving the cheap part on the client:

- figuring out which song should be live right now
- calculating elapsed time into the current song
- building `Up Next`

## Endpoint

`GET /api/radio/live`

Returns:

```json
{
  "station": {
    "key": "ahoy-radio-main",
    "name": "Ahoy Radio",
    "epoch_ms": 1767225600000,
    "computed_locally": true,
    "track_count": 123
  },
  "server_time_ms": 1776859200000,
  "tracks": [
    {
      "id": "track-1",
      "title": "Song Title",
      "artist": "Artist Name",
      "audio_url": "https://...",
      "cover_art": "https://...",
      "duration_seconds": 197
    }
  ]
}
```

## Client rules

- Never shuffle the manifest locally.
- Use `station.epoch_ms` plus `server_time_ms` to build the moving station clock.
- Treat the station as always live, even if no audio is currently playing.
- On tune-in:
  - load the current manifest track
  - seek to the computed live offset
  - unmute local playback
- On subsequent button taps:
  - mute or unmute only
  - do not pause the station conceptually
- In radio mode:
  - do not show `next`, `previous`, shuffle, repeat, or queue actions
  - keep queue-style controls for on-demand playback only
- If on-demand playback interrupts radio:
  - preserve the station timeline
  - rejoining radio should always seek to the current live offset, not an old paused position

## TL;DR

Radio is now one shared station timeline across the app.

- The server owns the manifest
- The client does the cheap clock math
- The station is always live
- Tune in joins the current moment
- Mute is local
- On-demand can interrupt
- `Back To Live Radio` rejoins the broadcast

## When to move beyond this

This should move to a more server-authoritative model only when radio needs:

- injected plugs, ads, or DJ breaks on demand
- daypart scheduling
- multiple stations with editorial control
- instant emergency changes to the live order
- stricter analytics or broadcast correctness

Until then, the manifest approach is the right tradeoff.
