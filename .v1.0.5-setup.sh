#!/bin/bash
# v1.0.5 Multi-Platform Testing Setup
# Saves Java 17 path and APK path for quick access

export JAVA_HOME="/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"
export APK_PATH="/Users/ag/ahoy-little-platform/android/app/build/outputs/apk/debug/app-debug.apk"

echo "v1.0.5 Environment Ready"
echo "========================"
echo "JAVA_HOME: $JAVA_HOME"
echo "APK_PATH: $APK_PATH"
echo ""
echo "To install on emulator:"
echo "  adb install -r \$APK_PATH"
echo ""
echo "To launch on emulator:"
echo "  adb shell am start -n ooo.ahoy.app/.MainActivity"
echo ""
