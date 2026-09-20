#!/bin/bash
# Automated deployment: bump version, tag, trigger builds, output checklist

set -e

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}🚀 Ahoy Deployment Automation${NC}\n"

# Parse args
if [ $# -ne 1 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 0.2.4"
    exit 1
fi

NEW_VERSION="$1"
TAG="v$NEW_VERSION"

# Validate version format (supports both 0.2.4 and 0.2.4.1)
if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(\.[0-9]+)?(-[a-zA-Z0-9]+)?$ ]]; then
    echo -e "${RED}❌ Invalid version format. Expected: 0.2.4 or 0.2.4.1 (or with -beta suffix)${NC}"
    exit 1
fi

# Check git is clean
if ! git -C "$PROJECT_ROOT" diff-index --quiet HEAD --; then
    echo -e "${RED}❌ Uncommitted changes detected. Commit or stash first.${NC}"
    exit 1
fi

# Check tag doesn't exist
if git -C "$PROJECT_ROOT" rev-parse "$TAG" 2>/dev/null; then
    echo -e "${RED}❌ Tag $TAG already exists.${NC}"
    exit 1
fi

cd "$PROJECT_ROOT"

echo -e "${YELLOW}Updating base version to $NEW_VERSION...${NC}"

# Update package.json (stores base version only, e.g., 0.2.4)
# Extract base version if 4-part provided (e.g., 0.2.4.1 → 0.2.4)
BASE_VERSION=$(echo "$NEW_VERSION" | sed 's/\([0-9]*\.[0-9]*\.[0-9]*\).*/\1/')

sed -i.bak "s/\"version\": \"[^\"]*\"/\"version\": \"$BASE_VERSION\"/" package.json
rm package.json.bak

# Update spa/package.json version
sed -i.bak "s/\"version\": \"[^\"]*\"/\"version\": \"$BASE_VERSION\"/" spa/package.json
rm spa/package.json.bak 2>/dev/null || true

if [ "$BASE_VERSION" = "$NEW_VERSION" ]; then
  echo -e "${GREEN}✅ Base version updated to $NEW_VERSION${NC}\n"
  echo "   (Next auto-release will be v${NEW_VERSION}.1)"
else
  echo -e "${GREEN}✅ Base version updated to $BASE_VERSION${NC}\n"
  echo "   (Forcing tag to v${NEW_VERSION})"
fi
echo ""

# Commit version bump
echo -e "${YELLOW}Creating version commit...${NC}"
git add package.json spa/package.json 2>/dev/null || git add package.json
git commit -m "chore: bump version to $NEW_VERSION"
echo -e "${GREEN}✅ Committed${NC}\n"

# Create and push tag
echo -e "${YELLOW}Creating tag $TAG and pushing...${NC}"
git tag "$TAG"
git push origin main "$TAG"
echo -e "${GREEN}✅ Tag pushed — GitHub Actions building now${NC}\n"

# Platform status
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 DEPLOYMENT CHECKLIST — $TAG${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo -e "${GREEN}✅ AUTOMATED${NC}"
if [ "$BASE_VERSION" = "$NEW_VERSION" ]; then
  echo "  • Base version set to $NEW_VERSION"
  echo "  • Next auto-releases will be: $NEW_VERSION.1, $NEW_VERSION.2, etc."
else
  echo "  • Forced tag: $TAG (build number override)"
fi
echo "  • Git tag pushed: $TAG"
echo "  • GitHub Actions started (3 runners: Linux/Windows/Mac)"
echo "  • Artifacts → GitHub Releases (auto-uploaded)"
echo "  • Snap Store → auto-published (if creds set)"
echo ""

echo -e "${YELLOW}⏳ WAIT FOR BUILDS${NC}"
echo "  1. Go to: https://github.com/oooAHOYooo/ahoy-little-platform/actions"
echo "  2. Watch 'release-desktop' workflow complete (all 3 jobs)"
echo "  3. Once done → artifacts in Releases tab"
echo ""

echo -e "${RED}⚠️  MANUAL — Linux (AUR)${NC}"
echo "  1. Update PKGBUILD:"
echo "     • Edit: packaging/PKGBUILD-bin"
echo "     • Change pkgver=$NEW_VERSION"
echo "     • Update sha256sum (get from GitHub Release)"
echo "  2. Regenerate .SRCINFO:"
echo "     $ cd packaging && makepkg --printsrcinfo > .SRCINFO"
echo "  3. Push to AUR:"
echo "     $ git push ssh://aur@aur.archlinux.org/ahoy.git main"
echo ""

echo -e "${RED}⚠️  MANUAL — macOS App Store${NC}"
echo "  1. Open Xcode Organizer or run:"
echo "     $ ./packaging/build-ios.sh upload"
echo "  2. Wait for App Review (typically 24–48h)"
echo ""

echo -e "${RED}⚠️  MANUAL — Android Play Store${NC}"
echo "  1. Build release AAB:"
echo "     $ cd android && ./gradlew bundleRelease"
echo "  2. Upload to Play Console:"
echo "     • Go to: https://play.google.com/console"
echo "     • Internal Testing → Upload AAB"
echo "     • Promote to Production when ready"
echo ""

echo -e "${GREEN}✅ Status Overview${NC}"
echo "  GitHub: https://github.com/oooAHOYooo/ahoy-little-platform/releases/tag/$TAG"
echo "  Actions: https://github.com/oooAHOYooo/ahoy-little-platform/actions"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
