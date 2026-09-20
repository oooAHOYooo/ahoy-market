#!/bin/bash
# Quick Android APK installer for v1.0.5

set -e

APK="/Users/ag/ahoy-little-platform/android/app/build/outputs/apk/debug/app-debug.apk"
APP_ID="ooo.ahoy.app"

echo "📱 Android v1.0.5 Installer"
echo "============================"
echo ""

# Check if emulator is connected
echo "Checking for connected emulator..."
DEVICES=$(adb devices | grep -E "emulator|device" | grep -v "List")

if [ -z "$DEVICES" ]; then
    echo "❌ No Android devices found!"
    echo ""
    echo "Start an emulator first:"
    echo "  1. Open Android Studio"
    echo "  2. Tools → Device Manager"
    echo "  3. Click ▶️ on Pixel Pro or Samsung A15"
    echo "  4. Wait for it to show 'device' status"
    echo ""
    exit 1
fi

echo "✅ Found device(s):"
echo "$DEVICES"
echo ""

# Install APK
echo "Installing APK..."
adb install -r "$APK"
echo "✅ APK installed"
echo ""

# Wait a moment for app to be ready
sleep 2

# Launch app
echo "Launching app..."
adb shell am start -n "$APP_ID/.MainActivity"
echo "✅ App launched!"
echo ""

echo "Watch the emulator - app should load in a few seconds..."
echo ""
echo "To view logs:"
echo "  adb logcat | grep 'Ahoy'"
