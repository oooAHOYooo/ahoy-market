#!/usr/bin/env bash
# Install Python deps and build Vue SPA so Flask can serve it at app.ahoy.ooo.
# On Render: use this as buildCommand so spa-dist exists before gunicorn starts.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "Installing Python dependencies..."
pip install -r requirements.txt

if command -v node >/dev/null 2>&1 && [ -f spa/package.json ]; then
  echo "Building Vue SPA (spa-dist)..."
  (
    cd spa
    npm ci --include=dev
    NODE_OPTIONS="--max-old-space-size=1024 ${NODE_OPTIONS:-}" npm run build
  )

  if [ -f spa-dist/index.html ]; then
    echo "Verifying SPA entrypoint assets..."
    missing_assets=0
    while IFS= read -r asset; do
      [ -n "$asset" ] || continue
      asset_path="spa-dist${asset}"
      if [ ! -f "$asset_path" ]; then
        echo "Missing SPA asset: $asset"
        missing_assets=1
      fi
    done <<EOF
$(grep -oE '/assets/index-[^"]+\.(js|css)' spa-dist/index.html | sort -u)
EOF
    if [ "$missing_assets" -ne 0 ]; then
      echo "SPA build verification failed."
      exit 1
    fi
  else
    echo "spa-dist/index.html missing after build."
    exit 1
  fi
else
  echo "Node not found or spa/package.json missing; skipping SPA build (web will use server-rendered pages)."
fi
