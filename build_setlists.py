#!/usr/bin/env python3
"""
build_setlists.py — build setlists.json, the per-show song lists that
build_pages.py prints on each /show/ page. Not used by the player itself.

    { "YYYY-MM-DD": [["Set 1", ["Tweezer", "Reba", ...]], ["Encore", [...]]] }

Incremental: only dates in shows.json that setlists.json doesn't have yet are
fetched, one /shows/<date> request each, so the weekly job makes a handful of
requests. When lots are missing (first build, or --full) it instead pages the
whole /tracks endpoint — ~40 requests of 1,000 tracks, ~200 MB, a few minutes.

Usage:
    python3 build_setlists.py          # fill in missing dates
    python3 build_setlists.py --full   # rebuild everything
"""
import json, sys, time
from collections import defaultdict
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

BASE  = "https://phish.in/api/v2"
OUT   = "setlists.json"
UA    = "dial-a-phish/1.1 (+https://dialaphish.com)"
DELAY = 0.5
BULK_OVER = 150   # more missing than this → page /tracks instead

def fetch(url, retries=4):
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(retries):
        try:
            with urlopen(req, timeout=60) as r:
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

def setlist(tracks):
    """[(set_name, position, title)] → [[set, [titles]]] in play order."""
    sets, order = defaultdict(list), []
    for set_name, pos, title in sorted(tracks, key=lambda t: t[1]):
        set_name = set_name or "Set"
        if set_name not in sets: order.append(set_name)
        if title and (not sets[set_name] or sets[set_name][-1] != title):
            sets[set_name].append(title)
    return [[s, sets[s]] for s in order if sets[s]]

def row(t):
    return (t.get("set_name") or "", t.get("position") or 0, (t.get("title") or "").strip())

def bulk():
    by_date, page, total = defaultdict(list), 1, 1
    while page <= total:
        d = fetch(f"{BASE}/tracks?per_page=1000&page={page}")
        if not isinstance(d, dict):
            raise RuntimeError(f"unexpected response on page {page}")
        for t in d.get("tracks") or []:
            if t.get("show_date"): by_date[t["show_date"]].append(row(t))
        total = d.get("total_pages") or 1
        print(f"  tracks page {page}/{total}", flush=True)
        page += 1
        time.sleep(DELAY)
    return {k: setlist(v) for k, v in by_date.items()}

def main():
    shows = json.load(open("shows.json", encoding="utf-8"))
    try:
        have = {} if "--full" in sys.argv else json.load(open(OUT, encoding="utf-8"))
    except (OSError, ValueError):
        have = {}
    have = {k: v for k, v in have.items() if k in shows}
    missing = sorted(k for k in shows if k not in have)
    print(f"{len(shows)} shows, {len(have)} setlists on file, {len(missing)} to fetch")
    if len(missing) > BULK_OVER:
        got = bulk()
        for k in missing:
            if got.get(k): have[k] = got[k]
    else:
        for k in missing:
            d = fetch(f"{BASE}/shows/{k}")
            if d and d.get("tracks"):
                have[k] = setlist([row(t) for t in d["tracks"]])
            print(f"  {k}: {sum(len(s[1]) for s in have.get(k, []))} songs", flush=True)
            time.sleep(DELAY)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(have.items())), f, separators=(",", ":"), ensure_ascii=False)
    print(f"Wrote {len(have)} setlists → {OUT}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print(f"\nFATAL: {e}")
        sys.exit(1)
