#!/bin/bash
# Production Audit Script for Ahoy Indie Media

echo "--- App Store Readiness Audit ---"

check_size() {
    local label="$1"
    local path="$2"
    local expected_w="$3"
    local expected_h="$4"

    if [ ! -f "$path" ]; then
        echo "❌ MISSING: $label ($path)"
        return
    fi

    local actual_w
    local actual_h
    actual_w=$(sips -g pixelWidth "$path" 2>/dev/null | awk -F': ' '/pixelWidth/ {print $2}')
    actual_h=$(sips -g pixelHeight "$path" 2>/dev/null | awk -F': ' '/pixelHeight/ {print $2}')

    if [ "$actual_w" = "$expected_w" ] && [ "$actual_h" = "$expected_h" ]; then
        echo "✅ $label is ${expected_w}x${expected_h}."
    else
        echo "❌ WRONG SIZE: $label is ${actual_w}x${actual_h}, expected ${expected_w}x${expected_h} ($path)"
    fi
}

# 1. Icons & Assets (iOS + web/PWA)
echo "[1/4] Checking icon assets..."
check_size "iOS App Icon" "ios/App/App/Assets.xcassets/AppIcon.appiconset/AppIcon-512@2x.png" 1024 1024
check_size "PWA icon 192" "static/images/icon-192.png" 192 192
check_size "PWA icon 512" "static/images/icon-512.png" 512 512
check_size "Store feature graphic" "packaging/icons/ahoy-feature-1024x500.png" 1024 500
check_size "Desktop icon PNG" "packaging/icons/ahoy-512.png" 512 512

# 2. Icons & Assets (Android)
echo -e "\n[2/4] Checking Android Assets..."
check_size "Android launcher icon" "android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png" 512 512
check_size "Android launcher foreground" "android/app/src/main/res/mipmap-xxxhdpi/ic_launcher_foreground.png" 192 192
if [ -d "android/app/src/main/res/mipmap-xhdpi" ]; then
    echo "✅ Android mipmap resources found."
else
    echo "❌ MISSING: Android mipmap resources in android/app/src/main/res"
fi

# 3. Legal Documents
echo -e "\n[3/4] Checking Legal Views..."
if grep -q "Information We Collect" spa/src/views/PrivacyView.vue && grep -q "Acceptance of Terms" spa/src/views/TermsView.vue; then
    echo "✅ Privacy and Terms views expanded."
else
    echo "❌ WARNING: Privacy or Terms views seem minimal."
fi

# 4. Account Deletion (REQUIRED)
echo -e "\n[4/4] Checking Account Deletion Flow..."
if grep -q "delete-account" blueprints/api/auth.py && grep -q "onDeleteAccount" spa/src/views/AccountView.vue; then
    echo "✅ Account deletion logic found in backend and frontend."
else
    echo "❌ MISSING: Account deletion logic!"
fi

echo -e "\n--- Audit Complete ---"
