# DIAL·A·PHISH

Stream any Phish show free. Enter a date. Hear the show.  
Audio via [phish.in](https://phish.in) — no API key required.

**Live at:** https://dialaphish.com (or your Cloudflare Pages URL)  
**Sister site:** https://dialadead.com

---

## How It Works

- `index.html` — single-file app, no build step, no dependencies
- `shows.json` — database of all shows (venue, city, date) for RANDOM + archive
- `generate_phish.py` — Python script that builds shows.json from phish.in API
- `.github/workflows/update-shows.yml` — auto-runs every Monday to catch new tour dates

ENGAGE always hits phish.in live — no shows.json needed for playback.  
RANDOM and the archive browser require shows.json.

---

## Setup

### 1. Build shows.json

```bash
python generate_phish.py
```

Takes ~2–3 minutes to pull all years. Outputs `shows.json`.

### 2. Deploy to Cloudflare Pages

1. Push repo to GitHub
2. Cloudflare Pages → New Project → Connect GitHub repo
3. Build settings: **none** (static site, no build command)
4. Root directory: `/` (or wherever index.html is)
5. Deploy

### 3. Auto-updates (GitHub Actions)

The included workflow runs every Monday and auto-commits an updated `shows.json` if new shows were added. Cloudflare Pages auto-deploys on push.

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
