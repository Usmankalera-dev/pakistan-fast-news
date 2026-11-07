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
            ' PKT</time></div><h3><a href="' + it.link + '" target="_blank" rel="noopener"></a></h3><a class="readmore" href="' + it.link + '" target="_blank" rel="noopener">Read full story at Dawn →</a>';
          art.querySelector("h3 a").textContent = it.title;
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
  Promise.all([usd, gold, wx, pr]).then(function (res) {
    var pkr = res[0], g = res[1], wxx = res[2], t = res[3];
    $("w-usd").textContent = pkr ? fmt(pkr) : "—";
    $("w-gold").textContent = (pkr && g) ? fmt(Math.round(g / 31.1035 * 11.664 * pkr / 100) * 100) + (ur ? " (تخمینہ)" : " (est.)") : "—";
    var wc = { 0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 45: "🌫️", 48: "🌫️", 51: "🌦️", 53: "🌦️", 55: "🌦️", 61: "🌧️", 63: "🌧️", 65: "🌧️", 71: "❄️", 73: "❄️", 75: "❄️", 95: "⛈️" };
    if (wxx && wxx.length >= 3) {
      var names = ur ? ["لاہور", "کراچی", "اسلام آباد"] : ["Lahore", "Karachi", "Islamabad"];
      $("w-weather").textContent = wxx.map(function (c, i) { return names[i] + " " + Math.round(c.current.temperature_2m) + "°C " + (wc[c.current.weather_code] || ""); }).join(" · ");
    } else { $("w-weather").textContent = "—"; }
    if (t) {
      var keys = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"];
      var names = ur ? ["فجر", "ظہر", "عصر", "مغرب", "عشاء"] : keys;
      var nowMin = pk.d.getHours() * 60 + pk.d.getMinutes(), next = null;
      var parts = keys.map(function (k, i) { return { n: names[i], m: toMin(t[k]), s: fmt12(t[k]) }; });
      for (var i = 0; i < parts.length; i++) { if (parts[i].m > nowMin) { next = parts[i]; break; } }
      if (!next) next = { n: names[0], s: parts[0].s };
      $("w-prayer").innerHTML = (ur ? "اگلی نماز" : "Next prayer") + ': <b class="next">' + next.n + " " + next.s + "</b> · " +
        parts.map(function (x) { return x.n + " " + x.s; }).join(" · ");
    } else { $("w-prayer").textContent = "—"; }
    $("w-updated").textContent = (ur ? "تازہ ترین " : "Live ") +
      new Date().toLocaleString("en-GB", { timeZone: "Asia/Karachi", hour: "2-digit", minute: "2-digit", hour12: true }) + " PKT";
  });
})();
