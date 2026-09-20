#!/usr/bin/env bash
# Ahoy — Universal Linux Installer
#
# ┌─────────────────────────────────────────────────────────────┐
# │  curl -sL get.ahoy.ooo | bash                               │
# └─────────────────────────────────────────────────────────────┘
#
# Works on: Garuda, Ubuntu, Raspberry Pi 5, Fedora, any Linux
# Installs:  `ahoy` command + desktop launcher
# Uninstall: sudo rm -rf /opt/ahoy /usr/local/bin/ahoy /usr/share/applications/ahoy.desktop

set -euo pipefail

REPO="oooAHOYooo/ahoy-little-platform"
INSTALL_DIR="/opt/ahoy"
BIN_PATH="/usr/local/bin/ahoy"
DESKTOP_PATH="/usr/share/applications/ahoy.desktop"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${BOLD}${BLUE}  ⚓  Ahoy — Linux Installer${NC}"
echo "  ────────────────────────────"
echo ""

# ── Architecture ─────────────────────────────────────────────────────────────
ARCH=$(uname -m)
case "$ARCH" in
  x86_64)  PKG_ARCH="x86_64" ;;
  aarch64) PKG_ARCH="arm64"  ;;
  *)
    echo -e "${RED}✗ Unsupported architecture: ${ARCH}${NC}"
    echo "  Supported: x86_64 (Intel/AMD) · aarch64 (Raspberry Pi 5, ARM64)"
    exit 1 ;;
esac
echo -e "  CPU: ${GREEN}${ARCH}${NC}"

# ── Sudo ─────────────────────────────────────────────────────────────────────
if [ "$(id -u)" = "0" ]; then
  SUDO=""
else
  if ! command -v sudo &>/dev/null; then
    echo -e "${RED}✗ Needs root or sudo.${NC}"
    exit 1
  fi
  SUDO="sudo"
fi

# ── Latest release ────────────────────────────────────────────────────────────
echo -n "  Latest version... "
LATEST=$(curl -sfL "https://api.github.com/repos/${REPO}/releases/latest" \
  | grep '"tag_name"' | head -1 | cut -d'"' -f4)
[ -z "$LATEST" ] && { echo -e "${RED}FAILED${NC} — check your internet connection"; exit 1; }
VERSION="${LATEST#v}"
echo -e "${GREEN}v${VERSION}${NC}"

# ── Download ──────────────────────────────────────────────────────────────────
APPIMAGE="ahoy-indie-media-${VERSION}-${PKG_ARCH}.AppImage"
URL="https://github.com/${REPO}/releases/download/${LATEST}/${APPIMAGE}"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "  Downloading..."
if ! curl -L --progress-bar "$URL" -o "${TMP}/ahoy.AppImage"; then
  echo -e "${RED}✗ Download failed.${NC}"
  echo "  URL tried: $URL"
  echo "  See releases: https://github.com/${REPO}/releases"
  exit 1
fi

# ── Install ───────────────────────────────────────────────────────────────────
echo "  Installing..."
$SUDO mkdir -p "${INSTALL_DIR}"
$SUDO cp "${TMP}/ahoy.AppImage" "${INSTALL_DIR}/ahoy.AppImage"
$SUDO chmod +x "${INSTALL_DIR}/ahoy.AppImage"

$SUDO tee "${BIN_PATH}" > /dev/null << WRAPPER
#!/bin/bash
exec ${INSTALL_DIR}/ahoy.AppImage "\$@"
WRAPPER
$SUDO chmod +x "${BIN_PATH}"

$SUDO mkdir -p "$(dirname "$DESKTOP_PATH")"
$SUDO tee "${DESKTOP_PATH}" > /dev/null << 'DESKTOP'
[Desktop Entry]
Type=Application
Name=Ahoy
GenericName=Media Player
Comment=Discover and play independent music and shows
Exec=ahoy %U
Icon=ahoy
Categories=AudioVideo;Music;
Terminal=false
Keywords=music;indie;media;podcast;ahoy;
DESKTOP

command -v update-desktop-database &>/dev/null && \
  $SUDO update-desktop-database /usr/share/applications 2>/dev/null || true

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}  ✅ Ahoy v${VERSION} installed!${NC}"
echo ""
echo -e "  Launch:    ${YELLOW}ahoy${NC}"
echo -e "  Or find it in your Applications menu"
echo ""
echo -e "  Uninstall: ${YELLOW}sudo rm -rf ${INSTALL_DIR} ${BIN_PATH} ${DESKTOP_PATH}${NC}"
echo ""
