# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Status:** v1.1.5 in progress. Live on Google Play and TestFlight. Identity `ooo.ahoy.app` active.

## Default Session Start

For any new task in this repository, read these files first before making assumptions:

1. `docs/APP_OVERVIEW.md`
2. `CLAUDE.md`
3. `README.md`

Use them as the default product-memory anchor for the repo.

If a task changes behavior, adds a feature, removes a feature, or clarifies architecture, update the relevant documentation before wrapping up. At minimum, update `docs/APP_OVERVIEW.md` when the change affects product shape, architecture, user flows, or major code ownership.

---

## Project

**Flask + Vue SPA** media platform (music, shows, artists, podcasts, payments, auth). SPA (`spa/src/`) is primary UI; Flask templates (`templates/`) legacy (API/auth only).

**Active:**
- **Current version**: v1.1.4 — Radio redesign, profile editing, search improvements, AHOY TV mobile polish.
- **Google Play**: Live. Next submission: v1.1.4 AAB via `cd android && ./gradlew bundleRelease`.
- **Apple TestFlight**: `ooo.ahoy.app` live as "Ahoy Indie Media App". Next: `./packaging/build-ios.sh upload`.
- **DNS/Branding**: `ahoy.ooo` and `ooo.ahoy.app` identifier active.
## Quick Commands

```bash
python dev.py                    # Start dev server (recommended)
python app.py                    # Run directly (auto-finds port 5001-5010)
pytest tests/                    # Run tests
alembic upgrade head             # Apply DB migrations
alembic revision --autogenerate -m "msg"  # Create migration
python crud.py                   # Content/release/DB-sync menu
npm run build                    # Build SPA (spa/ directory)
```

**Cache busting:** Bump `css_version` in `templates/base.html` (~line 144). Auto-releases on `git push main`.

## Architecture

| Layer | Location | Notes |
|---|---|---|
| Entry | `app.py` | Flask factory, ~210KB, most routes |
| DB | `db.py`, `models.py` | SQLAlchemy ORM, `get_session()` context |
| API | `blueprints/api/`, `routes/` | Auth, playlists, bookmarks, payments |
| Services | `services/` | Content DB, emailer, notifications |
| Config | `config.py`, `extensions.py` | `AHOY_ENV` switches test/live Stripe |
| Data | `static/data/*.json` | Fallback for music, shows, artists |
| SPA | `spa/src/` → `spa-dist/` | Vue 3, built by `npm run build` |

**Data source of truth:**
- **DB-backed:** Podcasts, music, shows, artists (edit JSON → sync → DB)
- **JSON-only:** Events, videos, what's new (git push = live)
- **User data:** Always Postgres (auth, playlists, bookmarks, payouts)

## Cache, Mobile, Builds

**Cache:**
- HTML: `no-cache, no-store` (never SW cached)
- CSS/JS: Long cache + versioned URLs (`?v=css_version`). Bump on deploy.
- Escape hatch: `/refresh` clears SW + caches
- Mobile app: Loads from deployed URL (baked into binary). Redeploy + `/refresh` to update.

**Mobile scroll fixes:**
1. Change `touch-action: none` → `pan-y`
2. Remove `event.preventDefault()` in touch handlers
3. Remove `overflow: hidden` from `html`/`body`
4. Check `loader.js` exit at top (line 25)
5. Increment `css_version` if SW cache is issue

**Android bottom deck safe-area note:**
- Before changing the mobile bottom deck, read `docs/mobile/ANDROID_BOTTOM_DECK_SAFE_AREA.md`.
- Current Android understanding: do not lift `.bottom-deck` with external `margin-bottom`; keep it flush at `bottom: 0`, add Android-only internal reserve on `.deck-frame`, and pin Deck 1 rows lower because `.mobile-dock` flex centering creates apparent hidden padding below the icons.
- Scope matters: Android rules belong under `body.platform-android`; do not apply the Android reserve to iOS or web (`app.ahoy.ooo`) unless real-device testing proves a separate issue.

**Releases:**
- Identity: `ooo.ahoy.app` (Identifier), "Ahoy Indie Media App" (Name).
- Versioning: `1.1.4` (current base). Auto-bumps: build number auto-incremented per push (`v1.1.4.N`).
- Version format: base in `package.json` (`1.1.4`) + build number suffix added by CI.
- Guided local mobile release: `python fire.py` runs preflight checks, syncs Capacitor, launches iOS/Android test targets, waits for manual approval, then builds iOS archive + Android AAB.
- Scoped release helper modes: `python fire.py --test-only`, `--build-only`, `--ios-only`, `--android-only`
- Manual: `bash scripts/deploy.sh 0.2.5` (bump patch)
- AUR: Edit `pkgver` in `packaging/PKGBUILD-bin`, push to AUR
- iOS: `./packaging/build-ios.sh upload`
- Android: `cd android && ./gradlew bundleRelease` → Play Console

**Env vars (production):** `SECRET_KEY`, `DATABASE_URL`, `STRIPE_SECRET_KEY`, `RESEND_API_KEY`, `AHOY_ADMIN_EMAIL`

## Videos Page (Shows)

**Layout:** Grid displays videos in randomized order. Featured carousel moved below grid (not above). 

**"New" Tag Rule:** Videos released in the past 2 months get a "new" tag. Define by `release_date` / `released_at` / `date` fields in shows JSON. As of 2026-04-02, "new" = March 2026 and April 2026. **Apply this rule to all future videos:** always show "new" for videos released within the previous 2 months from today.

**Mobile:** Featured carousel uses 16:9 aspect ratio; arrows always visible.

## Documentation Maintenance

Treat docs as part of the feature, not follow-up work.

Update docs in the same task when you:

- add a user-facing feature
- fix a bug that changes behavior
- change setup, deployment, or environment requirements
- move ownership between Flask routes, blueprints, services, SPA, or native wrappers
- discover a product rule worth preserving

Preferred doc targets:

- `docs/APP_OVERVIEW.md` for product shape, architecture, and major flows
- `README.md` for developer-facing setup or top-level capabilities
- a focused file under `docs/` when a subsystem needs deeper explanation

When updating `docs/APP_OVERVIEW.md`, prefer concise additions that keep it readable as the first file to scan in future conversations.

## Release Notes Discipline

Every user-facing change must land in the in-progress release notes file for the current version before the task is considered done. This keeps TestFlight / Play Console submission notes, the `CHANGELOG.md`, and store copy all derivable from one file.

**The rule:**

1. The current release notes file lives at `docs/RELEASE_NOTES_v<version>.md` (e.g. `docs/RELEASE_NOTES_v1.0.8.md`). Version matches `package.json`.
2. If no release notes file exists for the current version, create one following the structure of the most recent prior file (`RELEASE_NOTES_v1.0.6.md` is the reference template).
3. After finishing any task that adds / changes / fixes user-visible behavior — UI, feature, API surface, perf that users feel, bug fix users noticed — append an entry to the correct section (`What's new`, `Fixes`, `Changed`, or `Known gaps`).
4. Internal refactors with no user-visible effect do **not** need a release-notes entry.
5. When bumping to a new version, create the next `RELEASE_NOTES_v<version>.md` on the same commit as the version bump — do not leave it until the end of the cycle.

**Closing-message convention:**

At the end of any turn where user-facing work shipped (code landed, feature merged, bug fixed), end the reply with a one-line reminder: **"Add to release notes?"** — naming the file and a suggested bullet. If the entry was already added during the turn, confirm it instead (`Added to docs/RELEASE_NOTES_v1.0.8.md under Fixes.`).

Skip the reminder for: pure research / questions, docs-only edits that already update release notes, or changes explicitly flagged as internal-only.
