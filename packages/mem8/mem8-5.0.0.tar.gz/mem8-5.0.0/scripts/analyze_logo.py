#!/usr/bin/env python3
"""Analyze logo to find the exact center of the infinity symbol."""

from PIL import Image
import numpy as np
from pathlib import Path

def analyze_logo():
    """Analyze the logo to find content bounds."""

    root = Path(__file__).parent.parent
    source_logo = root / "mem8.png"

    # Load image
    img = Image.open(source_logo)
    print(f"Image size: {img.size}")

    # Convert to numpy array for analysis
    img_array = np.array(img)

    # Find non-transparent pixels
    if img.mode == 'RGBA':
        # Alpha channel is the last one
        alpha = img_array[:, :, 3]

        # Find rows and columns with content
        rows_with_content = np.where(np.any(alpha > 0, axis=1))[0]
        cols_with_content = np.where(np.any(alpha > 0, axis=0))[0]

        if len(rows_with_content) > 0 and len(cols_with_content) > 0:
            top = rows_with_content[0]
            bottom = rows_with_content[-1]
            left = cols_with_content[0]
            right = cols_with_content[-1]

            print("\nContent bounds:")
            print(f"  Top: {top}")
            print(f"  Bottom: {bottom}")
            print(f"  Left: {left}")
            print(f"  Right: {right}")
            print(f"  Width: {right - left}")
            print(f"  Height: {bottom - top}")

            # Find the vertical center of content
            content_center_y = (top + bottom) // 2
            print(f"\nVertical center of content: {content_center_y}")

            # Look for the gap between infinity symbol and text
            # Scan from center downward to find where content drops significantly
            center_x = (left + right) // 2

            # Get column of pixels at center
            center_col = alpha[:, center_x]

            # Find gaps (multiple consecutive transparent pixels)
            gap_start = None
            for y in range(content_center_y, bottom):
                if center_col[y] < 10:  # Essentially transparent
                    if gap_start is None:
                        gap_start = y
                elif gap_start is not None:
                    gap_length = y - gap_start
                    if gap_length > 20:  # Significant gap
                        print(f"\nFound gap at y={gap_start}, length={gap_length}")
                        print(f"Infinity symbol likely ends around: {gap_start}")

                        # Suggest crop
                        suggested_crop_bottom = gap_start + 10  # Small padding
                        print("\nSuggested crop for icon:")
                        print(f"  crop((0, 0, {img.width}, {suggested_crop_bottom}))")
                        print(f"  This captures {suggested_crop_bottom}px from top ({suggested_crop_bottom/img.height*100:.1f}% of image)")
                        break
                    gap_start = None

if __name__ == "__main__":
    analyze_logo()
