#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

spa_bundle_ready() {
    [ -f spa-dist/index.html ] || return 1

    local missing_assets=0
    while IFS= read -r asset; do
        [ -n "$asset" ] || continue
        [ -f "spa-dist${asset}" ] || missing_assets=1
    done <<EOF
$(grep -oE '/assets/index-[^"]+\.(js|css)' spa-dist/index.html | sort -u || true)
EOF

    [ "$missing_assets" -eq 0 ]
}

if ! spa_bundle_ready; then
    echo "SPA bundle missing or stale; rebuilding spa-dist before startup..."
    ./scripts/build_with_spa.sh
fi

echo "Running database migrations..."
alembic upgrade head

echo "Importing content from legacy JSON into database..."
python scripts/import_content_from_json.py

echo "Importing events and merch (Render-dynamic)..."
python scripts/import_events_merch.py || true

echo "Importing podcast collection (flat list -> DB)..."
python scripts/import_podcast_collection.py || true

echo "Removing unwanted podcast shows..."
python scripts/remove_unwanted_podcast_shows.py || true

echo "Importing videos and what's new (Render-dynamic)..."
python scripts/import_videos_whats_new.py || true

echo "Seeding Kicker Pictures artist + Elvis short film..."
python scripts/seed_kicker_pictures.py || true

echo "Setting/resetting alexMaster password..."
python scripts/set_alexmaster_password.py || true

echo "Updating Tyler Needs a Break thumbnails..."
python scripts/update_tyler_thumbnails.py || true

echo "Starting gunicorn..."
exec gunicorn app:app --workers 2 --threads 4 --timeout 120
