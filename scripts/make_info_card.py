#!/usr/bin/env python3
"""
make_info_card.py - generate a neofetch-style animated info card SVG.

Renders a title bar plus colored key/value rows (Now, Prev, Stack,
Highlights). Each row fades and slides in on a short stagger so it looks
like it's printing next to the portrait.

Set STATIC=1 to emit a frozen (non-animated) frame, useful for local
Quick Look previews.

Usage:
    python scripts/make_info_card.py          # writes info-card.svg
    STATIC=1 python scripts/make_info_card.py  # frozen frame
"""
import os

OUTPUT_PATH = "info-card.svg"

WIDTH = 560
LINE_HEIGHT = 26
PADDING_X = 24
PADDING_TOP = 56
TITLE_BAR_HEIGHT = 36

FONT_FAMILY = "Menlo, Consolas, 'Courier New', monospace"
FONT_SIZE = 14
LABEL_COLOR = "#7ee787"
VALUE_COLOR = "#c9d1d9"
BG_COLOR = "#0d1117"
TITLE_BAR_COLOR = "#161b22"
BORDER_COLOR = "#30363d"

STAGGER = 0.12
FADE_DURATION = 0.5

# ---- Content: edit these to keep the card current ----
ROWS = [
    ("Now", "M.S. CS @ George Mason Univ. (Dec 2026)"),
    ("Prev", "B.Tech, Anurag University"),
    ("Stack", "Python / Java / FastAPI / LangGraph / Docker"),
    ("Highlights", "Auto Healing API - autonomous SRE agent"),
    ("", "Ticket Triage - full-stack RAG platform"),
]


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(rows, static: bool) -> str:
    height = PADDING_TOP + len(rows) * LINE_HEIGHT + 20

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}">'
    )

    # background + border
    parts.append(
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" '
        f'rx="8" fill="{BG_COLOR}" stroke="{BORDER_COLOR}"/>'
    )

    # title bar
    parts.append(
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{TITLE_BAR_HEIGHT}" '
        f'rx="8" fill="{TITLE_BAR_COLOR}"/>'
    )
    parts.append(
        f'<rect x="0.5" y="{TITLE_BAR_HEIGHT - 8}" width="{WIDTH - 1}" height="8" '
        f'fill="{TITLE_BAR_COLOR}"/>'
    )
    # traffic-light dots
    for i, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        cx = 20 + i * 18
        parts.append(f'<circle cx="{cx}" cy="{TITLE_BAR_HEIGHT / 2}" r="5" fill="{color}"/>')

    parts.append(
        f'<text x="{WIDTH / 2}" y="{TITLE_BAR_HEIGHT / 2 + 5}" '
        f'text-anchor="middle" fill="{VALUE_COLOR}" '
        f'font-family="{FONT_FAMILY}" font-size="12">akshay@github ~ neofetch</text>'
    )

    parts.append(
        f'<style>.row text {{ font-family: {FONT_FAMILY}; font-size: {FONT_SIZE}px; }}</style>'
    )

    for idx, (label, value) in enumerate(rows):
        y = PADDING_TOP + idx * LINE_HEIGHT
        start_time = idx * STAGGER

        group_attrs = 'class="row"'
        if not static:
            group_attrs += ' opacity="0"'

        parts.append(f'<g {group_attrs}>')

        if label:
            label_text = f'{escape_xml(label)}:'
            parts.append(
                f'<text x="{PADDING_X}" y="{y}" fill="{LABEL_COLOR}" font-weight="bold">{label_text}</text>'
            )
            value_x = PADDING_X + 13 * 8.4
        else:
            value_x = PADDING_X + 13 * 8.4

        parts.append(
            f'<text x="{value_x}" y="{y}" fill="{VALUE_COLOR}">{escape_xml(value)}</text>'
        )

        if not static:
            parts.append(
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{start_time:.2f}s" dur="{FADE_DURATION}s" fill="freeze"/>'
            )
            parts.append(
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="-8 0" to="0 0" begin="{start_time:.2f}s" '
                f'dur="{FADE_DURATION}s" fill="freeze" calcMode="spline" '
                f'keySplines="0.25 0.1 0.25 1" keyTimes="0;1" values="-8 0;0 0"/>'
            )

        parts.append('</g>')

    parts.append('</svg>')
    return "\n".join(parts)


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    svg = build_svg(ROWS, static=static)

    with open(OUTPUT_PATH, "w") as f:
        f.write(svg)

    mode = "static frame" if static else "animated"
    print(f"Saved {OUTPUT_PATH} ({mode})")


if __name__ == "__main__":
    main()
