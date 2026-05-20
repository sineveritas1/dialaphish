#!/usr/bin/env python3
"""
generate_phish.py — Build shows.json for Dial-A-Phish
Uses phish.in v2 API (no key required).

Usage:  python generate_phish.py
Output: shows.json
"""

import json, time, sys
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

BASE  = "https://phish.in/api/v2"
OUT   = "shows.json"
UA    = "dial-a-phish/1.0"
DELAY = 0.5
START_YEAR = 1983
END_YEAR   = datetime.now().year  # automatically includes 2026, 2027, etc.

def fetch(url, retries=3):
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(retries):
        try:
            with urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode("utf-8"))
        except HTTPError as e:
            if e.code == 429:
                wait = 15 * (attempt + 1)
                print(f" [rate limit, waiting {wait}s]", flush=True)
                time.sleep(wait)
            elif e.code == 404:
                return None
            else:
                print(f" [HTTP {e.code}]", end="", flush=True)
                if attempt == retries - 1:
                    return None
                time.sleep(3)
        except URLError as e:
            print(f" [network error]", end="", flush=True)
            if attempt == retries - 1:
                return None
            time.sleep(3)
    return None

def get_shows_for_year(year):
    shows = []
    page = 1
    while True:
        url = f"{BASE}/shows?per_page=100&page={page}&year={year}"
        data = fetch(url)
        if not data:
            break
        if isinstance(data, list):
            chunk, total_pages = data, 1
        elif isinstance(data, dict):
            chunk = data.get("shows") or data.get("data") or []
            total_pages = data.get("total_pages") or data.get("pages") or 1
        else:
            break
        shows.extend(chunk)
        if page >= total_pages or not chunk:
            break
        page += 1
        time.sleep(DELAY)
    return shows

def main():
    print("=" * 60)
    print("DIAL-A-PHISH — show database generator (v2 API)")
    print(f"Years: {START_YEAR}–{END_YEAR}")
    print("=" * 60)
    t0 = time.time()

    try:
        existing = json.load(open(OUT, encoding="utf-8"))
        print(f"\nExisting: {len(existing)} shows")
    except:
        existing = {}
        print("\nBuilding from scratch...")

    shows_dict = {}
    total = 0

    for year in range(START_YEAR, END_YEAR + 1):
        print(f"\n{year}:", end=" ", flush=True)
        year_shows = get_shows_for_year(year)

        if not year_shows:
            print("no shows")
            continue

        count = 0
        for s in year_shows:
            date = (s.get("date") or s.get("show_date", ""))[:10]
            if not date or len(date) < 10:
                continue
            v = s.get("venue") or {}
            venue = s.get("venue_name") or (v.get("name", "") if isinstance(v, dict) else "") or ""
            city  = (v.get("location", "") if isinstance(v, dict) else "") or s.get("location", "")
            shows_dict[date] = {"venue": venue, "city": city, "id": s.get("id", "")}
            count += 1

        print(f"{count} shows", flush=True)
        total += count

    merged = dict(sorted({**existing, **shows_dict}.items()))
    json.dump(merged, open(OUT, "w", encoding="utf-8"), separators=(",", ":"))

    print(f"\n{'='*60}")
    print(f"Done! {len(merged)} shows → {OUT}  ({time.time()-t0:.0f}s)")
    print(f"{'='*60}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\nFATAL: {e}")
        sys.exit(1)
