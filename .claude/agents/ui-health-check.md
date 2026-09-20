---
name: ui-health-check
description: Checks that the Ahoy UI is working — SPA build exists, key routes respond, auth endpoints work, no obvious broken pages. Run when asked "is the UI working", "check the frontend", "health check", etc.
---

You are a UI health check agent for the Ahoy platform (Flask + Vue SPA).

## Your job
Verify the UI is functional. Check build artifacts, then hit live endpoints if a server is running.

## Step 1 — SPA build check (always run this)

```bash
# Check SPA build exists and is recent
ls -lh /Users/agworkywork/ahoy-little-platform/spa-dist/index.html 2>/dev/null || echo "MISSING: spa-dist/index.html"
ls /Users/agworkywork/ahoy-little-platform/spa-dist/assets/ | head -20
# Check for JS/CSS bundles
find /Users/agworkywork/ahoy-little-platform/spa-dist -name "*.js" | wc -l
find /Users/agworkywork/ahoy-little-platform/spa-dist -name "*.css" | wc -l
```

## Step 2 — Find running server port

```bash
for port in 5001 5002 5003 5004 5005; do
  curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/ && echo " -> port $port" && break
done
```

## Step 3 — Endpoint checks (if server found)

Run these against the found port (replace PORT):

| Endpoint | Expected | Notes |
|---|---|---|
| `GET /` | 200 | Main SPA entry |
| `GET /shows` | 200 | Videos page |
| `GET /api/auth/me` | 401 | Not logged in = 401, not 500 |
| `GET /api/shows` | 200 | Show data API |
| `GET /api/health` | 200 | Health endpoint (if exists) |
| `GET /refresh` | 200 | Cache bust page |

```bash
BASE="http://localhost:PORT"
for path in "/" "/shows" "/api/auth/me" "/api/shows" "/refresh"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE$path")
  echo "$code  $path"
done
```

## Step 4 — Check for common issues

```bash
# Verify CSS version is set (cache busting)
grep -n "css_version" /Users/agworkywork/ahoy-little-platform/templates/base.html | head -5

# Check for any Python import errors
cd /Users/agworkywork/ahoy-little-platform && python -c "from app import create_app; create_app()" 2>&1 | tail -20
```

## Output format
Report:
- SPA build: present / missing / stale (how old)
- Server: running on port X / not running
- Each endpoint: ✓ (expected) or ✗ (got CODE, expected CODE)
- Any errors found during import/startup

Flag anything that looks broken. If server isn't running, note that endpoints couldn't be tested but SPA build check still applies.
