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
npm run dev
```

Visit `http://127.0.0.1:3020`.

## Paid digital checkout setup

Digital checkout uses Stripe Checkout. The server prices the release from its catalog, creates a pending order, and grants the buyer's authenticated AHOY ID entitlement only after a signed `checkout.session.completed` or `checkout.session.async_payment_succeeded` event reports `payment_status=paid`. The browser return page does not grant ownership.

Configure these environment variables on the service:

| Variable | Value |
| --- | --- |
| `STRIPE_SECRET_KEY` | Secret API key from the Stripe account receiving payments |
| `STRIPE_WEBHOOK_SECRET` | Signing secret for the webhook endpoint below |
| `PUBLIC_BASE_URL` | Public HTTPS origin of this market, such as `https://market.ahoy.ooo` |
| `AHOY_ID_URL` | AHOY ID issuer origin |
| `AHOY_CLIENT_ID` | Registered marketplace OAuth client ID |
| `AHOY_REDIRECT_URI` | Registered `https://.../api/auth/callback` URL |
| `DATABASE_PATH` | SQLite path on a persistent disk or volume |
| `COOKIE_SECRET` | Random private cookie signing secret |

Create a Stripe webhook destination at `https://<market-host>/api/stripe/webhook` for `checkout.session.completed` and `checkout.session.async_payment_succeeded`. Test with Stripe test keys and a real AHOY ID login before switching to live keys. An ephemeral container filesystem loses pending orders and entitlements after restart, so mount persistent storage before accepting live payments.

The current seeded catalog uses public S3 MP3 URLs for both previews and purchased audio. The checkout records ownership in the market ledger, but it does not make the audio file private. Separate preview assets and private full files with short-lived authorized downloads are still needed for exclusive paid access. Physical editions and artist boosts do not have paid checkout yet; their direct purchase endpoints are disabled in production.
