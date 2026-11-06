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
