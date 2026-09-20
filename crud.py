#!/usr/bin/env python3
"""
Ahoy command center.  python crud.py
"""
import os, sys, json, re, subprocess, tty, termios
from datetime import date
from pathlib import Path

import manage as m

ROOT          = Path(__file__).parent
VERSIONS_FILE = ROOT / "packaging" / "versions.json"
README_FILE   = ROOT / "README.md"
REPO          = "oooAHOYooo/ahoy-little-platform"

# ── colours ───────────────────────────────────────────────────────────────────
C  = "\033[1;36m"   # cyan bold
Y  = "\033[1;33m"   # yellow bold
G  = "\033[1;32m"   # green bold
R  = "\033[1;31m"   # red
DIM= "\033[2m"
X  = "\033[0m"      # reset

# ── terminal helpers ──────────────────────────────────────────────────────────
def clear():
    os.system("clear")

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def pause(msg="  Press Enter to continue..."):
    input(f"\n{DIM}{msg}{X}")

def confirm(msg):
    return input(f"  {Y}{msg}{X} [y/N]: ").strip().lower() == "y"

def run(cmd, check=False):
    return subprocess.run(cmd, shell=True, cwd=ROOT,
                          check=check, text=True)

def run_out(cmd):
    r = subprocess.run(cmd, shell=True, cwd=ROOT,
                       capture_output=True, text=True)
    return r.stdout.strip()

# ── version helpers ───────────────────────────────────────────────────────────
def pkg_version():
    try:
        return json.loads((ROOT / "package.json").read_text()).get("version", "?")
    except Exception:
        return "?"

def load_versions():
    if VERSIONS_FILE.exists():
        return json.loads(VERSIONS_FILE.read_text())
    return {}

def save_versions(v):
    VERSIONS_FILE.write_text(json.dumps(v, indent=2) + "\n")

def mark_released(keys, version):
    v = load_versions()
    for key in keys:
        v[key] = {"version": version, "released": str(date.today())}
    save_versions(v)
    _update_readme(v)
    print(f"  {G}versions.json + README updated{X}")

# ── README auto-update ────────────────────────────────────────────────────────
_README_ROWS = [
    ("web",            "Web",               "[app.ahoy.ooo](https://app.ahoy.ooo)"),
    ("linux_appimage", "Linux — AppImage",  "[Download](https://github.com/oooAHOYooo/ahoy-little-platform/releases/latest)"),
    ("linux_aur",      "Linux — AUR",       "`yay ahoy`"),
    ("linux_snap",     "Linux — Snap",      "`snap install ahoy`"),
    ("windows_nsis",   "Windows",           "`winget install ahoy`"),
    ("mac_dmg",        "Mac",               "`brew install oooAHOYooo/tap/ahoy`"),
    ("android",        "Android",           "Play Store"),
    ("ios",            "iOS",               "TestFlight"),
]

def _update_readme(versions):
    rows = ["| Platform | Version | Released | Install |", "|---|---|---|---|"]
    for key, label, install in _README_ROWS:
        info = versions.get(key, {})
        ver  = info.get("version") or "—"
        rel  = info.get("released") or "—"
        rows.append(f"| {label} | {ver} | {rel} | {install} |")
    block = (
        "<!-- VERSIONS:START -->\n"
        + "\n".join(rows)
        + f"\n*Last updated: {date.today()}*\n"
        + "<!-- VERSIONS:END -->"
    )
    readme = README_FILE.read_text()
    readme = re.sub(
        r"<!-- VERSIONS:START -->.*?<!-- VERSIONS:END -->",
        block, readme, flags=re.DOTALL
    )
    README_FILE.write_text(readme)

# ── platform definitions ──────────────────────────────────────────────────────
# (key, label, on_by_default)
PLATFORMS = [
    ("web",            "Web / Render",       True),
    ("linux_appimage", "Linux — AppImage",   True),
    ("linux_aur",      "Linux — AUR",        True),
    ("linux_snap",     "Linux — Snap",       False),
    ("windows_nsis",   "Windows — NSIS",     True),
    ("windows_winget", "Windows — winget",   True),
    ("mac_dmg",        "Mac — DMG",          True),
    ("mac_homebrew",   "Mac — Homebrew",     True),
    ("android",        "Android",            False),
    ("ios",            "iOS",                False),
]

# ── release actions ───────────────────────────────────────────────────────────
def do_sync():
    """Push JSON changes to Render DB via the import scripts."""
    if not os.environ.get("DATABASE_URL"):
        print(f"  {R}DATABASE_URL not set — skipping DB sync{X}")
        print(f"  {DIM}Set DATABASE_URL to your Render Postgres URL to sync{X}")
        return
    print(f"\n  {C}→ Syncing JSON → Render DB...{X}")
    run("python scripts/import_podcast_collection.py")
    run("python scripts/import_events_merch.py")
    run("python scripts/import_videos_whats_new.py")
    print(f"  {G}✓ DB sync complete{X}")

def do_web():
    print(f"\n  {C}→ Pushing to Render...{X}")
    run("git add static/data/ spa-dist/")
    result = run("git diff --cached --quiet")
    if result.returncode != 0:
        run('git commit -m "Deploy content update"')
    run("git push origin main")
    print(f"  {G}✓ Pushed — Render redeploys in ~30s{X}")
    mark_released(["web"], "live")
    if os.environ.get("DATABASE_URL"):
        if confirm("Sync changes to Render DB now?"):
            do_sync()

def do_desktop_all(version):
    print(f"\n  {C}→ Running build_all.sh v{version}...{X}")
    run(f"bash build_all.sh {version}", check=False)
    mark_released(
        ["linux_appimage", "linux_aur", "windows_nsis", "windows_winget",
         "mac_dmg", "mac_homebrew"],
        version
    )

def do_linux_appimage(version):
    print(f"\n  {C}→ Building Linux AppImage v{version}...{X}")
    run(f"npx electron-builder --linux --x64 --arm64")
    print(f"  {G}✓ Built — push tag to publish to GitHub Releases{X}")
    run(f"git tag v{version} 2>/dev/null || true")
    run(f"git push origin main && git push origin v{version}")
    mark_released(["linux_appimage"], version)

def do_linux_aur(version):
    print(f"\n  {C}→ Updating AUR (yay ahoy)...{X}")
    run(f'sed -i "s/^pkgver=.*/pkgver={version}/" packaging/PKGBUILD-bin')
    aur = "/tmp/aur-ahoy-update"
    run(f"rm -rf {aur}")
    run(f'GIT_SSH_COMMAND="ssh -i ~/.ssh/aur" git clone ssh://aur@aur.archlinux.org/ahoy.git {aur}')
    run(f"cp packaging/PKGBUILD-bin {aur}/PKGBUILD")
    run(f'cd {aur} && makepkg --printsrcinfo > .SRCINFO'
        f' && git config user.name ahoyadmin'
        f' && git config user.email alex@littlemarket.org'
        f' && git add PKGBUILD .SRCINFO'
        f' && git commit -m "Update to {version}"'
        f' && GIT_SSH_COMMAND="ssh -i ~/.ssh/aur" git push origin master')
    print(f"  {G}✓ AUR updated — yay ahoy installs v{version}{X}")
    mark_released(["linux_aur"], version)

def do_windows(version):
    print(f"\n  {C}→ Tagging v{version} for Windows GitHub Actions build...{X}")
    run(f"git tag v{version} 2>/dev/null || true")
    run(f"git push origin main && git push origin v{version}")
    print(f"  {G}✓ GitHub Actions will build Windows NSIS installer{X}")
    mark_released(["windows_nsis"], version)

def do_winget(version):
    print(f"\n  {C}→ Updating winget manifests...{X}")
    run(f'sed -i "s/^PackageVersion:.*/PackageVersion: {version}/" packaging/winget/LittleMarket.Ahoy*.yaml')
    print(f"  {DIM}Run scripts/winget-sha256.sh {version} after artifacts are ready{X}")
    mark_released(["windows_winget"], version)

def do_mac(version):
    print(f"\n  {C}→ Tagging v{version} for Mac GitHub Actions build...{X}")
    run(f"git tag v{version} 2>/dev/null || true")
    run(f"git push origin main && git push origin v{version}")
    print(f"  {G}✓ GitHub Actions will build Mac DMG{X}")
    mark_released(["mac_dmg"], version)

def do_homebrew(version):
    print(f"\n  {C}→ Updating Homebrew tap...{X}")
    print(f"  {DIM}(Homebrew cask updated by build_all.sh step 7){X}")
    mark_released(["mac_homebrew"], version)

def do_android(version):
    print(f"\n  {C}→ Building Android release...{X}")
    run("npx cap sync android")
    run("cd android && ./gradlew bundleRelease assembleRelease")
    print(f"  {G}✓ AAB ready: android/app/build/outputs/bundle/release/app-release.aab{X}")
    print(f"  {DIM}Upload to Play Console → Internal testing{X}")
    mark_released(["android"], version)

def do_ios(version):
    print(f"\n  {C}→ Building iOS release...{X}")
    run("bash packaging/build-ios.sh upload")
    print(f"  {G}✓ Uploaded to TestFlight{X}")
    mark_released(["ios"], version)

PLATFORM_ACTIONS = {
    "web":            do_web,
    "linux_appimage": do_linux_appimage,
    "linux_aur":      do_linux_aur,
    "windows_nsis":   do_windows,
    "windows_winget": do_winget,
    "mac_dmg":        do_mac,
    "mac_homebrew":   do_homebrew,
    "android":        do_android,
    "ios":            do_ios,
}

_ALL_DESKTOP = {"linux_appimage", "linux_aur", "windows_nsis",
                "windows_winget", "mac_dmg", "mac_homebrew"}

# ── release menu ──────────────────────────────────────────────────────────────
def menu_release():
    version  = pkg_version()
    selected = {p[0]: p[2] for p in PLATFORMS}

    while True:
        clear()
        vers = load_versions()
        print(f"{C}{'─'*50}{X}")
        print(f"{C}  Ahoy  v{version}  →  Release{X}")
        print(f"{C}{'─'*50}{X}\n")

        for i, (key, label, _) in enumerate(PLATFORMS, 1):
            chk   = f"{G}x{X}" if selected[key] else " "
            cur   = vers.get(key, {}).get("version") or "—"
            rel   = vers.get(key, {}).get("released") or "—"
            print(f"  {DIM}{i:2}.{X} [{chk}]  {label:<28} {DIM}current: {cur} ({rel}){X}")

        print()
        print(f"  {Y}a{X} select all   {Y}n{X} none   {Y}1-0{X} toggle   {Y}Enter{X} release   {Y}b{X} back")
        print()
        new_ver = input(f"  New version [{Y}{version}{X}]: ").strip() or version
        print(f"\n  Key: ", end="", flush=True)
        k = getch()
        print(k)

        if k == "b":
            return
        elif k == "a":
            for key in selected: selected[key] = True
        elif k == "n":
            for key in selected: selected[key] = False
        elif k in ("\r", "\n"):
            chosen_keys = [key for key, label, _ in PLATFORMS if selected[key]]
            if not chosen_keys:
                print(f"  {R}Nothing selected.{X}"); pause(); continue

            print(f"\n  {Y}Will release v{new_ver} to:{X}")
            for key in chosen_keys:
                label = next(l for k, l, _ in PLATFORMS if k == key)
                print(f"    {G}•{X} {label}")
            print()
            if not confirm("Confirm release?"):
                continue

            version = new_ver

            # if all desktop selected, use build_all.sh in one shot
            if _ALL_DESKTOP.issubset(set(chosen_keys)):
                do_web() if "web" in chosen_keys else None
                do_desktop_all(version)
                if "android" in chosen_keys: do_android(version)
                if "ios"     in chosen_keys: do_ios(version)
            else:
                for key in chosen_keys:
                    if key in PLATFORM_ACTIONS:
                        PLATFORM_ACTIONS[key](version)

            print(f"\n  {G}✓ Release complete — v{version}{X}")
            pause()
            return
        elif k.isdigit():
            idx = int(k) - 1
            if k == "0": idx = 9
            if 0 <= idx < len(PLATFORMS):
                key = PLATFORMS[idx][0]
                selected[key] = not selected[key]

# ── content menu ──────────────────────────────────────────────────────────────
CONTENT_COLLECTIONS = [
    ("1", "Podcasts",    "podcasts"),
    ("2", "Events",      "events"),
    ("3", "Videos",      "videos"),
    ("4", "Ambient",     "ambient"),
    ("5", "What's New",  "news"),
]

def menu_collection(name, cfg):
    while True:
        clear()
        print(f"{C}{'─'*40}{X}")
        print(f"{C}  Content → {name}{X}")
        print(f"{C}{'─'*40}{X}\n")
        print(f"  {Y}l{X}  List")
        print(f"  {Y}a{X}  Add")
        print(f"  {Y}t{X}  Toggle  <id>")
        print(f"  {Y}e{X}  Edit    <id> <field> <value>")
        print(f"  {Y}r{X}  Remove  <id>")
        print()
        print(f"  {Y}d{X}  {G}Deploy to Render{X}  (git push)")
        print(f"  {Y}s{X}  {G}Sync to DB{X}       (JSON → Render Postgres)")
        if os.environ.get("DATABASE_URL"):
            print(f"  {Y}x{X}  {G}Deploy + Sync{X}   (push then JSON → DB)")
        print()
        print(f"  {Y}b{X}  Back")
        print()
        cmd = input("  > ").strip().lower()

        if cmd == "b":
            break
        elif cmd == "s":
            do_sync()
            pause()
        elif cmd == "x" and os.environ.get("DATABASE_URL"):
            do_deploy_sync()
            pause()
        elif cmd == "l":
            clear()
            if name == "What's New":
                m.cmd_news("list", [])
            else:
                m.cmd_list(cfg, [])
            pause()
        elif cmd == "a":
            clear()
            if name == "What's New":
                m.cmd_news("add", [])
            else:
                m.cmd_add(cfg, [])
            pause()
        elif cmd == "t":
            _, items = m.load(cfg)
            ids = [str(i.get(cfg["id"])) for i in items]
            print(f"  IDs: {', '.join(ids[:20])}{'...' if len(ids) > 20 else ''}")
            id_val = input("  ID to toggle: ").strip()
            m.cmd_toggle(cfg, [id_val])
            pause()
        elif cmd == "e":
            id_val = input("  ID: ").strip()
            _, items = m.load(cfg)
            item = m.find(items, cfg["id"], id_val)
            if item:
                print(f"  Fields: {', '.join(item.keys())}")
            field  = input("  Field: ").strip()
            value  = input("  Value: ").strip()
            m.cmd_edit(cfg, [id_val, field, value])
            pause()
        elif cmd == "r":
            _, items = m.load(cfg)
            ids = [str(i.get(cfg["id"])) for i in items]
            print(f"  IDs: {', '.join(ids[:20])}{'...' if len(ids) > 20 else ''}")
            id_val = input("  ID to remove: ").strip()
            if confirm(f"Remove {id_val}?"):
                m.cmd_remove(cfg, [id_val])
            pause()
        elif cmd == "d":
            do_web()
            pause()

def do_deploy_sync():
    """Deploy to Render then sync JSON to DB if DATABASE_URL set."""
    do_web()
    if os.environ.get("DATABASE_URL"):
        do_sync()
    else:
        print(f"  {DIM}(DATABASE_URL not set — skip DB sync){X}")

def menu_content():
    while True:
        clear()
        print(f"{C}{'─'*40}{X}")
        print(f"{C}  Ahoy  →  Content{X}")
        print(f"{C}{'─'*40}{X}\n")
        for key, label, _ in CONTENT_COLLECTIONS:
            print(f"  {Y}{key}{X}  {label}")
        print()
        print(f"  {Y}d{X}  {G}Deploy to Render{X}  (git push)")
        print(f"  {Y}s{X}  {G}Sync to DB{X}       (JSON → Render Postgres)")
        if os.environ.get("DATABASE_URL"):
            print(f"  {Y}x{X}  {G}Deploy + Sync{X}   (push then JSON → DB)")
        print()
        print(f"  {Y}b{X}  Back")
        print()
        k = input("  > ").strip().lower()

        if k == "b":
            return
        elif k == "d":
            do_web(); pause()
        elif k == "s":
            do_sync(); pause()
        elif k == "x":
            do_deploy_sync(); pause()
        else:
            match = next(((l, c) for key, l, c in CONTENT_COLLECTIONS if key == k), None)
            if match:
                label, coll = match
                cfg = m.COLLECTIONS.get(coll)
                menu_collection(label, cfg)

# ── git menu ──────────────────────────────────────────────────────────────────
def menu_git():
    clear()
    print(f"{C}{'─'*50}{X}")
    print(f"{C}  Ahoy  →  Git{X}")
    print(f"{C}{'─'*50}{X}\n")

    print(f"{Y}Recent commits:{X}")
    print(run_out("git log --oneline -15"))

    print(f"\n{Y}Tags (releases):{X}")
    tags = run_out("git tag --sort=-version:refname | head -10")
    for tag in tags.splitlines():
        date_str = run_out(f"git log -1 --format=%ci {tag}")[:10]
        msg      = run_out(f"git log -1 --format=%s {tag}")
        print(f"  {G}{tag:<12}{X}  {date_str}  {DIM}{msg}{X}")

    print(f"\n{Y}Most changed files (all time):{X}")
    hot = run_out(
        "git log --pretty=format: --name-only | sort | uniq -c | sort -rn | head -12"
    )
    print(hot)

    print(f"\n{Y}Commits per month (last 6):{X}")
    log = run_out("git log --date=format:'%Y-%m' --format='%ad'")
    from collections import Counter
    counts = Counter(log.splitlines())
    for month in sorted(counts)[-6:]:
        bar = "█" * min(counts[month], 40)
        print(f"  {month}  {bar} {DIM}{counts[month]}{X}")

    pause()

# ── main menu ─────────────────────────────────────────────────────────────────
def main():
    while True:
        clear()
        v    = pkg_version()
        vers = load_versions()
        live = sum(
            1 for k, info in vers.items()
            if info.get("version") not in ("?", "pending", None)
            and k != "web"
        )
        print(f"{C}{'─'*50}{X}")
        print(f"{C}  Ahoy Indie Media  v{v}{X}")
        print(f"{C}{'─'*50}{X}")
        print(f"  {DIM}{live} platforms live  •  {date.today()}{X}")
        if not os.environ.get("DATABASE_URL"):
            print(f"  {DIM}(Set DATABASE_URL to enable DB sync){X}")
        print()

        print(f"  {Y}1{X}  Content    podcasts · events · videos · ambient · news")
        print(f"  {Y}2{X}  {G}Release    push web · desktop · mobile{X}")
        print(f"  {Y}3{X}  Stats      users · listening · revenue  {DIM}[coming soon]{X}")
        print(f"  {Y}4{X}  Users      list · disable · promote      {DIM}[coming soon]{X}")
        print(f"  {Y}5{X}  Git        history · releases · hot files")
        print(f"  {Y}6{X}  {G}Sync DB    push JSON changes → Render Postgres{X}")
        print()
        print(f"  {Y}q{X}  Quit")
        print()

        k = input("  > ").strip().lower()

        if   k == "q": break
        elif k == "1": menu_content()
        elif k == "2": menu_release()
        elif k == "5": menu_git()
        elif k == "6": do_sync(); pause()
        elif k in ("3", "4"):
            print(f"\n  {DIM}Coming soon — needs DATABASE_URL configured.{X}")
            pause()

if __name__ == "__main__":
    main()
