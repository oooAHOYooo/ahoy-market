#!/usr/bin/env bash
# build_desktop_backend.sh — Package the Flask backend for Electron using PyInstaller

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Building Ahoy Python Backend ==="

cd "$ROOT_DIR"

# Ensure PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# We use --onedir to create a folder with the executable and its libraries.
# We include critical data directories so they are available in sys._MEIPASS
# Alternatively, since Electron bundles these in extraResources, we could rely on that.
# For maximum compatibility, we'll bundle the python code and rely on Electron for static/templates.

pyinstaller --name ahoy-backend \
    --onedir \
    --clean \
    --noconfirm \
    --add-data "templates:templates" \
    --add-data "static:static" \
    --add-data "data:data" \
    --add-data "alembic.ini:." \
    --add-data "alembic:alembic" \
    --hidden-import "psycopg2" \
    --hidden-import "email_validator" \
    --hidden-import "authlib.integrations.flask_client" \
    desktop_main.py

echo "Backend built successfully in dist/ahoy-backend/"
