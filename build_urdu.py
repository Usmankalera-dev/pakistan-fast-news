#!/usr/bin/env python3
"""Pakistan Fast News — Urdu edition (Phase 2).
Builds ur/ pages from real Urdu RSS feeds (Dawn Urdu, ARY Urdu, Express, BBC Urdu).
Run: python3 build_urdu.py   (does NOT touch the English pages or build.py)
Excerpts only; full stories open on the publishers' sites, same as the English edition.
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
    ("https://www.dawnnews.tv/feeds/home", "ڈان اردو", None),
    ("https://www.dawnnews.tv/feeds/pakistan", "ڈان اردو", "pakistan"),
    ("https://urdu.arynews.tv/feed/", "اے آر وائی اردو", None),
    ("https://www.express.pk/feed/", "ایکسپریس", None),
    ("https://www.bbc.com/urdu/index.xml", "بی بی سی اردو", None),
]
CATS = ["pakistan", "world", "business", "sports", "tech", "entertainment"]
CAT_LABEL = {"pakistan": "پاکستان", "world": "دنیا", "business": "کاروبار",
             "sports": "کھیل", "tech": "ٹیکنالوجی", "entertainment": "تفریح"}
CAT_EMOJI = {"pakistan": "🇵🇰", "world": "🌍", "business": "💼",
             "sports": "🏏", "tech": "💻", "entertainment": "🎬"}
LOGOS = {"ڈان اردو": ("logo-urdu-dawn.png", 20, 20),
         "اے آر وائی اردو": ("logo-urdu-ary.png", 20, 20),
         "ایکسپریس": ("logo-urdu-express.png", 47, 20),
         "بی بی سی اردو": ("logo-urdu-bbc.png", 57, 20)}
KW = {
    "sports": ["کرکٹ", "فٹبال", "ہاکی", "پی ایس ایل", "میچ", "ٹورنامنٹ", "کھلاڑی",
               "اولمپک", "فیفا", "ٹینس", "بیڈمنٹن", "اسکواش", "ورلڈ کپ", "ٹی ٹوئنٹی",
               "ون ڈے", "ٹیسٹ میچ", "بلے باز", "بولر", "پی سی بی", "چیمپئنز ٹرافی"],
    "business": ["معیشت", "روپیہ", "ڈالر", "آئی ایم ایف", "اسٹاک", "مارکیٹ", "تجارت",
                 "مہنگائی", "بجٹ", "ٹیکس", "جی ڈی پی", "ترسیلات", "پٹرول", "ڈیزل",
                 "شرح سود", "اسٹیٹ بینک", "پی ایس ایکس", "کاروبار", "برآمدات", "درآمدات"],
    "tech": ["اے آئی", "ٹیکنالوجی", "اسمارٹ فون", "انٹرنیٹ", "سائبر", "گوگل", "ایپل",
             "میٹا", "سافٹ ویئر", "ڈیجیٹل", "فائیو جی", "سیٹلائٹ", "روبوٹ", "چپ",
             "اوپن اے آئی", "چیٹ جی پی ٹی"],
    "entertainment": ["فلم", "ڈرامہ", "اداکار", "اداکارہ", "گلوکار", "شوبز", "موسیقی",
                      "بالی ووڈ", "لالی ووڈ", "گانا", "کنسرٹ", "مشہور", "نیٹ فلکس"],
}
PK_KW = ["پاکستان", "لاہور", "کراچی", "اسلام آباد", "پنجاب", "سندھ", "خیبر",
         "بلوچستان", "پشاور", "کوئٹہ", "شہباز", "عمران خان", "پی ٹی آئی", "ن لیگ",
         "پیپلز پارٹی", "عدالت", "پارلیمنٹ", "سینٹ", "اسمبلی", "سپریم کورٹ",
         "الیکشن کمیشن", "نیب", "ایف بی آر", "فوج", "حکومت", "کابینہ", "وزیراعظم", "صدر"]
NS = {"media": "http://search.yahoo.com/mrss/"}


def clean(txt):
    txt = H.unescape(re.sub(r"<[^>]+>", " ", txt or ""))
    return re.sub(r"\s+", " ", txt).strip()


def categorize(title, desc, feed_cat):
    if feed_cat:
        return feed_cat
    t = " " + title + " " + desc + " "
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
            key = title[:40]
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
    if mins < 1:
        return "ابھی"
    if mins < 60:
        return f"{mins} منٹ پہلے"
    h = mins // 60
    if h < 24:
        return f"{h} گھنٹے پہلے"
    return f"{h // 24} دن پہلے"


def share_row(it):
    enc = urlquote(it["title"] + " " + it["link"])
    fb = urlquote(it["link"])
    return (f'<div class="share"><a class="share-wa" href="https://wa.me/?text={enc}" target="_blank" rel="noopener">واٹس ایپ ↗</a>'
            f'<a class="share-x" href="https://twitter.com/intent/tweet?text={enc}" target="_blank" rel="noopener">X ↗</a>'
            f'<a class="share-fb" href="https://www.facebook.com/sharer/sharer.php?u={fb}" target="_blank" rel="noopener">Facebook ↗</a>'
            f'<button class="share-copy" type="button" data-link="{H.escape(it["link"])}">لنک کاپی کریں</button>'
            f'<button class="share-native" type="button" data-title="{H.escape(it["title"])}" data-link="{H.escape(it["link"])}">شیئر کریں</button></div>')


def ticker(items, label):
    seq = "".join(f'<a href="{H.escape(i["link"])}" target="_blank" rel="noopener">{H.escape(i["title"])}</a><span class="ticker-sep">•</span>' for i in items)
    return (f'<div class="ticker"><span class="ticker-label">{H.escape(label)}</span>'
            f'<div class="ticker-viewport"><div class="ticker-track">{seq}{seq}</div></div></div>')


def card(it, now, big=False):
    logo, lw, lh = LOGOS.get(it["source"], ("logo-urdu-dawn.png", 20, 20))
    link = H.escape(it["link"])
    meta = (f'<div class="meta">'
            f'<img class="srclogo" src="../{logo}" alt="{H.escape(it["source"])} logo" width="{lw}" height="{lh}" loading="lazy">'
            f'<span class="src">{H.escape(it["source"])}</span>'
            f'<span class="chip {it["cat"]}">{CAT_LABEL[it["cat"]]}</span>'
            f'<time datetime="{it["dt"].isoformat()}">{rel(it["dt"], now)} · {it["dt"].strftime("%d %b %Y, %I:%M %p")} PKT</time></div>')
    title = f'<h3><a href="{link}" target="_blank" rel="noopener">{H.escape(it["title"])}</a></h3>'
    desc = (f'<p>{H.escape(it["desc"])}</p>' if it["desc"] else "")
    readmore = f'<a class="readmore" href="{link}" target="_blank" rel="noopener">مکمل خبر {H.escape(it["source"])} پر پڑھیں →</a>'
    if big and it.get("img"):
        return (f'<article class="card hero heroimg cat-{it["cat"]}">'
                f'<div class="herowrap"><a class="heropic" href="{link}" target="_blank" rel="noopener" tabindex="-1" aria-hidden="true">'
                f'<img src="{H.escape(it["img"])}" alt="" loading="eager" onerror="this.closest(\'.herowrap\').classList.add(\'imgfail\');this.closest(\'article\').classList.add(\'hero-noimg\')"></a>'
                f'<span class="herograd"></span>'
                f'<div class="heroover">{title}</div></div>'
                f'<div class="herobody">{meta}{desc}{readmore}' + share_row(it) + '</div></article>')
    thumb = ""
    if it.get("img"):
        thumb = (f'<a class="thumbwrap" href="{link}" target="_blank" rel="noopener" tabindex="-1" aria-hidden="true">'
                 f'<img class="thumb" src="{H.escape(it["img"])}" alt="" loading="lazy" onerror="this.closest(\'.thumbwrap\').remove()"></a>')
    else:
        thumb = (f'<a class="thumbwrap fallback" href="{link}" target="_blank" rel="noopener" tabindex="-1" aria-hidden="true">'
                 f'<img src="../{logo}" alt="{H.escape(it["source"])} logo"></a>')
    cls = "card hero" if big else "card"
    return (f'<article class="{cls} cat-{it["cat"]}">{thumb}{meta}{title}{desc}{readmore}' + share_row(it) + '</article>')


def load_editorial(lang):
    """عثمان کی لکھی ہوئی اصل خبریں، نئی پہلے۔ فائل: editorial.json (ریپو روٹ)۔"""
    try:
        data = json.loads((Path(__file__).parent / "editorial.json").read_text(encoding="utf-8"))
        items = [i for i in data.get("items", []) if i.get("lang", "en") == lang]
    except Exception:
        items = []
    items.sort(key=lambda i: i.get("date", ""), reverse=True)
    return items


def ed_card(it, now, idx, base_url):
    """اصل خبر کا ایک کارڈ۔ شیئر لنک اداریہ صفحے کے اینکر پر جاتا ہے۔"""
    dt = datetime.fromisoformat(it["date"]).replace(tzinfo=PKT, hour=12, minute=0)
    link = f"{base_url}#ed-{idx}"
    meta = (f'<div class="meta">'
            f'<span class="src">✍️ عثمان کلیرہ</span>'
            f'<span class="chip {it.get("cat", "pakistan")}">{CAT_LABEL[it.get("cat", "pakistan")]}</span>'
            f'<time datetime="{it["date"]}">{rel(dt, now)} · {dt.strftime("%d %b %Y")} PKT</time></div>')
    return (f'<article class="card cat-{it.get("cat", "pakistan")}" id="ed-{idx}">{meta}'
            f'<h3>{H.escape(it["title"])}</h3>'
            f'<p>{H.escape(it["body"])}</p>' + share_row({"title": it["title"], "link": link}) + '</article>')


def nav(active=""):
    links = [("index.html", "ہوم")] + [(f"{c}.html", CAT_LABEL[c]) for c in CATS] + [("editorial.html", "✍️ خصوصی")]
    out = []
    for href, label in links:
        cls = ' class="active"' if href == active else ""
        out.append(f'<a href="{href}"{cls}>{label}</a>')
    out.append('<a href="../videos.html" class="vidlink">▶ ویڈیوز</a>')
    out.append('<a href="../index.html" class="vidlink">English</a>')
    return "\n".join(out)


def page(title, desc, canon, h1, body_html, json_ld, active="index.html", ticker=""):
    now_s = datetime.now(PKT).strftime("%d %B %Y, %I:%M %p PKT")
    fsecs = "".join(f'<li><a href="{c}.html">{CAT_LABEL[c]}</a></li>' for c in CATS)
    fsecs += '<li><a href="editorial.html">✍️ خصوصی خبریں</a></li>'
    footer_html = (
        '<footer><div class="wrap"><div class="fgrid">'
        '<div class="fcol fbrand"><a class="flogo" href="index.html"><img src="../favicon.svg" alt="" width="38" height="38"> پاکستان <b>فاسٹ نیوز</b></a>'
        '<p>پاکستان اور دنیا کی تیز ترین خبریں — سیاست، کاروبار، کھیل، ٹیکنالوجی اور تفریح، چوبیس گھنٹے تازہ۔</p>'
        '<p>تیز اور مفت: کوئی اشتہار نہیں، کوئی ٹریکر نہیں، کوئی بھاری اسکرپٹ نہیں۔</p></div>'
        '<div class="fcol"><h4>شعبے</h4><ul>' + fsecs + '</ul></div>'
        '<div class="fcol"><h4>زبان</h4><ul><li><a href="index.html">اردو</a></li><li><a href="../index.html">English</a></li></ul></div>'
        '<div class="fcol fsources"><h4>ذرائع</h4><p>خبریں ان ذرائع سے:</p>'
        '<span class="srclogochip"><img src="../logo-urdu-dawn.png" alt="ڈان اردو لوگو" height="24"></span>'
        '<span class="srclogochip"><img src="../logo-urdu-ary.png" alt="اے آر وائی اردو لوگو" height="24"></span>'
        '<span class="srclogochip"><img src="../logo-urdu-express.png" alt="ایکسپریس لوگو" height="24"></span>'
        '<span class="srclogochip"><img src="../logo-urdu-bbc.png" alt="بی بی سی اردو لوگو" height="24"></span>'
        '<p class="fine">مکمل خبریں ناشرین کی ویب سائٹس پر کھلتی ہیں — ہم مکمل مضامین کاپی نہیں کرتے۔</p></div>'
        '</div><div class="fbot"><span>© 2026 پاکستان فاسٹ نیوز</span>'
        '<span>اپ ڈیٹ ' + now_s + ' · <a href="../sitemap.xml">سائٹ میپ</a></span></div></div></footer>')
    return f"""<!DOCTYPE html>
<html lang="ur" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>try{{var f=localStorage.getItem("pfn-fss");if(f)document.documentElement.style.setProperty("--fss",f);var t=localStorage.getItem("pfn-theme");if(t){{document.documentElement.setAttribute("data-theme",t)}}else if(window.matchMedia("(prefers-color-scheme: dark)").matches){{document.documentElement.setAttribute("data-theme","dark")}}}}catch(e){{}}</script>
<title>{H.escape(title)}</title>
<meta name="description" content="{H.escape(desc)}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="پاکستان فاسٹ نیوز">
<meta property="og:title" content="{H.escape(title)}">
<meta property="og:description" content="{H.escape(desc)}">
<meta property="og:url" content="{canon}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{H.escape(title)}">
<meta name="twitter:description" content="{H.escape(desc)}">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<link rel="manifest" href="../manifest.json">
<meta name="theme-color" content="#c8102e">
<link rel="apple-touch-icon" href="../apple-touch-icon.png">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu:wght@400;700&family=Noto+Naskh+Arabic:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../styles.css?v=20261107r3">
<script type="application/ld+json">{json_ld}</script>
</head>
<body>
<header class="topbar"><div class="wrap">
<a class="logo" href="index.html"><img src="../favicon.svg" alt="پاکستان فاسٹ نیوز لوگو" width="36" height="36" class="sitelogo"><span class="logotext">پاکستان <b>فاسٹ نیوز</b><small>پاکستان کی تیز ترین خبریں</small></span></a>
<div class="clock"><span class="livedot" aria-hidden="true"></span><b>LIVE</b> <span id="clock"></span><span class="upd">اپ ڈیٹ {now_s}</span></div>
<button id="theme-toggle" class="themetoggle" type="button" aria-label="ڈارک موڈ">🌙</button>
<span class="fss"><button id="fs-minus" class="fsbtn" type="button" aria-label="چھوٹا متن">A−</button><button id="fs-plus" class="fsbtn" type="button" aria-label="بڑا متن">A+</button></span>
</div></header>
<nav class="mainnav" aria-label="شعبے"><div class="wrap">{nav(active)}</div></nav>
{ticker}<main class="wrap">
<div class="today" id="today-widget" role="status">
<div class="trow"><span class="tlabel">💵 ڈالر</span><span class="tval">$1 = <span id="w-usd">…</span><span class="conv"><input id="w-conv" type="number" value="10" min="0" inputmode="decimal" aria-label="امریکی ڈالر"> USD = <b id="w-conv-out">…</b></span></span></div>
<div class="trow"><span class="tlabel">🪙 سونا · 1 تولہ</span><span class="tval" id="w-gold">…</span></div>
<div class="trow"><span class="tlabel">🌤️ موسم</span><span class="tval" id="w-weather">…</span></div>
<div class="trow"><span class="tlabel">🕌 نماز</span><span class="tval"><span class="pcities"><button type="button" class="pcity active" data-city="Lahore">لاہور</button><button type="button" class="pcity" data-city="Karachi">کراچی</button><button type="button" class="pcity" data-city="Islamabad">اسلام آباد</button></span><span id="w-prayer">…</span></span></div>
<div class="trow"><span class="tlabel">📅 لاہور · 7 دن</span><span class="tval"><span class="fgrid" id="w-forecast"></span></span></div>
<div class="tsrc" id="w-updated"></div>
</div>
<h1>{H.escape(h1)}</h1>
<div class="search"><span class="searchicon" aria-hidden="true">🔍</span><input id="q" type="search" placeholder="خبریں تلاش کریں…" aria-label="خبریں تلاش کریں"></div>
{body_html}
</main>
{footer_html}
<script src="../script.js" defer></script>
<button id="totop" class="totop" type="button" aria-label="اوپر جائیں">↑</button>
</body>
</html>
"""


def main():
    out_dir = Path(__file__).parent / "ur"
    out_dir.mkdir(exist_ok=True)
    items = fetch()
    now = datetime.now(PKT)
    print("urdu items:", len(items), "| by cat:",
          {c: sum(1 for i in items if i["cat"] == c) for c in CATS},
          "| by source:", {s: sum(1 for i in items if i["source"] == s) for s in
                            ["ڈان اردو", "اے آر وائی اردو", "ایکسپریس", "بی بی سی اردو"]})
    by_cat = {c: [i for i in items if i["cat"] == c] for c in CATS}
    today = now.strftime("%Y-%m-%d")
    org_ld = {"@context": "https://schema.org", "@type": "NewsMediaOrganization",
              "name": "پاکستان فاسٹ نیوز", "url": BASE + "/ur/",
              "logo": {"@type": "ImageObject", "url": BASE + "/favicon.svg"}}
    hero = items[0]
    rest = items[1:19]
    ed_items = load_editorial("ur")
    ed_cards = [ed_card(it, now, i, BASE + "/ur/editorial.html") for i, it in enumerate(ed_items)]
    ed_section = ('<section><h2>✍️ خصوصی خبریں <span class="h2note">· عثمان کلیرہ کی تحریر</span> <a class="more" href="editorial.html">تمام →</a></h2><div class="grid">' + "".join(ed_cards[:4]) + '</div></section>' if ed_cards else
                  '<section><h2>✍️ خصوصی خبریں <span class="h2note">· عثمان کلیرہ کی تحریر</span></h2><p>ہمارا اپنا نیوز روم تیار ہو رہا ہے — پہلی خبر جلد آ رہی ہے۔</p></section>')
    sections = ""
    for c in CATS:
        lst = by_cat[c][:4]
        if len(lst) < 2:
            continue
        sections += f'<section><h2>{CAT_EMOJI[c]} {CAT_LABEL[c]} <span class="h2note">· تازہ ترین {rel(max(i["dt"] for i in lst), now)}</span> <a class="more" href="{c}.html">مزید →</a></h2><div class="grid">{"".join(card(i, now) for i in lst)}</div></section>'
    # NOTE: id="latest-ur" (not "latest") so script.js does not inject English Dawn cards here.
    home_body = (f'<section><h2 class="toplabel">اہم خبر</h2>{card(hero, now, big=True)}</section>'
                 f'<section><h2>تازہ ترین خبریں</h2><div class="grid" id="latest-ur">{"".join(card(i, now) for i in rest)}</div></section>'
                 + ed_section + sections)
    hero_ld = {"@context": "https://schema.org", "@type": "NewsArticle",
               "headline": hero["title"], "datePublished": hero["dt"].isoformat(),
               "dateModified": hero["dt"].isoformat(), "author": {"@type": "Organization", "name": hero["source"]},
               "publisher": org_ld, "mainEntityOfPage": hero["link"], "url": hero["link"]}
    site_ld = {"@context": "https://schema.org", "@type": "WebSite", "name": "پاکستان فاسٹ نیوز",
               "url": BASE + "/ur/", "inLanguage": "ur"}
    home_ld = json.dumps([site_ld, org_ld, hero_ld], ensure_ascii=False)
    (out_dir / "index.html").write_text(page(
        "پاکستان فاسٹ نیوز اردو — تازہ ترین پاکستانی خبریں",
        "پاکستان کی تیز ترین اردو خبریں — سیاست، کاروبار، کھیل، ٹیکنالوجی اور دنیا کی خبریں، ڈان اردو، اے آر وائی اردو، ایکسپریس اور بی بی سی اردو سے۔",
        BASE + "/ur/", "📰 پاکستان کی تازہ ترین خبریں", home_body, home_ld, "index.html", ticker=ticker(items[:5], "تازہ ترین")), encoding="utf-8")
    # ---- Editorial page (اصل خبریں) ----
    ed_ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "خصوصی خبریں — عثمان کلیرہ کی تحریر",
             "url": f"{BASE}/ur/editorial.html",
             "hasPart": [{"@type": "NewsArticle", "headline": i["title"], "datePublished": i["date"],
                          "author": {"@type": "Person", "name": "Usman Kalera"}, "url": f"{BASE}/ur/editorial.html#ed-{n}"} for n, i in enumerate(ed_items[:10])]}
    ed_body = ('<p class="crumb"><a href="index.html">ہوم</a> / خصوصی خبریں</p>'
               '<p class="secupd">پاکستان فاسٹ نیوز کے لیے عثمان کلیرہ کی لکھی ہوئی اصل خبریں — روزانہ تازہ کہانیاں۔</p>'
               '<div class="grid">' + "".join(ed_cards) + '</div>' if ed_cards else
               '<p class="crumb"><a href="index.html">ہوم</a> / خصوصی خبریں</p><p>ہمارا اپنا نیوز روم تیار ہو رہا ہے — پہلی خبر جلد آ رہی ہے۔</p>')
    (out_dir / "editorial.html").write_text(page(
        "خصوصی خبریں — عثمان کلیرہ کی تحریر | پاکستان فاسٹ نیوز اردو",
        "پاکستان فاسٹ نیوز کے لیے عثمان کلیرہ کی لکھی ہوئی اصل خبریں — روزانہ تازہ کہانیاں۔",
        f"{BASE}/ur/editorial.html", "✍️ خصوصی خبریں", ed_body, json.dumps(ed_ld, ensure_ascii=False), "editorial.html"), encoding="utf-8")
    for c in CATS:
        lst = by_cat[c][:30]
        ld = {"@context": "https://schema.org", "@type": "CollectionPage",
              "name": f"{CAT_LABEL[c]} خبریں — پاکستان فاسٹ نیوز",
              "url": f"{BASE}/ur/{c}.html",
              "hasPart": [{"@type": "NewsArticle", "headline": i["title"],
                           "datePublished": i["dt"].isoformat(), "url": i["link"]} for i in lst[:10]]}
        body = (f'<p class="crumb"><a href="index.html">ہوم</a> / {CAT_LABEL[c]}</p>'
                f'<p class="secupd">اپ ڈیٹ {now.strftime("%d %B %Y, %I:%M %p PKT")} · تازہ ترین خبر {rel(max(i["dt"] for i in lst), now)}</p>'
                f'<div class="grid">{"".join(card(i, now) for i in lst)}</div>' if lst else
                '<p>اس شعبے میں ابھی کوئی خبر نہیں — تھوڑی دیر بعد دوبارہ دیکھیں۔</p>')
        (out_dir / f"{c}.html").write_text(page(
            f"{CAT_LABEL[c]} خبریں — پاکستان فاسٹ نیوز اردو",
            f"پاکستان اور دنیا کی تازہ ترین {CAT_LABEL[c]} خبریں اردو میں۔",
            f"{BASE}/ur/{c}.html", f"{CAT_EMOJI[c]} {CAT_LABEL[c]} خبریں", body,
            json.dumps(ld, ensure_ascii=False), f"{c}.html"), encoding="utf-8")
    print("built urdu", today, "| pages:", len(list(out_dir.glob('*.html'))))


if __name__ == "__main__":
    main()
