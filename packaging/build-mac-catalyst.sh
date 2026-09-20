#!/bin/bash
set -e

# ──────────────────────────────────────────────
# Ahoy Indie Media — Mac Catalyst Build for App Store Connect
# ──────────────────────────────────────────────
#
# Usage:
#   ./packaging/build-mac-catalyst.sh
#
# What it does:
#   1. Syncs Capacitor iOS assets
#   2. Installs CocoaPods
#   3. Archives the iOS target as Mac Catalyst
#   4. Opens the archive in Xcode Organizer for Distribute App
#
# Prerequisites:
#   - Xcode signed in to your Apple Developer account
#   - Mac Catalyst support enabled in the iOS target
#   - App Store Connect macOS app record created

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IOS_DIR="$PROJECT_ROOT/ios/App"
BUILD_TS=$(date +%Y%m%d%H%M)
ARCHIVE_PATH="$IOS_DIR/build/App-MacCatalyst-$BUILD_TS.xcarchive"

APP_VERSION=$(node -e "console.log(require('$PROJECT_ROOT/package.json').version)")

echo "═══════════════════════════════════════════"
echo "  Ahoy Indie Media — Mac Catalyst Build"
echo "  Build timestamp: $BUILD_TS"
echo "═══════════════════════════════════════════"

mkdir -p "$IOS_DIR/build"
xattr -w com.apple.xcode.CreatedByBuildSystem true "$IOS_DIR/build" 2>/dev/null || true

echo ""
echo "▸ Syncing Capacitor..."
cd "$PROJECT_ROOT"
npx cap sync ios

echo ""
echo "▸ Installing CocoaPods..."
cd "$IOS_DIR"
pod install

echo ""
echo "▸ Cleaning this build's outputs..."
rm -rf "$ARCHIVE_PATH"

echo ""
echo "▸ Building Mac Catalyst archive (version $APP_VERSION / build $BUILD_TS)..."
XC_LOG="$PROJECT_ROOT/ios/App/xcodebuild-maccatalyst-$$.log"
if ! xcodebuild \
    -workspace "$IOS_DIR/App.xcworkspace" \
    -scheme App \
    -configuration Release \
    -destination "generic/platform=macOS,variant=Mac Catalyst" \
    -archivePath "$ARCHIVE_PATH" \
    CURRENT_PROJECT_VERSION="$BUILD_TS" \
    SUPPORTS_MACCATALYST=YES \
    archive \
    > "$XC_LOG" 2>&1; then
    echo ""
    echo "❌ Archive failed. Last 30 lines:"
    tail -30 "$XC_LOG"
    echo ""
    echo "Full log: $XC_LOG"
    rm -f "$XC_LOG"
    exit 1
fi
tail -20 "$XC_LOG"
rm -f "$XC_LOG"

echo "Build: $BUILD_TS | Version: $APP_VERSION | $(date '+%Y-%m-%dT%H:%M:%S%z')" > "$IOS_DIR/build/build-maccatalyst-$BUILD_TS.txt"
echo ""
echo "✅ Archive built: $ARCHIVE_PATH"

echo ""
echo "▸ Opening archive in Xcode Organizer..."
open "$ARCHIVE_PATH"

echo ""
echo "═══════════════════════════════════════════"
echo "  Done!"
echo "═══════════════════════════════════════════"
