# App Health Agent

This is a small, repository-owned health runner for the web app served at `app.ahoy.ooo`. It is read-only by default: it does not deploy, commit, push, release, message anyone, or load `.env` files. Generated reports and run state are written below `.local/app-health-agent/`, which is gitignored.

## Verified application map

- Backend entrypoints: `app.py` creates the Flask app; `wsgi.py` exposes it to Gunicorn.
- Frontend: `spa/` is a Vue 3/Vite app. `spa/vite.config.js` normally emits `spa-dist/`.
- Local commands: `python dev.py` starts the development stack; `cd spa && npm run build` builds; `cd spa && npm run preview` previews a build; Python tests are run with `python -m pytest`. No lint command is presently configured.
- Deployment: `render.yaml` uses `scripts/build_with_spa.sh`, starts `gunicorn -c gunicorn.conf.py app:app`, declares `https://app.ahoy.ooo` as `BASE_URL`, and configures Render to probe `/ops/selftest`.
- Existing app checks: `/healthz`, `/readyz`, and `/ops/selftest`. The agent only probes public URLs when explicitly enabled.

## Manual use

From the repository root:

```bash
python tools/app-health-agent/app-health-agent.py --dry-run
python tools/app-health-agent/app-health-agent.py
python tools/app-health-agent/app-health-agent.py --browser
```

### Later: the two commands to remember

For the normal local check, use:

```bash
python tools/app-health-agent/app-health-agent.py
```

To include the configured public app and the rendered desktop/mobile check in a deliberate operator run, use:

```bash
APP_HEALTH_PUBLIC_URL=https://app.ahoy.ooo \
  python tools/app-health-agent/app-health-agent.py --browser
```

Open the newest Markdown file in `.local/app-health-agent/reports/` for the result. That folder is intentionally local and gitignored.

The normal run builds the SPA in a disposable temporary copy. This protects the current worktree and, in particular, never replaces the checked-in `spa-dist/` directory. It runs pytest using `.venv/bin/python` when available.

To enable the optional public-domain checks for this run only:

```bash
APP_HEALTH_PUBLIC_URL=https://app.ahoy.ooo \
  python tools/app-health-agent/app-health-agent.py
```

The public URL is intentionally not a default, even though Render configuration documents one. This avoids unexpected network traffic and makes the target an explicit operator choice. Change checked public SPA routes with `APP_HEALTH_ROUTES=/,/music,/artists` or `--routes`.

## Report format

Each Markdown report includes build/test/lint/public-route results, Git changes from `main`, a comparison to the previous local run, and a severity-ranked attention list. The process exits nonzero if a performed check fails; skipped checks do not fail the run. Output is kept to short diagnostic summaries and sensitive-looking command output is suppressed.

## Browser QA and scheduling

`--browser` is an explicit opt-in local browser check. It serves the existing `spa-dist/` output only on `127.0.0.1`, opens the configured routes at 1440x900 and 390x844, and stores full-page PNGs next to the report. It fails on route HTTP failures, JavaScript console errors, failed network requests, empty same-origin links, or horizontal overflow. It does not log in, submit forms, make purchases, or touch public services. Because it tests the existing local build, run the normal isolated build check first; its output does not replace `spa-dist/`.

The checked-in Playwright package also needs a local Chromium binary. If the agent reports that it is absent, an operator may install it separately with `cd spa && npx playwright install chromium`; that download is intentionally not performed by the health agent.

For scheduling later, use a user-controlled launcher (for example macOS `launchd` or a CI scheduled workflow) that invokes the same command with `APP_HEALTH_PUBLIC_URL` only if public probing is desired. Keep output directed to `.local/app-health-agent/`; do not give the scheduled job deployment, Git write, payment, or messaging credentials.
