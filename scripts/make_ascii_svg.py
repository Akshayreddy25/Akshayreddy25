#!/usr/bin/env python3
"""
make_ascii_svg.py - convert a prepped grayscale photo into a self-typing
ASCII-art SVG.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

RAMP = " .`:-=+*cs#%@"

GRID_COLS = 100
GRID_ROWS = 53

FONT_FAMILY = "Menlo, Consolas, 'Courier New', monospace"
CHAR_W = 8
CHAR_H = 14
FONT_SIZE = 12
FILL_COLOR = "#c9d1d9"

ROW_STAGGER = 0.04
ROW_DURATION = 0.9


def image_to_ascii_grid(image_path: str, cols: int, rows: int):
    img = Image.open(image_path).convert("L")
    img = img.resize((cols, rows), Image.LANCZOS)
    pixels = np.array(img)

    ramp_len = len(RAMP)
    lines = []
    for row in pixels:
        line_chars = []
        for value in row:
            idx = int((255 - value) / 255 * (ramp_len - 1))
            line_chars.append(RAMP[idx])
        lines.append("".join(line_chars))
    return lines


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(lines) -> str:
    width = GRID_COLS * CHAR_W
    height = GRID_ROWS * CHAR_H + 20

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" width="{width}" height="{height}">'
    )
    parts.append(f'<rect width="{width}" height="{height}" fill="transparent"/>')
    parts.append(
        f'<style>text {{ font-family: {FONT_FAMILY}; font-size: {FONT_SIZE}px; '
        f'fill: {FILL_COLOR}; white-space: pre; }}</style>'
    )

    for row_idx, line in enumerate(lines):
        if line.strip() == "":
            continue

        y = (row_idx + 1) * CHAR_H
        start_time = row_idx * ROW_STAGGER
        row_width = len(line) * CHAR_W
        clip_id = f"clip-row-{row_idx}"

        parts.append(f'<clipPath id="{clip_id}">')
        parts.append(f'  <rect x="0" y="{y - CHAR_H}" width="0" height="{CHAR_H + 4}">')
        parts.append(
            f'    <animate attributeName="width" from="0" to="{row_width}" '
            f'begin="{start_time:.2f}s" dur="{ROW_DURATION}s" '
            f'fill="freeze" calcMode="spline" '
            f'keySplines="0.25 0.1 0.25 1" keyTimes="0;1" values="0;{row_width}"/>'
        )
        parts.append('  </rect>')
        parts.append('</clipPath>')

        parts.append(f'<g clip-path="url(#{clip_id})">')
        parts.append(f'  <text x="0" y="{y}">{escape_xml(line)}</text>')
        parts.append('</g>')

        parts.append(
            f'<rect x="0" y="{y - CHAR_H + 3}" width="{CHAR_W - 1}" height="{CHAR_H - 3}" '
            f'fill="{FILL_COLOR}" opacity="0">'
        )
        parts.append(
            f'  <animate attributeName="x" from="0" to="{row_width}" '
            f'begin="{start_time:.2f}s" dur="{ROW_DURATION}s" fill="freeze"/>'
        )
        parts.append(
            f'  <animate attributeName="opacity" values="0;1;1;0" '
            f'keyTimes="0;0.02;0.9;1" begin="{start_time:.2f}s" '
            f'dur="{ROW_DURATION}s" fill="freeze"/>'
        )
        parts.append('</rect>')

    parts.append('</svg>')
    return "\n".join(parts)


def main() -> None:
    input_path = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "avi-ascii.svg"

    if not Path(input_path).exists():
        print(f"Error: {input_path} not found. Run prep_photo.py first.")
        sys.exit(1)

    print(f"Converting {input_path} to a {GRID_COLS}x{GRID_ROWS} ASCII grid...")
    lines = image_to_ascii_grid(input_path, GRID_COLS, GRID_ROWS)

    print("Building self-typing SVG...")
    svg = build_svg(lines)

    with open(output_path, "w") as f:
        f.write(svg)

    total_duration = GRID_ROWS * ROW_STAGGER + ROW_DURATION
    print(f"Saved {output_path} (~{total_duration:.1f}s animation)")


if __name__ == "__main__":
    main()
