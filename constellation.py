"""The spectator constellation — one self-contained page, no dependencies.

Served at `/` by the game's HTTP server. Shows the shape of the run —
rooms, the proven web, the clock — and never a word of message content.

It is also the front door: the three rooms are listed as tappable doors,
fed by `/state.json`, so a visitor who has never read the README can be
in the game in one tap. When someone else is mid-run, the doors say so
instead of letting the visitor bounce off a BUSY line.
"""

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SAFE OR SURE</title>
<meta name="description" content="Three strangers message you across Telegram, Discord and your inbox. They are one thing. Prove it — you have six flags.">
<meta property="og:title" content="SAFE OR SURE">
<meta property="og:description" content="Three strangers, three apps, one thing. Prove it before you seal yourself in.">
<meta property="og:type" content="website">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='9' fill='%23e8a13a'/%3E%3C/svg%3E">
<style>
  :root {
    --bg: #0d0d0f;
    --ink: #e8e6e1;
    --dim: #85837e;
    --faint: #3a3a40;
    --accent: #e8a13a;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html { height: 100%; }
  body {
    min-height: 100%;
    background: var(--bg);
    color: var(--ink);
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 5vmin 20px;
    overflow-x: hidden;
    -webkit-text-size-adjust: 100%;
  }
  main { width: 100%; max-width: 460px; }
  header { text-align: center; }
  h1 {
    font-size: clamp(1.1rem, 3.2vmin, 1.6rem);
    font-weight: 600;
    letter-spacing: .45em;
    text-indent: .45em; /* balances the trailing letter-space */
  }
  .tagline {
    margin-top: .9em;
    color: var(--dim);
    font-size: clamp(.72rem, 1.9vmin, .85rem);
    letter-spacing: .06em;
    text-align: center;
  }
  .sky { margin: 2.4vmin 0 1vmin; }
  svg {
    /* viewBox is cropped tight to the three nodes and their labels, so the
       doors below stay above the fold on a laptop. */
    display: block;
    margin: 0 auto;
    width: min(88vw, 70vmin, 380px);
    height: auto;
  }
  .weblink {
    stroke: var(--accent);
    stroke-width: 1.5;
    fill: none;
    transition: opacity .4s ease;
  }
  .weblink.draw { animation: drawin .7s ease forwards; }
  @keyframes drawin { to { stroke-dashoffset: 0; } }
  .node { transition: transform 1s cubic-bezier(0.22, 1, 0.36, 1); }
  .node circle {
    fill: none;
    stroke: var(--faint);
    stroke-width: 1.5;
    transition: stroke .4s ease, fill .4s ease;
  }
  .node.open circle { stroke: var(--ink); stroke-width: 2; }
  .node.woven circle { stroke: var(--accent); fill: var(--accent); }
  .node.sealed circle { stroke: var(--faint); fill: none; }
  .node .x { stroke: var(--dim); stroke-width: 1.5; opacity: 0; transition: opacity .4s ease; }
  .node.sealed .x { opacity: 1; }
  .node text {
    fill: var(--dim);
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 12px;
    letter-spacing: .04em;
    text-anchor: middle;
    transition: opacity .5s ease;
  }
  .node.sealed text { fill: var(--faint); text-decoration: line-through; }
  svg.done .weblink, svg.done .node text, svg.done .node .x { opacity: 0; }
  .strip {
    display: flex;
    gap: 2.4em;
    justify-content: center;
    color: var(--dim);
    font-size: clamp(.78rem, 2vmin, .92rem);
    letter-spacing: .08em;
    margin-top: 1.5vmin;
  }
  .strip .flag { color: var(--accent); }
  .key {
    margin-top: 1.1em;
    text-align: center;
    color: var(--dim);
    font-size: .68rem;
    letter-spacing: .1em;
    opacity: 0;
    transition: opacity .4s ease;
  }
  .key.show { opacity: .8; }
  .stateline {
    margin-top: 2.6vmin;
    min-height: 1.6em;
    font-size: clamp(.82rem, 2.3vmin, 1rem);
    letter-spacing: .14em;
    color: var(--ink);
    text-align: center;
  }
  .stateline.dormant { color: var(--dim); letter-spacing: .06em; }

  /* the doors */
  .doors { margin-top: 2.8vmin; }
  .door {
    display: flex;
    align-items: center;
    gap: 1em;
    padding: .95em .2em;
    border-top: 1px solid var(--faint);
    color: var(--ink);
    text-decoration: none;
    font-size: clamp(.78rem, 2.1vmin, .9rem);
    transition: color .2s ease, opacity .3s ease, padding-left .2s ease;
  }
  .doors .door:last-of-type { border-bottom: 1px solid var(--faint); }
  .door .tag {
    color: var(--faint);
    letter-spacing: .1em;
    width: 2.2em;
    flex: none;
    transition: color .2s ease;
  }
  .door .who { flex: 1; letter-spacing: .04em; min-width: 0; }
  .door .who.addr { font-size: .84em; }
  .door .who.addr span {
    display: block;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }
  .door .who b { font-weight: 600; }
  .door .who span { color: var(--dim); font-weight: 400; }
  .door .go { color: var(--dim); letter-spacing: .08em; flex: none; }
  .door:hover, .door:focus-visible { color: var(--accent); padding-left: .5em; outline: none; }
  .door:hover .tag, .door:focus-visible .tag { color: var(--accent); }
  .door:hover .go, .door:focus-visible .go { color: var(--accent); }
  .copy {
    background: none;
    border: 1px solid var(--faint);
    color: var(--dim);
    font: inherit;
    font-size: .82em;
    letter-spacing: .08em;
    padding: .3em .7em;
    cursor: pointer;
    flex: none;
    transition: color .2s ease, border-color .2s ease;
  }
  .copy:hover, .copy:focus-visible { color: var(--accent); border-color: var(--accent); outline: none; }
  .doorline {
    margin-top: 1.3em;
    color: var(--dim);
    font-size: clamp(.7rem, 1.8vmin, .78rem);
    letter-spacing: .05em;
    text-align: center;
  }
  .doors.busy .door { opacity: .35; }
  .doors.busy .doorline { color: var(--accent); opacity: .85; }
  footer {
    margin-top: 4vmin;
    color: var(--dim);
    font-size: clamp(.68rem, 1.7vmin, .78rem);
    letter-spacing: .06em;
    text-align: center;
    display: none;
  }
  footer.show { display: block; }
  @media (prefers-reduced-motion: reduce) {
    * { transition-duration: .01ms !important; animation-duration: .01ms !important; }
  }
</style>
</head>
<body>
 <main>
  <header>
    <h1>SAFE OR SURE</h1>
    <p class="tagline">You can be safe or you can be sure. Not both.</p>
  </header>

  <div class="sky">
    <svg id="sky" viewBox="24 34 392 300" aria-label="constellation">
      <g id="glinks"></g>
      <g id="gnodes"></g>
    </svg>
  </div>

  <div class="strip">
    <span id="clock">&mdash;</span>
    <span><span class="flag">&#9873;</span> <span id="flags">&mdash;</span></span>
    <span id="up">&mdash;</span>
  </div>

  <p class="key" id="key">&#9676; open &nbsp;·&nbsp; &#9673; linked &nbsp;·&nbsp; &#10005; sealed</p>

  <p class="stateline" id="stateline">&nbsp;</p>

  <nav class="doors" id="doors" hidden>
    <div id="doorrows"></div>
    <p class="doorline" id="doorline"></p>
  </nav>

  <footer id="foot"></footer>
 </main>

<script>
(function () {
  "use strict";
  var CX = 220, CY = 208, R = 148;
  var svg = document.getElementById("sky");
  var gLinks = document.getElementById("glinks");
  var gNodes = document.getElementById("gnodes");
  var elClock = document.getElementById("clock");
  var elFlags = document.getElementById("flags");
  var elUp = document.getElementById("up");
  var elKey = document.getElementById("key");
  var elState = document.getElementById("stateline");
  var elDoors = document.getElementById("doors");
  var elDoorRows = document.getElementById("doorrows");
  var elDoorLine = document.getElementById("doorline");
  var elFoot = document.getElementById("foot");
  var NS = "http://www.w3.org/2000/svg";

  var pos = {};          // room id -> {x, y}
  var nodeEls = {};      // room id -> <g>
  var roomKey = "";
  var doorKey = "";
  var seenLinks = {};    // "a|b" -> true
  var collapsed = false;
  var baseSeconds = null, baseAt = 0, running = false, ended = false;
  var WHERE = { telegram: "on telegram", discord: "on discord", email: "by email" };

  function fmt(t) {
    t = Math.max(0, Math.floor(t));
    var s = t % 60;
    return Math.floor(t / 60) + ":" + (s < 10 ? "0" : "") + s;
  }

  function mk(tag, attrs) {
    var el = document.createElementNS(NS, tag);
    for (var k in attrs) el.setAttribute(k, attrs[k]);
    return el;
  }

  function buildNodes(rooms) {
    gNodes.textContent = "";
    gLinks.textContent = "";
    pos = {}; nodeEls = {};
    var n = rooms.length;
    for (var i = 0; i < n; i++) {
      var room = rooms[i] || {};
      var id = String(room.id == null ? i : room.id);
      var a = -Math.PI / 2 + (2 * Math.PI * i) / Math.max(n, 1);
      var x = n > 1 ? CX + R * Math.cos(a) : CX;
      var y = n > 1 ? CY + R * Math.sin(a) : CY;
      pos[id] = { x: x, y: y };
      var g = mk("g", { "class": "node" });
      g.style.transform = "translate(" + x + "px," + y + "px)";
      g.appendChild(mk("circle", { r: 13 }));
      g.appendChild(mk("line", { "class": "x", x1: -9, y1: -9, x2: 9, y2: 9 }));
      g.appendChild(mk("line", { "class": "x", x1: -9, y1: 9, x2: 9, y2: -9 }));
      var label = mk("text", { y: 34 });
      var tag = room.tag != null ? String(room.tag) : id;
      var who = room.persona != null ? String(room.persona) : "";
      label.textContent = who ? tag + " · " + who : tag;
      g.appendChild(label);
      gNodes.appendChild(g);
      nodeEls[id] = g;
    }
  }

  function drawLinks(links) {
    gLinks.textContent = "";
    for (var i = 0; i < links.length; i++) {
      var pair = links[i];
      if (!pair || pair.length < 2) continue;
      var a = pos[String(pair[0])], b = pos[String(pair[1])];
      if (!a || !b) continue;
      var key = [String(pair[0]), String(pair[1])].sort().join("|");
      var line = mk("line", {
        "class": "weblink", x1: a.x, y1: a.y, x2: b.x, y2: b.y
      });
      if (!seenLinks[key]) {
        seenLinks[key] = true;
        var len = Math.hypot(b.x - a.x, b.y - a.y);
        line.setAttribute("stroke-dasharray", len);
        line.setAttribute("stroke-dashoffset", len);
        line.setAttribute("class", "weblink draw");
      }
      gLinks.appendChild(line);
    }
  }

  // --------------------------------------------------------------- doors
  function copyText(text, btn) {
    function done() {
      var was = btn.textContent;
      btn.textContent = "copied";
      setTimeout(function () { btn.textContent = was; }, 1600);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, fallback);
    } else {
      fallback();
    }
    function fallback() {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      var ok = false;
      try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
      document.body.removeChild(ta);
      if (ok) done(); else btn.textContent = text;
    }
  }

  function buildDoors(rooms, doors) {
    elDoorRows.textContent = "";
    var any = false;
    for (var i = 0; i < rooms.length; i++) {
      var r = rooms[i] || {};
      var id = String(r.id);
      var target = doors[id];
      if (!target) continue;
      any = true;
      var isMail = id === "email";
      var a = document.createElement("a");
      a.className = "door";
      a.href = isMail ? "mailto:" + target + "?subject=hi" : target;
      if (!isMail) { a.target = "_blank"; a.rel = "noopener"; }

      var tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = r.tag || id;
      a.appendChild(tag);

      var who = document.createElement("span");
      who.className = "who";
      var name = document.createElement("b");
      name.textContent = r.persona || id;
      who.appendChild(name);
      var where = document.createElement("span");
      where.textContent = " " + (WHERE[id] || id);
      who.appendChild(where);
      a.appendChild(who);

      var go = document.createElement("span");
      go.className = "go";
      go.textContent = isMail ? "write →" : "say hi →";
      a.appendChild(go);
      elDoorRows.appendChild(a);

      if (isMail) {
        var wrap = document.createElement("div");
        wrap.className = "door";
        wrap.style.borderTop = "none";
        wrap.style.paddingTop = "0";
        var spacer = document.createElement("span");
        spacer.className = "tag";
        wrap.appendChild(spacer);
        var addr = document.createElement("span");
        addr.className = "who addr";
        var s = document.createElement("span");
        s.textContent = target;      // long: ellipsised, the button has the whole of it
        s.title = target;
        addr.appendChild(s);
        wrap.appendChild(addr);
        var btn = document.createElement("button");
        btn.className = "copy";
        btn.type = "button";
        btn.textContent = "copy";
        (function (address, button) {
          button.addEventListener("click", function () { copyText(address, button); });
        })(target, btn);
        wrap.appendChild(btn);
        elDoorRows.appendChild(wrap);
      }
    }
    elDoors.hidden = !any;
  }

  function collapse() {
    // Declarative on purpose: the target is set once and the CSS
    // transition owns the motion — a JS animation loop can stall,
    // and this is the money shot.
    collapsed = true;
    svg.classList.add("done");
    for (var id in nodeEls) {
      nodeEls[id].setAttribute("class", "node woven");
      nodeEls[id].style.transform = "translate(" + CX + "px," + CY + "px)";
    }
  }

  function uncollapse() {
    collapsed = false;
    svg.classList.remove("done");
    for (var id in nodeEls) {
      nodeEls[id].style.transform =
        "translate(" + pos[id].x + "px," + pos[id].y + "px)";
    }
  }

  function apply(s) {
    if (!s || typeof s !== "object") return;
    var rooms = Array.isArray(s.rooms) ? s.rooms : [];
    var links = Array.isArray(s.links) ? s.links : [];
    var ending = typeof s.ending === "string" ? s.ending : null;
    var inRun = !!s.in_run;
    var best = Array.isArray(s.best_named) ? s.best_named : [];
    var doors = (s.doors && typeof s.doors === "object") ? s.doors : {};

    // clock base
    baseSeconds = (typeof s.run_seconds === "number" && isFinite(s.run_seconds))
      ? s.run_seconds : null;
    baseAt = Date.now();
    running = inRun;
    ended = !!ending;

    // A fresh run: stale collapse state and link-animation memory die
    // BEFORE nodes and links render — no one-poll flash of the old web,
    // and re-proven links get their draw-in again next run.
    if (ending !== "NAMED" && collapsed) uncollapse();
    if (!links.length) seenLinks = {};

    // layout (rebuild only when the set of rooms changes)
    var key = rooms.map(function (r) { return r && r.id; }).join(",");
    if (key !== roomKey) {
      roomKey = key;
      if (collapsed) uncollapse();
      buildNodes(rooms);
      seenLinks = {};
    }

    // which rooms are woven into the proven web
    var woven = {};
    for (var i = 0; i < links.length; i++) {
      var p = links[i];
      if (p && p.length >= 2) { woven[String(p[0])] = true; woven[String(p[1])] = true; }
    }

    var alive = 0;
    for (var j = 0; j < rooms.length; j++) {
      var r = rooms[j] || {};
      var id = String(r.id == null ? j : r.id);
      var isAlive = r.alive !== false;
      if (isAlive) alive++;
      var g = nodeEls[id];
      if (!g) continue;
      var cls = "node";
      if (!isAlive) cls += " sealed";
      else if (r.linked === true || woven[id]) cls += " open woven";
      else if (r.opened === true) cls += " open";
      if (collapsed) cls = "node woven";
      g.setAttribute("class", cls);
    }

    if (!collapsed) drawLinks(links);

    // strip
    elFlags.textContent = (typeof s.flags_left === "number" && isFinite(s.flags_left))
      ? s.flags_left + " left" : "—";
    elUp.textContent = alive + " rooms up";
    // The dot key earns its space only once the dots start meaning things.
    elKey.className = (inRun || ended) && !collapsed ? "key show" : "key";

    // doors (rebuild only when what's on offer changes)
    var dkey = rooms.map(function (r) {
      return r && r.id + ":" + (doors[r && r.id] || "");
    }).join("|");
    if (dkey !== doorKey) {
      doorKey = dkey;
      buildDoors(rooms, doors);
    }
    elDoors.className = inRun ? "doors busy" : "doors";
    elDoorLine.textContent = inRun
      ? "someone's mid-run. the seat frees up when they finish."
      : (ended ? "that run just ended. say hi and take the seat."
               : "start with Maria. she hands you the other two.");

    // state line
    if (ending === "NAMED") {
      elState.textContent = "NAMED IT";
      elState.className = "stateline";
      if (!collapsed) collapse();
    } else if (ending === "CORNERED" || ending === "SWARMED") {
      elState.textContent = ending;
      elState.className = "stateline";
    } else {
      if (!inRun) {
        elState.textContent = "three rooms up. say hi to start.";
        elState.className = "stateline dormant";
      } else {
        elState.innerHTML = "&nbsp;";
        elState.className = "stateline";
      }
    }

    // footer
    var times = [];
    for (var k = 0; k < best.length; k++) {
      if (typeof best[k] === "number" && isFinite(best[k])) times.push(fmt(best[k]));
    }
    if (times.length) {
      elFoot.textContent = "fastest naming " + times.join(" · ");
      elFoot.className = "show";
    } else {
      elFoot.textContent = "";
      elFoot.className = "";
    }
    tick();
  }

  function tick() {
    if (baseSeconds === null) {
      elClock.textContent = "—";
      return;
    }
    var extra = (running && !ended) ? (Date.now() - baseAt) / 1000 : 0;
    elClock.textContent = fmt(baseSeconds + extra);
  }

  function poll() {
    fetch("/state.json", { cache: "no-store" })
      .then(function (r) { return r.json(); })
      .then(apply)
      .catch(function () { /* keep polling */ });
  }

  poll();
  setInterval(poll, 2500);
  setInterval(tick, 250);
})();
</script>
</body>
</html>
"""


def render_page() -> str:
    """The complete spectator page as one HTML document."""
    return PAGE
