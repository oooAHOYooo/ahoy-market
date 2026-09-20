#!/usr/bin/env python3
"""
fire.py — Ahoy Mobile Release Build Script

Default workflow:
1. Read version from package.json and confirm to proceed
2. Sync Capacitor to prepare iOS + Android projects
3. Boot iOS simulator + Android emulator
4. Build and launch Ahoy on both test targets for manual QA
5. Wait for explicit human approval before store builds
6. Build iOS archive + Android AAB
7. Print artifact paths for manual TestFlight/Play Store upload

Usage:
    python fire.py
    python fire.py --help
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"


def log(msg: str, icon: str = "▸") -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{Colors.BLUE}[{ts}]{Colors.RESET} {icon} {msg}")


def success(msg: str) -> None:
    log(msg, f"{Colors.GREEN}OK{Colors.RESET}")


def error(msg: str) -> None:
    log(msg, f"{Colors.RED}ERR{Colors.RESET}")


def warn(msg: str) -> None:
    log(msg, f"{Colors.YELLOW}WARN{Colors.RESET}")


@dataclass(frozen=True)
class ReleaseConfig:
    project_root: Path
    package_json: Path
    ios_workspace: Path
    android_dir: Path
    android_apk: Path
    android_aab: Path
    bundle_id: str = "ooo.ahoy.app"
    ios_scheme: str = "App"
    preferred_android_avd: str = "Pixel_9_Pro"

    @property
    def android_activity(self) -> str:
        return f"{self.bundle_id}/.MainActivity"


@dataclass(frozen=True)
class FireOptions:
    yes_version: bool
    skip_sync: bool
    skip_launch: bool
    skip_test_gate: bool
    build_only: bool
    test_only: bool
    ios_only: bool
    android_only: bool


@dataclass(frozen=True)
class IOSSimulator:
    name: str
    udid: str
    runtime: str


def parse_args() -> FireOptions:
    parser = argparse.ArgumentParser(
        description="Guided local mobile release helper for Ahoy."
    )
    parser.add_argument(
        "--yes-version",
        action="store_true",
        help="skip the version confirmation prompt",
    )
    parser.add_argument(
        "--skip-sync",
        action="store_true",
        help="skip Capacitor sync",
    )
    parser.add_argument(
        "--skip-launch",
        action="store_true",
        help="skip launching emulators/simulators and app QA targets",
    )
    parser.add_argument(
        "--skip-test-gate",
        action="store_true",
        help="skip the YES/QUIT approval prompt before store builds",
    )
    parser.add_argument(
        "--build-only",
        action="store_true",
        help="skip device launch + QA and only build release artifacts",
    )
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="run sync + launch + QA flow without building store artifacts",
    )
    parser.add_argument(
        "--ios-only",
        action="store_true",
        help="run only iOS steps",
    )
    parser.add_argument(
        "--android-only",
        action="store_true",
        help="run only Android steps",
    )
    args = parser.parse_args()

    if args.ios_only and args.android_only:
        parser.error("choose at most one of --ios-only or --android-only")
    if args.build_only and args.test_only:
        parser.error("choose at most one of --build-only or --test-only")

    return FireOptions(
        yes_version=args.yes_version,
        skip_sync=args.skip_sync,
        skip_launch=args.skip_launch or args.build_only,
        skip_test_gate=args.skip_test_gate or args.build_only,
        build_only=args.build_only,
        test_only=args.test_only,
        ios_only=args.ios_only,
        android_only=args.android_only,
    )


def run_cmd(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    stream: bool = False,
) -> str:
    try:
        if stream:
            process = subprocess.Popen(
                cmd,
                cwd=str(cwd) if cwd else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            output_lines: list[str] = []
            assert process.stdout is not None
            for line in process.stdout:
                print(line, end="")
                output_lines.append(line)
            process.wait()
            if check and process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd)
            return "".join(output_lines)

        result = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=check,
        )
        return (result.stdout or "") + (result.stderr or "")
    except FileNotFoundError as exc:
        error(f"Command not found: {cmd[0]}")
        raise RuntimeError(f"missing required tool: {cmd[0]}") from exc
    except subprocess.CalledProcessError as exc:
        error(f"Command failed: {' '.join(cmd)}")
        combined = (exc.stdout or "") + (exc.stderr or "")
        if combined.strip():
            print(combined)
        raise


def confirm(prompt: str) -> bool:
    return input(prompt).strip().lower() in {"y", "yes"}


def read_version(config: ReleaseConfig) -> str:
    with config.package_json.open() as f:
        data = json.load(f)
    return data.get("version", "unknown")


def ensure_path(path: Path, label: str) -> None:
    if not path.exists():
        raise RuntimeError(f"{label} not found: {path}")


def require_tools(tools: Iterable[str]) -> None:
    missing = [tool for tool in tools if shutil.which(tool) is None]
    if missing:
        raise RuntimeError(f"missing required tools: {', '.join(missing)}")


def preflight(config: ReleaseConfig, options: FireOptions) -> None:
    ensure_path(config.package_json, "package.json")

    if not options.android_only:
        ensure_path(config.ios_workspace, "iOS workspace")
    if not options.ios_only:
        ensure_path(config.android_dir / "gradlew", "Android gradle wrapper")

    tools = {"npx"}
    if not options.android_only:
        tools.update({"xcrun", "xcodebuild", "open"})
    if not options.ios_only:
        tools.update({"adb", "emulator"})
    require_tools(sorted(tools))


def get_ios_simulator() -> IOSSimulator | None:
    output = run_cmd(["xcrun", "simctl", "list", "devices", "available", "--json"])
    data = json.loads(output)

    for runtime, devices in data.get("devices", {}).items():
        for device in devices:
            if "iPhone" not in device.get("name", ""):
                continue
            if not device.get("isAvailable"):
                continue
            return IOSSimulator(
                name=device["name"],
                udid=device["udid"],
                runtime=runtime,
            )
    return None


def get_android_avds() -> list[str]:
    output = run_cmd(["emulator", "-list-avds"])
    return [line.strip() for line in output.splitlines() if line.strip()]


def launch_ios_simulator() -> IOSSimulator | None:
    log("Checking iOS simulators...")
    simulator = get_ios_simulator()
    if simulator is None:
        warn("No available iPhone simulator found")
        return None

    log(f"Booting iOS simulator: {simulator.name}")
    subprocess.Popen(
        ["open", "-a", "Simulator"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2)
    run_cmd(["xcrun", "simctl", "boot", simulator.udid], check=False)
    run_cmd(["xcrun", "simctl", "bootstatus", simulator.udid, "-b"], check=False)
    success(f"iOS simulator ready: {simulator.name}")
    return simulator


def run_ios_app(config: ReleaseConfig, simulator: IOSSimulator) -> bool:
    log(f"Building Ahoy for iOS simulator: {simulator.name}")
    cmd = [
        "xcodebuild",
        "-workspace",
        str(config.ios_workspace),
        "-scheme",
        config.ios_scheme,
        "-configuration",
        "Debug",
        "-destination",
        f"id={simulator.udid}",
        "run",
    ]
    try:
        run_cmd(cmd, stream=True)
        success("Ahoy running on iOS simulator")
        return True
    except Exception as exc:
        error(f"iOS build failed: {exc}")
        try:
            subprocess.Popen(["open", str(config.ios_workspace)])
            warn("Xcode opened for manual iOS run")
        except OSError:
            warn("Could not open Xcode automatically")
        return False


def choose_android_avd(config: ReleaseConfig) -> str | None:
    avds = get_android_avds()
    if not avds:
        return None
    if config.preferred_android_avd in avds:
        return config.preferred_android_avd
    return avds[0]


def wait_for_android_boot(timeout_seconds: int = 120) -> None:
    run_cmd(["adb", "wait-for-device"], check=False)
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        output = run_cmd(["adb", "shell", "getprop", "sys.boot_completed"], check=False)
        if output.strip() == "1":
            return
        time.sleep(3)
    warn("Android emulator did not report full boot before timeout")


def launch_android_emulator(config: ReleaseConfig) -> str | None:
    log("Checking Android emulators...")
    avd = choose_android_avd(config)
    if avd is None:
        error("No Android emulators found")
        return None

    log(f"Launching Android emulator: {avd}")
    subprocess.Popen(
        ["emulator", "-avd", avd],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    wait_for_android_boot()
    success(f"Android emulator ready: {avd}")
    return avd


def run_android_app(config: ReleaseConfig) -> bool:
    log("Building Ahoy for Android emulator...")
    try:
        run_cmd(["./gradlew", "assembleDebug"], cwd=config.android_dir, stream=True)
        success("Android debug APK built")

        log("Installing APK to emulator...")
        run_cmd(["adb", "install", "-r", str(config.android_apk)])
        success("Android APK installed")

        log("Launching Ahoy on Android...")
        run_cmd(
            ["adb", "shell", "am", "start", "-n", config.android_activity],
            check=False,
        )
        success("Ahoy running on Android emulator")
        return True
    except Exception as exc:
        error(f"Android build/run failed: {exc}")
        try:
            run_cmd(["npx", "cap", "open", "android"])
            warn("Android Studio opened for manual build/run")
        except Exception:
            warn("Could not open Android Studio automatically")
        return False


def wait_for_approval() -> None:
    print("\n" + "=" * 60)
    print(f"{Colors.YELLOW}Test both targets now.{Colors.RESET}")
    print(f"{Colors.YELLOW}When ready to build for stores:{Colors.RESET}")
    print(f"{Colors.BLUE}Type: YES{Colors.RESET} or {Colors.RED}QUIT{Colors.RESET}")
    print("=" * 60 + "\n")

    while True:
        user_input = input("> ").strip().upper()
        if user_input == "YES":
            return
        if user_input == "QUIT":
            log("Build cancelled")
            sys.exit(0)
        warn("Please type YES or QUIT")


def cap_sync(options: FireOptions) -> None:
    log("Syncing Capacitor...")
    if not options.android_only:
        log("Syncing iOS...")
        run_cmd(["npx", "cap", "sync", "ios"])
        success("iOS synced")
    if not options.ios_only:
        log("Syncing Android...")
        run_cmd(["npx", "cap", "sync", "android"])
        success("Android synced")


def build_ios_archive(config: ReleaseConfig, version: str) -> Path | None:
    log(f"Building iOS archive (v{version})...")
    build_timestamp = datetime.now().strftime("%Y%m%d%H%M")
    archive_path = config.project_root / "ios" / "App" / "build" / f"App-{version}-{build_timestamp}.xcarchive"

    cmd = [
        "xcodebuild",
        "-workspace",
        str(config.ios_workspace),
        "-scheme",
        config.ios_scheme,
        "-configuration",
        "Release",
        "-archivePath",
        str(archive_path),
        "-destination",
        "generic/platform=iOS",
        "archive",
    ]

    try:
        run_cmd(cmd, stream=True)
        success(f"iOS archive built: {archive_path}")
        return archive_path
    except Exception as exc:
        error(f"iOS build failed: {exc}")
        return None


def build_android_aab(config: ReleaseConfig) -> Path | None:
    log("Building Android AAB...")
    try:
        run_cmd(["./gradlew", "bundleRelease"], cwd=config.android_dir, stream=True)
        success(f"Android AAB built: {config.android_aab}")
        return config.android_aab
    except Exception as exc:
        error(f"Android build failed: {exc}")
        return None


def run_launch_phase(config: ReleaseConfig, options: FireOptions) -> None:
    ios_ok = options.android_only
    android_ok = options.ios_only

    if not options.android_only:
        ios_simulator = launch_ios_simulator()
        if ios_simulator:
            print()
            ios_ok = run_ios_app(config, ios_simulator)
        else:
            warn("iOS simulator failed to launch")
            ios_ok = False

    if not options.ios_only:
        print()
        android_avd = launch_android_emulator(config)
        if android_avd:
            print()
            android_ok = run_android_app(config)
        else:
            warn("Android emulator failed to launch")
            android_ok = False

    if not (ios_ok and android_ok):
        warn("One or more QA targets failed. Check logs above.")


def print_summary(
    ios_archive: Path | None,
    android_aab: Path | None,
    options: FireOptions,
) -> None:
    print("\n" + "=" * 60)
    print(f"{Colors.GREEN}FIRE COMPLETE{Colors.RESET}\n")

    if options.test_only:
        print("QA launch flow finished. No store artifacts were built.\n")
        print("=" * 60 + "\n")
        return

    if ios_archive is not None:
        print("iOS Archive (TestFlight):")
        print(f"  {Colors.BLUE}{ios_archive}{Colors.RESET}\n")
    if android_aab is not None:
        print("Android AAB (Google Play):")
        print(f"  {Colors.BLUE}{android_aab}{Colors.RESET}\n")

    print(f"{Colors.YELLOW}Next steps:{Colors.RESET}")
    if ios_archive is not None:
        print("  1. iOS: Open in Xcode and distribute to TestFlight")
    if android_aab is not None:
        print("  2. Android: Upload the AAB to the Google Play release track")
    print("=" * 60 + "\n")


def build_config(project_root: Path) -> ReleaseConfig:
    return ReleaseConfig(
        project_root=project_root,
        package_json=project_root / "package.json",
        ios_workspace=project_root / "ios" / "App" / "App.xcworkspace",
        android_dir=project_root / "android",
        android_apk=project_root / "android" / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk",
        android_aab=project_root / "android" / "app" / "build" / "outputs" / "bundle" / "release" / "app-release.aab",
    )


def main() -> None:
    project_root = Path(__file__).resolve().parent
    os.chdir(project_root)

    config = build_config(project_root)
    options = parse_args()
    preflight(config, options)

    print("\n" + "=" * 60)
    print(f"{Colors.BLUE}Ahoy Mobile Release Build{Colors.RESET}")
    print("=" * 60 + "\n")

    version = read_version(config)
    log(f"Version: {Colors.YELLOW}{version}{Colors.RESET}")

    if not options.yes_version and not confirm(f"\nBuild for v{version}? (yes/no): "):
        log("Build cancelled")
        sys.exit(0)

    if not options.skip_sync:
        print()
        cap_sync(options)

    if not options.skip_launch:
        print()
        run_launch_phase(config, options)

    if not options.skip_test_gate:
        print()
        wait_for_approval()

    if options.test_only:
        print_summary(None, None, options)
        return

    ios_archive: Path | None = None
    android_aab: Path | None = None

    if not options.android_only:
        print()
        ios_archive = build_ios_archive(config, version)
        if ios_archive is None:
            sys.exit(1)

    if not options.ios_only:
        print()
        android_aab = build_android_aab(config)
        if android_aab is None:
            sys.exit(1)

    print_summary(ios_archive, android_aab, options)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user")
        sys.exit(0)
    except Exception as exc:
        error(f"Unexpected error: {exc}")
        sys.exit(1)
