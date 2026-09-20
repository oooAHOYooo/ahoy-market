# Mac App Store Build Guide

This repo can build a Mac Catalyst archive from the existing iOS Capacitor target and open it in Xcode Organizer for distribution.

## Prerequisites

1. Xcode with your Apple ID signed in.
2. An App Store Connect macOS app record for the app.
3. Mac Catalyst support enabled in the iOS target.

## Build and open in Xcode

From the repo root:

```bash
./packaging/build-mac-catalyst.sh
```

That script:

- syncs Capacitor
- runs `pod install`
- archives the iOS target as a Mac Catalyst app
- opens the `.xcarchive` in Xcode Organizer

## Distribute from Xcode

In Organizer:

1. Select the new archive.
2. Click **Distribute App**.
3. Choose **App Store Connect**.
4. Upload the build.

If the archive opens but Mac support is missing in Xcode, enable Mac Catalyst on the App target in the iOS project:

- Open `ios/App/App.xcworkspace`
- Select the App target
- Go to **General**
- Under **Supported Destinations**, add **Mac (Mac Catalyst)**

The project now also applies a macOS-only entitlements file at `ios/App/App/MacCatalyst.entitlements` so the archive can satisfy App Sandbox requirements during App Store Connect upload.

## Notes

- This is a separate path from the Electron desktop DMG/ZIP build.
- The Mac Catalyst archive uses the existing app shell and loads the same hosted production app.
