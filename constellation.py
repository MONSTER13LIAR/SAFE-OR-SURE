"""The spectator constellation — one self-contained page, no dependencies.

Served at `/` by the game's HTTP server. Shows the shape of every live run
— rooms, the proven web, the clock — and never a word of message content.

It is also the front door: the three rooms are listed as tappable doors,
fed by `/state.json`, so a visitor who has never read the README can be in
the game in one tap. One run gets the full-size constellation; a crowd
tiles into a wall of them.
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
  main { width: 100%; max-width: 460px; transition: max-width .3s ease; }
  main.wide { max-width: 940px; }
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

  /* the wall: one run full size, a crowd tiles */
  .wall {
    display: grid;
    gap: 3vmin 2.4vmin;
    justify-items: center;
    margin: 2.4vmin 0 1vmin;
  }
  .wall.many {
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    align-items: start;
    justify-content: center;
  }
  .tile { width: 100%; max-width: 380px; }
  .wall.many .tile { max-width: 210px; }
  /* viewBox is cropped tight to the three nodes and their labels, so the
     doors below stay above the fold on a laptop. */
  .tile svg { display: block; margin: 0 auto; width: 100%; height: auto; }
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
  .many .node text { font-size: 18px; }
  .strip {
    display: flex;
    gap: 2.4em;
    justify-content: center;
    color: var(--dim);
    font-size: clamp(.78rem, 2vmin, .92rem);
    letter-spacing: .08em;
    margin-top: 1.5vmin;
  }
  /* In a crowd the tiles are read at a glance: clock and flags only, and
     never wrapped — the dots already say which rooms are still up. */
  .many .strip { gap: 1em; font-size: .68rem; letter-spacing: .04em; white-space: nowrap; }
  .many .strip .rooms { display: none; }
  .strip .flag { color: var(--accent); }
  .tstate {
    margin-top: 1.6vmin;
    min-height: 1.5em;
    font-size: clamp(.82rem, 2.3vmin, 1rem);
    letter-spacing: .14em;
    text-align: center;
  }
  .many .tstate { font-size: .74rem; letter-spacing: .1em; min-height: 1.2em; }
  .tstate.dormant { color: var(--dim); letter-spacing: .06em; }
  .key {
    margin-top: 1.4em;
    text-align: center;
    color: var(--dim);
    font-size: .68rem;
    letter-spacing: .1em;
    opacity: 0;
    transition: opacity .4s ease;
  }
  .key.show { opacity: .8; }

  /* the rules, in the four lines they actually are */
  .rules {
    max-width: 460px;
    margin: 2.6vmin auto 0;
    color: var(--dim);
    font-size: clamp(.72rem, 1.9vmin, .82rem);
    line-height: 1.7;
    letter-spacing: .02em;
  }
  .rules b { color: var(--ink); font-weight: 500; }

  /* the doors */
  .doors { margin-top: 2.2vmin; max-width: 460px; margin-left: auto; margin-right: auto; }
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
  .doors.full .door { opacity: .35; }
  .doors.full .doorline { color: var(--accent); opacity: .85; }
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
 <main id="main">
  <header>
    <h1>SAFE OR SURE</h1>
    <p class="tagline">You can be safe or you can be sure. Not both.</p>
  </header>

  <div class="wall one" id="wall"></div>

  <p class="key" id="key">&#9676; open &nbsp;·&nbsp; &#9673; linked &nbsp;·&nbsp; &#10005; sealed</p>

  <p class="rules">three people message you on three different apps.
  <b>they are one thing.</b> tell them things &mdash; each fact goes to one of
  them only. when one knows something you told somebody else, tap &#9873;.</p>

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
  var NS = "http://www.w3.org/2000/svg";
  var elMain = document.getElementById("main");
  var elWall = document.getElementById("wall");
  var elKey = document.getElementById("key");
  var elDoors = document.getElementById("doors");
  var elDoorRows = document.getElementById("doorrows");
  var elDoorLine = document.getElementById("doorline");
  var elFoot = document.getElementById("foot");
  var WHERE = { telegram: "on telegram", discord: "on discord", email: "by email" };

  var tiles = {};        // run id -> tile
  var doorKey = "";

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

  function el(tag, cls) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    return e;
  }

  // --------------------------------------------------------------- a run
  function makeTile() {
    var root = el("div", "tile");
    var svg = mk("svg", { viewBox: "24 34 392 300", "aria-label": "constellation" });
    var gLinks = mk("g", {});
    var gNodes = mk("g", {});
    svg.appendChild(gLinks);
    svg.appendChild(gNodes);
    root.appendChild(svg);

    var strip = el("div", "strip");
    var clock = el("span"); clock.textContent = "—";
    var flagWrap = el("span");
    var flagMark = el("span", "flag"); flagMark.textContent = "⚑";
    var flags = el("span"); flags.textContent = "—";
    flagWrap.appendChild(flagMark);
    flagWrap.appendChild(document.createTextNode(" "));
    flagWrap.appendChild(flags);
    var up = el("span", "rooms"); up.textContent = "—";
    strip.appendChild(clock); strip.appendChild(flagWrap); strip.appendChild(up);
    root.appendChild(strip);

    var state = el("p", "tstate");
    state.innerHTML = "&nbsp;";
    root.appendChild(state);

    var pos = {}, nodeEls = {}, seenLinks = {}, roomKey = "";
    var collapsed = false;
    var baseSeconds = null, baseAt = 0, running = false, ended = false;

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

    function tick() {
      if (baseSeconds === null) { clock.textContent = "—"; return; }
      var extra = (running && !ended) ? (Date.now() - baseAt) / 1000 : 0;
      clock.textContent = fmt(baseSeconds + extra);
    }

    function apply(run, idle, many) {
      var rooms = Array.isArray(run.rooms) ? run.rooms : [];
      var links = Array.isArray(run.links) ? run.links : [];
      var ending = typeof run.ending === "string" ? run.ending : null;
      var inRun = !!run.in_run;

      baseSeconds = (typeof run.run_seconds === "number" && isFinite(run.run_seconds))
        ? run.run_seconds : null;
      baseAt = Date.now();
      running = inRun;
      ended = !!ending;

      // A fresh run: stale collapse state and link-animation memory die
      // BEFORE nodes and links render — no one-poll flash of the old web,
      // and re-proven links get their draw-in again next run.
      if (ending !== "NAMED" && collapsed) uncollapse();
      if (!links.length) seenLinks = {};

      var key = rooms.map(function (r) { return r && r.id; }).join(",");
      if (key !== roomKey) {
        roomKey = key;
        if (collapsed) uncollapse();
        buildNodes(rooms);
        seenLinks = {};
      }

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

      flags.textContent = (typeof run.flags_left === "number" && isFinite(run.flags_left))
        ? (many ? String(run.flags_left) : run.flags_left + " left") : "—";
      up.textContent = alive + " rooms up";

      if (ending === "NAMED") {
        state.textContent = "NAMED IT";
        state.className = "tstate";
        if (!collapsed) collapse();
      } else if (ending === "CORNERED" || ending === "SWARMED") {
        state.textContent = ending;
        state.className = "tstate";
      } else if (idle) {
        state.textContent = "three rooms up. say hi to start.";
        state.className = "tstate dormant";
      } else {
        state.innerHTML = "&nbsp;";
        state.className = "tstate";
      }
      tick();
      return ending;
    }

    return { el: root, apply: apply, tick: tick };
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

      var tag = el("span", "tag");
      tag.textContent = r.tag || id;
      a.appendChild(tag);

      var who = el("span", "who");
      var name = document.createElement("b");
      name.textContent = r.persona || id;
      who.appendChild(name);
      var where = el("span");
      where.textContent = " " + (WHERE[id] || id);
      who.appendChild(where);
      a.appendChild(who);

      var go = el("span", "go");
      go.textContent = isMail ? "write →" : "say hi →";
      a.appendChild(go);
      elDoorRows.appendChild(a);

      if (isMail) {
        var wrap = el("div", "door");
        wrap.style.borderTop = "none";
        wrap.style.paddingTop = "0";
        wrap.appendChild(el("span", "tag"));
        var addr = el("span", "who addr");
        var s = el("span");
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

  // --------------------------------------------------------------- page
  function apply(s) {
    if (!s || typeof s !== "object") return;
    var runs = Array.isArray(s.runs) ? s.runs : [];
    var template = Array.isArray(s.rooms) ? s.rooms : [];
    var doors = (s.doors && typeof s.doors === "object") ? s.doors : {};
    var best = Array.isArray(s.best_named) ? s.best_named : [];
    var playing = typeof s.playing === "number" ? s.playing : 0;
    var full = !!s.full;
    var idle = runs.length === 0;

    // An empty house still shows the shape of the game, so a visitor can
    // see what they'd be walking into.
    var shown = idle ? [{ id: "idle", rooms: template, links: [], flags_left: 6,
                          ending: null, run_seconds: null, in_run: false }] : runs;

    var many = shown.length > 1;
    elWall.className = many ? "wall many" : "wall one";
    elMain.className = many ? "wide" : "";

    var live = {};
    var anyRunning = false;
    for (var i = 0; i < shown.length; i++) {
      var run = shown[i] || {};
      var id = String(run.id == null ? i : run.id);
      live[id] = true;
      var tile = tiles[id];
      if (!tile) {
        tile = makeTile();
        tiles[id] = tile;
      }
      if (tile.el.parentNode !== elWall) elWall.appendChild(tile.el);
      tile.apply(run, idle, many);
      if (run.in_run || run.ending) anyRunning = true;
    }
    // Runs that ended and aged out take their tile with them.
    for (var id2 in tiles) {
      if (!live[id2]) {
        if (tiles[id2].el.parentNode) tiles[id2].el.parentNode.removeChild(tiles[id2].el);
        delete tiles[id2];
      }
    }
    // Keep the wall in the server's order, newest activity first.
    for (var k = 0; k < shown.length; k++) {
      var t = tiles[String(shown[k].id == null ? k : shown[k].id)];
      if (t) elWall.appendChild(t.el);
    }

    elKey.className = anyRunning ? "key show" : "key";

    var dkey = template.map(function (r) {
      return r && r.id + ":" + (doors[r && r.id] || "");
    }).join("|");
    if (dkey !== doorKey) {
      doorKey = dkey;
      buildDoors(template, doors);
    }
    elDoors.className = full ? "doors full" : "doors";
    if (full) {
      elDoorLine.textContent = "every seat is taken right now. try again in a few minutes.";
    } else if (playing === 1) {
      elDoorLine.textContent = "one person is playing right now. there's room for you.";
    } else if (playing > 1) {
      elDoorLine.textContent = playing + " people are playing right now. there's room for you.";
    } else {
      elDoorLine.textContent = "start with Maria. she hands you the other two.";
    }

    var times = [];
    for (var m = 0; m < best.length; m++) {
      if (typeof best[m] === "number" && isFinite(best[m])) times.push(fmt(best[m]));
    }
    if (times.length) {
      elFoot.textContent = "fastest naming " + times.join(" · ");
      elFoot.className = "show";
    } else {
      elFoot.textContent = "";
      elFoot.className = "";
    }
  }

  function tickAll() {
    for (var id in tiles) tiles[id].tick();
  }

  function poll() {
    fetch("/state.json", { cache: "no-store" })
      .then(function (r) { return r.json(); })
      .then(apply)
      .catch(function () { /* keep polling */ });
  }

  poll();
  setInterval(poll, 2500);
  setInterval(tickAll, 250);
})();
</script>
</body>
</html>
"""


def render_page() -> str:
    """The complete spectator page as one HTML document."""
    return PAGE
