# Release Notes — v1.0.6

**Target platforms:** Web, iOS (TestFlight), Android (Play Store internal), Desktop  
**Status:** In progress — SPA built and tested locally; requires `alembic upgrade head` + `npm run build` + `cap sync` before store submission.

---

## What's new

### Radio — live station architecture

Radio has been rebuilt from page-local shuffled queue into a real app-wide live station.

**What changed:**
- One manifest-backed station (`GET /api/radio/live`) is the single source of truth for what's playing
- Tune-in joins the current song at its live position — you're joining a broadcast, not starting a new queue
- Shared radio timeline across the home page and `/radio` — the station plays on regardless of which page you're on
- Mute/unmute is local; the station itself never pauses
- On-demand playback (playing a specific track) overrides radio without destroying the live timeline — switching back to radio resumes at the correct live offset

**UI changes:**
- `/radio` is no longer a full-screen takeover. It stays inside the normal app shell with the bottom dock visible
- The radio page is now a compact station header showing the current song, with the owl scene as ambient background
- Controls simplified to tune in / mute / unmute — next, previous, shuffle, repeat removed from radio mode
- Mini-player no longer shows radio navigation controls (was fighting the bottom dock)
- "Back to Live Radio" button on the radio page when you've drifted to on-demand playback

**What's not in this release:** Social radio features, shared world-building, finished owl minigame loop, server-authoritative editorial scheduling. Those are v1.0.7+ territory.

---

### Playlists — public sharing and full rebuild

The playlist system has been rebuilt from the ground up. This is the biggest feature drop in this release.

**Visibility levels**
Playlists now have three visibility states instead of a boolean public/private flag:

| State | Who can see it |
|---|---|
| Private | Owner only (default) |
| Unlisted | Anyone with the link — not listed publicly |
| Public | Anyone — appears in the Community Playlists feed |

Toggle visibility with one tap from the playlist list (cycling private → unlisted → public) or from inside the playlist detail view.

**Shared playlist URLs**
`/playlists/:id` now works for guests on public and unlisted playlists. Previously any visit to a playlist URL resulted in a 401 error for non-logged-in users. Guests see a "Sign up free / Log in" call-to-action inline with the content.

**Real track metadata in playlist detail**
Playlist items used to display raw IDs (`music: abc-123`). The detail view now resolves each item to its full title, artist name, album artwork, and duration by calling the new batch endpoint `POST /api/media/resolve`. This avoids downloading the full music or podcast catalog just to show a playlist.

**Play all / play from track**
Clicking any track in a playlist now loads the full playlist into the player queue starting from that track. The "Play all" button does the same from the top. The currently-playing track is highlighted.

**Share button**
Public and unlisted playlists show a "Share" button in the detail header. Tapping it copies the URL to the clipboard with a brief "Copied!" confirmation.

**Create with description and visibility**
The playlist creation form now includes an optional description field and a visibility selector. Previously you had to create then edit to set these.

**Description shown in list**
If a playlist has a description it appears as a subtitle line on the playlist card.

---

### Community Playlists on the Music page

A horizontally-scrollable "Community Playlists" row now appears on the Music page, showing up to 6 recently-updated public playlists. Tapping a card goes directly to the playlist detail. The section is hidden when there are no public playlists yet.

---

### Add to Playlist — fixed and wired up

The "Add to playlist" modal was previously built but never connected to the app. It is now:

- Mounted globally in `App.vue` (same pattern as the queue modal)
- Triggered from the track overlay button in Music view (the button that previously said "Add to queue" but had `add-to-playlist-btn` class — now actually opens the playlist modal)
- Shows "Already in this playlist" when a duplicate is detected, instead of a generic error

---

## Technical changes

### New API endpoints

| Endpoint | Auth | Description |
|---|---|---|
| `POST /api/media/resolve` | None | Batch-resolve `{media_type, media_id}` pairs to full metadata. Used by playlist detail to avoid fetching full catalogs. |
| `GET /api/playlists/public` | None | Recently-updated public playlists for discovery feed. Default 12/page. |

### Database migrations

Run in order before deploying:

```bash
alembic upgrade head
```

| Migration | Change |
|---|---|
| `a3f1b2c4d5e6` | Adds `description` (varchar 500, nullable) to `playlists` |
| `b4g2c3d5e6f7` | Replaces `is_public` (boolean) with `visibility` (varchar 20: `private` \| `public` \| `unlisted`) |

### Media type normalisation

Podcast episodes are stored in playlist items as `media_type = 'clip'` (matching `ALLOWED_MEDIA_TYPES`). The resolve endpoint keys them as `clip:<id>`. The detail view normalises `clip → podcast` for display labels only. This was previously inconsistent (some code used `podcast`, some `clip`), causing episode metadata to never resolve.

### Files changed

| File | What changed |
|---|---|
| `models.py` | `Playlist` gets `description`, `visibility` fields |
| `blueprints/api/playlists.py` | Full rewrite: `_is_readable()`, `_is_owner()`, `_playlist_json()`, public discovery endpoint, `is_owner` in all responses |
| `app.py` | New `POST /api/media/resolve` endpoint |
| `spa/src/composables/usePlaylists.js` | `create()` accepts description/visibility; `update()` replaces rename; `listPublic()` and `resolveMedia()` added |
| `spa/src/views/PlaylistsView.vue` | Visibility cycle toggle, description in card, upgraded create form |
| `spa/src/views/PlaylistDetailView.vue` | Media resolution, playerStore queue integration, guest CTA, share button, visibility cycle |
| `spa/src/views/MusicView.vue` | Community Playlists section, overlay button wired to playlist modal |
| `spa/src/components/AddToPlaylistModal.vue` | 409 duplicate handling |
| `spa/src/App.vue` | `AddToPlaylistModal` mounted globally |

---

## Deploy checklist

- [ ] `alembic upgrade head` (migrations `a3f1b2c4d5e6` and `b4g2c3d5e6f7`)
- [ ] `cd spa && npm run build`
- [ ] `npx cap sync`
- [ ] Smoke test: create playlist → toggle to public → share link → visit as guest → play from playlist
- [ ] Smoke test: Music page → hover track → click playlist icon → add to playlist
- [ ] Smoke test: add same track twice → confirm "Already in this playlist" toast
- [ ] Verify Community Playlists row appears on Music page after making a playlist public
- [ ] iOS archive + TestFlight upload
- [ ] Android AAB + Play Console

---

## Repository security

The GitHub repository (`oooAHOYooo/ahoy-little-platform`) was made **private** during this release cycle (2026-04-22). Previously public.

**Why:** The repo contains full business logic, payment flows, admin route paths, DB schema history, and infrastructure config. Additionally, the OpenClaw agent framework (used by Codex) writes personal context to `USER.md` and daily `memory/` files — those must never be public.

**What changed:**
- Repo visibility: public → private via `gh repo edit --visibility private`
- `.gitignore` additions: `.openclaw/` (runtime state) and `memory/` diary files
- Render auto-deploy is unaffected — Render uses an authorized GitHub App connection, not public access

---

## Known gaps / next release candidates

- **Podcast list view** — `PodcastsView` episode rows don't have "Add to playlist" yet. Only `PodcastDetailView` and Music view do.
- **Playlist cover art** — model supports arbitrary items but no cover image. Could auto-generate from first track's artwork.
- **Edit description in-place** — currently requires going to a separate edit flow. Consider inline editing.
