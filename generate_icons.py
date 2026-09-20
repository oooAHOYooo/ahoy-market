#!/usr/bin/env python3
"""Generate all app icon variants from source logo with safe-zone padding."""

from PIL import Image
import os

# Source logo path
SOURCE_LOGO = "design/logo-source/AHOY-LOGO-SOURCE.png"

# Icon specifications: (output_path, size_px, safe_zone_ratio)
# safe_zone_ratio: 0.7 = logo occupies 70% of icon, 30% padding
ICON_SPECS = [
    # iOS app icons
    ("spa/public/ios-icon-120.png", 120, 0.7),
    ("spa/public/ios-icon-167.png", 167, 0.7),
    ("spa/public/ios-icon-180.png", 180, 0.7),
    ("spa/public/ios-icon-1024.png", 1024, 0.7),

    # Android app icons
    ("spa/public/android-icon-48.png", 48, 0.7),
    ("spa/public/android-icon-72.png", 72, 0.7),
    ("spa/public/android-icon-96.png", 96, 0.7),
    ("spa/public/android-icon-144.png", 144, 0.7),
    ("spa/public/android-icon-192.png", 192, 0.7),
    ("spa/public/android-icon-512.png", 512, 0.7),

    # Web favicons
    ("static/img/favicon-32.png", 32, 0.8),
    ("static/img/favicon-64.png", 64, 0.8),

    # Website logo
    ("static/img/ahoy_logo.png", 512, 0.8),
    ("spa/public/ahoy_logo.png", 512, 0.8),
]

def generate_icons(source_path):
    """Generate all icon variants from source logo."""

    if not os.path.exists(source_path):
        print(f"❌ Source logo not found: {source_path}")
        return False

    # Load source logo
    try:
        logo = Image.open(source_path).convert("RGBA")
        print(f"✓ Loaded source: {os.path.basename(source_path)} ({logo.size})")
    except Exception as e:
        print(f"❌ Failed to load source: {e}")
        return False

    # Generate each icon variant
    for output_path, size, safe_zone in ICON_SPECS:
        try:
            # Create output directory if needed
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Create icon with safe-zone padding
            # Calculate logo size within safe zone
            logo_size = int(size * safe_zone)

            # Resize source logo to fit in safe zone
            resized_logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

            # Create icon background (white)
            icon = Image.new("RGBA", (size, size), (255, 255, 255, 255))

            # Center logo in icon
            offset = (size - logo_size) // 2
            icon.paste(resized_logo, (offset, offset), resized_logo)

            # iOS icons must be opaque RGB (no alpha channel)
            if "ios-icon" in output_path:
                icon = icon.convert("RGB")

            # Save icon
            icon.save(output_path, "PNG")
            print(f"✓ Generated {size}×{size}: {output_path}")

        except Exception as e:
            print(f"❌ Failed to generate {output_path}: {e}")
            return False

    # Generate Windows .ico file (uses largest size)
    try:
        ico_source = Image.open(source_path).convert("RGBA")
        ico = Image.new("RGBA", (256, 256), (255, 255, 255, 255))

        logo_size = int(256 * 0.7)
        resized = ico_source.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        offset = (256 - logo_size) // 2
        ico.paste(resized, (offset, offset), resized)

        # Convert to RGB for .ico (some tools don't like RGBA)
        ico_rgb = Image.new("RGB", ico.size, (255, 255, 255))
        ico_rgb.paste(ico, mask=ico.split()[3])

        ico_path = "packaging/icons/ahoy.ico"
        os.makedirs(os.path.dirname(ico_path), exist_ok=True)
        ico_rgb.save(ico_path, "ICO", sizes=[(256, 256)])
        print(f"✓ Generated Windows icon: {ico_path}")

    except Exception as e:
        print(f"❌ Failed to generate .ico: {e}")
        return False

    print("\n✅ All icons generated successfully!")
    return True

if __name__ == "__main__":
    generate_icons(SOURCE_LOGO)
