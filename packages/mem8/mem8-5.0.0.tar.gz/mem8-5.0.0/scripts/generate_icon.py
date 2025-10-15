#!/usr/bin/env python3
"""Generate a square icon focused on the infinity symbol."""

from PIL import Image
from pathlib import Path

def generate_icon():
    """Generate square icon cropped to infinity symbol."""

    root = Path(__file__).parent.parent
    source_logo = root / "mem8.png"
    docs_static = root / "documentation" / "static" / "img"
    docs_static.mkdir(parents=True, exist_ok=True)

    # Load image
    img = Image.open(source_logo)
    print(f"Source image: {img.size}")

    # The infinity symbol appears to be in roughly the top 45% of the image
    # Let's crop a square region centered on it
    # Based on visual inspection, the infinity symbol is centered horizontally
    # and located in the upper portion

    # Calculate square crop centered on infinity symbol
    # Infinity symbol is roughly at y=200-450 (estimate)
    symbol_center_y = 300  # Approximate center of infinity symbol
    symbol_size = 350  # Approximate height of symbol

    # Create square crop
    crop_size = symbol_size + 100  # Add padding
    left = (img.width - crop_size) // 2
    top = symbol_center_y - (crop_size // 2)
    right = left + crop_size
    bottom = top + crop_size

    # Ensure we don't go out of bounds
    if top < 0:
        bottom += abs(top)
        top = 0
    if bottom > img.height:
        top -= (bottom - img.height)
        bottom = img.height
    if left < 0:
        right += abs(left)
        left = 0
    if right > img.width:
        left -= (right - img.width)
        right = img.width

    print(f"Crop region: ({left}, {top}, {right}, {bottom})")
    print(f"Crop size: {right-left}x{bottom-top}")

    # Crop to square
    icon = img.crop((left, top, right, bottom))

    # Save at original resolution
    icon.save(docs_static / "logo-icon.png")
    print(f"✓ Saved: logo-icon.png ({icon.size})")

    # Also create a version that's explicitly square in case crop wasn't perfect
    size = max(icon.width, icon.height)
    icon_square = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    icon_square.paste(icon, ((size - icon.width) // 2, (size - icon.height) // 2))

    icon_square.save(docs_static / "logo-icon-square.png")
    print(f"✓ Saved: logo-icon-square.png ({icon_square.size})")

if __name__ == "__main__":
    generate_icon()
