// Pakistan Fast News — tiny progressive enhancement: live PKT clock, headline search,
// and a best-effort refresh of the Latest list from Dawn's public RSS (falls back silently).
(function () {
  var clock = document.getElementById("clock");
  function tick() {
    if (!clock) return;
    clock.textContent = new Date().toLocaleString("en-GB", {
      timeZone: "Asia/Karachi", weekday: "short", day: "2-digit", month: "short",
      hour: "2-digit", minute: "2-digit", hour12: true
    }) + " PKT";
  }
  tick(); setInterval(tick, 30000);
  var q = document.getElementById("q");
  if (q) q.addEventListener("input", function () {
    var v = q.value.toLowerCase();
    document.querySelectorAll(".card").forEach(function (c) {
      c.style.display = c.textContent.toLowerCase().includes(v) ? "" : "none";
    });
  });
  var latest = document.getElementById("latest");
  if (latest) {
    fetch("https://api.rss2json.com/v1/api.json?rss_url=" + encodeURIComponent("https://www.dawn.com/feeds/home"))
      .then(function (r) { return r.json(); }).then(function (d) {
        if (!d || !d.items) return;
        var have = new Set(Array.from(latest.querySelectorAll("h3 a")).map(function (a) { return a.href; }));
        var fresh = d.items.filter(function (it) { return it.link && !have.has(it.link); }).slice(0, 5);
        fresh.reverse().forEach(function (it) {
          var art = document.createElement("article");
          art.className = "card";
          var when = it.pubDate ? new Date(it.pubDate) : new Date();
          art.innerHTML = '<div class="meta"><img class="srclogo" src="logo-dawn.png" alt="Dawn logo" width="84" height="20" loading="lazy"><span class="src">Dawn</span><span class="chip pakistan">Pakistan</span><time>' +
            when.toLocaleString("en-GB", { timeZone: "Asia/Karachi", day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", hour12: true }) +
            ' PKT</time></div><h3><a href="' + it.link + '" target="_blank" rel="noopener"></a></h3><a class="readmore" href="' + it.link + '" target="_blank" rel="noopener">Read full story at Dawn →</a>' +
            '<div class="share"><a class="share-wa" href="https://wa.me/?text=' + encodeURIComponent(it.title + " " + it.link) + '" target="_blank" rel="noopener">WhatsApp ↗</a>' +
            '<a class="share-x" href="https://twitter.com/intent/tweet?text=' + encodeURIComponent(it.title + " " + it.link) + '" target="_blank" rel="noopener">X ↗</a>' +
            '<a class="share-fb" href="https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(it.link) + '" target="_blank" rel="noopener">Facebook ↗</a>' +
            '<button class="share-copy" type="button" data-link="' + it.link.replace(/"/g, "%22") + '">Copy link</button>' +
            '<button class="share-native" type="button" data-link="' + it.link.replace(/"/g, "%22") + '">Share</button></div>';
          art.querySelector("h3 a").textContent = it.title;
          var sb = document.createElement("button");
          sb.className = "suno-btn"; sb.type = "button";
          sb.setAttribute("data-speak", it.title); sb.setAttribute("data-lang", "en");
          sb.textContent = "🔊 Listen";
          art.appendChild(sb);
          var nb = art.querySelector(".share-native");
          nb.setAttribute("data-title", it.title);
          if (navigator.share) { nb.style.display = "inline-block"; }
          latest.prepend(art);
        });
      }).catch(function () { /* keep the baked headlines */ });
  }
})();

// Today widget: live USD/PKR rate, gold-per-tola estimate, 3-city weather, Lahore prayer times.
// All sources are free, no-key APIs; every value degrades to "—" if its source fails.
(function () {
  var w = document.getElementById("today-widget");
  if (!w) return;
  var ur = document.documentElement.lang === "ur";
  function $(id) { return document.getElementById(id); }
  function fmt(n) { return "Rs " + Math.round(n).toLocaleString("en-US"); }
  function toMin(t) { var p = String(t).replace(/\(.*\)/, "").trim().split(":"); return (+p[0]) * 60 + (+p[1]); }
  function fmt12(t) {
    var p = String(t).replace(/\(.*\)/, "").trim().split(":"), h = +p[0], m = p[1];
    var ap = h >= 12 ? "PM" : "AM"; h = h % 12; if (h === 0) h = 12;
    return h + ":" + m + " " + ap;
  }
  function pktParts() {
    var s = new Date().toLocaleString("en-US", { timeZone: "Asia/Karachi" });
    var d = new Date(s);
    return { d: d, dd: String(d.getDate()).padStart(2, "0"), mm: String(d.getMonth() + 1).padStart(2, "0"), yy: d.getFullYear() };
  }
  var pk = pktParts();
  var cities = ["Lahore", "Karachi", "Islamabad"];
  var prs = Promise.all(cities.map(function (c) {
    return getJSON("https://api.aladhan.com/v1/timingsByCity/" + pk.dd + "-" + pk.mm + "-" + pk.yy + "?city=" + c + "&country=Pakistan&method=1").then(function (d) { return d && d.data ? d.data : null; });
  }));
  var prayerCity = "Lahore";
  try { prayerCity = localStorage.getItem("pfn-prayer-city") || "Lahore"; } catch (e) {}
  var prayerData = {};
  var prayerTimer = null;
  function renderPrayer() {
    var t = prayerData[prayerCity];
    if (!t) { $("w-prayer").textContent = "—"; return; }
    var keys = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"];
    var names = ur ? ["فجر", "ظہر", "عصر", "مغرب", "عشاء"] : keys;
    prayerParts = keys.map(function (k, i) { return { k: k, n: names[i], m: toMin(t[k]), s: fmt12(t[k]) }; });
    var nowMin = pktParts().d.getHours() * 60 + pktParts().d.getMinutes(), next = null;
    for (var i = 0; i < prayerParts.length; i++) { if (prayerParts[i].m > nowMin) { next = prayerParts[i]; break; } }
    if (!next) next = prayerParts[0];
    $("w-prayer").innerHTML = '<div class="pnext">' + (ur ? "اگلی نماز" : "Next") + ': <b class="next">' + next.n + " " + next.s + '</b> <span id="w-countdown"></span></div>' +
      '<div class="pgrid">' + prayerParts.map(function (x) { return '<span class="ptime" data-k="' + x.k + '">' + x.n + ' <b>' + x.s + '</b></span>'; }).join("") + '</div>';
    document.querySelectorAll(".pcity").forEach(function (b) { b.classList.toggle("active", b.getAttribute("data-city") === prayerCity); });
    prayerTick();
    if (!prayerTimer) prayerTimer = setInterval(prayerTick, 30000);
  }
  var usdRate = null, fxRates = null;
  function convTick() {
    var inp = document.getElementById("w-conv"), out = document.getElementById("w-conv-out"), sel = document.getElementById("w-cur");
    if (!inp || !out) return;
    var v = parseFloat(inp.value);
    var cur = sel ? sel.value : "USD";
    var rate = (cur === "USD") ? usdRate : (fxRates && fxRates[cur] && usdRate ? usdRate / fxRates[cur] : null);
    out.textContent = (rate && !isNaN(v) && v >= 0) ? fmt(v * rate) : "—";
  }
  var convInp = document.getElementById("w-conv");
  if (convInp) convInp.addEventListener("input", convTick);
  var convSel = document.getElementById("w-cur");
  if (convSel) convSel.addEventListener("change", convTick);
  function getJSON(url) { return fetch(url).then(function (r) { if (!r.ok) throw new Error("http " + r.status); return r.json(); }).catch(function () { return null; }); }
  var usd = getJSON("https://open.er-api.com/v6/latest/USD").then(function (d) { return d && d.rates ? d.rates : null; });
  var gold = getJSON("https://api.gold-api.com/price/XAU").then(function (d) { return d && d.price ? d.price : null; });
  var wx = getJSON("https://api.open-meteo.com/v1/forecast?latitude=31.52,24.86,33.69&longitude=74.35,67.01,73.06&current=temperature_2m,weather_code&timezone=Asia%2FKarachi");
  var fc = getJSON("https://api.open-meteo.com/v1/forecast?latitude=31.52&longitude=74.35&daily=temperature_2m_max,temperature_2m_min,weather_code&timezone=Asia%2FKarachi&forecast_days=7");
  var prayerParts = null;
  function prayerTick() {
    if (!prayerParts) return;
    var now = pktParts().d, nowMin = now.getHours() * 60 + now.getMinutes(), next = null, diff = 0;
    for (var i = 0; i < prayerParts.length; i++) { if (prayerParts[i].m > nowMin) { next = prayerParts[i]; diff = next.m - nowMin; break; } }
    if (!next) { next = prayerParts[0]; diff = 1440 - nowMin + next.m; }
    var h = Math.floor(diff / 60), m = diff % 60;
    var cd = document.getElementById("w-countdown");
    if (cd) cd.textContent = h > 0 ? (ur ? "(" + h + " گھنٹے " + m + " منٹ میں)" : "(in " + h + "h " + m + "m)") : (ur ? "(" + m + " منٹ میں)" : "(in " + m + "m)");
    var nb = document.querySelector("#w-prayer .next");
    if (nb) nb.textContent = next.n + " " + next.s;
    document.querySelectorAll("#w-prayer .ptime").forEach(function (el) { el.classList.toggle("now", el.getAttribute("data-k") === next.k); });
  }
  Promise.all([usd, gold, wx, prs, fc]).then(function (res) {
    var rates = res[0], pkr = rates ? rates.PKR : null, g = res[1], wxx = res[2];
    $("w-usd").textContent = pkr ? fmt(pkr) : "—";
    usdRate = pkr; fxRates = rates; convTick();
    var fxEl = $("w-fx");
    if (fxEl) {
      if (rates && pkr) {
        var sym = { GBP: "£", EUR: "€", SAR: "SR ", AED: "AED ", CNY: "¥" };
        fxEl.innerHTML = ["GBP", "EUR", "SAR", "AED", "CNY"].map(function (c) {
          var v = rates[c] ? pkr / rates[c] : null;
          return '<span class="fxchip">' + sym[c] + '1 = ' + (v ? fmt(v) : "—") + '</span>';
        }).join("");
      } else { fxEl.textContent = "—"; }
    }
    if (pkr && g) {
      var g24 = Math.round(g / 31.1035 * 11.664 * pkr / 100) * 100;
      var g22 = Math.round(g24 * 22 / 24 / 100) * 100;
      $("w-gold").textContent = (ur ? "24 قیراط " : "24k ") + fmt(g24) + " · " + (ur ? "22 قیراط " : "22k ") + fmt(g22) + (ur ? " (تخمینہ)" : " (est.)");
    } else { $("w-gold").textContent = "—"; }
    var wc = { 0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 45: "🌫️", 48: "🌫️", 51: "🌦️", 53: "🌦️", 55: "🌦️", 61: "🌧️", 63: "🌧️", 65: "🌧️", 71: "❄️", 73: "❄️", 75: "❄️", 95: "⛈️" };
    if (wxx && wxx.length >= 3) {
      var names = ur ? ["لاہور", "کراچی", "اسلام آباد"] : ["Lahore", "Karachi", "Islamabad"];
      $("w-weather").innerHTML = wxx.map(function (c, i) { return '<span class="wcity">' + names[i] + ' <b>' + Math.round(c.current.temperature_2m) + '°C</b> ' + (wc[c.current.weather_code] || "") + '</span>'; }).join("");
    } else { $("w-weather").textContent = "—"; }
    var f = res[4];
    var fel = document.getElementById("w-forecast");
    if (f && f.daily && f.daily.time && f.daily.time.length >= 7 && fel) {
      var wdEn = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
      var wdUr = ["اتوار", "پیر", "منگل", "بدھ", "جمعرات", "جمعہ", "ہفتہ"];
      var rows = f.daily.time.map(function (ds, i) {
        var p = ds.split("-"), dow = new Date(Date.UTC(+p[0], +p[1] - 1, +p[2])).getUTCDay();
        return '<span class="fday"><i>' + (ur ? wdUr[dow] : wdEn[dow]) + '</i><b>' + Math.round(f.daily.temperature_2m_max[i]) + '°/' + Math.round(f.daily.temperature_2m_min[i]) + '°</b>' + (wc[f.daily.weather_code[i]] || "") + '</span>';
      });
      fel.innerHTML = rows.join("");
    }
    var prAll = res[3];
    if (prAll) { cities.forEach(function (c, i) { if (prAll[i] && prAll[i].timings) prayerData[c] = prAll[i].timings; }); }
    if (Object.keys(prayerData).length) renderPrayer();
    else $("w-prayer").textContent = "—";
    var hjEl = $("w-hijri");
    if (hjEl) {
      var hj = (prAll && prAll[0] && prAll[0].date) ? prAll[0].date.hijri : null;
      hjEl.textContent = hj ? (ur ? (hj.day + " " + hj.month.ar + " " + hj.year + "ھ") : (hj.day + " " + hj.month.en + " " + hj.year + " AH")) : "—";
    }
    $("w-updated").textContent = (ur ? "تازہ ترین " : "Live ") +
      new Date().toLocaleString("en-GB", { timeZone: "Asia/Karachi", hour: "2-digit", minute: "2-digit", hour12: true }) + " PKT" +
      (ur ? " · ذرائع: exchangerate-api، gold-api، Open-Meteo، Aladhan" : " · Sources: exchangerate-api, gold-api, Open-Meteo, Aladhan");
  });
  document.addEventListener("click", function (e) {
    var pc = e.target.closest(".pcity");
    if (pc) {
      prayerCity = pc.getAttribute("data-city");
      try { localStorage.setItem("pfn-prayer-city", prayerCity); } catch (err) {}
      renderPrayer();
    }
  });
})();

// Phase 4: dark-mode toggle (saved in localStorage; falls back to the system preference),
// share buttons (copy link + native share), shown on every card.
(function () {
  var btn = document.getElementById("theme-toggle");
  var root = document.documentElement;
  function apply(t) {
    root.setAttribute("data-theme", t);
    if (btn) btn.textContent = t === "dark" ? "☀️" : "🌙";
    try { localStorage.setItem("pfn-theme", t); } catch (e) {}
  }
  if (btn) {
    btn.textContent = root.getAttribute("data-theme") === "dark" ? "☀️" : "🌙";
    btn.addEventListener("click", function () {
      apply(root.getAttribute("data-theme") === "dark" ? "light" : "dark");
    });
  }
  if (navigator.share) {
    document.querySelectorAll(".share-native").forEach(function (b) { b.style.display = "inline-block"; });
  }
  function fallbackCopy(t) {
    var ta = document.createElement("textarea");
    ta.value = t; ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); } catch (e) {}
    document.body.removeChild(ta);
  }
  document.addEventListener("click", function (e) {
    var c = e.target.closest(".share-copy");
    if (c) {
      var link = c.getAttribute("data-link"), done = function () {
        var o = c.textContent;
        c.textContent = root.lang === "ur" ? "کاپی ہو گیا ✓" : "Copied ✓";
        setTimeout(function () { c.textContent = o; }, 2000);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(link).then(done, function () { fallbackCopy(link); done(); });
      } else { fallbackCopy(link); done(); }
      return;
    }
    var n = e.target.closest(".share-native");
    if (n && navigator.share) {
      navigator.share({ title: n.getAttribute("data-title") || document.title, url: n.getAttribute("data-link") }).catch(function () {});
    }
  });
})();

// Text size (A- / A+) + back-to-top button + PWA service-worker registration.
(function () {
  var FSS = [0.9, 1, 1.1, 1.2], fss = 1;
  try { fss = parseFloat(localStorage.getItem("pfn-fss")) || 1; } catch (e) {}
  if (FSS.indexOf(fss) < 0) fss = 1;
  function applyFss() {
    document.documentElement.style.setProperty("--fss", fss);
    try { localStorage.setItem("pfn-fss", fss); } catch (e) {}
  }
  applyFss();
  var minus = document.getElementById("fs-minus"), plus = document.getElementById("fs-plus");
  if (minus) minus.addEventListener("click", function () { var i = FSS.indexOf(fss); if (i > 0) { fss = FSS[i - 1]; applyFss(); } });
  if (plus) plus.addEventListener("click", function () { var i = FSS.indexOf(fss); if (i < FSS.length - 1) { fss = FSS[i + 1]; applyFss(); } });
  var tt = document.getElementById("totop");
  if (tt) {
    window.addEventListener("scroll", function () { tt.classList.toggle("show", window.scrollY > 600); }, { passive: true });
    tt.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); });
  }
  if ("serviceWorker" in navigator && window.location.protocol === "https:") {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/pakistan-fast-news/sw.js").catch(function () {});
    });
  }
})();

// "Suno" listen buttons: browser speechSynthesis (free, no key). One at a time;
// tapping another card (or the same button) stops the current reading.
(function () {
  function hideAll() {
    document.querySelectorAll(".suno-btn").forEach(function (b) { b.style.display = "none"; });
  }
  if (!("speechSynthesis" in window)) { hideAll(); return; }
  var currentBtn = null;
  function stopAll() {
    try { window.speechSynthesis.cancel(); } catch (e) {}
    if (currentBtn) {
      currentBtn.classList.remove("speaking");
      currentBtn.textContent = currentBtn.getAttribute("data-label") || "🔊 Listen";
      currentBtn = null;
    }
  }
  document.addEventListener("click", function (e) {
    var b = e.target.closest(".suno-btn");
    if (!b) return;
    if (currentBtn === b) { stopAll(); return; }
    stopAll();
    var text = b.getAttribute("data-speak") || "";
    if (!text) return;
    var isUr = b.getAttribute("data-lang") === "ur";
    if (!b.getAttribute("data-label")) b.setAttribute("data-label", b.textContent);
    var u = new SpeechSynthesisUtterance(text);
    u.lang = isUr ? "ur-PK" : "en-US";
    u.rate = 1;
    b.classList.add("speaking");
    b.textContent = isUr ? "⏹ بند کریں" : "⏹ Stop";
    currentBtn = b;
    u.onend = function () { stopAll(); };
    u.onerror = function () { stopAll(); };
    window.speechSynthesis.speak(u);
  });
})();

// Cricket live score strip (SportScore free API, no key; verified 2026-11-11:
// GET https://sportscore.com/api/v1/matches/?sport=cricket&status=live returns
// {matches:[{home,away,home_score,away_score,status,status_text,time,competition,url}]}.
// The status filter is loose, so live matches are filtered client-side.
// Order: live match with a real score first (Pakistan preferred) -> any live match
// -> latest finished match with its time -> clean "no live match" state. Never faked.
(function () {
  var el = document.getElementById("cricket-strip");
  if (!el) return;
  var isUr = el.getAttribute("data-lang") === "ur";
  var body = el.querySelector(".cbody");
  function esc(s) { return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
  function scoreTxt(v) { return (v && v !== "-") ? v : "—"; }
  function hasScore(m) { return (m.home_score && m.home_score !== "-") || (m.away_score && m.away_score !== "-"); }
  function isPak(m) { return /pakistan/i.test((m.home || "") + " " + (m.away || "")); }
  function link(url, label) { return '<p class="clink"><a href="https://sportscore.com' + esc(url || "/cricket") + '" target="_blank" rel="noopener">' + label + '</a></p>'; }
  function renderMatch(m, state) {
    var badge = state === "live" ? (isUr ? "🔴 لائیو" : "🔴 LIVE") : (isUr ? "مکمل" : "Finished");
    var when = "";
    try {
      var d = new Date(m.time);
      when = d.toLocaleString(isUr ? "ur-PK" : "en-GB", { timeZone: "Asia/Karachi", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
    } catch (e) {}
    body.innerHTML = '<p class="cbadge">' + badge + ' · ' + esc(m.competition || "") + '</p>'
      + '<p class="cteams">' + esc(m.home) + ' <b>' + esc(scoreTxt(m.home_score)) + '</b> vs <b>' + esc(scoreTxt(m.away_score)) + '</b> ' + esc(m.away) + '</p>'
      + '<p class="cstatus">' + esc(m.status_text || "") + (when ? ' · ' + esc(when) + ' PKT' : '') + '</p>'
      + link(m.url, isUr ? 'مکمل اسکور کارڈ دیکھیں ↗' : 'Full scorecard ↗');
  }
  function renderEmpty() {
    body.innerHTML = '<p class="cstatus">' + (isUr ? 'اس وقت کوئی لائیو میچ نہیں ہے۔' : 'No live match right now.') + '</p>'
      + link("/cricket", isUr ? 'لائیو اسکور دیکھیں ↗' : 'See live scores ↗');
  }
  // Last good score is cached on this device, so a failed request shows the
  // previous score with its time instead of a bare error. A Retry button lets
  // the reader try again at once (some mobile networks rate-limit the free
  // API on shared IPs, so the first attempt can fail while a retry works).
  var CACHE_KEY = "pfn-cricket-v1";
  function fmtTimePKT(ts) {
    try {
      return new Date(ts).toLocaleTimeString(isUr ? "ur-PK" : "en-GB", { timeZone: "Asia/Karachi", hour: "numeric", minute: "2-digit" });
    } catch (e) { return ""; }
  }
  function saveCache(m, state) {
    try { localStorage.setItem(CACHE_KEY, JSON.stringify({ m: m, state: state, ts: Date.now() })); } catch (e) {}
  }
  function readCache() {
    try {
      var c = JSON.parse(localStorage.getItem(CACHE_KEY) || "null");
      return (c && c.m && c.ts) ? c : null;
    } catch (e) { return null; }
  }
  function renderCached() {
    var c = readCache();
    if (!c) return false;
    renderMatch(c.m, c.state);
    var note = (isUr ? "آخری اپڈیٹ " : "Last updated ") + fmtTimePKT(c.ts) + " PKT";
    body.insertAdjacentHTML("beforeend", '<p class="cstatus">' + esc(note) + '</p>'
      + '<button class="cRetry" type="button">' + (isUr ? "↻ دوبارہ کوشش کریں" : "↻ Retry") + '</button>');
    var btn = body.querySelector(".cRetry");
    if (btn) btn.addEventListener("click", function () { body.innerHTML = '<p class="cloading">' + (isUr ? "لائیو اسکور لوڈ ہو رہا ہے…" : "Loading live score…") + '</p>'; load(); });
    return true;
  }
  function renderError() {
    if (renderCached()) return;
    body.innerHTML = '<p class="cstatus">' + (isUr ? "اسکور ابھی دستیاب نہیں ہے — براہ کرم دوبارہ کوشش کریں۔" : "Score unavailable right now — please try again.") + '</p>'
      + '<button class="cRetry" type="button">' + (isUr ? "↻ دوبارہ کوشش کریں" : "↻ Retry") + '</button><br>'
      + link("/cricket", isUr ? "لائیو اسکور دیکھیں ↗" : "See live scores ↗");
    var btn = body.querySelector(".cRetry");
    if (btn) btn.addEventListener("click", function () { body.innerHTML = '<p class="cloading">' + (isUr ? "لائیو اسکور لوڈ ہو رہا ہے…" : "Loading live score…") + '</p>'; load(); });
  }
  function fetchJson(url, ms) {
    var ctrl = ("AbortController" in window) ? new AbortController() : null;
    var timer = null;
    if (ctrl) timer = setTimeout(function () { ctrl.abort(); }, ms || 10000);
    return fetch(url, ctrl ? { signal: ctrl.signal } : {})
      .then(function (r) { if (timer) clearTimeout(timer); if (!r.ok) throw new Error("http " + r.status); return r.json(); })
      .catch(function (e) { if (timer) clearTimeout(timer); throw e; });
  }
  function pick(list) {
    var live = list.filter(function (m) { return m.status === "live"; });
    live.sort(function (a, b) {
      if (hasScore(b) !== hasScore(a)) return (hasScore(b) ? 1 : 0) - (hasScore(a) ? 1 : 0);
      return (isPak(b) ? 1 : 0) - (isPak(a) ? 1 : 0);
    });
    if (live.length) return { m: live[0], state: "live" };
    var fin = list.filter(function (m) { return m.status === "finished"; });
    fin.sort(function (a, b) { return new Date(b.time) - new Date(a.time); });
    if (fin.length) return { m: fin[0], state: "finished" };
    return null;
  }
  function load() {
    fetchJson("https://sportscore.com/api/v1/matches/?sport=cricket&status=live")
      .catch(function () { return fetchJson("https://sportscore.com/api/v1/matches/?sport=cricket"); })
      .then(function (d) {
        var picked = pick((d && d.matches) || []);
        if (!picked) { renderEmpty(); return; }
        renderMatch(picked.m, picked.state);
        saveCache(picked.m, picked.state);
      })
      .catch(function () { renderError(); });
  }
  load();
  setInterval(function () { if (!document.hidden) load(); }, 120000);
})();
