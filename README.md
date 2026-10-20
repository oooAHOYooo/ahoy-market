# AHOY Market (`market.ahoy.ooo`)

Sovereign digital music & merchandise storefront for the AHOY Indie Media Ecosystem.

## Features

- **Sovereign AHOY ID Sign-In**: Authenticates with `id.ahoy.ooo` via OAuth 2.1 PKCE (`app.ahoy.market`).
- **Artist-Approved Storefront**: Digital singles, EPs, and albums with previews.
- **Entitlement Ledger**: Purchases write permanent ownership to the buyer's sovereign `ahoy_id`.
- **AHOY Player Integration**: `player.ahoy.ooo` queries `/api/entitlements` to stream and play owned tracks.
- **Streamer Cross-Linking**: Direct product links from `app.ahoy.ooo` (The Streamer).

## API Endpoints

### Storefront & Catalog
- `GET /api/releases`: List available catalog releases with track info.
- `GET /api/releases/:slug`: Get single release details.
- `GET /api/stream/:trackId`: Stream track (full audio for entitled users, preview otherwise).

### AHOY ID Auth
- `GET /api/auth/login`: Initiate PKCE login redirect to AHOY ID.
- `GET /api/auth/callback`: OAuth callback code exchange & session creation.
- `GET /api/auth/me`: Current session status & owned track count.
- `POST /api/auth/logout`: Sign out and destroy session.

### Purchases & Entitlements
- `POST /api/checkout/purchase`: Buy release/track and grant entitlement to `ahoy_id`.
- `GET /api/me/library`: User's purchased music library.
- `GET /api/entitlements?ahoy_id=...`: Player API returning all owned tracks for an `ahoy_id`.

## Quick Start

```bash
npm install
cp .env.example .env
npm run dev
```

Visit `http://127.0.0.1:3020`.

Use Node 22 for local development. Run `npm run build` and `npm test` before release; the tests use the native `better-sqlite3` module and require dependencies installed for the active Node version.

AHOY ID registers separate market clients with `openid profile` scopes: `app.ahoy.market.local` for `http://127.0.0.1:3020/api/auth/callback`, and `app.ahoy.market` for `https://market.ahoy.ooo/api/auth/callback`. Apply the AHOY ID market-client migration before real sign-in. The local development login helper exercises only the market session flow.

## Paid digital checkout setup

Digital checkout uses Stripe Checkout. The server prices the release from its catalog, creates a pending order, and grants the buyer's authenticated AHOY ID entitlement only after a signed `checkout.session.completed` or `checkout.session.async_payment_succeeded` event reports `payment_status=paid`. The browser return page does not grant ownership.

Configure these environment variables on the service:

| Variable | Value |
| --- | --- |
| `STRIPE_SECRET_KEY` | Secret API key from the Stripe account receiving payments |
| `STRIPE_WEBHOOK_SECRET` | Signing secret for the webhook endpoint below |
| `PUBLIC_BASE_URL` | Public HTTPS origin of this market, such as `https://market.ahoy.ooo` |
| `AHOY_ID_URL` | AHOY ID issuer origin (`https://id.ahoy.ooo` in production) |
| `AHOY_CLIENT_ID` | Registered marketplace OAuth client ID |
| `AHOY_REDIRECT_URI` | Registered `https://.../api/auth/callback` URL |
| `DATABASE_PATH` | SQLite path on a persistent disk or volume |
| `COOKIE_SECRET` | Random private cookie signing secret |
| `AWS_ACCESS_KEY_ID` | (Optional) AWS / R2 / S3 access key ID for private audio pre-signing |
| `AWS_SECRET_ACCESS_KEY` | (Optional) AWS / R2 / S3 secret access key |
| `AWS_REGION` | (Optional) AWS / S3 region (defaults to `us-east-2`) |
| `AWS_S3_BUCKET` | (Optional) Private audio master storage bucket |
| `S3_ENDPOINT` | (Optional) Custom endpoint for Cloudflare R2 / MinIO storage |
| `S3_URL_EXPIRATION_SECONDS`| (Optional) Expiration window for pre-signed URLs (defaults to 900s / 15m) |
| `CLOUDFRONT_DOMAIN` | (Optional) CloudFront distribution domain for CDN signed URLs |
| `CLOUDFRONT_KEY_ID` | (Optional) CloudFront public key ID |
| `CLOUDFRONT_PRIVATE_KEY`| (Optional) CloudFront RSA private key in PEM format |

Create a Stripe webhook destination at `https://<market-host>/api/stripe/webhook` for `checkout.session.completed` and `checkout.session.async_payment_succeeded`. Test with Stripe test keys and a real AHOY ID login before switching to live keys. An ephemeral container filesystem loses pending orders and entitlements after restart, so mount persistent storage before accepting live payments.

For the first paid release, configure the production URL and registered AHOY ID callback, mount a persistent directory for `DATABASE_PATH`, set the two Stripe secrets, and verify a test card purchase reaches My Library and downloads an MP3. The buyer return page checks the pending order until the signed webhook confirms it. The market currently sells digital music only; physical editions and boosts have no live checkout.

### Private Audio Vault & Pre-Signed URLs

Purchased master audio files can be placed in a private AWS S3, Cloudflare R2, or CloudFront distribution with public access blocked:
- **Short-Lived Ephemeral Links:** When an entitled user requests playback or a download (`/api/stream/:trackId`, `/api/download/:trackId`, or `/api/entitlements`), the server verifies entitlement in the local SQLite ledger and signs an ephemeral AWS SigV4 pre-signed URL or CloudFront signed URL valid for 15 minutes (`X-Amz-Expires=900`).
- **Unentitled Protection:** Users without an active entitlement are redirected strictly to public 30-second preview clips and cannot acquire pre-signed links.
- **Graceful Fallback:** If storage credentials are omitted (e.g. in local development or test runners), the system falls back to the database-cataloged URLs without breaking existing workflows.

## Security Architecture & Hardening

The marketplace incorporates several layers of defense to protect user identity, payment integrity, and sovereign entitlements:

- **Scoped CORS with Credentials:**
  Cross-origin requests with credentials (`cookies`, `Authorization`) are restricted to verified origins (`PUBLIC_BASE_URL`, `AHOY_PLAYER_URL`, `AHOY_STREAMER_URL`, `AHOY_ID_URL`, plus loopback interfaces during local development). Untrusted external websites are prohibited from reading authenticated session data or initiating orders on behalf of users.
- **Defensive HTTP Response Headers:**
  Standard defense-in-depth headers are injected into all HTTP responses:
  - `X-Content-Type-Options: nosniff`: Mitigates MIME-type confusion and content sniffing.
  - `X-Frame-Options: SAMEORIGIN`: Prevents clickjacking and unauthorized embedding in external iframes.
  - `Referrer-Policy: strict-origin-when-cross-origin`: Restricts sensitive path/token leakage via referrers to external origins.
  - `X-XSS-Protection: 0`: Modern secure setting disabling legacy buggy browser XSS filters in favor of robust parsing.
- **Dual-Layer Contextual HTML & JS Escaping:**
  The frontend UI uses strict context-aware escaping:
  - `escapeHtml()`: Escapes `&`, `<`, `>`, `"`, `'`, and `` ` `` to HTML entities (`&amp;`, `&lt;`, `&gt;`, `&quot;`, `&#39;`, `&#96;`).
  - `escapeJsAttr()`: Encodes backslashes and single quotes (`\'`) when data attributes or JS parameters are passed inside inline HTML event handlers, preventing attribute breakouts and script injection even with titles containing apostrophes.
- **Upstream Network Request Timeouts:**
  All server-side outbound `fetch()` requests (Stripe Checkout creation, AHOY ID token exchange, userinfo queries, and audio downloads) enforce strict `AbortSignal.timeout(10_000)` (or 30s for large audio proxying), preventing worker thread socket starvation and denial-of-service under slow-loris or upstream outage conditions.
- **Bounded In-Memory PKCE State Cache:**
  The OAuth PKCE cache evicts entries older than 10 minutes and enforces an upper bound of 1,000 active states to mitigate memory-exhaustion attacks.
- **Replay-Resistant & Constant-Time Webhook Verification:**
  Stripe webhook events are verified using HMAC-SHA256 signatures with constant-time equality comparisons (`crypto.timingSafeEqual`) and a strict 300-second timestamp freshness tolerance to eliminate timing attacks and replay exploits.
- **Safe Database Queries & Durability:**
  All SQL queries in `better-sqlite3` use parameterized prepared statements; no string concatenation is used for database inputs. Foreign key constraints (`PRAGMA foreign_keys = ON`) and WAL mode with synchronous normalization (`PRAGMA synchronous = NORMAL`) are enforced at connection initialization.
- **Graceful Shutdown & Signal Handling:**
  The server process intercepts `SIGINT` and `SIGTERM` signals to cleanly shut down active Fastify HTTP connections and close SQLite database handles, flushing WAL journals to prevent database corruption during container restarts or deployments.
- **Container Hardening:**
  The production `Dockerfile` enforces the principle of least privilege, running as the unprivileged `node` user rather than `root`.
- **Query Parameter Bounding:**
  Endpoints accepting pagination or count limits (e.g., `/api/artists/:slug/boosts`, `/api/leaderboard/boosters`) enforce strict numeric clamping (1 to 100) to prevent denial-of-service from unbounded queries.
- **CRLF & Header Injection Protection:**
  Audio download filenames strip newline characters (`\r`, `\n`) and invalid filesystem characters before formatting `Content-Disposition` attachment headers.
- **Environment & Secret Safeguards:**
  In production (`NODE_ENV=production`), missing `COOKIE_SECRET` triggers runtime security warnings, and development-only bypasses (`/api/auth/dev-login`, direct test card checkout, unauthenticated boost query inspections) are strictly locked down.

## Performance Optimizations

- **SQLite In-Memory Caching & Indexing:**
  - WAL journal mode with 64 MB page cache (`PRAGMA cache_size = -64000`) and in-memory temporary storage (`PRAGMA temp_store = MEMORY`).
  - Added indexes for release timestamps (`ix_releases_created_at`), artist releases (`ix_releases_artist_slug`), track sequence (`ix_tracks_release_track`), active entitlement lookups (`ix_entitlements_lookup`), and boost amounts (`ix_boosts_artist_amount`).
  - Catalog and market snapshot queries use `getPublicArtists()` to perform a direct indexed table query, skipping redundant aggregation joins over private patron records.
- **Client-Side DocumentFragment Batching & Reflow Prevention:**
  Card list rendering (`renderFeatured`, `renderAlbumsView`, `renderCdsView`, `renderCardsView`, `renderArtists`, `renderCdPoolTracks`) builds DOM trees in memory with `DocumentFragment` before attaching to the document, eliminating repeated layout recalculations and browser paints.
- **Asynchronous Image Decoding & Lazy Loading:**
  All artwork and avatar `<img>` tags declare `loading="lazy"` and `decoding="async"`, preventing offscreen image decoding from blocking the main UI thread during scrolling.
- **Differentiated Static Asset Caching:**
  Static assets (wordmarks, images, favicons) are served with `Cache-Control: public, max-age=86400, stale-while-revalidate=604800`, while `index.html` uses `Cache-Control: no-cache` to ensure browser clients always display the newest releases without stale client states.
