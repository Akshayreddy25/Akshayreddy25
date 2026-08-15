#!/usr/bin/env python3
"""
render_heatmap_svg.py - render data/contributions.json as a GitHub-style
contribution heatmap SVG, revealed with a diagonal line-after-line
slide-down animation that plays once on load then freezes.

Usage:
    python scripts/render_heatmap_svg.py
"""
import json
from datetime import datetime
from pathlib import Path

DATA_PATH = Path("data/contributions.json")
OUTPUT_PATH = "contrib-heatmap.svg"

CELL_SIZE = 11
CELL_GAP = 3
CELL_RADIUS = 2

LEFT_MARGIN = 35
TOP_MARGIN = 40
BOTTOM_MARGIN = 40

# none -> brightest (level 5 is a neon top end)
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

BG_COLOR = "#0d1117"
TEXT_COLOR = "#7d8590"
FONT_FAMILY = "Menlo, Consolas, 'Courier New', monospace"

WEEKDAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""]
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

COL_STAGGER = 0.03
ROW_STAGGER_WITHIN_COL = 0.015
CELL_FADE_DURATION = 0.35


def load_data():
    with open(DATA_PATH) as f:
        return json.load(f)


def bucket_into_weeks(days):
    """Group days into columns of 7 (Sun-Sat), matching GitHub's layout."""
    if not days:
        return []

    weeks = []
    current_week = [None] * 7

    for day in days:
        date = datetime.strptime(day["date"], "%Y-%m-%d")
        weekday = (date.weekday() + 1) % 7  # convert Mon=0 -> Sun=0 indexing

        if weekday == 0 and any(current_week):
            weeks.append(current_week)
            current_week = [None] * 7

        current_week[weekday] = day

    if any(current_week):
        weeks.append(current_week)

    return weeks


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(weeks, stats) -> str:
    num_cols = len(weeks)
    grid_width = num_cols * (CELL_SIZE + CELL_GAP)
    grid_height = 7 * (CELL_SIZE + CELL_GAP)

    width = LEFT_MARGIN + grid_width + 10
    height = TOP_MARGIN + grid_height + BOTTOM_MARGIN + 20

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" width="{width}" height="{height}">'
    )
    parts.append(f'<rect width="{width}" height="{height}" fill="{BG_COLOR}" rx="6"/>')
    parts.append(
        f'<style>text {{ font-family: {FONT_FAMILY}; fill: {TEXT_COLOR}; }}</style>'
    )

    # weekday labels (left side)
    for row_idx, label in enumerate(WEEKDAY_LABELS):
        if not label:
            continue
        y = TOP_MARGIN + row_idx * (CELL_SIZE + CELL_GAP) + CELL_SIZE - 2
        parts.append(f'<text x="2" y="{y}" font-size="9">{label}</text>')

    # month labels (top), placed at the first column where that month appears
    last_month = None
    for col_idx, week in enumerate(weeks):
        first_valid = next((d for d in week if d), None)
        if not first_valid:
            continue
        month_idx = int(first_valid["date"][5:7]) - 1
        if month_idx != last_month:
            x = LEFT_MARGIN + col_idx * (CELL_SIZE + CELL_GAP)
            parts.append(
                f'<text x="{x}" y="{TOP_MARGIN - 8}" font-size="9">'
                f'{MONTH_LABELS[month_idx]}</text>'
            )
            last_month = month_idx

    # the grid itself, diagonal stagger: column start + row-within-column offset
    for col_idx, week in enumerate(weeks):
        col_start = col_idx * COL_STAGGER
        for row_idx, day in enumerate(week):
            if day is None:
                continue

            x = LEFT_MARGIN + col_idx * (CELL_SIZE + CELL_GAP)
            y = TOP_MARGIN + row_idx * (CELL_SIZE + CELL_GAP)
            level = min(day.get("level", 0), len(PALETTE) - 1)
            color = PALETTE[level]
            begin = col_start + row_idx * ROW_STAGGER_WITHIN_COL

            title = escape_xml(f'{day["count"]} contributions on {day["date"]}')

            parts.append(
                f'<rect x="{x}" y="{y - 6}" width="{CELL_SIZE}" height="{CELL_SIZE}" '
                f'rx="{CELL_RADIUS}" fill="{color}" opacity="0">'
            )
            parts.append(f'<title>{title}</title>')
            parts.append(
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin:.3f}s" dur="{CELL_FADE_DURATION}s" fill="freeze"/>'
            )
            parts.append(
                f'<animate attributeName="y" from="{y - 6}" to="{y}" '
                f'begin="{begin:.3f}s" dur="{CELL_FADE_DURATION}s" fill="freeze" '
                f'calcMode="spline" keySplines="0.25 0.1 0.25 1" '
                f'keyTimes="0;1" values="{y - 6};{y}"/>'
            )
            parts.append('</rect>')

    # legend: Less -> More
    legend_y = TOP_MARGIN + grid_height + 22
    legend_x = LEFT_MARGIN
    parts.append(f'<text x="{legend_x}" y="{legend_y + 8}" font-size="10">Less</text>')
    lx = legend_x + 32
    for color in PALETTE:
        parts.append(
            f'<rect x="{lx}" y="{legend_y}" width="{CELL_SIZE}" height="{CELL_SIZE}" '
            f'rx="{CELL_RADIUS}" fill="{color}"/>'
        )
        lx += CELL_SIZE + CELL_GAP
    parts.append(f'<text x="{lx + 4}" y="{legend_y + 8}" font-size="10">More</text>')

    # stats footer
    footer_y = legend_y + 26
    total = stats["total_contributions"]
    footer_text = f"{total:,} contributions in the last year"
    parts.append(
        f'<text x="{LEFT_MARGIN}" y="{footer_y}" font-size="11">{escape_xml(footer_text)}</text>'
    )

    streak_text = (
        f'Current streak: {stats["current_streak"]} day(s)  |  '
        f'Longest streak: {stats["longest_streak"]} day(s)'
    )
    parts.append(
        f'<text x="{LEFT_MARGIN}" y="{footer_y + 16}" font-size="10">'
        f'{escape_xml(streak_text)}</text>'
    )

    parts.append('</svg>')
    return "\n".join(parts)


def main() -> None:
    if not DATA_PATH.exists():
        print(f"Error: {DATA_PATH} not found. Run fetch_contributions.py first.")
        return

    data = load_data()
    weeks = bucket_into_weeks(data["days"])
    svg = build_svg(weeks, data["stats"])

    with open(OUTPUT_PATH, "w") as f:
        f.write(svg)

    print(f"Saved {OUTPUT_PATH} ({len(weeks)} weeks)")


if __name__ == "__main__":
    main()
