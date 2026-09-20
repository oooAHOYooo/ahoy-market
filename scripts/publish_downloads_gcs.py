#!/usr/bin/env python3
"""
Upload desktop build artifacts to GCS and write a per-platform latest manifest.

The workflow uploads immutable versioned files under:
  gs://<bucket>/<prefix>/<platform>/v<version>/<asset>

Then it publishes a small mutable latest.json at:
  gs://<bucket>/<prefix>/<platform>/latest.json

The app and install script read latest.json instead of GitHub Releases.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def human_size(size_bytes: int) -> str:
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024.0 or unit == "TB":
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def canonical_asset_name(platform: str, version: str, filename: str) -> str:
    lower = filename.lower()
    if platform == "linux":
        if lower.endswith(".appimage"):
            return f"ahoy-indie-media-{version}-{'arm64' if 'arm64' in lower else 'x86_64'}.AppImage"
        if lower.endswith(".deb"):
            return f"ahoy-indie-media-{version}-{'arm64' if 'arm64' in lower else 'x86_64'}.deb"
        if lower.endswith(".snap"):
            return f"ahoy-indie-media-{version}-{'arm64' if 'arm64' in lower else 'x86_64'}.snap"
    if platform == "mac":
        if lower.endswith(".dmg"):
            return f"Ahoy Indie Media-{version}{'-arm64' if 'arm64' in lower else ''}.dmg"
        if lower.endswith(".zip"):
            return f"Ahoy Indie Media-{version}{'-arm64' if 'arm64' in lower else ''}.zip"
    if platform == "windows":
        if lower.endswith(".exe"):
            return f"ahoy-indie-media-{version}-{'arm64' if 'arm64' in lower else 'x64'}-setup.exe"
    return filename


def gcs_object_url(base_url: str, bucket: str, prefix: str, platform: str, version: str, object_name: str) -> str:
    rel = f"{prefix.strip('/')}/{platform}/v{version}/{object_name}".strip("/")
    return f"{base_url.rstrip('/')}/{bucket}/{quote(rel, safe='/')}"


def run_gsutil(*args: str) -> None:
    cmd = ["gsutil", *args]
    subprocess.run(cmd, check=True)


def discover_assets(dist_dir: Path, platform: str):
    if platform == "linux":
        patterns = ("*.AppImage", "*.deb", "*.snap")
    elif platform == "mac":
        patterns = ("*.dmg", "*.zip")
    elif platform == "windows":
        patterns = ("*-setup.exe",)
    else:
        raise ValueError(f"Unsupported platform: {platform}")

    assets = []
    for pattern in patterns:
        assets.extend(sorted(dist_dir.glob(pattern)))
    return [path for path in assets if path.is_file() and ".blockmap" not in path.name]


def build_manifest(platform: str, version: str, bucket: str, prefix: str, base_url: str, assets: list[Path], published_at: str):
    records = []
    for asset in assets:
        object_name = canonical_asset_name(platform, version, asset.name)
        object_path = f"{prefix.strip('/')}/{platform}/v{version}/{object_name}".strip("/")
        gcs_uri = f"gs://{bucket}/{object_path}"
        url = gcs_object_url(base_url, bucket, prefix, platform, version, object_name)
        records.append({
            "name": object_name,
            "source_name": asset.name,
            "platform": platform,
            "size_bytes": asset.stat().st_size,
            "size_human": human_size(asset.stat().st_size),
            "sha256": sha256sum(asset),
            "gcs_uri": gcs_uri,
            "url": url,
        })

    return {
        "platform": platform,
        "version": version,
        "released_at": published_at,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "assets": records,
    }


def upload_assets(bucket: str, prefix: str, platform: str, version: str, assets: list[Path]) -> None:
    for asset in assets:
        object_name = canonical_asset_name(platform, version, asset.name)
        object_path = f"{prefix.strip('/')}/{platform}/v{version}/{object_name}".strip("/")
        run_gsutil("cp", str(asset), f"gs://{bucket}/{object_path}")


def upload_manifest(bucket: str, prefix: str, platform: str, manifest: dict) -> None:
    payload = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    tmp_path = Path(os.getenv("RUNNER_TEMP", "/tmp")) / f"{platform}-latest.json"
    tmp_path.write_text(payload, encoding="utf-8")
    try:
        run_gsutil("cp", str(tmp_path), f"gs://{bucket}/{prefix.strip('/')}/{platform}/latest.json")
        run_gsutil("cp", str(tmp_path), f"gs://{bucket}/{prefix.strip('/')}/{platform}/v{manifest['version']}/manifest.json")
    finally:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload Ahoy desktop builds to GCS.")
    parser.add_argument("--platform", required=True, choices=["linux", "mac", "windows"])
    parser.add_argument("--version", required=True)
    parser.add_argument("--dist-dir", default="dist-electron")
    parser.add_argument("--bucket", default=os.getenv("AHOY_DOWNLOADS_BUCKET", os.getenv("GCS_BUCKET", "")))
    parser.add_argument("--prefix", default=os.getenv("AHOY_DOWNLOADS_PREFIX", "desktop"))
    parser.add_argument("--base-url", default=os.getenv("AHOY_DOWNLOADS_BASE_URL", "https://storage.googleapis.com"))
    parser.add_argument("--published-at", default=os.getenv("AHOY_DOWNLOADS_PUBLISHED_AT") or datetime.now(timezone.utc).isoformat())
    args = parser.parse_args()

    if not args.bucket:
        print("Missing bucket: set AHOY_DOWNLOADS_BUCKET or GCS_BUCKET.", file=sys.stderr)
        return 1

    dist_dir = Path(args.dist_dir)
    if not dist_dir.exists():
        print(f"Missing dist dir: {dist_dir}", file=sys.stderr)
        return 1

    assets = discover_assets(dist_dir, args.platform)
    if not assets:
        print(f"No assets found for {args.platform} in {dist_dir}", file=sys.stderr)
        return 1

    upload_assets(args.bucket, args.prefix, args.platform, args.version, assets)
    manifest = build_manifest(args.platform, args.version, args.bucket, args.prefix, args.base_url, assets, args.published_at)
    upload_manifest(args.bucket, args.prefix, args.platform, manifest)

    print(json.dumps({
        "platform": args.platform,
        "version": args.version,
        "assets": [asset.name for asset in assets],
        "manifest": f"gs://{args.bucket}/{args.prefix.strip('/')}/{args.platform}/latest.json",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
