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
