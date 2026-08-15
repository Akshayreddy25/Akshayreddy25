#!/usr/bin/env python3
"""
fetch_contributions.py - scrape the public contribution calendar HTML
fragment GitHub serves (no token needed) and write data/contributions.json
with raw days plus derived stats.

Usage:
    python scripts/fetch_contributions.py [username]
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DEFAULT_USERNAME = "Akshayreddy25"
OUTPUT_PATH = Path("data/contributions.json")


def fetch_html(username: str) -> str:
    url = f"https://github.com/users/{username}/contributions"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; contributions-fetcher/1.0)"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text


def _safe_int(value: str):
    try:
        return int(value)
    except ValueError:
        return 0


def parse_days(html: str):
    soup = BeautifulSoup(html, "html.parser")
    days = []

    cells = soup.select("td.ContributionCalendar-day")

    for cell in cells:
        date_str = cell.get("data-date")
        if not date_str:
            continue

        level_str = cell.get("data-level")
        level = int(level_str) if level_str is not None else 0

        count = 0
        cell_id = cell.get("id")
        if cell_id:
            tooltip = soup.find("tool-tip", attrs={"for": cell_id})
            if tooltip:
                tooltip_text = tooltip.get_text(strip=True)
                first_word = tooltip_text.split()[0] if tooltip_text else ""
                count = 0 if first_word.lower() == "no" else _safe_int(first_word)

        days.append({
            "date": date_str,
            "count": count,
            "level": level,
        })

    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days):
    total = sum(d["count"] for d in days)

    current_streak = 0
    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    best_day = max(days, key=lambda d: d["count"], default=None)

    monthly_totals = {}
    for d in days:
        month_key = d["date"][:7]
        monthly_totals[month_key] = monthly_totals.get(month_key, 0) + d["count"]

    return {
        "total_contributions": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly_totals": monthly_totals,
    }


def main() -> None:
    username = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USERNAME

    print(f"Fetching contributions for {username}...")
    html = fetch_html(username)

    print("Parsing day cells...")
    days = parse_days(html)

    if not days:
        print("Warning: no day cells parsed. GitHub's markup may have "
              "changed, or the profile could be private.")

    print("Computing stats...")
    stats = compute_stats(days)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "username": username,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "days": days,
        "stats": stats,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Saved {OUTPUT_PATH} "
          f"({len(days)} days, {stats['total_contributions']} total contributions)")


if __name__ == "__main__":
    main()
