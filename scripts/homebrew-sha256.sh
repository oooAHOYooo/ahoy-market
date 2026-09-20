#!/usr/bin/env bash
# homebrew-sha256.sh — Compute SHA256s for Mac DMGs and update the Homebrew cask.
#
# Usage:
#   bash scripts/homebrew-sha256.sh <version>
#   bash scripts/homebrew-sha256.sh 0.2.2
#
# After this runs, copy packaging/homebrew/ahoy.rb into:
#   oooAHOYooo/homebrew-tap → Casks/ahoy.rb
# and commit + push.
#
# Users install with:
#   brew tap oooAHOYooo/tap
#   brew install --cask ahoy

set -euo pipefail

VERSION=${1:-}
if [[ -z "$VERSION" ]]; then
  echo "Usage: bash scripts/homebrew-sha256.sh <version>   (e.g. 0.2.2)"
  exit 1
fi

REPO="oooAHOYooo/ahoy-little-platform"
BASE_URL="https://github.com/${REPO}/releases/download/v${VERSION}"
X64_URL="${BASE_URL}/Ahoy%20Indie%20Media-${VERSION}.dmg"
ARM64_URL="${BASE_URL}/Ahoy%20Indie%20Media-${VERSION}-arm64.dmg"
CASK="$(dirname "$0")/../packaging/homebrew/ahoy.rb"

echo "Fetching x64 DMG SHA256..."
X64_SHA=$(curl -sL "$X64_URL" | shasum -a 256 | awk '{print $1}')
echo "  x64:   $X64_SHA"

echo "Fetching arm64 DMG SHA256..."
ARM64_SHA=$(curl -sL "$ARM64_URL" | shasum -a 256 | awk '{print $1}')
echo "  arm64: $ARM64_SHA"

# Update cask file
sed -i '' "s/^  version .*/  version \"${VERSION}\"/" "$CASK"
sed -i '' "s/sha256 \"REPLACE_WITH_X64_SHA256\"/sha256 \"${X64_SHA}\"/" "$CASK"
sed -i '' "s/sha256 \"REPLACE_WITH_ARM64_SHA256\"/sha256 \"${ARM64_SHA}\"/" "$CASK"
# Also update existing sha256 lines (for re-runs on already-filled casks)
# (The sed above handles fresh templates; for updates use build_all.sh which rewrites the whole file)

echo ""
echo "Updated: packaging/homebrew/ahoy.rb"
echo ""
echo "Next steps:"
echo "  1. Clone oooAHOYooo/homebrew-ahoy"
echo "  2. Copy packaging/homebrew/ahoy.rb → Casks/ahoy.rb"
echo "  3. git add Casks/ahoy.rb && git commit -m 'Update ahoy to ${VERSION}' && git push"
echo ""
echo "Users install with:"
echo "  brew install --cask oooAHOYooo/ahoy/ahoy"
