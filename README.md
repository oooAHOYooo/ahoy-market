# 🎵 Ahoy Indie Media: Technical Platform Overview

[![GitHub Actions](https://github.com/oooAHOYooo/ahoy-little-platform/workflows/auto-release/badge.svg)](https://github.com/oooAHOYooo/ahoy-little-platform/actions)
[![Release](https://img.shields.io/github/v/release/oooAHOYooo/ahoy-little-platform)](https://github.com/oooAHOYooo/ahoy-little-platform/releases)
[![License](https://img.shields.io/badge/license-ISC-blue)](LICENSE)

Ahoy is a high-performance, direct-to-artist media and commerce infrastructure. It provides a unified ecosystem for independent creators to distribute music, video, and podcasts while leveraging a secure financial layer for fan-to-artist transactions.

## 🏗️ Technical Architecture

Ahoy is built on a modular **Flask + Vue 3 SPA** architecture, distributed across Web (PWA), Mobile (Capacitor), and Desktop (Electron).

### Backend (Python/Flask)
- **Framework:** Flask (Python 3.10+) utilizing Blueprints for modularity.
- **ORM:** SQLAlchemy with PostgreSQL (Production) and SQLite (Development/Local).
- **Migrations:** Alembic for schema evolution.
- **Security:** Integrated CSRF protection, Flask-Login for session-based auth, and specialized security header middleware.
- **Observability:** Sentry integration for error tracking and structured logging (structlog).
- **Caching & Rate Limiting:** Redis-backed sessions and Flask-Limiter for API protection.

### Frontend (Vue 3/TypeScript)
- **Framework:** Vue 3 (Composition API) with Vite for ultra-fast builds.
- **State Management:** Pinia for reactive global state.
- **Styling:** Tailwind CSS 4.0 for utility-first design and responsive layouts.
- **Interactive Layers:** Three.js-powered canvas elements for ambient experiences (e.g., Games Lab hidden under Settings).
- **PWA:** Service workers for offline capability and background sync.

### Distribution Targets
- **Web:** Responsive SPA optimized for all viewports (Mobile-first dock shell < 1024px).
- **Mobile:** Capacitor-wrapped native projects for iOS (TestFlight) and Android (Google Play).
- **Desktop:** Electron-based distribution for macOS (DMG/ZIP), Windows (NSIS), and Linux (AppImage/DEB/Snap).

---

## 💎 Core Systems

### 1. Hybrid Content & Data Synchronization
Ahoy uses a sophisticated hybrid model where content (Music, Shows, Podcasts, Events) is managed via local JSON manifests and synchronized to the production database via custom ingestion pipelines.
- **Data Flow:** `Edit JSON` → `Scripts` → `Database` → `Client API`.
- **Search Engine:** A custom in-memory search indexer that builds from DB records with JSON fallbacks, supporting relevance ranking and match highlighting.

### 2. Financial Infrastructure (Stripe Connect)
The platform facilitates direct fan-to-artist payments with a 0% platform fee on tips.
- **Wallet System:** A pre-funded wallet architecture allowing instant checkout without repeated card entry.
- **Automated Payouts:** Uses **Stripe Connect** for programmatic transfers to artists.
- **Transaction Integrity:** Full audit trails in Postgres, matching Stripe webhooks for reliability.

### 3. Personalization & Gamification
- **Activity Tracking:** High-granularity listening sessions and view tracking.
- **Playlists:** Support for Public, Private, and Unlisted visibilities with batch media resolution.
- **Engagement:** Gamification engine supporting "Quests" and "Achievements" stored as JSONB preferences.

---

## 🚀 Development & Deployment

### Prerequisites
- Node.js >= 20.0.0
- Python >= 3.10
- PostgreSQL (optional for local dev)

### Local Environment Setup
```bash
# Clone and enter repo
git clone https://github.com/oooAHOYooo/ahoy-little-platform.git && cd ahoy-little-platform

# Backend Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# Frontend Setup
cd spa && npm install && npm run build && cd ..

# Environment Configuration
cp .env.example .env # Configure DATABASE_URL and STRIPE_SECRET_KEY
```

### Operational Workflows
| Task | Command |
|---|---|
| **Dev Server** | `python dev.py` (Hot-reload, auto-migrations) |
| **Content CRUD** | `python crud.py` (Interactive CLI for data management) |
| **Analytics / Ops** | `ahoy-cli`, `ahoy-cli stats`, `ahoy-cli backfill`, `ahoy-cli posthog-env-check`, `ahoy-cli posthog-mirror-check`, `ahoy-cli posthog-sync-check`, `ahoy-cli posthog-import <file>`, `ahoy-cli handoff` |
| **Sync DB** | `python scripts/import_podcast_collection.py` |
| **Payout Scan** | `python scripts/scan_artist_payouts.py` |
| **Build Apps** | `bash build_all.sh <version>` (Trigger Electron/Mobile pipelines) |

#### PostHog CLI
- `ahoy-cli posthog-env-check`: validate SPA/server PostHog env parity only
- `ahoy-cli posthog-mirror-check`: inspect the PostHog-import mirror in `analytics_events`
- `ahoy-cli posthog-sync-check`: run both checks and print a combined sync report

---

## 📁 Repository Structure

- `app.py`: Main application entrypoint and core API routing.
- `spa/`: Vue 3 Single-Page Application source code.
- `blueprints/`: Modular backend features (Auth, Payments, Gamification, Admin).
- `services/`: Business logic layers (Content DB, Listening tracking, Emailer).
- `models.py`: SQLAlchemy database models (Users, Playlists, Tips, Purchases).
- `alembic/`: Database migration scripts and history.
- `scripts/`: Operational scripts for payouts, imports, and maintenance.
- `packaging/`: Configuration for Electron, AUR, and mobile targets.

---

## 📖 API Surface Summary

### Media & Discovery
- `GET /api/music`: Retrieve track library.
- `GET /api/search?q=...`: Unified search across all content types.
- `GET /api/radio/manifest`: Dynamically generated radio programming.

### Commerce
- `POST /payments/wallet/fund`: Initialize Stripe checkout for wallet funding.
- `POST /api/tips/send`: Execute a tip from wallet balance to an artist.
- `GET /api/artist/earnings`: (Authenticated) Artist-specific financial analytics.

---

## 🔐 Security & Compliance
- **PCI-DSS:** Compliant via Stripe Elements and Hosted Checkout (no card data touches the server).
- **Authentication:** Scoped JWT/Session hybrid with BCrypt hashing.
- **Isolation:** Strict CSP policies and CORS origins enforced via `utils/security_headers.py`.

---

**Built by [Little Market LLC](https://littlemarket.org) for independent creators.**
