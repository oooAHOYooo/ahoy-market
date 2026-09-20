# Radio v1.0.6 Summary

## TL;DR

Historical snapshot: this describes the original live-station refactor. The current `/radio` route is now station-only, and the game surfaces were later moved out of the route.

Radio is now a real app-wide live station concept instead of a page-local shuffled queue.

- one manifest-backed station source of truth
- one shared live timeline across home and `/radio`
- tune in joins the current song at its live offset
- mute/unmute is local; the station itself never pauses
- on-demand playback can override radio without destroying the live timeline
- `/radio` stays inside the normal app shell and keeps the bottom dock visible
- radio mode no longer exposes queue-style transport controls

## What changed

### Radio architecture

- Added `GET /api/radio/live`
- Added shared client radio timeline logic
- Added explicit `playbackSource: 'radio' | 'manual'`
- Added `Back To Live Radio` on the radio page

### UI and UX

- Refactored `/radio` out of full-screen takeover mode
- Reworked the radio hero into a compact station header with current song info
- Kept the owl scene as an atmospheric background instead of a separate page mode
- Simplified radio controls to `tune in / mute / unmute`
- Removed `next`, `previous`, shuffle, repeat, and queue affordances in radio mode
- Removed extra radio navigation from the mini-player to avoid fighting the bottom dock

### Current product scope

Shipped:

- live station page
- shared radio state across app surfaces
- ambient owl presentation
- feather accumulation / early game scaffolding

Not shipped yet:

- shared social radio features
- save/share world building
- finished minigame loop
- server-authoritative editorial scheduling beyond the manifest

## Release framing

`v1.0.6` should be described as:

- a radio architecture and UX cleanup release
- a compact live radio page with ambient owl-world polish

It should not be described as:

- the final social/world-building radio game
