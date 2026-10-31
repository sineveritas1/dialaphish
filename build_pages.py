#!/usr/bin/env python3
"""
build_pages.py — write the static, crawlable pages search engines index.

The app is one index.html that draws everything with JS, and every show lives
at /?date=YYYY-MM-DD, which nothing links to — so search engines have nothing
to index. This writes plain HTML that reads without JS:

    show/YYYY-MM-DD.html   one page per show in shows.json  -> /show/YYYY-MM-DD
    year/YYYY.html         every show that year, linked     -> /year/YYYY
    pages.css              the one stylesheet they share
    sitemap.xml            the homepage, every year and every show

Cloudflare Pages serves foo.html at /foo, so links carry no extension. Each
show page links into the player at /?date=…; the player sets its canonical
back to /show/… so the two don't compete in search results.

Generated, not hand-edited. Re-run after shows.json or setlists.json change
and commit the output. Makes no network requests.

Usage:
    python3 build_pages.py
"""
import html, json, os, shutil
from collections import defaultdict

SITE = 'https://dialaphish.com'
LOGO = 'https://res.cloudinary.com/dmbeoutyi/image/upload/v1779241581/phish-logo_al1k0a.png'
BRAND = 'https://res.cloudinary.com/dmbeoutyi/image/upload/h_72,c_fit,f_auto,q_auto/v1779241581/phish-logo_al1k0a.png'
MONTHS = ['January','February','March','April','May','June','July','August',
          'September','October','November','December']

esc = lambda s: html.escape(s or '', quote=True)
def long_date(k):
    y, m, d = map(int, k.split('-')); return f'{MONTHS[m-1]} {d}, {y}'
def where(s): return ', '.join(x for x in (s.get('venue'), s.get('city')) if x)

GRAD = 'linear-gradient(90deg,#2E3192,#22B14C,#FFF200,#F7941E,#ED1C24)'
CSS = f"""*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'JetBrains Mono',monospace;color:#1A1A2E;display:flex;justify-content:center;padding:10px;line-height:1.6;min-height:100vh;
background:linear-gradient(160deg,#a8aee8 0%,#8ed8a8 22%,#ede070 48%,#edba78 72%,#ed9898 100%);background-attachment:fixed}}
.machine{{width:100%;max-width:640px;align-self:flex-start;background:#fff;border:2px solid #C8C2B0;border-radius:20px;padding:18px 16px 24px;box-shadow:0 6px 30px rgba(46,49,146,.08),0 2px 8px rgba(0,0,0,.08)}}
a{{color:#2E3192;text-decoration:none}}a:hover{{color:#F7941E}}
.brand{{display:flex;align-items:center;gap:10px;margin-bottom:14px;font-family:'Syne',sans-serif;font-weight:800;letter-spacing:3px;font-size:18px}}
.brand img{{height:36px;width:auto}}
.brand span{{background:{GRAD};-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}}
.crumbs{{font-size:12px;color:#666;margin-bottom:12px}}
h1{{font-family:'Syne',sans-serif;font-size:clamp(18px,5vw,24px);color:#F7941E;letter-spacing:1px;line-height:1.3;margin-bottom:6px}}
h2{{font-family:'Syne',sans-serif;font-size:13px;color:#2E3192;letter-spacing:2px;margin:18px 0 6px}}
.where{{color:#2E3192;font-size:15px;font-weight:700}}.meta{{color:#22B14C;font-size:13px;margin-top:2px;font-weight:700}}
.play{{display:inline-block;margin:16px 0 4px;background:{GRAD};color:#fff;font-family:'Syne',sans-serif;font-weight:700;letter-spacing:2px;padding:12px 18px;border-radius:8px;box-shadow:0 0 20px rgba(168,85,247,.5)}}
.play:hover{{color:#fff;filter:brightness(1.1)}}
ul,ol{{list-style:none}}.set{{font-size:14px}}.set li{{padding:1px 0}}
.shows li{{padding:6px 0;border-bottom:1px solid #EEE9DC;font-size:14px}}.shows .v{{color:#555}}
.nav{{display:flex;justify-content:space-between;gap:10px;margin-top:20px;font-size:13px}}
.years{{display:flex;flex-wrap:wrap;gap:6px;font-size:13px}}.years a,.years span{{border:1px solid #DDD8C8;border-radius:4px;padding:2px 7px}}.years span{{background:#F7941E;color:#fff;border-color:#F7941E}}
p{{font-size:14px;margin-top:8px}}.foot{{margin-top:24px;font-size:12px;color:#666;text-align:center}}
html.darkpuddle body{{background:linear-gradient(160deg,#12154a 0%,#0a3018 22%,#2a2600 48%,#2a1200 72%,#2a0606 100%);background-attachment:fixed;color:#DDD}}
html.darkpuddle .machine{{background:#111118;border-color:#2A2A3A}}
html.darkpuddle a,html.darkpuddle .where,html.darkpuddle h2{{color:#9BA0F0}}html.darkpuddle a:hover{{color:#F7941E}}
html.darkpuddle .crumbs,html.darkpuddle .foot,html.darkpuddle .shows .v{{color:#888}}
html.darkpuddle .shows li{{border-color:#1E1E2E}}html.darkpuddle .years a{{border-color:#2A2A3A}}
html.darkpuddle .play{{color:#fff}}"""

def page(title, desc, path, body, ld=None):
    url = SITE + path
    lds = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n' if ld else ''
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/png" href="{LOGO}">
<meta name="theme-color" content="#2E3192">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{LOGO}">
<meta property="og:site_name" content="DIAL·A·PHISH">
<meta name="twitter:card" content="summary">
{lds}<script>try{{if(localStorage.getItem('darkPuddle'))document.documentElement.classList.add('darkpuddle')}}catch(e){{}}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/pages.css">
</head>
<body>
<main class="machine">
<a class="brand" href="/"><img src="{BRAND}" alt="" height="36"><span>DIAL·A·PHISH</span></a>
{body}
<div class="foot"><a href="/">DIAL·A·PHISH</a> · Phish time machine · audio streams free from <a href="https://phish.in">phish.in</a><br>Fan-made site</div>
</main>
</body>
</html>
"""

def year_links(years, cur=None):
    return '<div class="years">' + ''.join(
        f'<span>{y}</span>' if y == cur else f'<a href="/year/{y}">{y}</a>' for y in years) + '</div>'

def load_setlists():
    try: return json.load(open('setlists.json', encoding='utf-8'))
    except (OSError, ValueError): return {}

def show_page(k, s, prev, nxt, sets):
    y = k[:4]; ld_date = long_date(k); w = where(s)
    songs = [t for _, ts in sets for t in ts]
    title = f'Phish {ld_date}' + (f' — {w}' if w else '') + ' | DIAL·A·PHISH'
    desc = (f'Stream the Phish concert from {ld_date}' + (f' at {w}' if w else '')
            + '. Free from phish.in' + (f' — {len(songs)} songs incl. ' + ', '.join(songs[:3]) if songs else '') + '.')
    body = [f'<div class="crumbs"><a href="/">Home</a> › <a href="/year/{y}">{y}</a> › {esc(ld_date)}</div>',
            f'<h1>Phish — {esc(ld_date)}</h1>']
    if w: body.append(f'<div class="where">{esc(w)}</div>')
    body.append('<div class="meta">Audience recording · phish.in</div>')
    body.append(f'<a class="play" href="/?date={k}">▶ PLAY THIS SHOW</a>')
    for name, ts in sets:
        body.append(f'<h2>{esc(name.upper())}</h2><ol class="set">'
                    + ''.join(f'<li>{esc(t)}</li>' for t in ts) + '</ol>')
    nav = []
    nav.append(f'<a href="/show/{prev}">← {esc(long_date(prev))}</a>' if prev else '<span></span>')
    nav.append(f'<a href="/show/{nxt}">{esc(long_date(nxt))} →</a>' if nxt else '<span></span>')
    body.append('<div class="nav">' + ''.join(nav) + '</div>')
    ld = {"@context": "https://schema.org", "@type": "MusicEvent",
          "name": f"Phish — {ld_date}", "startDate": k, "endDate": k,
          "description": desc, "image": LOGO, "url": f"{SITE}/show/{k}",
          "eventStatus": "https://schema.org/EventScheduled",
          "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
          "performer": {"@type": "MusicGroup", "name": "Phish"},
          "location": {"@type": "Place", "name": s.get('venue') or 'Unknown venue',
                       "address": s.get('city') or 'Unknown'}}
    return page(title, desc, f'/show/{k}', '\n'.join(body), ld)

def year_page(y, keys, shows, years):
    title = f'Phish {y} — every show | DIAL·A·PHISH'
    desc = f'All {len(keys)} Phish shows from {y} with audio — stream any of them free from phish.in.'
    items = ''.join(f'<li><a href="/show/{k}">{esc(long_date(k))}</a> <span class="v">{esc(where(shows[k]))}</span></li>'
                    for k in keys)
    body = (f'<div class="crumbs"><a href="/">Home</a> › {y}</div><h1>Phish — {y}</h1>'
            f'<p>{len(keys)} shows. Tap one for its setlist, or play it straight away.</p>'
            f'<h2>YEARS</h2>{year_links(years, y)}<h2>SHOWS</h2><ul class="shows">{items}</ul>')
    return page(title, desc, f'/year/{y}', body)

def main():
    shows = json.load(open('shows.json', encoding='utf-8'))
    setlists = load_setlists()
    keys = sorted(shows)
    by_year = defaultdict(list)
    for k in keys: by_year[k[:4]].append(k)
    years = sorted(by_year)
    for d in ('show', 'year'):
        shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    for i, k in enumerate(keys):
        prev = keys[i-1] if i else None
        nxt = keys[i+1] if i + 1 < len(keys) else None
        with open(f'show/{k}.html', 'w', encoding='utf-8') as f:
            f.write(show_page(k, shows[k], prev, nxt, setlists.get(k, [])))
    for y in years:
        with open(f'year/{y}.html', 'w', encoding='utf-8') as f:
            f.write(year_page(y, by_year[y], shows, years))
    with open('pages.css', 'w', encoding='utf-8') as f:
        f.write(CSS + '\n')
    urls = [f'{SITE}/'] + [f'{SITE}/year/{y}' for y in years] + [f'{SITE}/show/{k}' for k in keys]
    with open('sitemap.xml', 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(''.join(f'  <url><loc>{u}</loc></url>\n' for u in urls))
        f.write('</urlset>\n')
    print(f'{len(keys)} show pages, {len(years)} year pages, {len(urls)} sitemap URLs '
          f'({sum(1 for k in keys if setlists.get(k))} with setlists)')

if __name__ == '__main__':
    main()
