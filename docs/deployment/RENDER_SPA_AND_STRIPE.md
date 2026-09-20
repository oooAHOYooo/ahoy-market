# Render: SPA + Stripe (no extra config)

On Render, the **same web service** serves both the Vue SPA and Flask. You do **not** need to configure routing in the Render dashboard. It’s all handled inside the Flask app.

## How it works

1. **Build** (`buildCommand: ./scripts/build_with_spa.sh`)
   - Installs Python deps and builds the Vue SPA into `spa-dist/`.
   - So by the time the app starts, `spa-dist/index.html` and assets exist.
   - If the build step is skipped or incomplete, the start script now self-heals by rebuilding `spa-dist` before gunicorn starts.
   - The rebuild path installs the SPA dev dependencies explicitly so the `vite` CLI is available even when the host environment omits dev packages by default.
   - The SPA build also sets a larger Node heap during Vite compilation so the Render worker does not abort on large bundle transforms.

2. **Request handling** (in `app.py`)
   - **Before other routes:** A `before_request` hook runs. For **GET** requests whose path does **not** start with certain prefixes, Flask serves `spa-dist/index.html` (the SPA). The Vue router then handles the path on the client.
   - **Reserved for Flask:** Paths that **do** start with these prefixes are **not** served the SPA; they hit the normal Flask routes (and blueprints).

Reserved prefixes (Flask, not SPA):

- `api/` — all API endpoints
- `static/` — static files
- `ops/` — health, debug, etc.
- `checkout` — universal checkout page and process
- `success` — checkout success page
- `payments/` — wallet, fund, success/cancel
- `healthz`, `readyz`, `refresh`, `offline`
- `sitemap`, `robots.txt`
- `auth`, `feedback`, `contact`, `debug`
- `cast` is a legacy/outdated route and is intentionally excluded from the active shipping nav
- plus a few others (see `_server_path_prefixes` and `server_prefixes` in `app.py`)

So:

- **SPA:** `/`, `/dashboard`, `/music`, `/account`, `/podcasts`, etc. → `spa-dist/index.html` → Vue router.
- **Stripe / payments:** `/checkout`, `/checkout/process`, `/success`, `/payments/wallet`, `/payments/wallet/fund`, `/payments/wallet/success`, etc. → Flask (templates and payment logic).

## What you need on Render

- **Build command:** `./scripts/build_with_spa.sh` (already in `render.yaml`).
- **Start command:** Your usual start (e.g. `./scripts/migrate_and_start.sh`).
- The start command now checks for the hashed SPA entrypoint assets and rebuilds `spa-dist` if they are missing or stale, which protects against deploys that boot Flask without a complete frontend bundle.
- **Env vars:** Same as before (e.g. `DATABASE_URL`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, etc.). No new Render-specific env vars for routing.

After you merge to `main`, Render will build and deploy. The same app will serve the SPA for app routes and Flask for Stripe/checkout/payments with no extra Render configuration.
