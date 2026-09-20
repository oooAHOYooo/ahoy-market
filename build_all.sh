#!/usr/bin/env bash
# build_all.sh — Build and publish Ahoy for all platforms.
#
# Usage:
#   bash build_all.sh <version>        # e.g. bash build_all.sh 0.2.2
#
# What it does:
#   1. Bumps version in package.json
#   2. Builds SPA
#   3. Tags + pushes → triggers GitHub Actions (Linux AppImage/DEB, Windows NSIS, Mac DMG)
#   4. Waits for release artifacts to appear
#   5. Updates AUR PKGBUILD and pushes to aur.archlinux.org
#   6. Updates winget manifest with SHA256 and opens PR to microsoft/winget-pkgs
#   7. Updates Homebrew tap cask and pushes to oooAHOYooo/homebrew-tap
#
# Prerequisites:
#   - gh CLI authenticated (gh auth status)
#   - AUR SSH key at ~/.ssh/aur
#   - homebrew-tap repo cloned at ../homebrew-tap (or set HOMEBREW_TAP_DIR)
#   - AUR repo cloned at ../aur-ahoy (or set AUR_DIR)

set -euo pipefail

VERSION=${1:-}
if [[ -z "$VERSION" ]]; then
  echo "Usage: bash build_all.sh <version>  (e.g. 0.2.2)"
  exit 1
fi

REPO="oooAHOYooo/ahoy-little-platform"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUR_DIR="${AUR_DIR:-/tmp/aur-ahoy}"
HOMEBREW_TAP_DIR="${HOMEBREW_TAP_DIR:-/tmp/homebrew-tap-push}"

echo "=== Ahoy build_all v${VERSION} ==="
echo ""

# ── 1. Bump version ───────────────────────────────────────────────────────────
echo "[1/7] Bumping version to ${VERSION}..."
cd "$SCRIPT_DIR"
node -e "
const fs = require('fs');
const p = JSON.parse(fs.readFileSync('package.json'));
p.version = '${VERSION}';
fs.writeFileSync('package.json', JSON.stringify(p, null, 2) + '\n');
"
# Update PKGBUILD-bin version
sed -i "s/^pkgver=.*/pkgver=${VERSION}/" packaging/PKGBUILD-bin
# Update winget manifests version
sed -i "s/^PackageVersion:.*/PackageVersion: ${VERSION}/" packaging/winget/LittleMarket.Ahoy*.yaml
# Update Homebrew cask version (we'll push after SHA256s are ready)
echo "  ✓ Version bumped"

# ── 2. Build SPA ──────────────────────────────────────────────────────────────
echo "[2/7] Building SPA..."
cd "$SCRIPT_DIR/spa" && npm install --legacy-peer-deps --silent && npm run build --silent
cd "$SCRIPT_DIR"
echo "  ✓ SPA built"

# ── 3. Commit + tag + push → triggers GitHub Actions ─────────────────────────
echo "[3/7] Tagging v${VERSION} and pushing..."
git add package.json packaging/PKGBUILD-bin packaging/winget/ spa-dist/
git commit -m "Release v${VERSION}" || true
git tag "v${VERSION}"
git push origin main
git push origin "v${VERSION}"
echo "  ✓ Pushed — GitHub Actions building Linux + Windows + Mac in parallel"
echo "     Watch: https://github.com/${REPO}/actions"

# ── 4. Wait for release artifacts ────────────────────────────────────────────
echo "[4/7] Waiting for GitHub Release artifacts (this takes ~15 min)..."
for i in $(seq 1 60); do
  sleep 30
  ASSETS=$(gh release view "v${VERSION}" --repo "$REPO" --json assets -q '.assets[].name' 2>/dev/null || echo "")
  HAS_APPIMAGE=$(echo "$ASSETS" | grep -c "x86_64.AppImage" || true)
  HAS_EXE=$(echo "$ASSETS"     | grep -c "setup.exe"        || true)
  HAS_DMG=$(echo "$ASSETS"     | grep -c ".dmg"             || true)
  echo "  [${i}/60] AppImage:${HAS_APPIMAGE} EXE:${HAS_EXE} DMG:${HAS_DMG}"
  if [[ "$HAS_APPIMAGE" -ge 1 && "$HAS_EXE" -ge 1 && "$HAS_DMG" -ge 1 ]]; then
    echo "  ✓ All artifacts ready"
    break
  fi
done

# ── 5. Update AUR ─────────────────────────────────────────────────────────────
echo "[5/7] Updating AUR (yay ahoy)..."
rm -rf "$AUR_DIR"
GIT_SSH_COMMAND="ssh -i ~/.ssh/aur" git clone ssh://aur@aur.archlinux.org/ahoy.git "$AUR_DIR"
cp "$SCRIPT_DIR/packaging/PKGBUILD-bin" "$AUR_DIR/PKGBUILD"
cd "$AUR_DIR"
makepkg --printsrcinfo > .SRCINFO
git config user.name "ahoyadmin"
git config user.email "alex@littlemarket.org"
git add PKGBUILD .SRCINFO
git commit -m "Update to ${VERSION}"
GIT_SSH_COMMAND="ssh -i ~/.ssh/aur" git push origin master
cd "$SCRIPT_DIR"
echo "  ✓ AUR updated — yay ahoy installs v${VERSION}"

# ── 6. Update winget ──────────────────────────────────────────────────────────
echo "[6/7] Updating winget (winget install ahoy)..."
BASE_URL="https://github.com/${REPO}/releases/download/v${VERSION}"
X64_EXE="ahoy-indie-media-${VERSION}-x64-setup.exe"
ARM64_EXE="ahoy-indie-media-${VERSION}-arm64-setup.exe"

X64_SHA=$(curl -sL "${BASE_URL}/${X64_EXE}" | sha256sum | awk '{print $1}')
ARM64_SHA=$(curl -sL "${BASE_URL}/${ARM64_EXE}" | sha256sum | awk '{print $1}')

INSTALLER_FILE="$SCRIPT_DIR/packaging/winget/LittleMarket.Ahoy.installer.yaml"
sed -i "s|InstallerUrl:.*x64-setup.exe|InstallerUrl: ${BASE_URL}/${X64_EXE}|" "$INSTALLER_FILE"
sed -i "s|InstallerUrl:.*arm64-setup.exe|InstallerUrl: ${BASE_URL}/${ARM64_EXE}|" "$INSTALLER_FILE"
# Replace SHA256 placeholders
python3 - <<PYEOF
import re, pathlib
f = pathlib.Path("$INSTALLER_FILE")
content = f.read_text()
shas = ["$X64_SHA", "$ARM64_SHA"]
i = 0
def replace(m):
    global i
    val = shas[i]; i += 1; return f"InstallerSha256: {val}"
content = re.sub(r"InstallerSha256:.*", replace, content)
f.write_text(content)
PYEOF

git add "$INSTALLER_FILE"
git commit -m "winget: update SHA256 for v${VERSION}"
git push origin main

# Fork + PR to microsoft/winget-pkgs
WINGET_DIR="/tmp/winget-pkgs-ahoy"
rm -rf "$WINGET_DIR"
gh repo fork microsoft/winget-pkgs --clone --remote 2>/dev/null || true
git clone "https://github.com/ahoymrag/winget-pkgs.git" "$WINGET_DIR" 2>/dev/null || true
MANIFEST_PATH="$WINGET_DIR/manifests/l/LittleMarket/Ahoy/${VERSION}"
mkdir -p "$MANIFEST_PATH"
cp "$SCRIPT_DIR/packaging/winget/"*.yaml "$MANIFEST_PATH/"
cd "$WINGET_DIR"
git config user.email "alex@littlemarket.org"
git config user.name "ahoyadmin"
git checkout -b "ahoy-${VERSION}" 2>/dev/null || git checkout "ahoy-${VERSION}"
git add "$MANIFEST_PATH"
git commit -m "Add LittleMarket.Ahoy version ${VERSION}"
git push origin "ahoy-${VERSION}" --force
gh pr create --repo microsoft/winget-pkgs \
  --title "Add LittleMarket.Ahoy ${VERSION}" \
  --body "New version of Ahoy Indie Media desktop app." \
  --base main 2>/dev/null || echo "  (PR may already exist)"
cd "$SCRIPT_DIR"
echo "  ✓ winget PR submitted to microsoft/winget-pkgs"

# ── 7. Update Homebrew tap ────────────────────────────────────────────────────
echo "[7/7] Updating Homebrew tap (brew install --cask ahoy)..."
DMG_X64="ahoy-indie-media-${VERSION}-x64.dmg"
DMG_ARM64="ahoy-indie-media-${VERSION}-arm64.dmg"
X64_DMG_SHA=$(curl -sL "${BASE_URL}/${DMG_X64}" | sha256sum | awk '{print $1}')
ARM64_DMG_SHA=$(curl -sL "${BASE_URL}/${DMG_ARM64}" | sha256sum | awk '{print $1}')

rm -rf "$HOMEBREW_TAP_DIR"
git clone "https://github.com/oooAHOYooo/homebrew-tap.git" "$HOMEBREW_TAP_DIR"
mkdir -p "$HOMEBREW_TAP_DIR/Casks"

cat > "$HOMEBREW_TAP_DIR/Casks/ahoy.rb" <<CASK
cask "ahoy" do
  version "${VERSION}"

  on_intel do
    url "https://github.com/${REPO}/releases/download/v${VERSION}/${DMG_X64}"
    sha256 "${X64_DMG_SHA}"
  end

  on_arm do
    url "https://github.com/${REPO}/releases/download/v${VERSION}/${DMG_ARM64}"
    sha256 "${ARM64_DMG_SHA}"
  end

  name "Ahoy"
  desc "Discover and play independent music and shows"
  homepage "https://ahoy.ooo"

  app "Ahoy Indie Media.app"

  zap trash: [
    "~/Library/Application Support/ahoy-indie-media",
    "~/Library/Preferences/com.ahoyindiemedia.desktop.plist",
    "~/Library/Caches/com.ahoyindiemedia.desktop",
    "~/Library/Logs/ahoy-indie-media",
  ]
end
CASK

cd "$HOMEBREW_TAP_DIR"
git config user.email "alex@littlemarket.org"
git config user.name "ahoyadmin"
git add Casks/ahoy.rb
git commit -m "Update ahoy to ${VERSION}"
git push origin main
cd "$SCRIPT_DIR"
echo "  ✓ Homebrew tap updated — brew install oooAHOYooo/tap/ahoy installs v${VERSION}"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "=== All done! v${VERSION} is live on: ==="
echo "  Linux (Arch/Garuda):  yay ahoy"
echo "  Linux (Ubuntu/RPi):   curl -sL get.ahoy.ooo/install | bash"
echo "  Windows:              winget install ahoy  (after MS approves PR)"
echo "  Mac:                  brew install oooAHOYooo/tap/ahoy"
echo "  Direct download:      https://github.com/${REPO}/releases/tag/v${VERSION}"
