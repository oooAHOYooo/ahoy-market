# Mac App Store Checklist

This repo currently has a working Electron desktop build for direct download, plus a separate iOS / TestFlight path. A Mac App Store submission is a third path and needs its own sandboxed target.

## Current repo state

- `package.json` is configured for Electron `mac` builds that produce DMG and ZIP artifacts.
- `electron/main.js` starts a Python/Flask process when the packaged app launches.
- `packaging/entitlements.mac.plist` is a hardened-runtime style entitlement set for the direct desktop build.
- `packaging/release-desktop.sh` publishes desktop artifacts to GitHub Releases, not App Store Connect.
- The Mac App Store path is now based on the Capacitor iOS project as a Mac Catalyst archive, built by `packaging/build-mac-catalyst.sh`.
- `ios/App/App/MacCatalyst.entitlements` is the macOS-only sandbox entitlement file used for the archive.

## What Apple needs

- A macOS app record in App Store Connect.
- A Mac App Store-compatible archive.
- App Sandbox enabled.
- Code signing with the correct Apple distribution identity.
- Upload through Xcode Organizer or Transporter.

Apple’s current guidance also says macOS apps distributed through the Mac App Store must use App Sandbox.

## Repo-specific changes needed

### 1. Split the packaging targets

Keep the current `mac` target for direct downloads.

Add a separate `mas` target for App Store distribution.

Suggested shape:

- `mac` - DMG / ZIP for GitHub Releases and `app.ahoy.ooo/downloads`
- `mas` - sandboxed App Store build for App Store Connect

Repo scripts now reflect that split:

- `npm run electron:build:mac:dmg`
- `npm run electron:build:mas`
- `npm run electron:build:mas-dev`

### 2. Add a sandboxed entitlements file

Create a dedicated App Store entitlements file, separate from the current desktop one.

The current `packaging/entitlements.mac.plist` includes flags that are fine for a direct desktop build but are not a good starting point for a sandboxed Mac App Store app:

- `com.apple.security.cs.allow-jit`
- `com.apple.security.cs.allow-unsigned-executable-memory`
- `com.apple.security.cs.allow-dyld-environment-variables`
- `com.apple.security.cs.disable-library-validation`

For an App Store build, start from the minimum sandboxed entitlement set and add only what the app actually needs.

The repo now applies `ios/App/App/MacCatalyst.entitlements` only when the SDK resolves to macOS, so the iOS build stays on its current signing path.

### 3. Rework the runtime model

The biggest blocker is `electron/main.js`.

Right now the packaged app can launch `desktop_main.py` and then spawn `python3`:

- that is fine for a direct desktop distribution flow
- it is not the shape you want to rely on for a Mac App Store submission

The current `electron/main.js` now disables the local Python server automatically when `process.mas` is true, so the App Store build path loads the hosted production URL instead.

For a Mac App Store build, the app should avoid depending on a system Python process at launch time.

Practical options:

- Serve only the hosted web app in the Electron shell for the App Store build.
- Bundle the backend differently so it does not depend on spawning `python3` from the user machine.
- Keep the App Store target limited to a web-view style client if the backend can stay remote.

### 4. Add App Sandbox in Xcode / build config

If this becomes a true Mac App Store target, the Xcode project needs App Sandbox enabled and aligned with the entitlements file.

That usually means:

- App Sandbox on
- network access only if needed
- file access limited to what the app really uses
- no ad hoc process spawning assumptions

### 5. Archive and upload

Once the app is sandboxed and signed:

- archive the app in Xcode
- use **Distribute App**
- choose **App Store Connect**
- upload the build
- wait for processing
- assign the build to TestFlight or submit it for review

## Suggested order

1. Run `./packaging/build-mac-catalyst.sh`.
2. Open the archive in Xcode Organizer and verify the Mac build is present.
3. Distribute through App Store Connect.
4. Keep the current `mac` DMG/ZIP path intact for direct desktop downloads.

## Bottom line

The repo already has a desktop macOS release path.

The Mac App Store path is a separate Mac Catalyst archive built from the iOS project. It is not the same as the Electron DMG/ZIP path, and it still has different signing and distribution constraints.
