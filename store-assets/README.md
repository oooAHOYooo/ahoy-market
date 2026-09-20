# Store Assets — Screenshots & Marketing Materials

**Location:** `store-assets/`  
**Updated:** 2026-04-12  
**App Version:** 1.0.0

This directory contains screenshots and marketing assets for app store listings.

---

## 📁 Folder Structure

```
store-assets/
├── google-play/          # Google Play Console screenshots
│   ├── 01_home.png      # Home screen / content grid
│   ├── 02_player.png    # Music player interface
│   ├── 03_artist.png    # Artist detail page
│   ├── 04_search.png    # Search / discovery UI
│   └── 05_saved.png     # Playlists / saved content
├── app-store/           # App Store Connect screenshots
│   ├── 01_home.png
│   ├── 02_player.png
│   ├── 03_artist.png
│   ├── 04_search.png
│   └── 05_saved.png
└── README.md           # This file
```

---

## 📸 Screenshot Details

### Google Play Console (Android)

| Screenshot | File | Size | Purpose |
|-----------|------|------|---------|
| 1 | `01_home.png` | 1080x1920 | Hero: content grid + library |
| 2 | `02_player.png` | 1080x1920 | Music player with controls |
| 3 | `03_artist.png` | 1080x1920 | Artist detail + bio |
| 4 | `04_search.png` | 1080x1920 | Search / browsing UI |
| 5 | `05_saved.png` | 1080x1920 | Playlists / bookmarks |

**Requirements:**
- ✅ PNG format
- ✅ 1080x1920 px (9:16 aspect ratio)
- ✅ 5 screenshots minimum
- ✅ No visible branding/watermarks (optional)

**Where to upload:**
1. [Google Play Console](https://play.google.com/console)
2. Select "Ahoy Indie Media" app
3. **Left sidebar → Google Play → Screenshots**
4. Upload 5 images (drag & drop or select files)
5. Reorder if needed (Google shows them in order)
6. **Save & continue** to next step

---

### App Store Connect (iOS)

| Screenshot | File | Size | Purpose |
|-----------|------|------|---------|
| 1 | `01_home.png` | 1242x2688 | Hero: content grid + library |
| 2 | `02_player.png` | 1242x2688 | Music player with controls |
| 3 | `03_artist.png` | 1242x2688 | Artist detail + bio |
| 4 | `04_search.png` | 1242x2688 | Search / browsing UI |
| 5 | `05_saved.png` | 1242x2688 | Playlists / bookmarks |

**Requirements:**
- ✅ PNG format
- ✅ 1242x2688 px (6.7" iPhone Pro Max)
- ✅ 5 screenshots minimum
- ✅ Can also upload for iPad (1536x2048)

**Where to upload:**
1. [App Store Connect](https://appstoreconnect.apple.com)
2. Select "Ahoy Indie Media" app
3. **App → TestFlight** (or **Pricing & Availability**)
4. Click **Screenshots**
5. Select device size: **iPhone 6.7"** (or others)
6. Upload 5 images
7. **Save & continue** to next step

---

## 🔄 How to Update Screenshots

### Automated (Recommended)

Use Fastlane to generate fresh screenshots:

```bash
# Android
fastlane android manual_screenshots

# iOS
fastlane ios screenshots

# Or follow the interactive guide:
bash scripts/take_store_screenshots.sh
```

### Manual Update Steps

#### Android
1. Start Android Emulator (Android Studio → Device Manager)
2. Install debug APK:
   ```bash
   cd android
   ./gradlew assembleDebug
   adb install -r app/build/outputs/apk/debug/app-debug.apk
   ```
3. Launch app and navigate to each screen
4. Screenshot (emulator menu or `Ctrl+S` / `Cmd+S`)
5. Save to: `store-assets/google-play/`
   - `01_home.png` - home screen
   - `02_player.png` - play any song
   - `03_artist.png` - tap an artist
   - `04_search.png` - open search
   - `05_saved.png` - open saved/playlists

#### iOS
1. Start iOS Simulator:
   ```bash
   open -a Simulator
   ```
2. Build for simulator:
   ```bash
   cd ios/App
   npm run build    # or equivalent
   xcodebuild -workspace App.xcworkspace -scheme App -destination 'platform=iOS Simulator,name=iPhone 15 Pro Max'
   ```
3. Or open in Safari:
   ```bash
   open -a Safari http://localhost:5001
   # Then use Simulator menu: Device → Screenshot
   ```
4. Screenshot using: `Device → Screenshot` (Cmd+S)
5. Save to: `store-assets/app-store/` (same naming as Android)

---

## 📝 Screenshot Checklist

Before uploading, verify:

- [ ] All 5 screenshots present
- [ ] Correct size (1080x1920 for Android, 1242x2688 for iOS)
- [ ] PNG format (not JPEG)
- [ ] No sensitive data visible (emails, tokens, personal info)
- [ ] UI is clear and readable (16px+ text)
- [ ] App branding visible (Ahoy logo or title)
- [ ] Consistent device/simulator used
- [ ] Latest app version running
- [ ] No debug UI or overlays visible

---

## 🚀 Uploading to Stores

### Google Play Console

```
Google Play Console
  → Your App: "Ahoy Indie Media"
  → Left sidebar: Google Play → Screenshots
  → Upload google-play/*.png
  → Click "Save" or "Next"
```

**Timing:** Changes live in ~1-2 hours

### App Store Connect

```
App Store Connect
  → Your App: "Ahoy Indie Media"
  → App → TestFlight → Screenshots
  → Upload app-store/*.png
  → Click "Save"
```

**Timing:** Changes live in ~15 minutes (TestFlight)

---

## 💡 Tips & Best Practices

✅ **DO:**
- Use the latest app version
- Keep screenshots consistent in style
- Show core features (player, browsing, saving)
- Use same device resolution for all 5
- Update before major feature releases
- Test locally before uploading

❌ **DON'T:**
- Mix different aspect ratios/devices
- Include outdated screenshots
- Show debug/error messages
- Include personal data
- Use different sizes per screenshot
- Upload JPEG or low-quality images

---

## 📅 Version History

| Date | App Version | Platform | Notes |
|------|-------------|----------|-------|
| 2026-04-12 | 1.0.0 | Android + iOS | Initial screenshots for launch |

---

## 🔗 Related Files

- `SCREENSHOT_GUIDE.md` — Detailed guide for what to screenshot
- `android/fastlane/Fastfile` — Fastlane config for Android
- `ios/App/fastlane/Fastfile` — Fastlane config for iOS
- `scripts/take_store_screenshots.sh` — Interactive screenshot helper

---

## ❓ FAQ

**Q: Can I use the same screenshots for Android and iOS?**  
A: Yes, but Apple requires 1242x2688 for iPhone. Google accepts 1080x1920. You can take Android shots and upscale, but new native iOS screenshots will look better.

**Q: How often should I update screenshots?**  
A: Every major release (v1.0 → v1.1) or when UI changes significantly. For bug fixes, no need to update.

**Q: Can I add text/captions to screenshots?**  
A: Both stores accept this, but it's optional. Google shows screenshots "as-is". Apple allows you to add captions/descriptions separately.

**Q: What if I change the app significantly?**  
A: Re-run the screenshot process:
```bash
bash scripts/take_store_screenshots.sh
```
Then re-upload to both stores.

---

**Last updated:** 2026-04-12  
**Maintained by:** Ahoy Indie Media team
