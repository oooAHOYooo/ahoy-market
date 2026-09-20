#!/bin/bash
# Auto-update AUR package (PKGBUILD + .SRCINFO)
# Usage: bash scripts/update-aur.sh 0.2.5
# or just: bash scripts/update-aur.sh (uses current version from package.json)

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}🐧 AUR Package Update${NC}\n"

# Get version
if [ -z "$1" ]; then
  VERSION=$(grep '"version"' "$PROJECT_ROOT/package.json" | head -1 | sed 's/.*"\([^"]*\)".*/\1/')
else
  VERSION="$1"
fi

echo "Version: $VERSION"
REPO_URL="https://github.com/oooAHOYooo/ahoy-little-platform"
RELEASE_URL="$REPO_URL/releases/tag/v$VERSION"

# Get latest release info
echo -e "\n${YELLOW}Fetching release info...${NC}"
RELEASE_JSON=$(curl -s "https://api.github.com/repos/oooAHOYooo/ahoy-little-platform/releases/tags/v$VERSION")

# Extract AppImage download URL and get SHA256
APPIMAGE_URL=$(echo "$RELEASE_JSON" | grep -o '"browser_download_url":"[^"]*x86_64.AppImage' | cut -d'"' -f4)

if [ -z "$APPIMAGE_URL" ]; then
  echo -e "${RED}❌ Could not find AppImage in release v$VERSION${NC}"
  echo "Check: $RELEASE_URL"
  exit 1
fi

echo "Downloading AppImage for SHA256 calculation..."
TEMP_DIR=$(mktemp -d)
APPIMAGE_FILE="$TEMP_DIR/ahoy.AppImage"
curl -sL "$APPIMAGE_URL" -o "$APPIMAGE_FILE"

SHA256=$(sha256sum "$APPIMAGE_FILE" | cut -d' ' -f1)
rm -rf "$TEMP_DIR"

echo -e "${GREEN}✅ SHA256: $SHA256${NC}\n"

# Update PKGBUILD
echo -e "${YELLOW}Updating packaging/PKGBUILD-bin...${NC}"
PKGBUILD_FILE="$PROJECT_ROOT/packaging/PKGBUILD-bin"

if [ ! -f "$PKGBUILD_FILE" ]; then
  echo -e "${RED}❌ PKGBUILD-bin not found at $PKGBUILD_FILE${NC}"
  exit 1
fi

# Update version
sed -i.bak "s/^pkgver=.*/pkgver=$VERSION/" "$PKGBUILD_FILE"
# Update SHA256
sed -i.bak "s/sha256sum=.*/sha256sum='$SHA256'/" "$PKGBUILD_FILE"
rm "$PKGBUILD_FILE.bak"

echo -e "${GREEN}✅ Updated PKGBUILD-bin${NC}\n"

# Regenerate .SRCINFO
echo -e "${YELLOW}Regenerating .SRCINFO...${NC}"
cd "$PROJECT_ROOT/packaging"

if ! command -v makepkg &> /dev/null; then
  echo -e "${RED}❌ makepkg not found. Install: sudo pacman -S base-devel${NC}"
  exit 1
fi

makepkg --printsrcinfo > .SRCINFO
cd "$PROJECT_ROOT"

echo -e "${GREEN}✅ Regenerated .SRCINFO${NC}\n"

# Show summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ AUR Package Ready for v$VERSION${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo "Next steps:"
echo ""
echo "  1. Review changes:"
echo "     $ git diff packaging/PKGBUILD-bin packaging/.SRCINFO"
echo ""
echo "  2. Commit:"
echo "     $ cd $PROJECT_ROOT"
echo "     $ git add packaging/PKGBUILD-bin packaging/.SRCINFO"
echo "     $ git commit -m 'aur: v$VERSION'"
echo ""
echo "  3. Push to AUR:"
echo "     $ git push ssh://aur@aur.archlinux.org/ahoy.git main"
echo ""
echo "  4. Users can then install:"
echo "     $ yay ahoy"
echo ""
