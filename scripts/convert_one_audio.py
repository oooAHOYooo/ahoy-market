#!/usr/bin/env python3
"""Convert one audio file to AAC .m4a for Ahoy Indie Media."""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def check_ffmpeg():
    if shutil.which("ffmpeg") is None:
        print("ffmpeg is not installed. Install it with: brew install ffmpeg")
        sys.exit(1)


def human_size(bytes_val):
    for unit in ("B", "KB", "MB", "GB"):
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"


def convert(input_path: Path, output_dir: Path, bitrate: str, overwrite: bool):
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / (input_path.stem + ".m4a")

    if output_path.exists() and not overwrite:
        print(f"Output already exists: {output_path}")
        print("Pass --overwrite to replace it.")
        sys.exit(1)

    cmd = [
        "ffmpeg",
        "-y" if overwrite else "-n",
        "-i", str(input_path),
        "-c:a", "aac",
        "-b:a", bitrate,
        "-vn",
        str(output_path),
    ]

    print(f"Converting: {input_path.name} → {output_path.name}  [{bitrate}]")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("ffmpeg error:")
        print(result.stderr[-2000:])
        sys.exit(1)

    original_size = input_path.stat().st_size
    new_size = output_path.stat().st_size

    print()
    print("Done!")
    print(f"  Input : {input_path}  ({human_size(original_size)})")
    print(f"  Output: {output_path}  ({human_size(new_size)})")


def main():
    parser = argparse.ArgumentParser(
        description="Convert one audio file to AAC .m4a for Ahoy Indie Media."
    )
    parser.add_argument("input", help="Path to the source audio file")
    parser.add_argument(
        "--output-dir",
        default="~/Downloads/ahoy_converted",
        help="Folder for the converted file (default: ~/Downloads/ahoy_converted)",
    )
    parser.add_argument(
        "--bitrate",
        default="256k",
        help="AAC bitrate (default: 256k)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite output file if it already exists",
    )
    args = parser.parse_args()

    check_ffmpeg()

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        sys.exit(1)
    if not input_path.is_file():
        print(f"Not a file: {input_path}")
        sys.exit(1)

    output_dir = Path(args.output_dir).expanduser().resolve()

    convert(input_path, output_dir, args.bitrate, args.overwrite)


if __name__ == "__main__":
    main()
