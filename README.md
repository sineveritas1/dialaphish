# DIAL·A·PHISH

Stream any Phish show free. Enter a date. Hear the show.  
Audio via [phish.in](https://phish.in) — no API key required.

**Live at:** https://dialaphish.com (or your Cloudflare Pages URL)  
**Sister site:** https://dialadead.com

---

## How It Works

- `index.html` — single-file app, no build step, no dependencies
- `shows.json` — every show phish.in has audio for (venue, city, id) — RANDOM, archive, ← / →
- `generate_phish.py` — rebuilds shows.json from the phish.in API (~22 requests, <1 min)
- `setlists.json` + `build_setlists.py` — per-show setlists for the static pages (incremental)
- `build_pages.py` — **generates** `show/`, `year/`, `pages.css`, `sitemap.xml` (crawlable pages; don't hand-edit)
- `_headers`, `_redirects`, `404.html`, `robots.txt`, `llms.txt`, `opensearch.xml` — Cloudflare Pages / SEO bits
- `.github/workflows/update-shows.yml` — runs every Monday: new shows → setlists → pages → commit

ENGAGE always hits phish.in live — no shows.json needed for playback.  
RANDOM and the archive browser require shows.json.

---

## Setup

### 1. Build shows.json

```bash
python3 generate_phish.py --dry-run   # show what would change
python3 generate_phish.py             # write shows.json (replaces it; refuses a >5% drop without --force)
python3 build_setlists.py             # fetch setlists for any new dates
python3 build_pages.py                # regenerate show/year pages + sitemap, then commit
```

### 2. Deploy to Cloudflare Pages

1. Push repo to GitHub
2. Cloudflare Pages → New Project → Connect GitHub repo
3. Build settings: **none** (static site, no build command)
4. Root directory: `/` (or wherever index.html is)
5. Deploy

### 3. Auto-updates (GitHub Actions)

The included workflow runs every Monday and auto-commits updated `shows.json`, setlists and pages when new shows land. Cloudflare Pages auto-deploys on push. It needs `permissions: contents: write` (already set) — without it every run fails at `git push`.

GitHub switches scheduled workflows **off** after 60 days without repo activity. If shows stop updating, check **Actions → Update Phish Show Database** for a "disabled" banner and re-enable it.

To trigger manually: **Actions → Update Phish Show Database → Run workflow**

---

## Architecture

```
phish.in API ──→ ENGAGE (live fetch by date)
shows.json   ──→ RANDOM, archive browser, ← / → navigation
localStorage ──→ FAVE SHOWS (saved in browser)
```

---

## Credits

- Audio: [phish.in](https://phish.in) open source Phish archive  
- Built by [NeonDeadhead](https://neondeadhead.com)
