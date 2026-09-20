# Deployment Automation Guide

**Zero thinking required.**

## TL;DR

1. **Make code changes** → commit to main
2. **Deploy to Render** (normal process)
3. **Push to main** (if not already)
4. **GitHub Actions does everything else** automatically

Desktop apps build and release within 15 minutes. No commands needed.

---

## Automatic Flow (Recommended)

```
You: git commit && git push origin main
     ↓
GitHub Actions detects new commits
     ↓
Auto-bumps build number (0.2.4.5 → 0.2.4.6)
     ↓
Creates tag v0.2.4.6
     ↓
Desktop release workflow starts (Linux/Windows/Mac)
     ↓
Complete in 10-15 min ✅
```

**Versioning scheme:**
- **0.2.4** = base version (major.minor.patch)
- **.6** = build number (auto-incremented per push)
- **0.2.4.6** = full version (base + build)

---

## Manual Override (if you need specific version)

```bash
bash scripts/deploy.sh 0.2.5
```

This does the same thing but with your chosen version number.

---

## What It Does

### Automatically ✅
1. Bumps version in `package.json` + `spa/package.json`
2. Commits version change
3. Creates git tag (`v0.2.4`)
4. Pushes tag to GitHub (triggers GitHub Actions)
5. Outputs platform checklist

### GitHub Actions Auto-Handles (10-15 min)
- **Linux:** Builds & uploads AppImage (x64 + arm64), DEB (x64 + arm64), Snap
- **Windows:** Builds & uploads NSIS installer (.exe, x64 + arm64)
- **macOS:** Builds & uploads DMG (x64 + arm64)
- **Snap Store:** Auto-publishes (if credentials are set)
- **Release Notes:** Auto-generated

### You Handle (when ready)
- **AUR:** Update PKGBUILD + push
- **macOS App Store:** Upload build (requires Apple ID)
- **Android Play Store:** Upload AAB (requires Play Console)

---

## Typical Flow

```bash
# 1. Make code changes (UI, content, features, etc.)
git add . && git commit -m "feature: add X"
git push origin main

# 2. When ready to release:
bash scripts/deploy.sh 0.2.4

# 3. Script outputs:
#    ✓ Version bumped
#    ✓ Tag pushed
#    ✓ GitHub Actions running
#    ⏳ Wait 10-15 min for builds
#    ⚠️ Manual tasks (AUR, App Store, Play Store)

# 4. Go to GitHub Releases tab
# https://github.com/oooAHOYooo/ahoy-little-platform/releases

# 5. Follow checklist for manual platforms
```

---

## The Platforms

| Platform | Auto? | Notes |
|---|---|---|
| **GitHub Releases** | ✅ Yes | AppImage, DEB, EXE, DMG |
| **Snap Store** | ✅ Yes | If `SNAPCRAFT_STORE_CREDENTIALS` GitHub secret is set |
| **AUR (Arch Linux)** | ⚠️ Manual | Edit PKGBUILD, regenerate .SRCINFO, push to AUR |
| **macOS App Store** | ⚠️ Manual | Run `./packaging/build-ios.sh upload` |
| **Android Play Store** | ⚠️ Manual | Build AAB, upload to Play Console |

---

## Example: Full Release Walkthrough

### Pre-release
```bash
# Make sure everything is committed
git status
# On branch main, nothing to commit

# Check version (currently 0.2.3)
grep '"version"' package.json
# "version": "0.2.3"
```

### Release Command
```bash
bash scripts/deploy.sh 0.2.4
```

**Output:**
```
🚀 Ahoy Deployment Automation

Bumping version to 0.2.4...
✅ Version updated to 0.2.4

Creating version commit...
✅ Committed

Creating tag v0.2.4 and pushing...
✅ Tag pushed — GitHub Actions building now

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 DEPLOYMENT CHECKLIST — Version 0.2.4
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ AUTOMATED
  • Version bumped to 0.2.4
  • Git tag pushed: v0.2.4
  • GitHub Actions started (3 runners: Linux/Windows/Mac)
  • Artifacts → GitHub Releases (auto-uploaded)
  • Snap Store → auto-published (if creds set)

⏳ WAIT FOR BUILDS
  1. Go to: https://github.com/oooAHOYooo/ahoy-little-platform/actions
  2. Watch 'release-desktop' workflow complete (all 3 jobs)
  3. Once done → artifacts in Releases tab

⚠️ MANUAL — Linux (AUR)
  1. Update PKGBUILD:
     • Edit: packaging/PKGBUILD-bin
     • Change pkgver=0.2.4
     • Update sha256sum (get from GitHub Release)
  2. Regenerate .SRCINFO:
     $ cd packaging && makepkg --printsrcinfo > .SRCINFO
  3. Push to AUR:
     $ git push ssh://aur@aur.archlinux.org/ahoy.git main

⚠️ MANUAL — macOS App Store
  1. Open Xcode Organizer or run:
     $ ./packaging/build-ios.sh upload
  2. Wait for App Review (typically 24–48h)

⚠️ MANUAL — Android Play Store
  1. Build release AAB:
     $ cd android && ./gradlew bundleRelease
  2. Upload to Play Console:
     • Go to: https://play.google.com/console
     • Internal Testing → Upload AAB
     • Promote to Production when ready

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### After GitHub Actions Completes (10-15 min)
```bash
# 1. Visit: https://github.com/oooAHOYooo/ahoy-little-platform/releases/tag/v0.2.4
# 2. Verify all artifacts present (AppImage, DEB, EXE, DMG)

# 3. Manual platforms — when you're ready:

# === AUR ===
sed -i 's/pkgver=.*/pkgver=0.2.4/' packaging/PKGBUILD-bin
# (get SHA256 from Release downloads)
sed -i "s/sha256sum=.*/sha256sum='<paste-here>'/" packaging/PKGBUILD-bin
cd packaging && makepkg --printsrcinfo > .SRCINFO
git add PKGBUILD-bin .SRCINFO && git commit -m "v0.2.4"
git push ssh://aur@aur.archlinux.org/ahoy.git main

# === macOS App Store ===
./packaging/build-ios.sh upload
# (wait 24-48h for Apple review)

# === Android Play Store ===
cd android && ./gradlew bundleRelease
# (upload to Play Console)
```

---

## Troubleshooting

### "Git error: uncommitted changes detected"
```bash
git status  # See what's uncommitted
git add . && git commit -m "fix: my changes"
bash scripts/deploy.sh 0.2.4  # Try again
```

### "Tag already exists"
```bash
git tag -d v0.2.4           # Delete local tag
git push origin :refs/tags/v0.2.4  # Delete remote tag
bash scripts/deploy.sh 0.2.4  # Try again
```

### "GitHub Actions failed"
```bash
# Check the workflow: https://github.com/oooAHOYooo/ahoy-little-platform/actions
# Look for "release-desktop" workflow run
# Click into failed job for logs
```

### "Snap publish failed but app is in Releases"
This is OK. The AppImage/DEB/EXE/DMG are still in GitHub Releases.
Users can install via `.AppImage` directly or `curl -sL get.ahoy.ooo/install | bash`.

---

## Platform Installation Commands (for users)

Once released:

```bash
# Arch/Garuda
yay ahoy

# Ubuntu / any snapd system
snap install ahoy

# Linux (any distro)
curl -sL get.ahoy.ooo/install | bash

# Then run
ahoy
```

---

## Environment Variables

- `AHOY_DESKTOP_LOCAL=1` — Desktop app loads from local Flask server instead of production URL
- `SNAPCRAFT_STORE_CREDENTIALS` — GitHub secret for auto-publishing to Snap Store (set in repo settings)

---

## Files Changed

- `scripts/deploy.sh` — Main automation script
- `CLAUDE.md` — Updated with new deployment commands
- `.github/workflows/release-desktop.yml` — Builds for Linux/Windows/Mac
- `package.json` — Version field (updated by deploy.sh)
- `spa/package.json` — Version field (updated by deploy.sh)
