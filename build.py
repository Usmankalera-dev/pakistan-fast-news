#!/usr/bin/env python3
"""Pakistan Fast News — builds a fast, SEO-ready static news site from real RSS feeds.
Run: python3 build.py  (fetches Dawn + ARY feeds, writes HTML pages in this folder)
"""
import html as H, json, re, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PKT = ZoneInfo("Asia/Karachi")
BASE = "https://usmankalera-dev.github.io/pakistan-fast-news"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
FEEDS = [
    ("https://www.dawn.com/feeds/home", "Dawn", None),
    ("https://www.dawn.com/feeds/pakistan", "Dawn", "pakistan"),
    ("https://www.dawn.com/feeds/business", "Dawn", "business"),
    ("https://www.dawn.com/feeds/sport", "Dawn", "sports"),
    ("https://www.dawn.com/feeds/world", "Dawn", "world"),
    ("https://www.dawn.com/feeds/tech", "Dawn", "tech"),
    ("https://images.dawn.com/feeds/home", "Dawn Images", "entertainment"),
    ("https://arynews.tv/feed/", "ARY News", None),
]
CATS = ["pakistan", "world", "business", "sports", "tech", "entertainment"]
CAT_LABEL = {"pakistan": "Pakistan", "world": "World", "business": "Business",
             "sports": "Sports", "tech": "Tech", "entertainment": "Entertainment"}
LOGOS = {"Dawn": ("logo-dawn.png", 84, 20), "ARY News": ("logo-ary.svg", 22, 24),
         "Dawn Images": ("logo-dawn.png", 84, 20)}
NS = {"media": "http://search.yahoo.com/mrss/"}
KW = {
    "sports": ["cricket", "football", "hockey", "psl", "match", "tournament", "athlete", "olympic", "fifa", "tennis", "badminton", "squash", "snooker", "world cup", "t20", "odi", "test match", "batsman", "bowler", "pcb", "fifa", "champions trophy"],
    "business": ["economy", "rupee", "dollar", "imf", "stock", "market", "trade", "inflation", "budget", "tax", "gdp", "remittance", "petrol", "diesel", "interest rate", "sbp", "psx", "business", "exports", "imports", "tariff"],
    "tech": [" ai ", "technology", "tech ", "smartphone", "internet", "cyber", "google", "apple", "meta", "software", "digital", "5g", "satellite", "robot", "chip", "openai", "chatgpt"],
    "entertainment": ["film", "drama", "actor", "actress", "singer", "showbiz", "music", "bollywood", "lollywood", "movie", "song", "concert", "celebrity", "netflix"],
}
PK_KW = ["pakistan", "lahore", "karachi", "islamabad", "punjab", "sindh", "khyber", "balochistan", "peshawar", "quetta", "shehbaz", "imran khan", "pti", "pml-n", "ppp", "court", "parliament", "senate", "assembly", "supreme court", "ecp", "nab", "fbr", "army", "ISPR".lower(), "govt", "cabinet", "pm ", "president"]

def clean(txt):
    txt = H.unescape(re.sub(r"<[^>]+>", " ", txt or ""))
    return re.sub(r"\s+", " ", txt).strip()

def categorize(title, desc, feed_cat):
    if feed_cat:
        return feed_cat
    t = " " + (title + " " + desc).lower() + " "
    for cat, kws in KW.items():
        if any(k in t for k in kws):
            return cat
    if any(k in t for k in PK_KW):
        return "pakistan"
    return "world"

def fetch():
    items, seen = [], set()
    for url, source, feed_cat in FEEDS:
        try:
            req = urllib.request.Request(url, headers=UA)
            data = urllib.request.urlopen(req, timeout=20).read()
            # some feeds ship bare & in titles; escape them so the XML parses
            data = re.sub(rb"&(?!(?:amp|lt|gt|quot|apos);|#\d+;|#x[0-9a-fA-F]+;)", b"&amp;", data)
            root = ET.fromstring(data)
        except Exception as e:
            print("feed failed:", url, e)
            continue
        for it in root.iter("item"):
            title = clean(it.findtext("title"))
            link = (it.findtext("link") or "").strip()
            if not title or not link:
                continue
            key = " ".join(re.sub(r"[^a-z0-9 ]", "", title.lower()).split()[:7])
            if key in seen:
                continue
            seen.add(key)
            raw_date = it.findtext("pubDate") or ""
            try:
                dt = parsedate_to_datetime(raw_date)
            except Exception:
                try:
                    dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                except Exception:
                    dt = datetime.now(PKT)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt = dt.astimezone(PKT)
            desc = clean(it.findtext("description"))[:400]
            img = None
            mc = it.find("media:content", NS)
            if mc is None:
                mc = it.find("media:thumbnail", NS)
            if mc is not None:
                img = mc.get("url")
            items.append({"title": title, "link": link, "dt": dt, "desc": desc,
                          "source": source, "cat": categorize(title, desc, feed_cat), "img": img})
    items.sort(key=lambda x: x["dt"], reverse=True)
    return items

def rel(dt, now):
    mins = max(0, int((now - dt).total_seconds() // 60))
    if mins < 1: return "just now"
    if mins < 60: return f"{mins}m ago"
    h = mins // 60
    if h < 24: return f"{h}h ago"
    return f"{h // 24}d ago"

def card(it, now, big=False):
    cls = "card hero" if big else "card"
    logo, lw, lh = LOGOS.get(it["source"], ("logo-dawn.png", 84, 20))
    thumb = ""
    if it.get("img"):
        thumb = (f"<a class=\"thumbwrap\" href=\"{H.escape(it['link'])}\" target=\"_blank\" rel=\"noopener\" tabindex=\"-1\" aria-hidden=\"true\">"
                 f"<img class=\"thumb\" src=\"{H.escape(it['img'])}\" alt=\"\" loading=\"lazy\" onerror=\"this.closest('.thumbwrap').remove()\"></a>")
    return (f'<article class="{cls}">{thumb}<div class="meta">'
            f'<img class="srclogo" src="{logo}" alt="{H.escape(it["source"])} logo" width="{lw}" height="{lh}" loading="lazy">'
            f'<span class="src">{H.escape(it["source"])}</span>'
            f'<span class="chip {it["cat"]}">{CAT_LABEL[it["cat"]]}</span>'
            f'<time datetime="{it["dt"].isoformat()}">{rel(it["dt"], now)} · {it["dt"].strftime("%d %b %Y, %I:%M %p")} PKT</time></div>'
            f'<h3><a href="{H.escape(it["link"])}" target="_blank" rel="noopener">{H.escape(it["title"])}</a></h3>'
            + (f'<p>{H.escape(it["desc"])}</p>' if it["desc"] else "")
            + f'<a class="readmore" href="{H.escape(it["link"])}" target="_blank" rel="noopener">Read full story at {H.escape(it["source"])} →</a></article>')

def nav(active=""):
    links = [("index.html", "Home")] + [(f"{c}.html", CAT_LABEL[c]) for c in CATS]
    out = []
    for href, label in links:
        cls = ' class="active"' if href == active else ""
        out.append(f'<a href="{href}"{cls}>{label}</a>')
    return "\n".join(out)

def page(title, desc, canon, h1, body_html, json_ld, active="index.html"):
    now_s = datetime.now(PKT).strftime("%d %B %Y, %I:%M %p PKT")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{H.escape(title)}</title>
<meta name="description" content="{H.escape(desc)}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Pakistan Fast News">
<meta property="og:title" content="{H.escape(title)}">
<meta property="og:description" content="{H.escape(desc)}">
<meta property="og:url" content="{canon}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{H.escape(title)}">
<meta name="twitter:description" content="{H.escape(desc)}">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="styles.css">
<script type="application/ld+json">{json_ld}</script>
</head>
<body>
<header class="topbar"><div class="wrap">
<a class="logo" href="index.html"><img src="favicon.svg" alt="" width="26" height="26" class="sitelogo"> Pakistan <b>Fast News</b></a>
<div class="clock"><span id="clock"></span><span class="upd">Updated {now_s}</span></div>
</div></header>
<nav class="mainnav" aria-label="Sections"><div class="wrap">{nav(active)}</div></nav>
<main class="wrap">
<h1>{H.escape(h1)}</h1>
<div class="search"><input id="q" type="search" placeholder="Search headlines…" aria-label="Search headlines"></div>
{body_html}
</main>
<footer><div class="wrap">
<p><b>Pakistan Fast News</b> — the fastest headlines from Pakistan and the world. Headlines link to the original publishers (Dawn, ARY News); we do not copy full articles.</p>
<p class="fine">Source names and logos belong to their publishers (Dawn, ARY News). Headlines and images link to the original stories.</p>
<p class="fine">Sections: {", ".join(f'<a href="{c}.html">{CAT_LABEL[c]}</a>' for c in CATS)} · Updated {now_s} · Built for speed: no ads, no trackers, no heavy scripts.</p>
</div></footer>
<script src="script.js" defer></script>
</body>
</html>
"""

def main():
    out_dir = Path(__file__).parent
    items = fetch()
    now = datetime.now(PKT)
    print("items:", len(items), "| by cat:", {c: sum(1 for i in items if i["cat"] == c) for c in CATS})
    by_cat = {c: [i for i in items if i["cat"] == c] for c in CATS}
    today = now.strftime("%Y-%m-%d")

    org_ld = {"@context": "https://schema.org", "@type": "NewsMediaOrganization",
              "name": "Pakistan Fast News", "url": BASE + "/",
              "logo": {"@type": "ImageObject", "url": BASE + "/favicon.svg"}}

    # ---- Home ----
    hero = items[0]
    rest = items[1:19]
    sections = ""
    for c in CATS:
        lst = by_cat[c][:4]
        if len(lst) < 2:
            continue
        sections += f'<section><h2>{CAT_LABEL[c]} <a class="more" href="{c}.html">More →</a></h2><div class="grid">{"".join(card(i, now) for i in lst)}</div></section>'
    home_body = (f'<section><h2>Top story</h2>{card(hero, now, big=True)}</section>'
                 f'<section><h2>Latest headlines</h2><div class="grid" id="latest">{"".join(card(i, now) for i in rest)}</div></section>'
                 + sections)
    hero_ld = {"@context": "https://schema.org", "@type": "NewsArticle",
               "headline": hero["title"], "datePublished": hero["dt"].isoformat(),
               "dateModified": hero["dt"].isoformat(), "author": {"@type": "Organization", "name": hero["source"]},
               "publisher": org_ld, "mainEntityOfPage": hero["link"], "url": hero["link"]}
    site_ld = {"@context": "https://schema.org", "@type": "WebSite", "name": "Pakistan Fast News",
               "url": BASE + "/", "inLanguage": "en"}
    home_ld = json.dumps([site_ld, org_ld, hero_ld], ensure_ascii=False)
    (out_dir / "index.html").write_text(page(
        "Pakistan Fast News — Latest Pakistan News, Fast",
        "The fastest Pakistan news headlines — politics, business, sports, tech and world news, updated around the clock from Dawn and ARY News.",
        BASE + "/", "Latest headlines from Pakistan", home_body, home_ld, "index.html"), encoding="utf-8")

    # ---- Category pages ----
    for c in CATS:
        lst = by_cat[c][:30]
        ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": f"{CAT_LABEL[c]} News — Pakistan Fast News",
              "url": f"{BASE}/{c}.html",
              "hasPart": [{"@type": "NewsArticle", "headline": i["title"], "datePublished": i["dt"].isoformat(), "url": i["link"]} for i in lst[:10]]}
        body = (f'<p class="crumb"><a href="index.html">Home</a> / {CAT_LABEL[c]}</p>'
                f'<div class="grid">{"".join(card(i, now) for i in lst)}</div>' if lst else
                '<p>No stories in this section yet — check back soon.</p>')
        (out_dir / f"{c}.html").write_text(page(
            f"{CAT_LABEL[c]} News — Pakistan Fast News",
            f"Latest {CAT_LABEL[c].lower()} news from Pakistan and the world, updated fast. Headlines from Dawn and ARY News.",
            f"{BASE}/{c}.html", f"{CAT_LABEL[c]} news", body, json.dumps(ld, ensure_ascii=False), f"{c}.html"), encoding="utf-8")

    # ---- sitemap + robots + 404 ----
    urls = [("", "1.0")] + [(f"{c}.html", "0.8") for c in CATS]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, pr in urls:
        sm.append(f"<url><loc>{BASE}/{u}</loc><lastmod>{today}</lastmod><priority>{pr}</priority></url>")
    sm.append("</urlset>")
    (out_dir / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")
    (out_dir / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")
    (out_dir / "404.html").write_text(page(
        "Page not found — Pakistan Fast News", "This page does not exist on Pakistan Fast News.",
        BASE + "/", "Page not found",
        '<p>That page is gone. <a href="index.html">Back to the latest headlines →</a></p>',
        json.dumps(site_ld, ensure_ascii=False)), encoding="utf-8")
    print("built", today)

if __name__ == "__main__":
    main()
