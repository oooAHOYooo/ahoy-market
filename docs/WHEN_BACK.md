# When you're back — quick handoff

Use this when returning to the project so you know where things stand and what to do next.

*Last updated: 2026-05-22*

---

## Current state

- **Branch:** `main` — all work is on main, deployed via Render on push.
- **Version:** `1.1.4` (see `docs/RELEASE_NOTES_v1.1.4.md`)
- **Repo visibility:** Private. Render deploy unaffected.
- **SPA:** Vue 3 SPA in `spa/src/`, built to `spa-dist/`. Mobile apps load from bundled `spa-dist`. UI changes require `npm run build` + `cap sync` + store resubmission.

---

## Before you do anything else

```bash
alembic upgrade head          # apply pending DB migrations
cd spa && npm run build       # rebuild SPA into spa-dist/
cd .. && npx cap sync         # sync to iOS/Android
```

---

## What shipped in v1.1.4

- Radio full-page redesign (album art hero, progress bar, Up Next queue, Media Session, Wake Lock)
- Profile editing (name, member-since date, PNG/WebP avatar, Sign Out in quick-access)
- Search page browse sections + wider 16:9 video thumbnails
- Games Lab moved under Settings; Radio is now a standalone route
- AHOY TV mobile polish (safe-area, progress bar, bottom sheet, mini player controls)
- Timer/memory cleanup across 5 components
- Debug user endpoints now require `@admin_required`

See `docs/RELEASE_NOTES_v1.1.4.md` for the full list.

---

## Store submission checklist for v1.1.4

- [ ] `cd spa && npm run build`
- [ ] `npx cap sync`
- [ ] Build Android AAB: `cd android && ./gradlew bundleRelease` → Play Console
- [ ] Build iOS archive: `./packaging/build-ios.sh upload` → TestFlight
- [ ] Update `packaging/versions.json` via `python crud.py` after each platform ships
- [ ] Smoke test Radio (tune in, media session on lock screen, wake lock)
- [ ] Smoke test Profile editing (name, avatar upload)
- [ ] Smoke test Search browse sections

---

## Quick orientation

| What | Where |
|---|---|
| App entry | `app.py` |
| SPA routes | `spa/src/router.js` |
| SPA views | `spa/src/views/` |
| SPA composables | `spa/src/composables/` |
| Radio station | `spa/src/composables/useRadioStation.js` |
| Playlist API | `blueprints/api/playlists.py` |
| DB models | `models.py` |
| DB migrations | `alembic/versions/` |
| Stripe/checkout | `app.py` + `blueprints/payments.py` |
| Mobile release script | `python fire.py` |
| Content sync | `python crud.py` |
| Render config | `render.yaml` |

---

## Dev server

```bash
python dev.py          # recommended (finds free port 5001-5010)
cd spa && npm run dev  # SPA hot-reload (optional, for frontend work)
```

---

## If something breaks

- Roll back migration: `alembic downgrade -1`
- Roll back on Render: redeploy previous commit from Render dashboard
- SPA cache issue on mobile: visit `/refresh` to clear SW + caches
