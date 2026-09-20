# Platform Release Checklists

When validating a release, ensure the following constraints and checks are applied per platform.

## iOS (TestFlight)
- **Version Numbering:** Ensure both `Version` (user-facing, e.g., 1.0.8) and `Build` (incremental integer) are updated.
- **Review Requirements:** Does this release require an App Store review, or just TestFlight distribution? (Patches usually need expedited review).
- **Checklist:**
  - [ ] Xcode project builds successfully in Release mode.
  - [ ] Provisioning profiles are active.
  - [ ] Fastlane or build scripts are executed to upload to TestFlight.

## Android (Google Play Internal)
- **Version Numbering:** Ensure `versionName` (e.g., 1.0.8) and `versionCode` (must be an integer that strictly increases) are updated in `app/build.gradle`.
- **Checklist:**
  - [ ] Keystore is available and referenced correctly.
  - [ ] `./gradlew bundleRelease` completes successfully.
  - [ ] AAB file is uploaded to the Google Play Console Internal testing track.

## MacOS (Desktop)
- **Checklist:**
  - [ ] Electron/Desktop build script (e.g., `npm run build:mac`) runs without errors.
  - [ ] App is properly signed/notarized to prevent "Unidentified Developer" warnings on MacOS.
  - [ ] DMG or Zip file is generated and tested locally.

## Linux
- **Checklist:**
  - [ ] AppImage, Snap, or Deb package is successfully generated.
  - [ ] Tested on a primary Linux distribution (e.g., Ubuntu).