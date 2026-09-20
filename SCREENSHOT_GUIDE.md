# App Store Screenshot Guide

**Date Updated:** 2026-04-12  
**Platforms:** Google Play Console & App Store Connect  
**Version:** 1.0.0

---

## 📱 Recommended Screenshots (5 total per platform)

Each screenshot should be **1080x1920px** (portrait) for best quality.

### Screenshot 1: 🏠 HOME SCREEN (Hero)
**What to show:** The main feed/grid of content  
**How to get there:** Launch app, see home page  
**What's compelling:**
- Large grid of music/shows/artists
- Shows content diversity
- Clean, modern UI
- Call-to-action: Browse or play

**File name:** `01_home.png`

---

### Screenshot 2: 🎵 NOW PLAYING / MUSIC PLAYER
**What to show:** Song playing with full player controls  
**How to get there:**
1. From home, tap any song/content
2. Player expands with album art
3. Show play/pause, queue, volume controls

**What's compelling:**
- Large album artwork
- Clear title + artist name
- Control buttons (play, next, volume, save)
- Shows polished player UI

**File name:** `02_player.png`

---

### Screenshot 3: 👤 ARTIST DETAIL PAGE
**What to show:** Artist profile with their content  
**How to get there:**
1. From home, find "Artists" view or scroll to artist card
2. Tap an artist (e.g., "Poets & Friends")
3. See artist bio, photo, their songs/tracks

**What's compelling:**
- Artist hero image
- Bio text
- "Play All" button
- List of their tracks
- Shows music discovery feature

**File name:** `03_artist_detail.png`

---

### Screenshot 4: 🔍 SEARCH / DISCOVERY
**What to show:** Search UI or browsing capability  
**How to get there:**
- Tap search icon in header
- OR navigate to "Artists" view to show browsing
- Show filter dropdown or search results

**What's compelling:**
- Shows you can find specific content
- Browse by category/filter
- Search input field
- Demonstrates navigation

**File name:** `04_search.png`

---

### Screenshot 5: ❤️ PLAYLISTS / SAVED CONTENT
**What to show:** User's saved/bookmarked content  
**How to get there:**
1. From any song, tap the heart/bookmark icon
2. Navigate to "Saved" or "Playlists" view
3. Show list of bookmarked songs

**What's compelling:**
- Heart icon shows save feature
- Personal library concept
- Shows user engagement
- "Add to Playlist" or collection feature

**File name:** `05_saved.png`

---

## 🛠️ How to Capture Screenshots

### Android (Google Play Console)

**Option 1: Android Emulator (easiest)**
```bash
# 1. Open Android Studio → Device Manager
# 2. Create/run an emulator (e.g., Pixel 6 - 1080x1920)
# 3. Install debug APK:
adb install android/app/build/outputs/apk/debug/app-debug.apk

# 4. In emulator, navigate to each screen
# 5. Press Ctrl+S (Windows) or use emulator menu → Screenshot
# 6. Save to: android/fastlane/screenshots/
```

**Option 2: Real Device**
- Connect Android phone via USB
- Same install: `adb install ...`
- Use: Volume Down + Power button to screenshot
- Pull files: `adb pull /sdcard/Pictures/Screenshots/`

### iOS (App Store Connect)

**Option 1: iOS Simulator (easiest)**
```bash
# 1. Start simulator:
open -a Simulator

# 2. In simulator, open Safari → http://localhost:5001
# (in another terminal: python dev.py)

# 3. Navigate to each screen
# 4. Device → Screenshot (or Cmd+S)
# 5. Simulator saves to ~/Desktop or ~/Downloads
# 6. Move to: ios/App/fastlane/screenshots/
```

**Option 2: Real Device**
- Plug in iPhone
- Xcode → Window → Devices and Simulators
- Run app on device
- Press Side Button + Volume Up → Screenshot saved to Photos app
- Export to files

---

## 📤 Upload to Stores

### Google Play Console
1. Go to [Google Play Console](https://play.google.com/console)
2. Select your app → "Ahoy Indie Media"
3. Left sidebar → **Google Play → Screenshots**
4. Upload 5 images (1080x1920 each):
   - Phone (required): 5 screenshots
   - Tablet (optional): 7 screenshots
5. **Save** and continue to next step

### App Store Connect
1. Go to [App Store Connect](https://appstoreconnect.apple.com)
2. Select your app → **TestFlight** or **App Store**
3. Click **Screenshots**
4. Upload 5 images for each device type:
   - iPhone 6.7" (required)
   - iPad (optional)
5. **Save** and move to next step

---

## 💡 Pro Tips

✅ **DO:**
- Use actual app screenshots (no mockups needed for now)
- Make sure UI is readable (16px+ text)
- Show your best, most polished screens
- Use consistent device size (same simulator/phone)
- Include app branding in shots

❌ **DON'T:**
- Use outdated screenshots
- Include personal info (emails, tokens, etc.)
- Screenshot with lots of debug UI visible
- Mix different aspect ratios

---

## 🔄 Running the Screenshot Helper

To get an interactive guide:
```bash
bash scripts/take_store_screenshots.sh
```

Or run fastlane lanes directly:
```bash
# Android guide:
fastlane android manual_screenshots

# iOS guide:
fastlane ios screenshots
```

---

## ✨ Next Steps After Screenshots

1. ✅ Upload to Google Play Console
2. ✅ Upload to App Store Connect
3. Fill in app description/keywords
4. Set pricing and availability
5. Submit for review
6. Await approval (Google: ~2 hours, Apple: 1-3 days)

---

**Questions?** Check your Fastfile for step-by-step guidance:
- Android: `android/fastlane/Fastfile`
- iOS: `ios/App/fastlane/Fastfile`
