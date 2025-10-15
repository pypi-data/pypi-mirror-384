#!/usr/bin/env python3
"""Generate logo variants for mem8 documentation and branding."""

from PIL import Image
from pathlib import Path

def generate_logos():
    """Generate various logo sizes and crops from the main logo."""

    # Paths
    root = Path(__file__).parent.parent
    source_logo = root / "mem8.png"
    docs_static = root / "documentation" / "static" / "img"
    frontend_public = root / "frontend" / "public"

    # Ensure directories exist
    docs_static.mkdir(parents=True, exist_ok=True)
    frontend_public.mkdir(parents=True, exist_ok=True)

    # Load source image
    img = Image.open(source_logo)
    print(f"Source image size: {img.size}")

    # Get the bounding box of non-transparent pixels
    if img.mode == 'RGBA':
        bbox = img.getbbox()
        print(f"Content bounding box: {bbox}")

        # Crop to content with some padding
        padding = 50
        cropped = img.crop((
            max(0, bbox[0] - padding),
            max(0, bbox[1] - padding),
            min(img.width, bbox[2] + padding),
            min(img.height, bbox[3] + padding)
        ))
    else:
        cropped = img

    print(f"Cropped size: {cropped.size}")

    # Generate full logo (cropped)
    cropped.save(docs_static / "logo.png")
    print(f"✓ Saved: logo.png ({cropped.size})")

    # Generate icon only (just the infinity symbol - top portion)
    # Crop to roughly the top 40% of the image to get just the infinity symbol
    icon_height = int(cropped.height * 0.42)
    icon_crop = cropped.crop((0, 0, cropped.width, icon_height))

    # Get tight bounding box of the icon content
    if icon_crop.mode == 'RGBA':
        icon_bbox = icon_crop.getbbox()
        if icon_bbox:
            # Add minimal padding
            pad = 20
            icon_crop = icon_crop.crop((
                max(0, icon_bbox[0] - pad),
                max(0, icon_bbox[1] - pad),
                min(icon_crop.width, icon_bbox[2] + pad),
                min(icon_crop.height, icon_bbox[3] + pad)
            ))

    # Make icon square with the cropped content
    icon_size = max(icon_crop.width, icon_crop.height)
    icon_square = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))
    icon_square.paste(icon_crop, ((icon_size - icon_crop.width) // 2, (icon_size - icon_crop.height) // 2))

    icon_square.save(docs_static / "logo-icon.png")
    print(f"✓ Saved: logo-icon.png ({icon_square.size})")

    # Generate favicons
    favicon_sizes = [16, 32, 64, 128, 192, 512]
    for size in favicon_sizes:
        favicon = icon_square.resize((size, size), Image.Resampling.LANCZOS)
        favicon.save(docs_static / f"favicon-{size}x{size}.png")
        print(f"✓ Saved: favicon-{size}x{size}.png")

    # Generate multi-size .ico
    icon_images = [icon_square.resize((s, s), Image.Resampling.LANCZOS) for s in [16, 32, 48, 64]]
    icon_images[0].save(docs_static / "favicon.ico", format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64)])
    print("✓ Saved: favicon.ico")

    # Generate apple-touch-icon
    apple_icon = icon_square.resize((180, 180), Image.Resampling.LANCZOS)
    apple_icon.save(docs_static / "apple-touch-icon.png")
    print("✓ Saved: apple-touch-icon.png")

    # Copy to frontend
    print("\nGenerating frontend assets...")

    # Copy full logo with text for frontend
    cropped.save(frontend_public / "logo_transparent_with_words.png")
    print("✓ Saved: frontend/public/logo_transparent_with_words.png")

    # Copy icon (just infinity symbol) for frontend
    icon_square.save(frontend_public / "logo_mark.png")
    print("✓ Saved: frontend/public/logo_mark.png")

    # Generate frontend favicons
    for size in favicon_sizes:
        favicon = icon_square.resize((size, size), Image.Resampling.LANCZOS)
        favicon.save(frontend_public / f"favicon-{size}x{size}.png")
        print(f"✓ Saved: frontend/public/favicon-{size}x{size}.png")

    # Add 48x48 for frontend (needed for .ico)
    if 48 not in favicon_sizes:
        favicon_48 = icon_square.resize((48, 48), Image.Resampling.LANCZOS)
        favicon_48.save(frontend_public / "favicon-48x48.png")
        print("✓ Saved: frontend/public/favicon-48x48.png")

    # Generate frontend favicon.ico
    icon_images = [icon_square.resize((s, s), Image.Resampling.LANCZOS) for s in [16, 32, 48, 64]]
    icon_images[0].save(frontend_public / "favicon.ico", format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64)])
    print("✓ Saved: frontend/public/favicon.ico")

    # Generate frontend apple-touch-icon
    apple_icon.save(frontend_public / "apple-touch-icon.png")
    print("✓ Saved: frontend/public/apple-touch-icon.png")

    # Generate social card (1200x630 with logo centered)
    social_card = Image.new('RGB', (1200, 630), (13, 17, 23))  # Dark background

    # Resize logo to fit nicely
    logo_for_card = cropped.resize((600, int(600 * cropped.height / cropped.width)), Image.Resampling.LANCZOS)

    # Center on card
    x = (1200 - logo_for_card.width) // 2
    y = (630 - logo_for_card.height) // 2

    # Convert logo to RGB for pasting
    if logo_for_card.mode == 'RGBA':
        # Create a white background for compositing
        bg = Image.new('RGB', logo_for_card.size, (13, 17, 23))
        bg.paste(logo_for_card, mask=logo_for_card.split()[3])  # Use alpha channel as mask
        logo_for_card = bg

    social_card.paste(logo_for_card, (x, y))

    social_card.save(docs_static / "mem8-social-card.jpg", quality=95)
    print("✓ Saved: mem8-social-card.jpg")

    print("\nAll logo variants generated successfully!")
    print(f"Output directory: {docs_static}")

if __name__ == "__main__":
    generate_logos()
