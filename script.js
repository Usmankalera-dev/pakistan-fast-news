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
  function getJSON(url) { return fetch(url).then(function (r) { if (!r.ok) throw new Error("http " + r.status); return r.json(); }).catch(function () { return null; }); }
  var usd = getJSON("https://open.er-api.com/v6/latest/USD").then(function (d) { return d && d.rates ? d.rates.PKR : null; });
  var gold = getJSON("https://api.gold-api.com/price/XAU").then(function (d) { return d && d.price ? d.price : null; });
  var wx = getJSON("https://api.open-meteo.com/v1/forecast?latitude=31.52,24.86,33.69&longitude=74.35,67.01,73.06&current=temperature_2m,weather_code&timezone=Asia%2FKarachi");
  var pr = getJSON("https://api.aladhan.com/v1/timingsByCity/" + pk.dd + "-" + pk.mm + "-" + pk.yy + "?city=Lahore&country=Pakistan&method=1").then(function (d) { return d && d.data ? d.data.timings : null; });
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
  }
  Promise.all([usd, gold, wx, pr, fc]).then(function (res) {
    var pkr = res[0], g = res[1], wxx = res[2], t = res[3];
    $("w-usd").textContent = pkr ? fmt(pkr) : "—";
    if (pkr && g) {
      var g24 = Math.round(g / 31.1035 * 11.664 * pkr / 100) * 100;
      var g22 = Math.round(g24 * 22 / 24 / 100) * 100;
      $("w-gold").textContent = (ur ? "24 قیراط " : "24k ") + fmt(g24) + " · " + (ur ? "22 قیراط " : "22k ") + fmt(g22) + (ur ? " (تخمینہ)" : " (est.)");
    } else { $("w-gold").textContent = "—"; }
    var wc = { 0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 45: "🌫️", 48: "🌫️", 51: "🌦️", 53: "🌦️", 55: "🌦️", 61: "🌧️", 63: "🌧️", 65: "🌧️", 71: "❄️", 73: "❄️", 75: "❄️", 95: "⛈️" };
    if (wxx && wxx.length >= 3) {
      var names = ur ? ["لاہور", "کراچی", "اسلام آباد"] : ["Lahore", "Karachi", "Islamabad"];
      $("w-weather").textContent = wxx.map(function (c, i) { return names[i] + " " + Math.round(c.current.temperature_2m) + "°C " + (wc[c.current.weather_code] || ""); }).join(" · ");
    } else { $("w-weather").textContent = "—"; }
    var f = res[4];
    var fel = document.getElementById("w-forecast");
    if (f && f.daily && f.daily.time && f.daily.time.length >= 7 && fel) {
      var wdEn = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
      var wdUr = ["اتوار", "پیر", "منگل", "بدھ", "جمعرات", "جمعہ", "ہفتہ"];
      var rows = f.daily.time.map(function (ds, i) {
        var p = ds.split("-"), dow = new Date(Date.UTC(+p[0], +p[1] - 1, +p[2])).getUTCDay();
        return (ur ? wdUr[dow] : wdEn[dow]) + " " + Math.round(f.daily.temperature_2m_max[i]) + "°/" + Math.round(f.daily.temperature_2m_min[i]) + "° " + (wc[f.daily.weather_code[i]] || "");
      });
      fel.textContent = (ur ? "لاہور اس ہفتے: " : "Lahore this week: ") + rows.join(" · ");
    }
    if (t) {
      var keys = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"];
      var names = ur ? ["فجر", "ظہر", "عصر", "مغرب", "عشاء"] : keys;
      prayerParts = keys.map(function (k, i) { return { n: names[i], m: toMin(t[k]), s: fmt12(t[k]) }; });
      var nowMin = pk.d.getHours() * 60 + pk.d.getMinutes(), next = null;
      for (var i = 0; i < prayerParts.length; i++) { if (prayerParts[i].m > nowMin) { next = prayerParts[i]; break; } }
      if (!next) next = prayerParts[0];
      $("w-prayer").innerHTML = (ur ? "اگلی نماز" : "Next prayer") + ': <b class="next">' + next.n + " " + next.s + '</b> <span id="w-countdown"></span> · ' +
        prayerParts.map(function (x) { return x.n + " " + x.s; }).join(" · ");
      prayerTick(); setInterval(prayerTick, 30000);
    } else { $("w-prayer").textContent = "—"; }
    $("w-updated").textContent = (ur ? "تازہ ترین " : "Live ") +
      new Date().toLocaleString("en-GB", { timeZone: "Asia/Karachi", hour: "2-digit", minute: "2-digit", hour12: true }) + " PKT";
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
