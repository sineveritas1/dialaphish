#!/usr/bin/env python3
"""
generate_phish.py — build shows.json for DIAL·A·PHISH from the phish.in v2 API.

    { "YYYY-MM-DD": { "venue": ..., "city": ..., "id": <phish.in show id> } }

One entry per show phish.in has audio for. It pages through /shows once
(~22 requests of 100), so a full rebuild takes well under a minute.

The result REPLACES shows.json — a show phish.in removes (or whose audio goes
missing) drops out too. If any page fails, nothing is written and the script
exits non-zero, so a flaky run can never truncate the index; it also refuses to
write if the count falls by more than 5%.

Usage:
    python3 generate_phish.py            # write shows.json
    python3 generate_phish.py --dry-run  # report what would change
    python3 generate_phish.py --force    # write even if the count drops >5%
"""
import json, sys, time
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

BASE  = "https://phish.in/api/v2"
OUT   = "shows.json"
UA    = "dial-a-phish/1.1 (+https://dialaphish.com)"
DELAY = 0.5
PER   = 100

def fetch(url, retries=4):
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(retries):
        try:
            with urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except HTTPError as e:
            if e.code == 404:
                return None
            wait = 15 * (attempt + 1) if e.code in (429, 503) else 3 * (attempt + 1)
            print(f" [HTTP {e.code}, retry in {wait}s]", flush=True)
        except (URLError, TimeoutError, ValueError) as e:
            wait = 3 * (attempt + 1)
            print(f" [{type(e).__name__}, retry in {wait}s]", flush=True)
        time.sleep(wait)
    raise RuntimeError(f"giving up on {url}")

def has_audio(s):
    st = s.get("audio_status")
    if st is not None:
        return st in ("complete", "partial")
    return bool(s.get("tracks_count") or s.get("duration"))

def all_shows():
    out, page, total = [], 1, 1
    while page <= total:
        d = fetch(f"{BASE}/shows?per_page={PER}&page={page}&sort=date:asc")
        if not isinstance(d, dict):
            raise RuntimeError(f"unexpected response on page {page}")
        out.extend(d.get("shows") or [])
        total = d.get("total_pages") or 1
        print(f"  page {page}/{total}", flush=True)
        page += 1
        time.sleep(DELAY)
    return out

def main():
    dry = "--dry-run" in sys.argv
    t0 = time.time()
    try:
        existing = json.load(open(OUT, encoding="utf-8"))
    except (OSError, ValueError):
        existing = {}
    print(f"Existing: {len(existing)} shows")

    shows, skipped = {}, 0
    for s in all_shows():
        date = (s.get("date") or "")[:10]
        if len(date) != 10:
            continue
        if not has_audio(s):
            skipped += 1
            continue
        v = s.get("venue") if isinstance(s.get("venue"), dict) else {}
        shows[date] = {"venue": s.get("venue_name") or v.get("name", ""),
                       "city": v.get("location", "") or s.get("location", ""),
                       "id": s.get("id", "")}
    shows = dict(sorted(shows.items()))

    added = sorted(set(shows) - set(existing))
    removed = sorted(set(existing) - set(shows))
    changed = sorted(k for k in set(shows) & set(existing) if shows[k] != existing[k])
    print(f"\nphish.in: {len(shows)} shows with audio ({skipped} without audio skipped)")
    print(f"added {len(added)}, removed {len(removed)}, changed {len(changed)}")
    for label, keys in (("+", added), ("-", removed), ("~", changed)):
        for k in keys[:40]:
            print(f"  {label} {k}  {(shows.get(k) or existing.get(k))['venue']}")

    if existing and "--force" not in sys.argv and len(shows) < len(existing) * 0.95:
        print(f"\nREFUSING: count fell from {len(existing)} to {len(shows)} — looks like a bad scrape (--force to override).")
        sys.exit(1)
    if dry:
        print("\n(dry run — nothing written)")
        return
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(shows, f, separators=(",", ":"), ensure_ascii=False)
    print(f"\nWrote {len(shows)} shows → {OUT} ({time.time()-t0:.0f}s)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print(f"\nFATAL: {e}")
        sys.exit(1)
