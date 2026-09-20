#!/bin/bash
# Run this after a Windows release is published to get SHA256s for winget manifests.
# Usage: bash scripts/winget-sha256.sh 0.2.2

VERSION=${1:-0.2.2}
BASE="https://github.com/oooAHOYooo/ahoy-little-platform/releases/download/v${VERSION}"

echo "Fetching SHA256 for v${VERSION}..."
echo ""

for ARCH in x64 arm64; do
  FILE="ahoy-indie-media-${VERSION}-${ARCH}-setup.exe"
  URL="${BASE}/${FILE}"
  echo "=== ${ARCH} ==="
  echo "URL: ${URL}"
  curl -sL "${URL}" | sha256sum | awk '{print $1}'
  echo ""
done
