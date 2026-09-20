#!/usr/bin/env python3
"""
Generate all icon variants from a source image for web, iOS, and Android.
"""

import sys
from pathlib import Path
from PIL import Image

def generate_icons(source_image_path, output_dir):
    """Generate all icon variants from source image."""

    # Load source image
    img = Image.open(source_image_path)

    # Ensure image is RGB
    if img.mode != 'RGB':
        img = img.convert('RGB')

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Define all required sizes for web and app stores
    # Format: (size, filename, format)
    icons = [
        # Web manifest icons
        ((192, 192), 'images/icon-192.png', 'PNG'),
        ((512, 512), 'images/icon-512.png', 'PNG'),

        # Favicon variants
        ((32, 32), 'img/favicon-32.png', 'PNG'),
        ((64, 64), 'img/favicon-64.png', 'PNG'),

        # iOS app icons
        ((120, 120), 'ios-icon-120.png', 'PNG'),  # iPhone app icon
        ((167, 167), 'ios-icon-167.png', 'PNG'),  # iPad app icon
        ((180, 180), 'ios-icon-180.png', 'PNG'),  # iPhone app icon (3x)
        ((1024, 1024), 'ios-icon-1024.png', 'PNG'),  # App Store

        # Android app icons (various densities)
        ((48, 48), 'android-icon-48.png', 'PNG'),    # ldpi
        ((72, 72), 'android-icon-72.png', 'PNG'),    # hdpi
        ((96, 96), 'android-icon-96.png', 'PNG'),    # xhdpi
        ((144, 144), 'android-icon-144.png', 'PNG'),  # xxhdpi
        ((192, 192), 'android-icon-192.png', 'PNG'),  # xxxhdpi
        ((512, 512), 'android-icon-512.png', 'PNG'),  # Play Store
    ]

    # Generate each icon size
    for size, filename, fmt in icons:
        # Resize image
        resized = img.resize(size, Image.Resampling.LANCZOS)

        # Save
        output_file = output_path / filename
        output_file.parent.mkdir(parents=True, exist_ok=True)
        resized.save(output_file, fmt)
        print(f"✓ Generated {filename} ({size[0]}x{size[1]})")

    # Generate ICO file with multiple sizes
    ico_path = output_path / 'img' / 'favicon.ico'
    ico_path.parent.mkdir(parents=True, exist_ok=True)

    sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
    ico_images = [img.resize(size, Image.Resampling.LANCZOS) for size in sizes]
    ico_images[0].save(ico_path, 'ICO', sizes=sizes)
    print(f"✓ Generated favicon.ico")

    print("\n✓ All icons generated successfully!")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate-icons.py <source_image> [output_dir]")
        sys.exit(1)

    source = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else 'static'

    generate_icons(source, output)
