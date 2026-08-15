#!/usr/bin/env python3
"""
prep_photo.py - prepare a photo for ASCII-art conversion.

Steps:
  1. Remove the background with rembg (isolates the subject).
  2. Boost local contrast with CLAHE so a flatly-lit face gets real
     highlights and shadows instead of converting to a dark blob.
  3. Composite onto pure white so the background maps to the blank
     end of the ASCII density ramp (white -> spaces).

Usage:
    python scripts/prep_photo.py source-photo.jpg

Output:
    source-prepped.png (grayscale, ready for make_ascii_svg.py)
"""
import io
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def prep_photo(input_path: str, output_path: str = "source-prepped.png") -> None:
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"No such file: {input_path}")

    print(f"Reading {input_path}...")
    with open(input_path, "rb") as f:
        input_bytes = f.read()

    print("Removing background (this may take a moment on first run "
          "while rembg downloads its model)...")
    output_bytes = remove(input_bytes)

    subject = Image.open(io.BytesIO(output_bytes)).convert("RGBA")

    print("Compositing onto white background...")
    white_bg = Image.new("RGBA", subject.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, subject).convert("RGB")

    gray = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2GRAY)

    print("Boosting local contrast (CLAHE)...")
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    contrasted = clahe.apply(gray)

    alpha = np.array(subject)[:, :, 3]
    background_mask = alpha < 10
    contrasted[background_mask] = 255

    result = Image.fromarray(contrasted)
    result.save(output_path)
    print(f"Saved {output_path} ({result.size[0]}x{result.size[1]})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/prep_photo.py <input-photo>")
        sys.exit(1)

    input_arg = sys.argv[1]
    output_arg = sys.argv[2] if len(sys.argv) > 2 else "source-prepped.png"
    prep_photo(input_arg, output_arg)
