#!/usr/bin/env python3
"""Pakistan Fast News — builds a fast, SEO-ready static news site from real RSS feeds.
Run: python3 build.py  (fetches Dawn + ARY feeds, writes HTML pages in this folder)
"""
import html as H, json, re, urllib.request, xml.etree.ElementTree as ET
from urllib.parse import quote as urlquote
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
    ("https://feeds.bbci.co.uk/news/rss.xml", "BBC News", None),
    ("https://feeds.bbci.co.uk/news/world/asia/rss.xml", "BBC News", None),
    ("https://www.thenews.com.pk/rss/1/2", "The News", "world"),
    ("https://www.thenews.com.pk/rss/1/3", "The News", "sports"),
    ("https://www.thenews.com.pk/rss/1/4", "The News", "business"),
]
CATS = ["pakistan", "world", "business", "sports", "tech", "entertainment"]
YT_CHANNELS = [
    ("Geo News", "UC_vt34wimdCzdkrzVejwX9g", "geo"),
    ("ARY News", "UCMmpLL2ucRHAXbNHiCPyIyg", "ary"),
    ("Dawn News", "UCaxR-D8FjZ-2otbU0_Y2grg", "dawn"),
    ("Samaa TV", "UCJekW1Vj5fCVEGdye_mBN6Q", "samaa"),
    ("Dunya News", "UCnMBV5Iw4WqKILKue1nP6Hg", "dunya"),
    ("Express News", "UCTur7oM6mLL0rM2k0znuZpQ", "express"),
    ("Hum News", "UC0Um3pnZ2WGBEeoA3BX2sKw", "hum"),
    ("BOL News", "UC2ToZG9RA1_A5kRwxqP7rZg", "bol"),
    ("92 News HD", "UCsgC5cbz3DE2Shh34gNKiog", "92news"),
    ("Aaj News", "UCgBAPAcLsh_MAPvJprIz89w", "aaj"),
    ("Neo News", "UCoVaeayixjVI12mAlmMSsXg", "neo"),
]
CAT_LABEL = {"pakistan": "Pakistan", "world": "World", "business": "Business",
             "sports": "Sports", "tech": "Tech", "entertainment": "Entertainment"}
CAT_EMOJI = {"pakistan": "🇵🇰", "world": "🌍", "business": "💼",
             "sports": "🏏", "tech": "💻", "entertainment": "🎬"}
LOGOS = {"Dawn": ("logo-dawn.png", 84, 20), "ARY News": ("logo-ary.svg", 22, 24),
         "Dawn Images": ("logo-dawn.png", 84, 20),
         "BBC News": ("logo-bbc.gif", 40, 20), "The News": ("logo-thenews.svg", 63, 20)}
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
            if "bbc.co.uk" in link or "bbc.com" in link:
                link = link.split("?")[0]  # drop BBC's RSS tracking params
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
            raw_desc = it.findtext("description") or ""
            desc = clean(raw_desc)[:400]
            img = None
            mc = it.find("media:content", NS)
            if mc is None:
                mc = it.find("media:thumbnail", NS)
            if mc is not None:
                img = mc.get("url")
            if not img:  # The News embeds its photo inside the description HTML
                m = re.search(r'<img[^>]+src="([^"]+)"', raw_desc)
                if m:
                    img = m.group(1)
            items.append({"title": title, "link": link, "dt": dt, "desc": desc,
                          "source": source, "cat": categorize(title, desc, feed_cat), "img": img})
    items.sort(key=lambda x: x["dt"], reverse=True)
    return items

YTNS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015",
        "m": "http://search.yahoo.com/mrss/"}

def fetch_videos():
    videos = []
    for name, cid, slug in YT_CHANNELS:
        try:
            req = urllib.request.Request(
                f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}", headers=UA)
            data = urllib.request.urlopen(req, timeout=20).read()
            root = ET.fromstring(data)
        except Exception as e:
            print("yt feed failed:", name, e)
            continue
        for e in root.findall("a:entry", YTNS):
            vid = e.findtext("yt:videoId", namespaces=YTNS)
            title = clean(e.findtext("a:title", namespaces=YTNS))
            link = None
            for ln in e.findall("a:link", YTNS):
                if ln.get("rel") == "alternate":
                    link = ln.get("href")
            try:
                dt = datetime.fromisoformat((e.findtext("a:published", namespaces=YTNS) or "").replace("Z", "+00:00"))
                dt = dt.astimezone(PKT)
            except Exception:
                dt = datetime.now(PKT)
            th = e.find("m:group/m:thumbnail", YTNS)
            thumb = th.get("url") if th is not None else (f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" if vid else None)
            desc = clean(e.findtext("m:group/m:description", namespaces=YTNS))[:160]
            if vid and title:
                videos.append({"vid": vid, "title": title, "link": link or f"https://www.youtube.com/watch?v={vid}",
                               "dt": dt, "thumb": thumb, "desc": desc, "channel": name, "slug": slug})
    videos.sort(key=lambda x: x["dt"], reverse=True)
    return videos

def rel(dt, now):
    mins = max(0, int((now - dt).total_seconds() // 60))
    if mins < 1: return "just now"
    if mins < 60: return f"{mins}m ago"
    h = mins // 60
    if h < 24: return f"{h}h ago"
    return f"{h // 24}d ago"

def suno_btn(text, lang, label):
    """One listen button per card (browser speechSynthesis, no key, no paid TTS)."""
    return (f'<button class="suno-btn" type="button" data-speak="{H.escape(text, quote=True)}" '
            f'data-lang="{lang}">{label}</button>')


def share_row(it):
    enc = urlquote(it["title"] + " " + it["link"])
    fb = urlquote(it["link"])
    return (f'<div class="share"><a class="share-wa" href="https://wa.me/?text={enc}" target="_blank" rel="noopener">WhatsApp ↗</a>'
            f'<a class="share-x" href="https://twitter.com/intent/tweet?text={enc}" target="_blank" rel="noopener">X ↗</a>'
            f'<a class="share-fb" href="https://www.facebook.com/sharer/sharer.php?u={fb}" target="_blank" rel="noopener">Facebook ↗</a>'
            f'<button class="share-copy" type="button" data-link="{H.escape(it["link"])}">Copy link</button>'
            f'<button class="share-native" type="button" data-title="{H.escape(it["title"])}" data-link="{H.escape(it["link"])}">Share</button></div>')


def ticker(items, label):
    seq = "".join(f'<a href="{H.escape(i["link"])}" target="_blank" rel="noopener">{H.escape(i["title"])}</a><span class="ticker-sep">•</span>' for i in items)
    return (f'<div class="ticker"><span class="ticker-label">{H.escape(label)}</span>'
            f'<div class="ticker-viewport"><div class="ticker-track">{seq}{seq}</div></div></div>')


def card(it, now, big=False):
    logo, lw, lh = LOGOS.get(it["source"], ("logo-dawn.png", 84, 20))
    link = H.escape(it["link"])
    meta = (f'<div class="meta">'
            f'<img class="srclogo" src="{logo}" alt="{H.escape(it["source"])} logo" width="{lw}" height="{lh}" loading="lazy">'
            f'<span class="src">{H.escape(it["source"])}</span>'
            f'<span class="chip {it["cat"]}">{CAT_LABEL[it["cat"]]}</span>'
            f'<time datetime="{it["dt"].isoformat()}">{rel(it["dt"], now)} · {it["dt"].strftime("%d %b %Y, %I:%M %p")} PKT</time></div>')
    title = f'<h3><a href="{link}" target="_blank" rel="noopener">{H.escape(it["title"])}</a></h3>'
    desc = (f'<p>{H.escape(it["desc"])}</p>' if it["desc"] else "")
    readmore = f'<a class="readmore" href="{link}" target="_blank" rel="noopener">Read full story at {H.escape(it["source"])} →</a>'
    if big and it.get("img"):
        return (f'<article class="card hero heroimg cat-{it["cat"]}">'
                f'<div class="herowrap"><a class="heropic" href="{link}" target="_blank" rel="noopener" tabindex="-1" aria-hidden="true">'
                f'<img src="{H.escape(it["img"])}" alt="" loading="eager" onerror="this.closest(\'.herowrap\').classList.add(\'imgfail\');this.closest(\'article\').classList.add(\'hero-noimg\')"></a>'
                f'<span class="herograd"></span>'
                f'<div class="heroover">{title}</div></div>'
                f'<div class="herobody">{meta}{desc}{readmore}' + share_row(it) + suno_btn(it["title"] + ". " + it.get("desc", ""), "en", "🔊 Listen") + '</div></article>')
    thumb = ""
    if it.get("img"):
        thumb = (f"<a class=\"thumbwrap\" href=\"{link}\" target=\"_blank\" rel=\"noopener\" tabindex=\"-1\" aria-hidden=\"true\">"
                 f"<img class=\"thumb\" src=\"{H.escape(it['img'])}\" alt=\"\" loading=\"lazy\" onerror=\"this.closest('.thumbwrap').remove()\"></a>")
    cls = "card hero" if big else "card"
    return (f'<article class="{cls} cat-{it["cat"]}">{thumb}{meta}{title}{desc}{readmore}' + share_row(it) + suno_btn(it["title"] + ". " + it.get("desc", ""), "en", "🔊 Listen") + '</article>')

def load_editorial(lang):
    """Original news written by Usman, newest first. File: editorial.json (repo root)."""
    try:
        data = json.loads((Path(__file__).parent / "editorial.json").read_text(encoding="utf-8"))
        items = [i for i in data.get("items", []) if i.get("lang", "en") == lang]
    except Exception:
        items = []
    items.sort(key=lambda i: i.get("date", ""), reverse=True)
    return items


def ed_card(it, now, idx, base_url):
    """One original-news card. Share links point at the editorial page anchor."""
    dt = datetime.fromisoformat(it["date"]).replace(tzinfo=PKT, hour=12, minute=0)
    link = f"{base_url}#ed-{idx}"
    meta = (f'<div class="meta">'
            f'<span class="src">✍️ Usman Kalera</span>'
            f'<span class="chip {it.get("cat", "pakistan")}">{CAT_LABEL[it.get("cat", "pakistan")]}</span>'
            f'<time datetime="{it["date"]}">{rel(dt, now)} · {dt.strftime("%d %b %Y")} PKT</time></div>')
    return (f'<article class="card cat-{it.get("cat", "pakistan")}" id="ed-{idx}">{meta}'
            f'<h3>{H.escape(it["title"])}</h3>'
            f'<p>{H.escape(it["body"])}</p>' + share_row({"title": it["title"], "link": link}) + suno_btn(it["title"] + ". " + it.get("body", ""), "en", "🔊 Listen") + '</article>')


def nav(active=""):
    links = [("index.html", "Home")] + [(f"{c}.html", CAT_LABEL[c]) for c in CATS] + [("editorial.html", "✍️ Exclusive"), ("videos.html", "Videos"), ("live-tv.html", "📺 Live TV"), ("prayer.html", "🕌 Prayer Times"), ("ur/index.html", "اردو")]
    out = []
    for href, label in links:
        cls = ' class="active"' if href == active else ""
        if href == "videos.html":
            label = "▶ Videos"
            cls = ' class="vidlink active"' if href == active else ' class="vidlink"'
        out.append(f'<a href="{href}"{cls}>{label}</a>')
    return "\n".join(out)

def newsletter_box(box_id=""):
    """Free FormSubmit signup (no account). Activation: Usman clicks the one
    confirmation email FormSubmit sends to his university inbox after the first signup."""
    idattr = f' id="{box_id}"' if box_id else ""
    return (f'<div class="newsbox"{idattr}>'
            '<h3>📬 Get the headlines in your inbox</h3>'
            '<p>One short email a day — the fastest Pakistan headlines, free. No spam, unsubscribe anytime.</p>'
            '<form action="https://formsubmit.co/su92-bsaim-f25-025@superior.edu.pk" method="POST">'
            '<input type="hidden" name="_subject" value="New subscriber — Pakistan Fast News">'
            '<input type="hidden" name="_template" value="table">'
            '<input type="hidden" name="_captcha" value="false">'
            '<input type="hidden" name="_autoresponse" value="Thank you for subscribing to Pakistan Fast News! You will get the fastest headlines from Pakistan and the world in your inbox. — Usman Kalera">'
            '<input type="email" name="email" placeholder="Your email address" required aria-label="Email address">'
            '<button type="submit">Subscribe</button></form>'
            '<p class="fine">Powered by FormSubmit — your email is only used for this newsletter.</p></div>')


def page(title, desc, canon, h1, body_html, json_ld, active="index.html", ticker=""):
    now_s = datetime.now(PKT).strftime("%d %B %Y, %I:%M %p PKT")
    fsecs = "".join(f'<li><a href="{c}.html">{CAT_LABEL[c]}</a></li>' for c in CATS)
    fsecs += '<li><a href="editorial.html">✍️ Exclusive</a></li>'
    fsecs += '<li><a href="videos.html">▶ Videos</a></li>'
    fsecs += '<li><a href="live-tv.html">📺 Live TV</a></li>'
    fsecs += '<li><a href="prayer.html">🕌 Prayer Times</a></li>'
    fchans = "".join(
        f'<li><a class="fchan" href="videos.html#{slug}"><img src="yt-{slug}.jpg" alt="" width="22" height="22" loading="lazy">{name}</a></li>'
        for name, _cid, slug in YT_CHANNELS)
    footer_html = (
        '<footer><div class="wrap"><div class="fgrid">'
        '<div class="fcol fbrand"><a class="flogo" href="index.html"><img src="favicon.svg" alt="" width="38" height="38"> Pakistan <b>Fast News</b></a>'
        '<p>The fastest headlines from Pakistan and the world — politics, business, sports, tech and entertainment, updated around the clock.</p>'
        '<p>Fast and free: no ads, no trackers, no heavy scripts.</p></div>'
        '<div class="fcol"><h4>Sections</h4><ul>' + fsecs + '</ul></div>'
        '<div class="fcol fwatch"><h4>Watch</h4><ul>' + fchans + '</ul></div>'
        '<div class="fcol fsources"><h4>Sources</h4><p>Headlines from:</p>'
        '<span class="srclogochip"><img src="logo-dawn.png" alt="Dawn logo" height="22"></span>'
        '<span class="srclogochip"><img src="logo-ary.svg" alt="ARY News logo" height="28"></span>'
        '<span class="srclogochip"><img src="logo-bbc.gif" alt="BBC News logo" height="22"></span>'
        '<span class="srclogochip"><img src="logo-thenews.svg" alt="The News logo" height="22"></span>'
        '<p class="fine">Full stories open on the publishers\u2019 sites — we never copy full articles. Videos play from the channels\u2019 official YouTube channels.</p></div>'
        '</div>' + newsletter_box() + '<div class="fbot"><span>© 2026 Pakistan Fast News</span>'
        '<span>Updated ' + now_s + ' · <a href="sitemap.xml">Sitemap</a></span></div></div></footer>')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>try{{var f=localStorage.getItem("pfn-fss");if(f)document.documentElement.style.setProperty("--fss",f);var t=localStorage.getItem("pfn-theme");if(t){{document.documentElement.setAttribute("data-theme",t)}}else if(window.matchMedia("(prefers-color-scheme: dark)").matches){{document.documentElement.setAttribute("data-theme","dark")}}}}catch(e){{}}</script>
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
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#c8102e">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@700;800;900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css?v=20261111r1">
<script type="application/ld+json">{json_ld}</script>
</head>
<body>
<header class="topbar"><div class="wrap">
<a class="logo" href="index.html"><img src="favicon.svg" alt="Pakistan Fast News logo" width="36" height="36" class="sitelogo"><span class="logotext">Pakistan <b>Fast News</b><small>Pakistan's fastest headlines</small></span></a>
<div class="clock"><span class="livedot" aria-hidden="true"></span><b>LIVE</b> <span id="clock"></span><span class="upd">Updated {now_s}</span></div>
<button id="theme-toggle" class="themetoggle" type="button" aria-label="Dark mode">🌙</button>
<span class="fss"><button id="fs-minus" class="fsbtn" type="button" aria-label="Smaller text">A−</button><button id="fs-plus" class="fsbtn" type="button" aria-label="Larger text">A+</button></span>
</div></header>
<nav class="mainnav" aria-label="Sections"><div class="wrap">{nav(active)}</div></nav>
{ticker}<main class="wrap">
<div class="today" id="today-widget" role="status">
<div class="trow"><span class="tlabel">💵 Dollar</span><span class="tval">$1 = <span id="w-usd">…</span><span class="conv"><input id="w-conv" type="number" value="10" min="0" inputmode="decimal" aria-label="Amount"> <select id="w-cur" aria-label="Currency"><option value="USD" selected>USD</option><option value="GBP">GBP</option><option value="EUR">EUR</option><option value="SAR">SAR</option><option value="AED">AED</option><option value="CNY">CNY</option></select> = <b id="w-conv-out">…</b></span></span></div>
<div class="trow"><span class="tlabel">💱 Currencies</span><span class="tval" id="w-fx">…</span></div>
<div class="trow"><span class="tlabel">🌙 Hijri date</span><span class="tval" id="w-hijri">…</span></div>
<div class="trow"><span class="tlabel">🪙 Gold · 1 tola</span><span class="tval" id="w-gold">…</span></div>
<div class="trow"><span class="tlabel">🌤️ Weather</span><span class="tval" id="w-weather">…</span></div>
<div class="trow"><span class="tlabel">🕌 Prayer</span><span class="tval"><span class="pcities"><button type="button" class="pcity active" data-city="Lahore">Lahore</button><button type="button" class="pcity" data-city="Karachi">Karachi</button><button type="button" class="pcity" data-city="Islamabad">Islamabad</button></span><span id="w-prayer">…</span></span></div>
<div class="trow"><span class="tlabel">📅 Lahore · 7 days</span><span class="tval"><span class="fgrid" id="w-forecast"></span></span></div>
<div class="tsrc" id="w-updated"></div>
</div>
<h1>{H.escape(h1)}</h1>
<div class="search"><span class="searchicon" aria-hidden="true">🔍</span><input id="q" type="search" placeholder="Search headlines…" aria-label="Search headlines"></div>
{body_html}
</main>
{footer_html}
<script src="script.js" defer></script>
<button id="totop" class="totop" type="button" aria-label="Back to top">↑</button>
</body>
</html>
"""

PRAYER_BODY_EN = '<p class="crumb"><a href="index.html">Home</a> / Prayer Times</p><p class="vintro">Monthly prayer timetable — Fajr to Isha for Lahore, Karachi and Islamabad. Times come live from the Aladhan prayer-times API (calculation method: University of Islamic Sciences, Karachi).</p><div class="prayerctl"><span class="pcities" id="prayer-cities"><button type="button" class="pcity active" data-city="Lahore">Lahore</button><button type="button" class="pcity" data-city="Karachi">Karachi</button><button type="button" class="pcity" data-city="Islamabad">Islamabad</button></span><span class="monthnav"><button type="button" id="pmonth-prev" aria-label="Previous month">‹ Prev</button><b id="pmonth-label">…</b><button type="button" id="pmonth-next" aria-label="Next month">Next ›</button></span></div><div class="ptable-wrap"><table class="ptable" id="prayer-table"><thead><tr><th>Day</th><th>Date</th><th>Fajr</th><th>Sunrise</th><th>Dhuhr</th><th>Asr</th><th>Maghrib</th><th>Isha</th></tr></thead><tbody><tr><td colspan="8" class="ploading">Loading prayer times…</td></tr></tbody></table></div><p class="fine">Source: Aladhan prayer times API · All times local (PKT). Hijri dates are shown under each Gregorian date.</p><script>\n(function(){\n  var months=["January","February","March","April","May","June","July","August","September","October","November","December"];\n  var city="Lahore";\n  var now=new Date(new Date().toLocaleString("en-US",{timeZone:"Asia/Karachi"}));\n  var year=now.getFullYear(), month=now.getMonth()+1;\n  function fmt12(t){var p=String(t).replace(/\\(.*\\)/,"").trim().split(":");var h=+p[0],m=p[1];var ap=h>=12?"PM":"AM";h=h%12;if(h===0)h=12;return h+":"+m+" "+ap;}\n  function load(){\n    document.getElementById("pmonth-label").textContent=months[month-1]+" "+year;\n    var tb=document.querySelector("#prayer-table tbody");\n    tb.innerHTML=\'<tr><td colspan="8" class="ploading">Loading prayer times…</td></tr>\';\n    fetch("https://api.aladhan.com/v1/calendarByCity/"+year+"/"+month+"?city="+encodeURIComponent(city)+"&country=Pakistan&method=1")\n      .then(function(r){if(!r.ok)throw new Error("http "+r.status);return r.json();}).then(function(d){\n        if(!d||!d.data||!d.data.length)throw new Error("empty");\n        var today=new Date(new Date().toLocaleString("en-US",{timeZone:"Asia/Karachi"}));\n        var rows=d.data.map(function(day){\n          var g=day.date.gregorian,hj=day.date.hijri,t=day.timings;\n          var isToday=(+g.day===today.getDate()&&+g.month.number===today.getMonth()+1&&+g.year===today.getFullYear());\n          return \'<tr\'+(isToday?\' class="today-row"\':\'\')+\'><td>\'+g.weekday.en.slice(0,3)+\'</td><td><b>\'+g.day+\' \'+g.month.en+\'</b><br><small>\'+hj.day+\' \'+hj.month.en+\' \'+hj.year+\' AH</small></td><td>\'+fmt12(t.Fajr)+\'</td><td>\'+fmt12(t.Sunrise)+\'</td><td>\'+fmt12(t.Dhuhr)+\'</td><td>\'+fmt12(t.Asr)+\'</td><td>\'+fmt12(t.Maghrib)+\'</td><td>\'+fmt12(t.Isha)+\'</td></tr>\';\n        });\n        tb.innerHTML=rows.join("");\n      }).catch(function(){\n        tb.innerHTML=\'<tr><td colspan="8" class="ploading">Could not load prayer times right now — please check your connection and try again.</td></tr>\';\n      });\n  }\n  document.querySelectorAll("#prayer-cities .pcity").forEach(function(b){b.addEventListener("click",function(){city=b.getAttribute("data-city");document.querySelectorAll("#prayer-cities .pcity").forEach(function(x){x.classList.toggle("active",x===b);});load();});});\n  document.getElementById("pmonth-prev").addEventListener("click",function(){month--;if(month<1){month=12;year--;}load();});\n  document.getElementById("pmonth-next").addEventListener("click",function(){month++;if(month>12){month=1;year++;}load();});\n  load();\n})();\n</script>'


LIVE_TV_BODY_EN = '<p class="crumb"><a href="index.html">Home</a> / Live TV</p><p class="vintro">Watch Pakistan’s top news channels live — straight from their official YouTube live streams. Pick a channel below; the stream loads right here on this page.</p><div class="tvplayer" id="tvplayer"><p class="tvhint">▶ Select a channel below to start its live stream.</p></div><div class="tvgrid"><article class="tvcard"><img src="yt-geo.jpg" alt="Geo News logo" width="64" height="64" loading="lazy"><h3>Geo News</h3><button class="tvbtn" type="button" data-ch="UC_vt34wimdCzdkrzVejwX9g" data-name="Geo News">▶ Watch live</button><a href="https://www.youtube.com/channel/UC_vt34wimdCzdkrzVejwX9g" target="_blank" rel="noopener">Open on YouTube ↗</a></article><article class="tvcard"><img src="yt-ary.jpg" alt="ARY News logo" width="64" height="64" loading="lazy"><h3>ARY News</h3><button class="tvbtn" type="button" data-ch="UCMmpLL2ucRHAXbNHiCPyIyg" data-name="ARY News">▶ Watch live</button><a href="https://www.youtube.com/channel/UCMmpLL2ucRHAXbNHiCPyIyg" target="_blank" rel="noopener">Open on YouTube ↗</a></article><article class="tvcard"><img src="yt-dawn.jpg" alt="Dawn News logo" width="64" height="64" loading="lazy"><h3>Dawn News</h3><button class="tvbtn" type="button" data-ch="UCaxR-D8FjZ-2otbU0_Y2grg" data-name="Dawn News">▶ Watch live</button><a href="https://www.youtube.com/channel/UCaxR-D8FjZ-2otbU0_Y2grg" target="_blank" rel="noopener">Open on YouTube ↗</a></article><article class="tvcard"><img src="yt-samaa.jpg" alt="Samaa TV logo" width="64" height="64" loading="lazy"><h3>Samaa TV</h3><button class="tvbtn" type="button" data-ch="UCJekW1Vj5fCVEGdye_mBN6Q" data-name="Samaa TV">▶ Watch live</button><a href="https://www.youtube.com/channel/UCJekW1Vj5fCVEGdye_mBN6Q" target="_blank" rel="noopener">Open on YouTube ↗</a></article><article class="tvcard"><img src="yt-dunya.jpg" alt="Dunya News logo" width="64" height="64" loading="lazy"><h3>Dunya News</h3><button class="tvbtn" type="button" data-ch="UCnMBV5Iw4WqKILKue1nP6Hg" data-name="Dunya News">▶ Watch live</button><a href="https://www.youtube.com/channel/UCnMBV5Iw4WqKILKue1nP6Hg" target="_blank" rel="noopener">Open on YouTube ↗</a></article><article class="tvcard"><img src="yt-express.jpg" alt="Express News logo" width="64" height="64" loading="lazy"><h3>Express News</h3><button class="tvbtn" type="button" data-ch="UCTur7oM6mLL0rM2k0znuZpQ" data-name="Express News">▶ Watch live</button><a href="https://www.youtube.com/channel/UCTur7oM6mLL0rM2k0znuZpQ" target="_blank" rel="noopener">Open on YouTube ↗</a></article></div><p class="fine">Streams are the channels’ official YouTube live broadcasts (youtube-nocookie embeds). If a channel is not live right now, YouTube shows its offline message — try another channel.</p><script>\n(function(){\n  var player=document.getElementById("tvplayer");\n  document.querySelectorAll(".tvbtn").forEach(function(b){\n    b.addEventListener("click",function(){\n      var ch=b.getAttribute("data-ch"), name=b.getAttribute("data-name");\n      player.innerHTML=\'<iframe title="Live TV — \'+name+\'" src="https://www.youtube-nocookie.com/embed/live_stream?channel=\'+ch+\'&autoplay=1" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>\';\n      document.querySelectorAll(".tvcard").forEach(function(c){c.classList.toggle("active", c===b.closest(".tvcard"));});\n      player.scrollIntoView({behavior:"smooth", block:"center"});\n    });\n  });\n})();\n</script>'


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
    ed_items = load_editorial("en")
    ed_cards = [ed_card(it, now, i, BASE + "/editorial.html") for i, it in enumerate(ed_items)]
    ed_section = ('<section><h2>✍️ Exclusive <span class="h2note">· written by Usman Kalera</span> <a class="more" href="editorial.html">All →</a></h2><div class="grid">' + "".join(ed_cards[:4]) + '</div></section>' if ed_cards else
                  '<section><h2>✍️ Exclusive <span class="h2note">· written by Usman Kalera</span></h2><p>Our own newsroom is getting ready — the first story is coming soon.</p></section>')
    sections = ""
    for c in CATS:
        lst = by_cat[c][:4]
        if len(lst) < 2:
            continue
        sections += f'<section><h2>{CAT_EMOJI[c]} {CAT_LABEL[c]} <span class="h2note">· newest {rel(max(i["dt"] for i in lst), now)}</span> <a class="more" href="{c}.html">More →</a></h2><div class="grid">{"".join(card(i, now) for i in lst)}</div></section>'
    cricket_strip = ('<section class="cstrip" id="cricket-strip" data-lang="en"><h2>🏏 Cricket live score</h2>'
                     '<div class="cbody"><p class="cloading">Loading live score…</p></div>'
                     '<p class="fine">Live scores: <a href="https://sportscore.com/cricket" target="_blank" rel="noopener">Powered by SportScore</a></p></section>')
    home_body = (f'<section><h2 class="toplabel">Top story</h2>{card(hero, now, big=True)}</section>'
                 + cricket_strip +
                 f'<section><h2>Latest headlines</h2><div class="grid" id="latest">{"".join(card(i, now) for i in rest)}</div></section>'
                 + ed_section + newsletter_box("newsletter") + sections)
    hero_ld = {"@context": "https://schema.org", "@type": "NewsArticle",
               "headline": hero["title"], "datePublished": hero["dt"].isoformat(),
               "dateModified": hero["dt"].isoformat(), "author": {"@type": "Organization", "name": hero["source"]},
               "publisher": org_ld, "mainEntityOfPage": hero["link"], "url": hero["link"]}
    site_ld = {"@context": "https://schema.org", "@type": "WebSite", "name": "Pakistan Fast News",
               "url": BASE + "/", "inLanguage": "en"}
    home_ld = json.dumps([site_ld, org_ld, hero_ld], ensure_ascii=False)
    (out_dir / "index.html").write_text(page(
        "Pakistan Fast News — Latest Pakistan News, Fast",
        "The fastest Pakistan news headlines — politics, business, sports, tech and world news, updated around the clock from Dawn, ARY News, BBC News and The News.",
        BASE + "/", "📰 Latest headlines from Pakistan", home_body, home_ld, "index.html", ticker=ticker(items[:5], "BREAKING")), encoding="utf-8")

    # ---- Editorial page (original news) ----
    ed_ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Exclusive — Original News by Usman Kalera",
             "url": f"{BASE}/editorial.html",
             "hasPart": [{"@type": "NewsArticle", "headline": i["title"], "datePublished": i["date"],
                          "author": {"@type": "Person", "name": "Usman Kalera"}, "url": f"{BASE}/editorial.html#ed-{n}"} for n, i in enumerate(ed_items[:10])]}
    comments_section = ('<section class="comments"><h2>💬 Comments</h2>'
        '<p class="cnote">Comments open soon — you\'ll be able to sign in with GitHub and join the discussion here.</p>'
        '<!-- GISCUS SETUP (once, in GitHub — then uncomment the script below):\n'
        '  1. Repo → Settings → General → Features → tick "Discussions".\n'
        '  2. Install the giscus app on this repo: https://github.com/apps/giscus\n'
        '  3. In Discussions, use the "General" category (created automatically when Discussions is enabled).\n'
        '  4. Go to https://giscus.app, enter repo Usmankalera-dev/pakistan-fast-news, pick the category,\n'
        '     copy the repo-id + category-id it shows, paste them below, and uncomment this script.\n'
        '  <script src="https://giscus.app/client.js" data-repo="Usmankalera-dev/pakistan-fast-news" data-repo-id="TODO-REPO-ID" data-category="General" data-category-id="TODO-CATEGORY-ID" data-mapping="pathname" data-strict="0" data-reactions-enabled="1" data-emit-metadata="0" data-input-position="top" data-theme="preferred_color_scheme" data-lang="en" crossorigin="anonymous" async></scr' + 'ipt>\n'
        '--></section>')
    ed_body = ('<p class="crumb"><a href="index.html">Home</a> / Exclusive</p>'
               '<p class="secupd">Original news written by Usman Kalera for Pakistan Fast News — fresh stories every day.</p>'
               '<div class="grid">' + "".join(ed_cards) + '</div>' + comments_section if ed_cards else
               '<p class="crumb"><a href="index.html">Home</a> / Exclusive</p><p>Our own newsroom is getting ready — the first story is coming soon.</p>')
    (out_dir / "editorial.html").write_text(page(
        "Exclusive — Original News by Usman Kalera | Pakistan Fast News",
        "Original news written by Usman Kalera for Pakistan Fast News — fresh stories every day, alongside headlines from Dawn, ARY News, BBC News and The News.",
        f"{BASE}/editorial.html", "✍️ Exclusive", ed_body, json.dumps(ed_ld, ensure_ascii=False), "editorial.html"), encoding="utf-8")

    # ---- Category pages ----
    for c in CATS:
        lst = by_cat[c][:30]
        ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": f"{CAT_LABEL[c]} News — Pakistan Fast News",
              "url": f"{BASE}/{c}.html",
              "hasPart": [{"@type": "NewsArticle", "headline": i["title"], "datePublished": i["dt"].isoformat(), "url": i["link"]} for i in lst[:10]]}
        body = (f'<p class="crumb"><a href="index.html">Home</a> / {CAT_LABEL[c]}</p>'
                f'<p class="secupd">Updated {now.strftime("%d %B %Y, %I:%M %p PKT")} · Newest story {rel(max(i["dt"] for i in lst), now)}</p>'
                f'<div class="grid">{"".join(card(i, now) for i in lst)}</div>' if lst else
                '<p>No stories in this section yet — check back soon.</p>')
        (out_dir / f"{c}.html").write_text(page(
            f"{CAT_LABEL[c]} News — Pakistan Fast News",
            f"Latest {CAT_LABEL[c].lower()} news from Pakistan and the world, updated fast. Headlines from Dawn and ARY News.",
            f"{BASE}/{c}.html", f"{CAT_EMOJI[c]} {CAT_LABEL[c]} news", body, json.dumps(ld, ensure_ascii=False), f"{c}.html"), encoding="utf-8")

    # ---- Videos page ----
    videos = fetch_videos()
    print("videos:", len(videos), "| by channel:", {n: sum(1 for v in videos if v["channel"] == n) for n, _, _ in YT_CHANNELS})
    cache_file = out_dir / "videos_cache.json"
    if len(videos) >= 100:
        cache_file.write_text(json.dumps([{**v, "dt": v["dt"].isoformat()} for v in videos], ensure_ascii=False), encoding="utf-8")
    else:
        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            videos = [{**v, "dt": datetime.fromisoformat(v["dt"])} for v in cached]
            print(f"videos: using cache ({len(videos)} videos)")
        except Exception as e:
            print("videos cache miss:", e)
    chan_btns = ['<button class="chan active" data-ch="all"><span class="chanlogo all">ALL</span><span>All Channels</span></button>']
    for name, cid, slug in YT_CHANNELS:
        chan_btns.append(
            '<button class="chan" data-ch="' + slug + '"><img class="chanlogo" src="yt-' + slug + '.jpg" alt="' + H.escape(name) + ' logo" width="64" height="64" loading="lazy"><span>' + H.escape(name) + '</span></button>')
    vcards = []
    for i, v in enumerate(videos):
        live = "LIVE" if ("live" in v["title"].lower() or v["title"].startswith("🔴")) else ""
        vcards.append(
            '<article class="vcard" data-ch="' + v["slug"] + '" data-title="' + H.escape(v["title"].lower()) + '" data-new="' + ('1' if i < 36 else '0') + '">'
            '<button class="vthumb" data-vid="' + v["vid"] + '" data-title="' + H.escape(v["title"]) + '" data-chname="' + H.escape(v["channel"]) + '" data-desc="' + H.escape(v["desc"]) + '" aria-label="Play video">'
            '<img src="' + H.escape(v["thumb"]) + '" alt="" loading="lazy" onerror="this.src=\'https://i.ytimg.com/vi/' + v["vid"] + '/hqdefault.jpg\'">'
            '<span class="play">▶</span>' + ('<span class="livebadge">🔴 LIVE</span>' if live else '') + '</button>'
            '<div class="vmeta"><img class="vchanlogo" src="yt-' + v["slug"] + '.jpg" alt="' + H.escape(v["channel"]) + ' logo" width="28" height="28" loading="lazy">'
            '<span class="vsrc">' + H.escape(v["channel"]) + '</span>'
            '<time datetime="' + v["dt"].isoformat() + '">' + rel(v["dt"], now) + '</time></div>'
            '<h3><button class="vtitle" data-vid="' + v["vid"] + '" data-title="' + H.escape(v["title"]) + '" data-chname="' + H.escape(v["channel"]) + '" data-desc="' + H.escape(v["desc"]) + '">' + H.escape(v["title"]) + '</button></h3>' + share_row({"title": v["title"], "link": v["link"]}) + '</article>')
    vids_ld = {"@context": "https://schema.org", "@type": "ItemList", "name": "Pakistan News Videos",
               "itemListElement": [{"@type": "VideoObject", "position": i + 1, "name": v["title"],
                                    "description": v["desc"], "thumbnailUrl": v["thumb"],
                                    "uploadDate": v["dt"].isoformat(),
                                    "embedUrl": "https://www.youtube-nocookie.com/embed/" + v["vid"],
                                    "contentUrl": v["link"]} for i, v in enumerate(videos[:10])]}
    videos_js = """
(function(){var grid=document.getElementById('vgrid'),cards=Array.from(grid.children),count=document.getElementById('vcount');
function show(){var ch=document.querySelector('.chan.active').dataset.ch,q=(document.getElementById('vq').value||'').toLowerCase(),n=0;
cards.forEach(function(c){var ok=(ch==='all'?c.dataset.new==='1':c.dataset.ch===ch)&&(!q||c.dataset.title.indexOf(q)>-1);c.style.display=ok?'':'none';if(ok)n++;});
count.textContent=n+' video'+(n===1?'':'s')+(ch==='all'?' — latest across all channels':' — '+document.querySelector('.chan.active span:last-child').textContent);}
document.querySelectorAll('.chan').forEach(function(b){b.addEventListener('click',function(){document.querySelectorAll('.chan').forEach(function(x){x.classList.remove('active')});b.classList.add('active');show();});});
document.getElementById('vq').addEventListener('input',show);show();
var h=location.hash.slice(1);if(h){var hb=document.querySelector('.chan[data-ch="'+h+'"]');if(hb)hb.click();}
var modal=document.getElementById('modal'),player=document.getElementById('player');
var curVid=null,ytPlayer=null,autoNext=false;
try{autoNext=localStorage.getItem('pfn-autoplay')==='1';}catch(e){}
document.getElementById('autoplay-next').checked=autoNext;
document.getElementById('autoplay-next').addEventListener('change',function(){autoNext=this.checked;try{localStorage.setItem('pfn-autoplay',autoNext?'1':'0');}catch(e){}});
function visibleCards(){return cards.filter(function(c){return c.style.display!=='none';});}
function vidOf(c){return c.querySelector('[data-vid]').dataset.vid;}
function upNextLabel(){var v=visibleCards(),i=v.findIndex(function(c){return vidOf(c)===curVid;}),n=v[(i+1)%v.length];document.getElementById('upnext').textContent=n?('Up next: '+n.querySelector('.vtitle').textContent):'';}
function playNext(){var v=visibleCards();if(!v.length)return;var i=v.findIndex(function(c){return vidOf(c)===curVid;}),n=v[(i+1)%v.length],b=n.querySelector('[data-vid]');openVid(b.dataset.vid,b.dataset.title,b.dataset.chname,b.dataset.desc);}
document.getElementById('nextvid').addEventListener('click',playNext);
function initYT(){if(ytPlayer||!window.YT||!YT.Player)return;try{ytPlayer=new YT.Player(player,{events:{onStateChange:function(e){if(e.data===YT.PlayerState.ENDED&&autoNext)playNext();}}});}catch(e){}}
window.onYouTubeIframeAPIReady=function(){initYT();};
if(!window.YT){var s=document.createElement('script');s.src='https://www.youtube.com/iframe_api';document.head.appendChild(s);}
function openVid(vid,title,chname,desc){curVid=vid;document.getElementById('modaltitle').textContent=title;
document.getElementById('modaldesc').textContent=desc||'';var a=document.getElementById('modalyt');a.href='https://www.youtube.com/watch?v='+vid;a.textContent='Watch on YouTube ('+chname+') →';
player.src='https://www.youtube-nocookie.com/embed/'+vid+'?autoplay=1&rel=0&enablejsapi=1';modal.hidden=false;document.body.style.overflow='hidden';upNextLabel();initYT();}
function closeVid(){curVid=null;player.src='';modal.hidden=true;document.body.style.overflow='';}
grid.addEventListener('click',function(e){var b=e.target.closest('[data-vid]');if(b)openVid(b.dataset.vid,b.dataset.title,b.dataset.chname,b.dataset.desc);});
document.getElementById('modalclose').addEventListener('click',closeVid);
modal.addEventListener('click',function(e){if(e.target===modal)closeVid();});
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!modal.hidden)closeVid();});
})();
"""
    videos_body = (
        '<p class="crumb"><a href="index.html">Home</a> / Videos</p>'
        '<p class="vintro">Latest videos from Pakistan\u2019s top news channels. Tap a channel logo to see only its videos, then tap any video to play it right here on this site.</p>'
        '<div class="chanbar" role="group" aria-label="News channels">' + ''.join(chan_btns) + '</div>'
        '<div class="search"><span class="searchicon" aria-hidden="true">🔍</span><input id="vq" type="search" placeholder="Search videos\u2026" aria-label="Search videos"></div>'
        '<div class="vgrid" id="vgrid">' + ''.join(vcards) + '</div>'
        '<p class="vcount" id="vcount"></p>'
        '<div class="modal" id="modal" role="dialog" aria-modal="true" aria-label="Video player" hidden>'
        '<div class="modalbox"><button class="modalclose" id="modalclose" aria-label="Close player">✕</button>'
        '<div class="playerwrap"><iframe id="player" title="YouTube video player" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div>'
        '<h3 id="modaltitle"></h3><p id="modaldesc"></p>'
        '<div class="playctl"><label class="autoplay"><input type="checkbox" id="autoplay-next"> Autoplay next</label><button id="nextvid" class="nextbtn" type="button">Next ▶</button><span id="upnext"></span></div>'
        '<p><a id="modalyt" href="#" target="_blank" rel="noopener">Watch on YouTube →</a></p></div></div>'
        '<script>' + videos_js + '</script>')
    (out_dir / "videos.html").write_text(page(
            "Pakistan News Videos — Watch Geo, ARY, Dawn, Samaa & More",
            "Watch the latest Pakistan news videos from Geo News, ARY News, Dawn News, Samaa, Dunya, Express, Hum, BOL, 92 News, Aaj and Neo — play them right here on Pakistan Fast News.",
            BASE + "/videos.html", "🎬 Pakistan news videos", videos_body, json.dumps(vids_ld, ensure_ascii=False), "videos.html"), encoding="utf-8")

    # ---- Live TV page (official YouTube live_stream embeds, click-to-load) ----
    live_ld = {"@context": "https://schema.org", "@type": "WebPage", "name": "Live TV — Pakistan News Channels | Pakistan Fast News",
               "url": BASE + "/live-tv.html"}
    (out_dir / "live-tv.html").write_text(page(
        "Live TV — Watch Geo, ARY, Dawn, Samaa, Dunya & Express Live | Pakistan Fast News",
        "Watch Pakistan news channels live — Geo News, ARY News, Dawn News, Samaa TV, Dunya News and Express News, from their official YouTube live streams.",
        BASE + "/live-tv.html", "📺 Live TV — Pakistan news channels", LIVE_TV_BODY_EN,
        json.dumps(live_ld, ensure_ascii=False), "live-tv.html"), encoding="utf-8")

    # ---- Prayer timetable page (monthly, Aladhan calendar API, client-side) ----
    prayer_ld = {"@context": "https://schema.org", "@type": "WebPage", "name": "Prayer Times — Monthly Timetable | Pakistan Fast News",
                 "url": BASE + "/prayer.html"}
    (out_dir / "prayer.html").write_text(page(
        "Prayer Times — Monthly Timetable (Lahore, Karachi, Islamabad) | Pakistan Fast News",
        "Monthly prayer timetable for Lahore, Karachi and Islamabad — Fajr, Sunrise, Dhuhr, Asr, Maghrib and Isha, with Hijri dates, from the Aladhan API.",
        BASE + "/prayer.html", "🕌 Prayer times — monthly timetable", PRAYER_BODY_EN,
        json.dumps(prayer_ld, ensure_ascii=False), "prayer.html"), encoding="utf-8")

    # ---- sitemap + robots + 404 ----
    urls = [("", "1.0"), ("editorial.html", "0.9"), ("videos.html", "0.9"), ("live-tv.html", "0.8"), ("prayer.html", "0.8"), ("ur/", "0.9"), ("ur/editorial.html", "0.8"), ("ur/live-tv.html", "0.7"), ("ur/prayer.html", "0.7")] + [(f"{c}.html", "0.8") for c in CATS] + [(f"ur/{c}.html", "0.8") for c in CATS]
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
