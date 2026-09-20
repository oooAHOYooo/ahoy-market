# Ahoy v1.0.6 Release Runbook

Use this as the single release checklist for web, GitHub, iOS, and Android.

## Current state

- Version source: `package.json` is `1.0.6`.
- iOS project: `MARKETING_VERSION = 1.0.6`, `CURRENT_PROJECT_VERSION = 6`.
- Android project: `versionName "1.0.6+${buildTimestampName}"`.
- Android notes: `release-notes/android/internal-beta.txt`.
- Full notes: `docs/RELEASE_NOTES_v1.0.6.md`.

## 1. Freeze the release candidate

```bash
git status --short
npm run build
npx cap sync
```

Do not start store uploads from a dirty or unbuilt SPA unless the dirty files are intentional release-note edits.

## 2. Smoke test locally

Use `fire.py` for the guided path:

```bash
python fire.py --test-only --yes-version
```

Minimum smoke tests:

- Home loads without blank/frozen screen.
- Music track starts immediately and mini-player stays in sync.
- Podcast episode starts immediately.
- AHOY TV mobile idle state shows channel actions before playback.
- AHOY TV playback controls appear only after a stream is active.
- Saved/bookmark flow works.
- Login and wallet pages still render.

## 3. Build store artifacts

After the smoke test passes:

```bash
python fire.py --build-only --yes-version
```

Expected outputs:

- iOS archive: `ios/App/build/App-1.0.6-*.xcarchive`
- Android AAB: `android/app/build/outputs/bundle/release/app-release.aab`

## 4. Web and GitHub

```bash
git diff --stat
git add CHANGELOG.md docs/RELEASE_NOTES_v1.0.6.md docs/deployment/V1_0_6_RELEASE_RUNBOOK.md release-notes/android/internal-beta.txt
git commit -m "Prepare v1.0.6 release notes"
git push origin main
git tag v1.0.6
git push origin v1.0.6
```

Before tagging, include any final app code fixes in the same release commit or in a clearly named fix commit.

## 5. iOS/TestFlight

Open the workspace:

```bash
open ios/App/App.xcworkspace
```

In Xcode:

- Select `Any iOS Device`.
- Product -> Archive.
- Organizer -> Distribute App -> App Store Connect -> Upload.
- Use the v1.0.6 notes from `docs/RELEASE_NOTES_v1.0.6.md`, shortened for TestFlight if needed.

## 6. Android/Play Console

Upload:

```text
android/app/build/outputs/bundle/release/app-release.aab
```

Paste notes from:

```text
release-notes/android/internal-beta.txt
```

Target first:

- Internal testing
- Then closed/open/production only after install verification passes

## 7. Final verification

- Install TestFlight build on iPhone.
- Install Play internal build on Android.
- Confirm version visible in store dashboards is `1.0.6`.
- Confirm release notes match the submitted build.
- Update `CHANGELOG.md` date from `(in progress)` to the actual release date when shipped.
