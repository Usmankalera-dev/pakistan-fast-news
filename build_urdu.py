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


def suno_btn(text, lang, label):
    """ایک کارڈ پر ایک سُنو بٹن (براؤزر کی speechSynthesis، بغیر چابی، بغیر خرچ)۔"""
    return (f'<button class="suno-btn" type="button" data-speak="{H.escape(text, quote=True)}" '
            f'data-lang="{lang}">{label}</button>')


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
                f'<div class="herobody">{meta}{desc}{readmore}' + share_row(it) + suno_btn(it["title"] + "۔ " + it.get("desc", ""), "ur", "🔊 سنو") + '</div></article>')
    thumb = ""
    if it.get("img"):
        thumb = (f'<a class="thumbwrap" href="{link}" target="_blank" rel="noopener" tabindex="-1" aria-hidden="true">'
                 f'<img class="thumb" src="{H.escape(it["img"])}" alt="" loading="lazy" onerror="this.closest(\'.thumbwrap\').remove()"></a>')
    else:
        thumb = (f'<a class="thumbwrap fallback" href="{link}" target="_blank" rel="noopener" tabindex="-1" aria-hidden="true">'
                 f'<img src="../{logo}" alt="{H.escape(it["source"])} logo"></a>')
    cls = "card hero" if big else "card"
    return (f'<article class="{cls} cat-{it["cat"]}">{thumb}{meta}{title}{desc}{readmore}' + share_row(it) + suno_btn(it["title"] + "۔ " + it.get("desc", ""), "ur", "🔊 سنو") + '</article>')


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
            f'<p>{H.escape(it["body"])}</p>' + share_row({"title": it["title"], "link": link}) + suno_btn(it["title"] + "۔ " + it.get("body", ""), "ur", "🔊 سنو") + '</article>')


def nav(active=""):
    links = [("index.html", "ہوم")] + [(f"{c}.html", CAT_LABEL[c]) for c in CATS] + [("editorial.html", "✍️ خصوصی")]
    out = []
    for href, label in links:
        cls = ' class="active"' if href == active else ""
        out.append(f'<a href="{href}"{cls}>{label}</a>')
    out.append('<a href="../videos.html" class="vidlink">▶ ویڈیوز</a>')
    out.append('<a href="live-tv.html">📺 لائیو ٹی وی</a>')
    out.append('<a href="prayer.html">🕌 نماز کے اوقات</a>')
    out.append('<a href="cricket.html">🏏 کرکٹ</a>')
    out.append('<a href="search.html">🔍 تلاش</a>')
    out.append('<a href="../index.html" class="vidlink">English</a>')
    return "\n".join(out)


def newsletter_box(box_id=""):
    """مفت FormSubmit سائن اپ (کوئی اکاؤنٹ نہیں)۔ چالو کرنا: پہلی سائن اپ کے بعد FormSubmit عثمان کے یونیورسٹی ان باکس میں تصدیقی ای میل بھیجے گا — اس پر کلک کریں۔"""
    idattr = f' id="{box_id}"' if box_id else ""
    return (f'<div class="newsbox"{idattr}>'
            '<h3>📬 سرخیاں اپنے ان باکس میں پائیں</h3>'
            '<p>روزانہ ایک مختصر ای میل — پاکستان کی تیز ترین سرخیاں، بالکل مفت۔ کوئی سپیم نہیں، کسی بھی وقت ان سبسکرائب کریں۔</p>'
            '<form action="https://formsubmit.co/su92-bsaim-f25-025@superior.edu.pk" method="POST">'
            '<input type="hidden" name="_subject" value="New subscriber — Pakistan Fast News">'
            '<input type="hidden" name="_template" value="table">'
            '<input type="hidden" name="_captcha" value="false">'
            '<input type="hidden" name="_autoresponse" value="Thank you for subscribing to Pakistan Fast News! You will get the fastest headlines from Pakistan and the world in your inbox. — Usman Kalera">'
            '<input type="email" name="email" placeholder="آپ کا ای میل پتہ" required aria-label="ای میل پتہ">'
            '<button type="submit">سبسکرائب کریں</button></form>'
            '<p class="fine">FormSubmit کے ذریعے — آپ کا ای میل صرف اس نیوز لیٹر کے لیے استعمال ہوگا۔</p></div>')


def page(title, desc, canon, h1, body_html, json_ld, active="index.html", ticker=""):
    now_s = datetime.now(PKT).strftime("%d %B %Y, %I:%M %p PKT")
    fsecs = "".join(f'<li><a href="{c}.html">{CAT_LABEL[c]}</a></li>' for c in CATS)
    fsecs += '<li><a href="editorial.html">✍️ خصوصی خبریں</a></li>'
    fsecs += '<li><a href="live-tv.html">📺 لائیو ٹی وی</a></li>'
    fsecs += '<li><a href="prayer.html">🕌 نماز کے اوقات</a></li>'
    fsecs += '<li><a href="cricket.html">🏏 کرکٹ</a></li>'
    fsecs += '<li><a href="search.html">🔍 تلاش</a></li>'
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
        '</div>' + newsletter_box() + '<div class="fbot"><span>© 2026 پاکستان فاسٹ نیوز</span>'
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
<link rel="stylesheet" href="../styles.css?v=20261114r1">
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
<div class="trow"><span class="tlabel">💵 ڈالر</span><span class="tval">$1 = <span id="w-usd">…</span><span class="conv"><input id="w-conv" type="number" value="10" min="0" inputmode="decimal" aria-label="رقم"> <select id="w-cur" aria-label="کرنسی"><option value="USD" selected>USD</option><option value="GBP">GBP</option><option value="EUR">EUR</option><option value="SAR">SAR</option><option value="AED">AED</option><option value="CNY">CNY</option><option value="JPY">JPY</option><option value="INR">INR</option></select> <button type="button" id="w-swap" title="سمت بدلیں" aria-label="سمت بدلیں">⇄</button> = <b id="w-conv-out">…</b></span></span></div>
<div class="trow trow-fx"><span class="tlabel">💱 کرنسیاں</span><span class="tval"><span id="w-fx">…</span><span class="fxtrend" id="w-fxtrend"></span></span></div>
<div class="trow"><span class="tlabel">🌙 ہجری تاریخ</span><span class="tval" id="w-hijri">…</span></div>
<div class="trow"><span class="tlabel">🪙 سونا · 1 تولہ</span><span class="tval" id="w-gold">…</span></div>
<div class="trow"><span class="tlabel">🌫️ ہوا کا معیار</span><span class="tval" id="w-aqi">…</span></div>
<div class="trow trow-wx"><span class="tlabel">🌤️ موسم</span><span class="tval" id="w-weather">…</span></div>
<div class="trow trow-pr"><span class="tlabel">🕌 نماز</span><span class="tval"><span class="pcities"><button type="button" class="pcity active" data-city="Lahore">لاہور</button><button type="button" class="pcity" data-city="Karachi">کراچی</button><button type="button" class="pcity" data-city="Islamabad">اسلام آباد</button></span><span id="w-prayer">…</span></span></div>
<div class="trow trow-fc"><span class="tlabel">📅 لاہور · 7 دن</span><span class="tval"><span class="fcrow" id="w-forecast"></span></span></div>
<div class="tsrc" id="w-updated"></div>
</div>
<h1>{H.escape(h1)}</h1>
<div class="search"><span class="searchicon" aria-hidden="true">🔍</span><input id="q" type="search" placeholder="خبریں تلاش کریں…" aria-label="خبریں تلاش کریں"></div>
{body_html}
</main>
{footer_html}
<script src="../script.js?v=20261114r1" defer></script>
<button id="totop" class="totop" type="button" aria-label="اوپر جائیں">↑</button>
</body>
</html>
"""


PRAYER_BODY_UR = '<p class="crumb"><a href="index.html">ہوم</a> / نماز کے اوقات</p><p class="vintro">ماہانہ نماز کا ٹائم ٹیبل — لاہور، کراچی اور اسلام آباد کے لیے فجر سے عشاء تک۔ اوقات Aladhan نماز API سے براہ راست آتے ہیں (طریقہ: یونیورسٹی آف اسلامک سائنسز، کراچی)۔</p><div class="prayerctl"><span class="pcities" id="prayer-cities"><button type="button" class="pcity active" data-city="Lahore">لاہور</button><button type="button" class="pcity" data-city="Karachi">کراچی</button><button type="button" class="pcity" data-city="Islamabad">اسلام آباد</button></span><span class="monthnav"><button type="button" id="pmonth-prev" aria-label="پچھلا مہینہ">‹ پچھلا</button><b id="pmonth-label">…</b><button type="button" id="pmonth-next" aria-label="اگلا مہینہ">اگلا ›</button></span></div><div class="ptable-wrap"><table class="ptable" id="prayer-table"><thead><tr><th>دن</th><th>تاریخ</th><th>فجر</th><th>طلوع آفتاب</th><th>ظہر</th><th>عصر</th><th>مغرب</th><th>عشاء</th></tr></thead><tbody><tr><td colspan="8" class="ploading">نماز کے اوقات لوڈ ہو رہے ہیں…</td></tr></tbody></table></div><section class="hijri-sec"><h2>📅 ہجری کیلنڈر — <span id="hijri-month-label">…</span></h2><div class="hijri-cal" id="hijri-cal"><p class="ploading">ہجری کیلنڈر لوڈ ہو رہا ہے…</p></div></section><section class="qibla-box" id="qibla-box" hidden><h2>🧭 قبلہ کی سمت — <span id="qibla-city">لاہور</span></h2><p class="qibla-line"><span class="qarrow" id="qibla-arrow">➤</span> <span id="qibla-text">…</span></p><p class="fine">ماخذ: Aladhan قبلہ API · سمت شہر کے مرکز سے ہے۔</p></section><p class="fine">ماخذ: Aladhan نماز API · تمام اوقات مقامی وقت (PKT) کے مطابق ہیں۔ ہجری تاریخ ہر عیسوی تاریخ کے نیچے دکھائی گئی ہے۔</p><script>\n(function(){\n  var months=["جنوری","فروری","مارچ","اپریل","مئی","جون","جولائی","اگست","ستمبر","اکتوبر","نومبر","دسمبر"];\n  var wdMap={"Monday":"پیر","Tuesday":"منگل","Wednesday":"بدھ","Thursday":"جمعرات","Friday":"جمعہ","Saturday":"ہفتہ","Sunday":"اتوار"};\n  var city="Lahore";\n  var now=new Date(new Date().toLocaleString("en-US",{timeZone:"Asia/Karachi"}));\n  var year=now.getFullYear(), month=now.getMonth()+1;\n  function fmt12(t){var p=String(t).replace(/\\(.*\\)/,"").trim().split(":");var h=+p[0],m=p[1];var ap=h>=12?"PM":"AM";h=h%12;if(h===0)h=12;return h+":"+m+" "+ap;}\n  function load(){\n    document.getElementById("pmonth-label").textContent=months[month-1]+" "+year;\n    loadQibla();\n    var tb=document.querySelector("#prayer-table tbody");\n    tb.innerHTML=\'<tr><td colspan="8" class="ploading">نماز کے اوقات لوڈ ہو رہے ہیں…</td></tr>\';\n    fetch("https://api.aladhan.com/v1/calendarByCity/"+year+"/"+month+"?city="+encodeURIComponent(city)+"&country=Pakistan&method=1")\n      .then(function(r){if(!r.ok)throw new Error("http "+r.status);return r.json();}).then(function(d){\n        if(!d||!d.data||!d.data.length)throw new Error("empty");\n        var today=new Date(new Date().toLocaleString("en-US",{timeZone:"Asia/Karachi"}));\n        var rows=d.data.map(function(day){\n          var g=day.date.gregorian,hj=day.date.hijri,t=day.timings;\n          var isToday=(+g.day===today.getDate()&&+g.month.number===today.getMonth()+1&&+g.year===today.getFullYear());\n          return \'<tr\'+(isToday?\' class="today-row"\':\'\')+\'><td>\'+(wdMap[g.weekday.en]||g.weekday.en)+\'</td><td><b>\'+g.day+\' \'+months[+g.month.number-1]+\'</b><br><small>\'+hj.day+\' \'+hj.month.ar+\' \'+hj.year+\'ھ</small></td><td>\'+fmt12(t.Fajr)+\'</td><td>\'+fmt12(t.Sunrise)+\'</td><td>\'+fmt12(t.Dhuhr)+\'</td><td>\'+fmt12(t.Asr)+\'</td><td>\'+fmt12(t.Maghrib)+\'</td><td>\'+fmt12(t.Isha)+\'</td></tr>\';\n        });\n        tb.innerHTML=rows.join("");\n        renderHijri(d.data);\n      }).catch(function(){\n        tb.innerHTML=\'<tr><td colspan="8" class="ploading">نماز کے اوقات ابھی لوڈ نہیں ہو سکے — براہ کرم اپنا انٹرنیٹ چیک کر کے دوبارہ کوشش کریں۔</td></tr>\';\n      });\n  }\n  document.querySelectorAll("#prayer-cities .pcity").forEach(function(b){b.addEventListener("click",function(){city=b.getAttribute("data-city");document.querySelectorAll("#prayer-cities .pcity").forEach(function(x){x.classList.toggle("active",x===b);});load();});});\n  document.getElementById("pmonth-prev").addEventListener("click",function(){month--;if(month<1){month=12;year--;}load();});\n  document.getElementById("pmonth-next").addEventListener("click",function(){month++;if(month>12){month=1;year++;}load();});\n    var qiblaCoords={"Lahore":[31.5204,74.3587],"Karachi":[24.8607,67.0011],"Islamabad":[33.6844,73.0479]};\n  var qiblaCityUr={"Lahore":"لاہور","Karachi":"کراچی","Islamabad":"اسلام آباد"};\n  function cardinal(deg){var dirs=["شمال","شمال مشرق","مشرق","جنوب مشرق","جنوب","جنوب مغرب","مغرب","شمال مغرب"];return dirs[Math.round(deg/45)%8];}\n  function renderHijri(data){\n    var cal=document.getElementById("hijri-cal");if(!cal)return;\n    var seen=[];data.forEach(function(day){var m=day.date.hijri.month.ar+" "+day.date.hijri.year;if(seen.indexOf(m)<0)seen.push(m);});\n    document.getElementById("hijri-month-label").textContent=seen.join(" – ")+"ھ";\n    var wd=["پیر","منگل","بدھ","جمعرات","جمعہ","ہفتہ","اتوار"];\n    var first=new Date(data[0].date.gregorian.year,data[0].date.gregorian.month.number-1,1);\n    var startIdx=(first.getDay()+6)%7;\n    var today=new Date(new Date().toLocaleString("en-US",{timeZone:"Asia/Karachi"}));\n    cal.innerHTML="";\n    var head=document.createElement("div");head.className="hcal-head";\n    wd.forEach(function(w){var s=document.createElement("span");s.textContent=w;head.appendChild(s);});\n    cal.appendChild(head);\n    var grid=document.createElement("div");grid.className="hcal-grid";\n    for(var i=0;i<startIdx;i++){var e=document.createElement("span");e.className="hday empty";grid.appendChild(e);}\n    data.forEach(function(day){\n      var g=day.date.gregorian,hj=day.date.hijri;\n      var c=document.createElement("span");c.className="hday";\n      var isToday=(+g.day===today.getDate()&&+g.month.number===today.getMonth()+1&&+g.year===today.getFullYear());\n      if(isToday)c.className="hday today";\n      var b=document.createElement("b");b.textContent=hj.day;c.appendChild(b);\n      var it=document.createElement("i");it.textContent=g.day+" "+months[+g.month.number-1].slice(0,3);c.appendChild(it);\n      grid.appendChild(c);\n    });\n    cal.appendChild(grid);\n  }\n  function loadQibla(){\n    var box=document.getElementById("qibla-box");if(!box)return;\n    var c=qiblaCoords[city]||qiblaCoords.Lahore;\n    document.getElementById("qibla-city").textContent=qiblaCityUr[city]||city;\n    fetch("https://api.aladhan.com/v1/qibla/"+c[0]+"/"+c[1])\n      .then(function(r){if(!r.ok)throw new Error("http "+r.status);return r.json();}).then(function(d){\n        if(!d||!d.data||d.data.direction==null)throw new Error("empty");\n        var deg=Math.round(d.data.direction*10)/10;\n        document.getElementById("qibla-text").textContent="قبلہ: "+deg+"° · "+cardinal(deg);\n        document.getElementById("qibla-arrow").style.transform="rotate("+(deg-90)+"deg)";\n        box.hidden=false;\n      }).catch(function(){box.hidden=true;});\n  }\n  load();\n})();\n</script>'


LIVE_TV_BODY_UR = '<p class="crumb"><a href="index.html">ہوم</a> / لائیو ٹی وی</p><p class="vintro">پاکستان کے 11 بڑے نیوز چینلز لائیو دیکھیں — ان کی آفیشل یوٹیوب لائیو اسٹریم سے۔ نیچے سے چینل چنیں، اسٹریم یہیں اسی صفحے پر چل پڑے گی۔</p><div class="tvplayer" id="tvplayer"><p class="tvhint">▶ لائیو اسٹریم شروع کرنے کے لیے نیچے سے چینل چنیں۔</p></div><div class="tvgrid"><article class="tvcard"><img src="../yt-geo.jpg" alt="جیو نیوز لوگو" width="64" height="64" loading="lazy"><h3>جیو نیوز</h3><button class="tvbtn" type="button" data-ch="UC_vt34wimdCzdkrzVejwX9g" data-name="جیو نیوز">▶ لائیو دیکھیں</button><a href="https://www.youtube.com/channel/UC_vt34wimdCzdkrzVejwX9g" target="_blank" rel="noopener">یوٹیوب پر کھولیں ↗</a></article><article class="tvcard"><img src="../yt-ary.jpg" alt="اے آر وائی نیوز لوگو" width="64" height="64" loading="lazy"><h3>اے آر وائی نیوز</h3><button class="tvbtn" type="button" data-ch="UCMmpLL2ucRHAXbNHiCPyIyg" data-name="اے آر وائی نیوز">▶ لائیو دیکھیں</button><a href="https://www.youtube.com/channel/UCMmpLL2ucRHAXbNHiCPyIyg" target="_blank" rel="noopener">یوٹیوب پر کھولیں ↗</a></article><article class="tvcard"><img src="../yt-dawn.jpg" alt="ڈان نیوز لوگو" width="64" height="64" loading="lazy"><h3>ڈان نیوز</h3><button class="tvbtn" type="button" data-ch="UCaxR-D8FjZ-2otbU0_Y2grg" data-name="ڈان نیوز">▶ لائیو دیکھیں</button><a href="https://www.youtube.com/channel/UCaxR-D8FjZ-2otbU0_Y2grg" target="_blank" rel="noopener">یوٹیوب پر کھولیں ↗</a></article><article class="tvcard"><img src="../yt-samaa.jpg" alt="سماء ٹی وی لوگو" width="64" height="64" loading="lazy"><h3>سماء ٹی وی</h3><button class="tvbtn" type="button" data-ch="UCJekW1Vj5fCVEGdye_mBN6Q" data-name="سماء ٹی وی">▶ لائیو دیکھیں</button><a href="https://www.youtube.com/channel/UCJekW1Vj5fCVEGdye_mBN6Q" target="_blank" rel="noopener">یوٹیوب پر کھولیں ↗</a></article><article class="tvcard"><img src="../yt-dunya.jpg" alt="دنیا نیوز لوگو" width="64" height="64" loading="lazy"><h3>دنیا نیوز</h3><button class="tvbtn" type="button" data-ch="UCnMBV5Iw4WqKILKue1nP6Hg" data-name="دنیا نیوز">▶ لائیو دیکھیں</button><a href="https://www.youtube.com/channel/UCnMBV5Iw4WqKILKue1nP6Hg" target="_blank" rel="noopener">یوٹیوب پر کھولیں ↗</a></article><article class="tvcard"><img src="../yt-express.jpg" alt="ایکسپریس نیوز لوگو" width="64" height="64" loading="lazy"><h3>ایکسپریس نیوز</h3><button class="tvbtn" type="button" data-ch="UCTur7oM6mLL0rM2k0znuZpQ" data-name="ایکسپریس نیوز">▶ لائیو دیکھیں</button><a href="https://www.youtube.com/channel/UCTur7oM6mLL0rM2k0znuZpQ" target="_blank" rel="noopener">یوٹیوب پر کھولیں ↗</a></article><article class="tvcard"><img src="../yt-hum.jpg" alt="ہم نیوز لوگو" width="64" height="64" loading="lazy"><h3>ہم نیوز</h3><button class="tvbtn" type="button" data-ch="UC0Um3pnZ2WGBEeoA3BX2sKw" data-name="ہم نیوز">▶ لائیو دیکھیں</button><a href="https://www.youtube.com/channel/UC0Um3pnZ2WGBEeoA3BX2sKw" target="_blank" rel="noopener">یوٹیوب پر کھولیں ↗</a></article><article class="tvcard"><img src="../yt-bol.jpg" alt="بول نیوز لوگو" width="64" height="64" loading="lazy"><h3>بول نیوز</h3><button class="tvbtn" type="button" data-ch="UC2ToZG9RA1_A5kRwxqP7rZg" data-name="بول نیوز">▶ لائیو دیکھیں</button><a href="https://www.youtube.com/channel/UC2ToZG9RA1_A5kRwxqP7rZg" target="_blank" rel="noopener">یوٹیوب پر کھولیں ↗</a></article><article class="tvcard"><img src="../yt-92news.jpg" alt="92 نیوز ایچ ڈی لوگو" width="64" height="64" loading="lazy"><h3>92 نیوز ایچ ڈی</h3><button class="tvbtn" type="button" data-ch="UCsgC5cbz3DE2Shh34gNKiog" data-name="92 نیوز ایچ ڈی">▶ لائیو دیکھیں</button><a href="https://www.youtube.com/channel/UCsgC5cbz3DE2Shh34gNKiog" target="_blank" rel="noopener">یوٹیوب پر کھولیں ↗</a></article><article class="tvcard"><img src="../yt-aaj.jpg" alt="آج نیوز لوگو" width="64" height="64" loading="lazy"><h3>آج نیوز</h3><button class="tvbtn" type="button" data-ch="UCgBAPAcLsh_MAPvJprIz89w" data-name="آج نیوز">▶ لائیو دیکھیں</button><a href="https://www.youtube.com/channel/UCgBAPAcLsh_MAPvJprIz89w" target="_blank" rel="noopener">یوٹیوب پر کھولیں ↗</a></article><article class="tvcard"><img src="../yt-neo.jpg" alt="نیو نیوز لوگو" width="64" height="64" loading="lazy"><h3>نیو نیوز</h3><button class="tvbtn" type="button" data-ch="UCoVaeayixjVI12mAlmMSsXg" data-name="نیو نیوز">▶ لائیو دیکھیں</button><a href="https://www.youtube.com/channel/UCoVaeayixjVI12mAlmMSsXg" target="_blank" rel="noopener">یوٹیوب پر کھولیں ↗</a></article></div><p class="fine">یہ چینلز کی آفیشل یوٹیوب لائیو نشریات ہیں (youtube-nocookie ایمبیڈ)۔ اگر کوئی چینل اس وقت لائیو نہیں ہے تو یوٹیوب اس کا آف لائن پیغام دکھائے گا — دوسرا چینل آزمائیں۔</p><script>\n(function(){\n  var player=document.getElementById("tvplayer");\n  document.querySelectorAll(".tvbtn").forEach(function(b){\n    b.addEventListener("click",function(){\n      var ch=b.getAttribute("data-ch"), name=b.getAttribute("data-name");\n      player.innerHTML=\'<iframe title="لائیو ٹی وی — \'+name+\'" src="https://www.youtube-nocookie.com/embed/live_stream?channel=\'+ch+\'&autoplay=1" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>\';\n      document.querySelectorAll(".tvcard").forEach(function(c){c.classList.toggle("active", c===b.closest(".tvcard"));});\n      player.scrollIntoView({behavior:"smooth", block:"center"});\n    });\n  });\n})();\n</script>'


def suno_player(lang):
    """Play-all bar for the homepage: reads every visible card's listen button in
    order, with a speed control. Shown only when speechSynthesis exists (script.js
    unhides it); the per-card buttons keep working on their own."""
    if lang == "ur":
        return ('<div class="suno-player" id="suno-player" hidden>'
                '<button type="button" class="suno-playall" id="suno-playall">▶ تمام سرخیاں سنو</button>'
                '<button type="button" class="suno-stop" id="suno-stop" hidden>⏹ بند کریں</button>'
                '<span class="suno-speed" role="group" aria-label="پڑھنے کی رفتار">'
                '<button type="button" data-rate="0.75">0.75x</button>'
                '<button type="button" data-rate="1" class="active">1x</button>'
                '<button type="button" data-rate="1.25">1.25x</button></span>'
                '<span class="suno-now" id="suno-now"></span></div>')
    return ('<div class="suno-player" id="suno-player" hidden>'
            '<button type="button" class="suno-playall" id="suno-playall">▶ Play all headlines</button>'
            '<button type="button" class="suno-stop" id="suno-stop" hidden>⏹ Stop</button>'
            '<span class="suno-speed" role="group" aria-label="Reading speed">'
            '<button type="button" data-rate="0.75">0.75x</button>'
            '<button type="button" data-rate="1" class="active">1x</button>'
            '<button type="button" data-rate="1.25">1.25x</button></span>'
            '<span class="suno-now" id="suno-now"></span></div>')


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
    cricket_strip = ('<section class="cstrip" id="cricket-strip" data-lang="ur"><h2>🏏 کرکٹ لائیو اسکور</h2>'
                     '<div class="cbody"><p class="cloading">لائیو اسکور لوڈ ہو رہا ہے…</p></div>'
                     '<p class="fine" id="cricket-src">لائیو اسکور: <a href="https://sportscore.com/cricket" target="_blank" rel="noopener">Powered by SportScore</a></p></section>')
    home_body = (f'<section><h2 class="toplabel">اہم خبر</h2>{card(hero, now, big=True)}</section>'
                 + suno_player("ur")
                 + cricket_strip +
                 f'<section><h2>تازہ ترین خبریں</h2><div class="grid" id="latest-ur">{"".join(card(i, now) for i in rest)}</div></section>'
                 + ed_section + newsletter_box("newsletter") + sections)
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
    comments_section = ('<section class="comments"><h2>💬 تبصرے</h2>'
        '<p class="cnote">تبصرے جلد کھلیں گے — آپ GitHub سے سائن ان کر کے یہاں گفتگو میں شامل ہو سکیں گے۔</p>'
        '<!-- GISCUS سیٹ اپ (ایک بار، GitHub میں — پھر نیچے والی اسکرپٹ کو ان کمنٹ کریں):\n'
        '  1. ریپو → Settings → General → Features → "Discussions" پر ٹک کریں۔\n'
        '  2. اس ریپو پر giscus ایپ انسٹال کریں: https://github.com/apps/giscus\n'
        '  3. Discussions میں "General" کیٹیگری استعمال کریں (Discussions چالو ہوتے ہی خود بن جاتی ہے)۔\n'
        '  4. https://giscus.app پر جائیں، ریپو Usmankalera-dev/pakistan-fast-news لکھیں، کیٹیگری چنیں،\n'
        '     وہاں دکھائی گئی repo-id + category-id نیچے چسپاں کریں، اور اسکرپٹ کو ان کمنٹ کریں۔\n'
        '  <script src="https://giscus.app/client.js" data-repo="Usmankalera-dev/pakistan-fast-news" data-repo-id="TODO-REPO-ID" data-category="General" data-category-id="TODO-CATEGORY-ID" data-mapping="pathname" data-strict="0" data-reactions-enabled="1" data-emit-metadata="0" data-input-position="top" data-theme="preferred_color_scheme" data-lang="ur" crossorigin="anonymous" async></scr' + 'ipt>\n'
        '--></section>')
    ed_body = ('<p class="crumb"><a href="index.html">ہوم</a> / خصوصی خبریں</p>'
               '<p class="secupd">پاکستان فاسٹ نیوز کے لیے عثمان کلیرہ کی لکھی ہوئی اصل خبریں — روزانہ تازہ کہانیاں۔</p>'
               '<div class="grid">' + "".join(ed_cards) + '</div>' + comments_section if ed_cards else
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
    # ---- Live TV page (official YouTube live_stream embeds, click-to-load) ----
    live_ld = {"@context": "https://schema.org", "@type": "WebPage", "name": "لائیو ٹی وی — پاکستانی نیوز چینلز | پاکستان فاسٹ نیوز",
               "url": BASE + "/ur/live-tv.html"}
    (out_dir / "live-tv.html").write_text(page(
        "لائیو ٹی وی — 11 پاکستانی نیوز چینلز لائیو | پاکستان فاسٹ نیوز اردو",
        "پاکستانی نیوز چینلز لائیو دیکھیں — جیو نیوز، اے آر وائی نیوز، ڈان نیوز، سماء ٹی وی، دنیا نیوز، ایکسپریس نیوز، ہم نیوز، بول نیوز، 92 نیوز ایچ ڈی، آج نیوز اور نیو نیوز، ان کی آفیشل یوٹیوب لائیو اسٹریم سے۔",
        BASE + "/ur/live-tv.html", "📺 لائیو ٹی وی — پاکستانی نیوز چینلز", LIVE_TV_BODY_UR,
        json.dumps(live_ld, ensure_ascii=False), "live-tv.html"), encoding="utf-8")

    # ---- Prayer timetable page (monthly, Aladhan calendar API, client-side) ----
    prayer_ld = {"@context": "https://schema.org", "@type": "WebPage", "name": "نماز کے اوقات — ماہانہ ٹائم ٹیبل | پاکستان فاسٹ نیوز",
                 "url": BASE + "/ur/prayer.html"}
    (out_dir / "prayer.html").write_text(page(
        "نماز کے اوقات — ماہانہ ٹائم ٹیبل (لاہور، کراچی، اسلام آباد) | پاکستان فاسٹ نیوز اردو",
        "لاہور، کراچی اور اسلام آباد کے لیے ماہانہ نماز کا ٹائم ٹیبل — فجر، طلوع آفتاب، ظہر، عصر، مغرب اور عشاء، ہجری تاریخوں کے ساتھ، Aladhan API سے۔",
        BASE + "/ur/prayer.html", "🕌 نماز کے اوقات — ماہانہ ٹائم ٹیبل", PRAYER_BODY_UR,
        json.dumps(prayer_ld, ensure_ascii=False), "prayer.html"), encoding="utf-8")
    # ---- Cricket full scores page (SportScore free API, client-side) ----
    cricket_ld = {"@context": "https://schema.org", "@type": "WebPage", "name": "کرکٹ لائیو اسکور — تمام لائیو میچ اور نتائج | پاکستان فاسٹ نیوز",
                  "url": BASE + "/ur/cricket.html"}
    cricket_body = ('<p class="crumb"><a href="index.html">ہوم</a> / کرکٹ</p>'
        '<p class="vintro">کرکٹ کے لائیو اسکور اور حالیہ نتائج — ہر لائیو میچ، ہر 2 منٹ بعد تازہ۔ اسکور SportScore سے براہ راست آتے ہیں؛ یہاں کچھ بھی بنایا ہوا نہیں ہے۔</p>'
        '<div id="cricket-page" data-lang="ur">'
        '<section><h2>🔴 ابھی لائیو</h2><div id="cricket-live-list"><p class="cloading">لائیو اسکور لوڈ ہو رہا ہے…</p></div></section>'
        '<section><h2>✅ حالیہ نتائج</h2><div id="cricket-fin-list"><p class="cloading">نتائج لوڈ ہو رہے ہیں…</p></div></section>'
        '<p class="fine">لائیو اسکور: <a href="https://sportscore.com/cricket" target="_blank" rel="noopener">Powered by SportScore</a> · <span id="cricket-updated"></span> <button class="cRetry" type="button" id="cricket-refresh">↻ تازہ کریں</button></p></div>')
    (out_dir / "cricket.html").write_text(page(
        "کرکٹ لائیو اسکور — تمام لائیو میچ اور نتائج | پاکستان فاسٹ نیوز اردو",
        "ہر لائیو میچ کے کرکٹ اسکور اور حالیہ نتائج، ہر 2 منٹ بعد تازہ — SportScore سے۔",
        BASE + "/ur/cricket.html", "🏏 کرکٹ لائیو اسکور", cricket_body,
        json.dumps(cricket_ld, ensure_ascii=False), "cricket.html"), encoding="utf-8")

    # ---- Global search page (تمام سرخیاں + خصوصی خبریں تلاش کریں) ----
    search_index = [{"t": i["title"], "l": i["link"], "c": CAT_LABEL[i["cat"]], "s": i["source"], "d": i["dt"].strftime("%d %b %Y")} for i in items]
    for n, i in enumerate(ed_items):
        search_index.append({"t": i["title"], "l": BASE + "/ur/editorial.html#ed-" + str(n), "c": CAT_LABEL[i.get("cat", "pakistan")], "s": "✍️ عثمان کلیرہ", "d": i["date"]})
    search_json = json.dumps(search_index, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    search_ld = {"@context": "https://schema.org", "@type": "WebPage", "name": "تمام خبریں تلاش کریں | پاکستان فاسٹ نیوز",
                 "url": BASE + "/ur/search.html"}
    search_body = ('<p class="crumb"><a href="index.html">ہوم</a> / تلاش</p>'
        '<p class="vintro">اس سائٹ کی ہر سرخی تلاش کریں — تمام شعبے، اور ہماری خصوصی خبریں بھی۔ کم از کم 2 حروف لکھیں۔</p>'
        '<div class="search big"><span class="searchicon" aria-hidden="true">🔍</span><input id="search-box" type="search" placeholder="تمام خبریں تلاش کریں…" aria-label="تمام خبریں تلاش کریں"></div>'
        '<p class="scount" id="search-count"></p>'
        '<div id="search-results"></div>'
        '<script type="application/json" id="search-index">' + search_json + '</script>')
    (out_dir / "search.html").write_text(page(
        "تمام خبریں تلاش کریں | پاکستان فاسٹ نیوز اردو",
        "پاکستان فاسٹ نیوز کی ہر سرخی تلاش کریں — تمام شعبے اور خصوصی خبریں، ایک ہی جگہ۔",
        BASE + "/ur/search.html", "🔍 تمام خبریں تلاش کریں", search_body,
        json.dumps(search_ld, ensure_ascii=False), "search.html"), encoding="utf-8")
    print("built urdu", today, "| pages:", len(list(out_dir.glob('*.html'))))


if __name__ == "__main__":
    main()
