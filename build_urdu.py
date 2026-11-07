#!/usr/bin/env python3
"""Pakistan Fast News — Urdu edition (Phase 2).
Builds ur/ pages from real Urdu RSS feeds (Dawn Urdu, ARY Urdu, Express, BBC Urdu).
Run: python3 build_urdu.py   (does NOT touch the English pages or build.py)
Excerpts only; full stories open on the publishers' sites, same as the English edition.
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
    ("https://www.dawnnews.tv/feeds/home", "ڈان اردو", None),
    ("https://www.dawnnews.tv/feeds/pakistan", "ڈان اردو", "pakistan"),
    ("https://urdu.arynews.tv/feed/", "اے آر وائی اردو", None),
    ("https://www.express.pk/feed/", "ایکسپریس", None),
    ("https://www.bbc.com/urdu/index.xml", "بی بی سی اردو", None),
]
CATS = ["pakistan", "world", "business", "sports", "tech", "entertainment"]
CAT_LABEL = {"pakistan": "پاکستان", "world": "دنیا", "business": "کاروبار",
             "sports": "کھیل", "tech": "ٹیکنالوجی", "entertainment": "تفریح"}
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


def card(it, now, big=False):
    cls = "card hero" if big else "card"
    logo, lw, lh = LOGOS.get(it["source"], ("logo-urdu-dawn.png", 20, 20))
    thumb = ""
    if it.get("img"):
        thumb = (f'<a class="thumbwrap" href="{H.escape(it["link"])}" target="_blank" rel="noopener" tabindex="-1" aria-hidden="true">'
                 f'<img class="thumb" src="{H.escape(it["img"])}" alt="" loading="lazy" onerror="this.closest(\'.thumbwrap\').remove()"></a>')
    else:
        thumb = (f'<a class="thumbwrap fallback" href="{H.escape(it["link"])}" target="_blank" rel="noopener" tabindex="-1" aria-hidden="true">'
                 f'<img src="../{logo}" alt="{H.escape(it["source"])} logo"></a>')
    return (f'<article class="{cls}">{thumb}<div class="meta">'
            f'<img class="srclogo" src="../{logo}" alt="{H.escape(it["source"])} logo" width="{lw}" height="{lh}" loading="lazy">'
            f'<span class="src">{H.escape(it["source"])}</span>'
            f'<span class="chip {it["cat"]}">{CAT_LABEL[it["cat"]]}</span>'
            f'<time datetime="{it["dt"].isoformat()}">{rel(it["dt"], now)} · {it["dt"].strftime("%d %b %Y, %I:%M %p")} PKT</time></div>'
            f'<h3><a href="{H.escape(it["link"])}" target="_blank" rel="noopener">{H.escape(it["title"])}</a></h3>'
            + (f'<p>{H.escape(it["desc"])}</p>' if it["desc"] else "")
            + f'<a class="readmore" href="{H.escape(it["link"])}" target="_blank" rel="noopener">مکمل خبر {H.escape(it["source"])} پر پڑھیں →</a></article>')


def nav(active=""):
    links = [("index.html", "ہوم")] + [(f"{c}.html", CAT_LABEL[c]) for c in CATS]
    out = []
    for href, label in links:
        cls = ' class="active"' if href == active else ""
        out.append(f'<a href="{href}"{cls}>{label}</a>')
    out.append('<a href="../videos.html" class="vidlink">▶ ویڈیوز</a>')
    out.append('<a href="../index.html" class="vidlink">English</a>')
    return "\n".join(out)


def page(title, desc, canon, h1, body_html, json_ld, active="index.html"):
    now_s = datetime.now(PKT).strftime("%d %B %Y, %I:%M %p PKT")
    fsecs = "".join(f'<li><a href="{c}.html">{CAT_LABEL[c]}</a></li>' for c in CATS)
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
<link rel="stylesheet" href="../styles.css">
<script type="application/ld+json">{json_ld}</script>
</head>
<body>
<header class="topbar"><div class="wrap">
<a class="logo" href="index.html"><img src="../favicon.svg" alt="پاکستان فاسٹ نیوز لوگو" width="36" height="36" class="sitelogo"><span class="logotext">پاکستان <b>فاسٹ نیوز</b><small>پاکستان کی تیز ترین خبریں</small></span></a>
<div class="clock"><span class="livedot" aria-hidden="true"></span><b>LIVE</b> <span id="clock"></span><span class="upd">اپ ڈیٹ {now_s}</span></div>
</div></header>
<nav class="mainnav" aria-label="شعبے"><div class="wrap">{nav(active)}</div></nav>
<main class="wrap">
<h1>{H.escape(h1)}</h1>
<div class="search"><input id="q" type="search" placeholder="خبریں تلاش کریں…" aria-label="خبریں تلاش کریں"></div>
{body_html}
</main>
{footer_html}
<script src="../script.js" defer></script>
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
    sections = ""
    for c in CATS:
        lst = by_cat[c][:4]
        if len(lst) < 2:
            continue
        sections += f'<section><h2>{CAT_LABEL[c]} <a class="more" href="{c}.html">مزید →</a></h2><div class="grid">{"".join(card(i, now) for i in lst)}</div></section>'
    # NOTE: id="latest-ur" (not "latest") so script.js does not inject English Dawn cards here.
    home_body = (f'<section><h2>اہم خبر</h2>{card(hero, now, big=True)}</section>'
                 f'<section><h2>تازہ ترین خبریں</h2><div class="grid" id="latest-ur">{"".join(card(i, now) for i in rest)}</div></section>'
                 + sections)
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
        BASE + "/ur/", "پاکستان کی تازہ ترین خبریں", home_body, home_ld, "index.html"), encoding="utf-8")
    for c in CATS:
        lst = by_cat[c][:30]
        ld = {"@context": "https://schema.org", "@type": "CollectionPage",
              "name": f"{CAT_LABEL[c]} خبریں — پاکستان فاسٹ نیوز",
              "url": f"{BASE}/ur/{c}.html",
              "hasPart": [{"@type": "NewsArticle", "headline": i["title"],
                           "datePublished": i["dt"].isoformat(), "url": i["link"]} for i in lst[:10]]}
        body = (f'<p class="crumb"><a href="index.html">ہوم</a> / {CAT_LABEL[c]}</p>'
                f'<div class="grid">{"".join(card(i, now) for i in lst)}</div>' if lst else
                '<p>اس شعبے میں ابھی کوئی خبر نہیں — تھوڑی دیر بعد دوبارہ دیکھیں۔</p>')
        (out_dir / f"{c}.html").write_text(page(
            f"{CAT_LABEL[c]} خبریں — پاکستان فاسٹ نیوز اردو",
            f"پاکستان اور دنیا کی تازہ ترین {CAT_LABEL[c]} خبریں اردو میں۔",
            f"{BASE}/ur/{c}.html", f"{CAT_LABEL[c]} خبریں", body,
            json.dumps(ld, ensure_ascii=False), f"{c}.html"), encoding="utf-8")
    print("built urdu", today, "| pages:", len(list(out_dir.glob('*.html'))))


if __name__ == "__main__":
    main()
