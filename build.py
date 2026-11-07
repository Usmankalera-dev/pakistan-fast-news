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
    links = [("index.html", "Home")] + [(f"{c}.html", CAT_LABEL[c]) for c in CATS] + [("videos.html", "Videos"), ("ur/index.html", "اردو")]
    out = []
    for href, label in links:
        cls = ' class="active"' if href == active else ""
        if href == "videos.html":
            label = "▶ Videos"
            cls = ' class="vidlink active"' if href == active else ' class="vidlink"'
        out.append(f'<a href="{href}"{cls}>{label}</a>')
    return "\n".join(out)

def page(title, desc, canon, h1, body_html, json_ld, active="index.html"):
    now_s = datetime.now(PKT).strftime("%d %B %Y, %I:%M %p PKT")
    fsecs = "".join(f'<li><a href="{c}.html">{CAT_LABEL[c]}</a></li>' for c in CATS)
    fsecs += '<li><a href="videos.html">▶ Videos</a></li>'
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
        '<p class="fine">Full stories open on the publishers\u2019 sites — we never copy full articles. Videos play from the channels\u2019 official YouTube channels.</p></div>'
        '</div><div class="fbot"><span>© 2026 Pakistan Fast News</span>'
        '<span>Updated ' + now_s + ' · <a href="sitemap.xml">Sitemap</a></span></div></div></footer>')
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
<a class="logo" href="index.html"><img src="favicon.svg" alt="Pakistan Fast News logo" width="36" height="36" class="sitelogo"><span class="logotext">Pakistan <b>Fast News</b><small>Pakistan's fastest headlines</small></span></a>
<div class="clock"><span class="livedot" aria-hidden="true"></span><b>LIVE</b> <span id="clock"></span><span class="upd">Updated {now_s}</span></div>
</div></header>
<nav class="mainnav" aria-label="Sections"><div class="wrap">{nav(active)}</div></nav>
<main class="wrap">
<h1>{H.escape(h1)}</h1>
<div class="search"><input id="q" type="search" placeholder="Search headlines…" aria-label="Search headlines"></div>
{body_html}
</main>
{footer_html}
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

    # ---- Videos page ----
    videos = fetch_videos()
    print("videos:", len(videos), "| by channel:", {n: sum(1 for v in videos if v["channel"] == n) for n, _, _ in YT_CHANNELS})
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
            '<h3><button class="vtitle" data-vid="' + v["vid"] + '" data-title="' + H.escape(v["title"]) + '" data-chname="' + H.escape(v["channel"]) + '" data-desc="' + H.escape(v["desc"]) + '">' + H.escape(v["title"]) + '</button></h3></article>')
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
function openVid(vid,title,chname,desc){document.getElementById('modaltitle').textContent=title;
document.getElementById('modaldesc').textContent=desc||'';var a=document.getElementById('modalyt');a.href='https://www.youtube.com/watch?v='+vid;a.textContent='Watch on YouTube ('+chname+') →';
player.src='https://www.youtube-nocookie.com/embed/'+vid+'?autoplay=1&rel=0';modal.hidden=false;document.body.style.overflow='hidden';}
function closeVid(){player.src='';modal.hidden=true;document.body.style.overflow='';}
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
        '<div class="search"><input id="vq" type="search" placeholder="Search videos\u2026" aria-label="Search videos"></div>'
        '<div class="vgrid" id="vgrid">' + ''.join(vcards) + '</div>'
        '<p class="vcount" id="vcount"></p>'
        '<div class="modal" id="modal" role="dialog" aria-modal="true" aria-label="Video player" hidden>'
        '<div class="modalbox"><button class="modalclose" id="modalclose" aria-label="Close player">✕</button>'
        '<div class="playerwrap"><iframe id="player" title="YouTube video player" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div>'
        '<h3 id="modaltitle"></h3><p id="modaldesc"></p>'
        '<p><a id="modalyt" href="#" target="_blank" rel="noopener">Watch on YouTube →</a></p></div></div>'
        '<script>' + videos_js + '</script>')
    if len(videos) >= 100:
        (out_dir / "videos.html").write_text(page(
            "Pakistan News Videos — Watch Geo, ARY, Dawn, Samaa & More",
            "Watch the latest Pakistan news videos from Geo News, ARY News, Dawn News, Samaa, Dunya, Express, Hum, BOL, 92 News, Aaj and Neo — play them right here on Pakistan Fast News.",
            BASE + "/videos.html", "Pakistan news videos", videos_body, json.dumps(vids_ld, ensure_ascii=False), "videos.html"), encoding="utf-8")
    else:
        # Too few videos fetched (feeds degraded) — keep the last good videos.html instead of publishing a near-empty page.
        print(f"WARNING: only {len(videos)} videos fetched — keeping existing videos.html")

    # ---- sitemap + robots + 404 ----
    urls = [("", "1.0"), ("videos.html", "0.9"), ("ur/", "0.9")] + [(f"{c}.html", "0.8") for c in CATS] + [(f"ur/{c}.html", "0.8") for c in CATS]
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
