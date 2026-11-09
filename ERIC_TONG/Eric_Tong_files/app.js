/* Project webpage. All data comes from site_data.js (window.SITE), built by scripts/build_site_data.py. */
(() => {
  "use strict";
  const S = window.SITE;
  const SCHEDULE = ["none", "polish", "paraphrase", "style", "compress", "expand", "style", "paraphrase", "polish"];
  const COVERAGE = [0, 15, 25, 40, 50, 60, 75, 90, 100];
  const DOMAIN = { news: "News article", essays: "Student essay", abstracts: "Scientific abstract", reports: "Government report" };
  const OPS = ["compress", "paraphrase", "expand"];
  const NS = "http://www.w3.org/2000/svg";
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  function el(tag, attrs = {}, ...kids) {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") n.className = v;
      else if (k === "text") n.textContent = v;
      else if (k === "style") n.style.cssText = v;
      else n.setAttribute(k, v);
    }
    for (const k of kids) if (k != null) n.append(k);
    return n;
  }
  function sv(tag, attrs = {}, parent) {
    const n = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "text") n.textContent = v;
      else n.setAttribute(k, v);
    }
    if (parent) parent.append(n);
    return n;
  }
  const fmt = (x, d = 1) => (x > 0 ? "+" : x < 0 ? "−" : "") + Math.abs(x).toFixed(d);
  const fmtPlain = (x, d = 1) => (x < 0 ? "−" : "") + Math.abs(x).toFixed(d);
  const lin = (d0, d1, r0, r1) => (x) => r0 + ((x - d0) / (d1 - d0)) * (r1 - r0);
  const logs = (d0, d1, r0, r1) => { const a = Math.log(d0), b = Math.log(d1); return (x) => r0 + ((Math.log(x) - a) / (b - a)) * (r1 - r0); };
  const shuffle = (a) => { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };

  /* ---------------------------------------------------------------- tooltip */
  const tip = $("#tip");
  function showTip(html, x, y) {
    tip.innerHTML = html;
    tip.hidden = false;
    const r = tip.getBoundingClientRect();
    let left = x + 14, top = y + 14;
    if (left + r.width > window.innerWidth - 8) left = x - r.width - 14;
    if (top + r.height > window.innerHeight - 8) top = y - r.height - 14;
    tip.style.left = Math.max(8, left) + "px";
    tip.style.top = Math.max(8, top) + "px";
  }
  function bindTip(node, html) {
    node.addEventListener("pointermove", (e) => showTip(typeof html === "function" ? html() : html, e.clientX, e.clientY));
    node.addEventListener("pointerleave", () => { tip.hidden = true; });
  }
  window.addEventListener("scroll", () => { tip.hidden = true; }, { passive: true });

  /* ---------------------------------------------------------------- charts on resize */
  const charts = [];
  function chart(id, draw) {
    const host = document.getElementById(id);
    const run = () => { host.replaceChildren(); draw(host, Math.max(260, host.clientWidth)); };
    charts.push(run);
    run();
    return run;
  }
  let resizeTimer;
  let lastWidth = window.innerWidth;
  window.addEventListener("resize", () => {
    if (window.innerWidth === lastWidth) return;
    lastWidth = window.innerWidth;
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => charts.forEach((c) => c()), 120);
  });
  function svgBox(host, w, h) {
    return sv("svg", { viewBox: `0 0 ${w} ${h}`, width: w, height: h, role: "img" }, host);
  }
  function legend(id, items) {
    const box = document.getElementById(id);
    box.replaceChildren(...items.map(([label, color, kind]) =>
      el("span", {}, el("i", { class: kind || "", style: `background:${color}` }), label)));
  }

  /* ---------------------------------------------------------------- model */
  const MODEL = new Map(S.model.words.map(([w, wt, mu, z]) => [w, { w: wt, mu, z }]));
  const RES0 = S.results;
  const TAU = S.model.tau;
  const TOKEN = /[\p{L}\p{M}\p{N}_]+/gu;

  function score(text) {
    const toks = text.toLowerCase().match(TOKEN) || [];
    const n = Math.max(toks.length, 1);
    let ai = 0, human = 0;
    for (const t of toks) {
      const m = MODEL.get(t);
      if (!m) continue;
      if (m.w < 0) ai += m.w / n; else human += m.w / n;
    }
    const base = -S.model.const;
    return { n: toks.length, ai, human, base, L: ai + human + base };
  }
  const alphaFor = (z) => 0.1 + 0.62 * Math.min(1, Math.max(0, Math.abs(z) - 6) / 24);

  /* Render text with model words wrapped in colored spans. side = "all" | "ai" */
  function colorize(text, side = "all") {
    const frag = document.createDocumentFragment();
    let last = 0;
    for (const m of text.matchAll(TOKEN)) {
      const info = MODEL.get(m[0].toLowerCase());
      if (!info || (side === "ai" && info.z > 0)) continue;
      if (m.index > last) frag.append(text.slice(last, m.index));
      const span = el("span", { class: "w " + (info.z < 0 ? "ai" : "human"), style: `--a:${alphaFor(info.z)}`, text: m[0] });
      bindTip(span, `<b>${m[0].toLowerCase()}</b> · ${info.z < 0 ? "AI" : "human"}-leaning<br>z = ${fmtPlain(info.z, 1)} · weight ${fmtPlain(info.w, 0)}`);
      frag.append(span);
      last = m.index + m[0].length;
    }
    frag.append(text.slice(last));
    return frag;
  }

  /* ---------------------------------------------------------------- hero schedule (also the version stepper) */
  {
    const box = $("#schedule");
    for (let k = 0; k <= 8; k++) {
      box.append(el("button", { type: "button", class: "sched-cell" + (k === 4 ? " dip" : ""), "data-v": k, "aria-pressed": "false" },
        el("span", { class: "v", text: "v" + k }),
        el("span", { class: "op", text: k === 0 ? "human original" : SCHEDULE[k] }),
        el("span", { class: "cov" }, el("i", { style: `width:${COVERAGE[k]}%` })),
        el("span", { class: "pct", text: COVERAGE[k] + "% AI" })));
    }
  }

  /* ---------------------------------------------------------------- intro: one document, version by version */
  /* Word diff between consecutive versions of a sentence: words kept, added (yellow) and removed (struck through),
     in reading order, from the longest common subsequence of the two word lists. */
  function diffOps(oldText, newText) {
    const a = oldText.split(/\s+/).filter(Boolean), b = newText.split(/\s+/).filter(Boolean);
    const L = Array.from({ length: a.length + 1 }, () => new Uint16Array(b.length + 1));
    for (let i = a.length - 1; i >= 0; i--)
      for (let j = b.length - 1; j >= 0; j--)
        L[i][j] = a[i] === b[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
    const ops = [];
    let i = 0, j = 0;
    while (i < a.length || j < b.length) {
      if (i < a.length && j < b.length && a[i] === b[j]) { ops.push(["same", b[j]]); i++; j++; }
      else if (j < b.length && (i === a.length || L[i][j + 1] >= L[i + 1][j])) { ops.push(["add", b[j]]); j++; }
      else { ops.push(["del", a[i]]); i++; }
    }
    // each run of removed words goes right before the words that replaced it
    const out = [];
    for (let k = 0; k < ops.length;) {
      if (ops[k][0] === "same") { out.push(ops[k++]); continue; }
      const adds = [], dels = [];
      while (k < ops.length && ops[k][0] !== "same") (ops[k][0] === "add" ? adds : dels).push(ops[k++][1]);
      if (dels.length) out.push(["del", dels.join(" ")]);
      if (adds.length) out.push(["add", adds.join(" ")]);
    }
    return out;
  }
  {
    const T = S.trajectories;
    const st = { doc: Math.floor(Math.random() * T.length), v: 0 };
    const words = (sents) => sents.join(" ").split(/\s+/).filter(Boolean).length;
    function render() {
      const t = T[st.doc], k = st.v;
      $$("#schedule .sched-cell").forEach((b) => b.setAttribute("aria-pressed", String(Number(b.dataset.v) === k)));
      $("#traj-prev").disabled = k === 0;
      $("#traj-next").disabled = k === 8;
      const sents = t.sents[k], labels = t.labels[k];
      const changed = k ? sents.filter((x, i) => x !== t.sents[k - 1][i]).length : 0;
      const n = words(sents), dn = k ? n - words(t.sents[k - 1]) : 0;
      $("#traj-meta").replaceChildren(el("b", { text: k ? `v${k} · ${SCHEDULE[k]}` : "v0 · human original" }),
        `${DOMAIN[t.domain]}, edited by ${t.generator} · ${labels.filter(Boolean).length} of ${labels.length} sentences AI-edited · ${n} words` +
        (k ? ` (${dn > 0 ? "+" : dn < 0 ? "−" : "±"}${Math.abs(dn)} from v${k - 1}) · ${changed} sentence${changed === 1 ? "" : "s"} changed this round` : ""));
      const box = $("#traj-text");
      box.replaceChildren();
      sents.forEach((x, i) => {
        const span = el("span", { class: "s" + (labels[i] ? " ai-soft" : "") });
        if (k && x !== t.sents[k - 1][i]) {
          diffOps(t.sents[k - 1][i], x).forEach(([op, w], m, arr) => {
            span.append(op === "same" ? w : el(op === "add" ? "mark" : "del", { class: op === "add" ? "diff" : "gone", text: w }));
            if (m < arr.length - 1) span.append(" ");
          });
        } else span.append(x);
        box.append(span, " ");
      });
    }
    function go(k) { st.v = Math.max(0, Math.min(8, k)); render(); }
    $$("#schedule .sched-cell").forEach((b) => b.addEventListener("click", () => go(Number(b.dataset.v))));
    $("#traj-prev").addEventListener("click", () => go(st.v - 1));
    $("#traj-next").addEventListener("click", () => go(st.v + 1));
    $("#traj-doc").addEventListener("click", () => { st.doc = (st.doc + 1) % T.length; render(); });
    $("#traj-del").addEventListener("change", (e) => $("#traj-text").classList.toggle("hide-del", !e.target.checked));
    render();
  }

  /* ---------------------------------------------------------------- intro: detection rates by version */
  {
    const D = S.detection;
    const styles = [["var(--ink)", "circle", 2.6], ["var(--det-1)", "square", 2], ["var(--det-2)", "triangle", 2], ["var(--det-3)", "diamond", 2]];
    function marker(parent, shape, cx, cy, r, color) {
      const a = { fill: color, stroke: "var(--surface)", "stroke-width": 1.5 };
      if (shape === "circle") return sv("circle", { cx, cy, r, ...a }, parent);
      if (shape === "square") return sv("rect", { x: cx - r * 0.9, y: cy - r * 0.9, width: r * 1.8, height: r * 1.8, rx: 1, ...a }, parent);
      if (shape === "triangle") return sv("polygon", { points: `${cx},${cy - r * 1.15} ${cx + r},${cy + r * 0.75} ${cx - r},${cy + r * 0.75}`, ...a }, parent);
      return sv("polygon", { points: `${cx},${cy - r * 1.2} ${cx + r},${cy} ${cx},${cy + r * 1.2} ${cx - r},${cy}`, ...a }, parent);
    }
    const leg = $("#dip-legend");
    D.forEach((d, i) => {
      const [color, shape] = styles[i];
      const icon = sv("svg", { width: 22, height: 12, viewBox: "0 0 22 12" });
      sv("line", { x1: 0, x2: 22, y1: 6, y2: 6, stroke: color, "stroke-width": 2 }, icon);
      marker(icon, shape, 11, 6, 4.2, color);
      leg.append(el("span", {}, icon, `${d.name}: ${d.data}`));
    });
    chart("dip-chart", (host, W) => {
      const H = 320, l = 44, r = 12, t = 14, b = 52;
      const svg = svgBox(host, W, H);
      const x = lin(-0.4, 8.4, l, W - r);
      const y = lin(0, 1, H - b, t);
      sv("rect", { x: x(3.55), y: t, width: x(4.45) - x(3.55), height: H - b - t, fill: "color-mix(in srgb, var(--compress) 12%, transparent)" }, svg);
      sv("text", { x: x(4), y: t + 12, "text-anchor": "middle", class: "t-strong", text: "compress" }, svg);
      for (const v of [0, 0.25, 0.5, 0.75, 1]) {
        sv("line", { x1: l, x2: W - r, y1: y(v), y2: y(v), class: v === 0 ? "axis" : "grid" }, svg);
        sv("text", { x: l - 6, y: y(v) + 4, "text-anchor": "end", text: Math.round(v * 100) + "%" }, svg);
      }
      for (let k = 0; k <= 8; k++) {
        sv("text", { x: x(k), y: H - b + 16, "text-anchor": "middle", class: k === 4 ? "t-strong" : "t-ink2", text: "v" + k }, svg);
        sv("text", { x: x(k), y: H - b + 30, "text-anchor": "middle", text: k === 0 ? "human" : W < 560 ? SCHEDULE[k].slice(0, 4) : SCHEDULE[k] }, svg);
        sv("text", { x: x(k), y: H - b + 43, "text-anchor": "middle", text: COVERAGE[k] + "%" }, svg);
      }
      D.slice().reverse().forEach((d, ri) => {
        const i = D.length - 1 - ri;
        const [color, shape, width] = styles[i];
        sv("polyline", { points: d.rates.map((p) => `${x(p[0])},${y(p[1])}`).join(" "), fill: "none", stroke: color, "stroke-width": width, "stroke-linejoin": "round" }, svg);
        for (const p of d.rates) marker(svg, shape, x(p[0]), y(p[1]), i === 0 ? 5 : 4.5, color);
      });
      for (let k = 0; k <= 8; k++) {
        const hit = sv("rect", { x: x(k - 0.5), y: t, width: x(k + 0.5) - x(k - 0.5), height: H - b - t, class: "hit" }, svg);
        bindTip(hit, `v${k} · ${k === 0 ? "human original" : SCHEDULE[k] + " · " + COVERAGE[k] + "% AI"}` + D.map((d) => {
          const p = d.rates[k][1];
          const step = k === 4 ? ` (${fmt((p - d.rates[3][1]) * 100, 1)} pts from v3)` : "";
          return `<br>${d.name.replace(" (ours)", "").replace("Word + character ", "")}, ${d.data.startsWith("OpAI") ? "OpAI-Bench" : "Newsroom"}: <b>${(p * 100).toFixed(1)}%</b>${step}`;
        }).join(""));
      }
    });
  }

  /* ---------------------------------------------------------------- game */
  const game = { order: shuffle(S.guess.map((_, i) => i)), pos: 0, you: 0, hc: 0, played: 0, answered: false, aiSide: "A" };
  const current = () => S.guess[game.order[game.pos % game.order.length]];

  function chainText(first, k) {
    const later = [];
    for (let j = first + 1; j <= k; j++) later.push(SCHEDULE[j]);
    return `v${first} ${SCHEDULE[first]}` + (later.length ? " → " + later.join(" → ") : "");
  }

  /* Word-level diff of two aligned sentences: the words of `a` that are not in their longest common
     subsequence with `b` are wrapped in <mark>, along with the spaces between neighboring changed words. */
  function diffWords(a, b) {
    const ta = a.match(/\S+|\s+/g) || [], tb = b.match(/\S+|\s+/g) || [];
    const wa = ta.filter((t) => /\S/.test(t)), wb = tb.filter((t) => /\S/.test(t));
    const L = Array.from({ length: wa.length + 1 }, () => new Uint16Array(wb.length + 1));
    for (let i = wa.length - 1; i >= 0; i--)
      for (let j = wb.length - 1; j >= 0; j--)
        L[i][j] = wa[i] === wb[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
    const changed = [];
    let i = 0, j = 0;
    while (i < wa.length) {
      if (j < wb.length && wa[i] === wb[j]) { changed.push(false); i++; j++; }
      else if (j < wb.length && L[i][j + 1] > L[i + 1][j]) j++;
      else { changed.push(true); i++; }
    }
    const frag = document.createDocumentFragment();
    let w = 0, run = null;
    ta.forEach((t, k) => {
      if (/\S/.test(t)) {
        if (changed[w]) { if (!run) { run = el("mark", { class: "diff" }); frag.append(run); } run.append(t); }
        else { run = null; frag.append(t); }
        w++;
      } else if (run && changed[w]) run.append(t);  // space between two changed words stays inside the mark
      else { run = null; frag.append(t); }
    });
    return frag;
  }

  function renderPassage(item, which, reveal) {
    const isAI = which === "ai";
    const tag = isAI === (game.aiSide === "A") ? "A" : "B";
    const card = el("article", { class: "passage" + (reveal ? (isAI ? " is-ai" : " is-human") : ""), "aria-label": "Passage " + tag });
    const head = el("div", { class: "passage-head" }, el("span", { class: "tag", text: "Passage " + tag }));
    if (reveal) head.append(el("span", { class: "verdict " + (isAI ? "ai" : "human"), text: isAI ? `AI-edited · v${item.k}` : "Human original · v0" }));
    else {
      const pick = el("button", { type: "button" }, "This one is AI-edited");
      pick.addEventListener("click", () => answer(tag));
      head.append(pick);
    }
    card.append(head);
    const doc = el("div", { class: "doc" });
    const sents = isAI ? item.ai : item.human;
    sents.forEach((s, i) => {
      const edited = item.labels[i] === 1;
      const other = isAI ? item.human[i] : item.ai[i];
      const span = el("span", { class: "s" + (reveal && edited ? (isAI ? " ai" : " was") : "") });
      span.append(s === other ? s : diffWords(s, other));
      doc.append(span);
      if (reveal && edited && isAI) doc.append(el("span", { class: "chain", text: chainText(item.first[i], item.k) }));
      doc.append(" ");
    });
    card.append(doc);
    return card;
  }

  function renderGame() {
    const item = current();
    const order = game.aiSide === "A" ? ["ai", "human"] : ["human", "ai"];
    $("#passages").replaceChildren(...order.map((w) => renderPassage(item, w, game.answered)));
    $("#game-context").textContent = `${DOMAIN[item.domain]} · the edited one is v${item.k} (${item.op}, ${item.coverage}% of sentences AI-edited)`;
    $("#tally").textContent = game.played ? `You ${game.you}/${game.played} · HC ${game.hc}/${game.played}` : `Pair 1`;
    $("#next-top").hidden = !game.answered;
    if (!game.answered) { $("#game-status").textContent = ""; $("#game-status").className = "game-status"; }
  }

  function answer(pick) {
    if (game.answered) return;
    const item = current();
    game.answered = true;
    game.played++;
    const right = pick === game.aiSide;
    if (right) game.you++;
    const hcPick = item.L_ai < item.L_human ? game.aiSide : (game.aiSide === "A" ? "B" : "A");
    const hcRight = hcPick === game.aiSide;
    if (hcRight) game.hc++;
    renderGame();
    const flag = (L) => (L < TAU ? "flagged as AI-edited" : "passed as human");
    const status = $("#game-status");
    status.textContent = right ? "Correct" : `No, it was ${game.aiSide}`;
    status.className = "game-status " + (right ? "right" : "wrong");
    const box = $("#result");
    const nEdited = item.labels.filter(Boolean).length;
    box.replaceChildren(
      el("div", { class: "head " + (right ? "right" : "wrong"), text: right ? `Correct: passage ${game.aiSide} is AI-edited.` : `Not this time: passage ${game.aiSide} is AI-edited.` }),
      el("p", { text: `${nEdited} of the ${item.labels.length} sentences shown were edited by ${item.generator}. Dotted underlines mark the same sentences in the original.` }),
      el("p", { text: `HC classifier on the full documents: the original scores L = ${fmtPlain(item.L_human)} (${flag(item.L_human)}), the v${item.k} version scores L = ${fmtPlain(item.L_ai)} (${flag(item.L_ai)}). Picking the lower score, it ${hcRight ? "also gets this pair right" : "gets this pair wrong"}.` }),
      el("div", { class: "controls" },
        el("button", { type: "button", id: "next-pair" }, "Next pair"),
        el("a", { href: "#method", class: "small" }, "How does the classifier decide?")));
    box.hidden = false;
    $("#next-pair").addEventListener("click", nextPair);
  }
  function nextPair() {
    game.pos++;
    game.answered = false;
    game.aiSide = Math.random() < 0.5 ? "A" : "B";
    $("#result").hidden = true;
    renderGame();
  }
  game.aiSide = Math.random() < 0.5 ? "A" : "B";
  $("#next-top").addEventListener("click", nextPair);
  renderGame();

  /* ---------------------------------------------------------------- step 1: bag of words */
  {
    const sentence = S.sentences[0].base;
    const toks = sentence.toLowerCase().match(TOKEN) || [];
    const counts = new Map();
    toks.forEach((t) => counts.set(t, (counts.get(t) || 0) + 1));
    const top = [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, 7);
    const hot = new Set(top.filter(([, c]) => c > 1).map(([w]) => w));
    $("#tok-demo").replaceChildren(...toks.map((t) => el("span", { class: "tok" + (hot.has(t) ? " hot" : ""), text: t })));
    const table = $("#count-demo");
    table.append(el("tr", {}, el("th", { text: "word" }), el("th", { class: "n", text: "count" }), el("th", { class: "n", text: "f = count / n" })));
    for (const [w, c] of top) table.append(el("tr", {}, el("td", { text: w }), el("td", { class: "n", text: c }), el("td", { class: "n", text: (c / toks.length).toFixed(3) })));
    table.append(el("tr", {}, el("td", { class: "muted", text: `+ ${counts.size - top.length} more words` }), el("td", { class: "n", text: "" }), el("td", { class: "n muted", text: `n = ${toks.length}` })));
  }

  /* ---------------------------------------------------------------- step 2: word rates */
  {
    const R = S.word_rates.rates;
    const cats = [["train_human", "Human original", "var(--human)"], ["train_ai", "AI-edited (one random version)", "var(--ai)"]];
    legend("rate-legend", cats.map(([, l, c, ring]) => [l, c, ring ? "ring" : ""]));
    const groups = [
      ["AI-leaning", ["significant", "specifically", "within", "effectively", "crucial", "comprehensive", "regarding", "numerous"]],
      ["Human-leaning", ["but", "have", "there", "just", "going"]],
      ["Common words", ["and", "a"]],
    ];
    const zOf = (w) => (MODEL.get(w) ? MODEL.get(w).z : S.word_rates.extra_z[w]);
    chart("rate-chart", (host, W) => {
      const rowH = 26, gapH = 26, left = 112, right = 16, top = 22;
      const rows = groups.reduce((n, [, ws]) => n + ws.length, 0);
      const H = top + rows * rowH + groups.length * gapH + 8;
      const svg = svgBox(host, W, H);
      const x = logs(0.2, 1000, left, W - right);
      for (const t of [0.3, 1, 3, 10, 30, 100, 300, 1000]) {
        sv("line", { x1: x(t), x2: x(t), y1: top - 4, y2: H - 6, class: "grid" }, svg);
        sv("text", { x: x(t), y: top - 10, "text-anchor": "middle", text: t >= 1 ? t : t.toString() }, svg);
      }
      let y = top;
      for (const [name, ws] of groups) {
        y += gapH;
        sv("text", { x: 0, y: y - 8, class: "t-strong", text: name }, svg);
        for (const w of ws) {
          const cy = y + rowH / 2;
          const z = zOf(w);
          sv("text", { x: 0, y: cy + 4, class: "t-ink", text: w }, svg);
          sv("text", { x: left - 10, y: cy + 4, "text-anchor": "end", class: "mono", text: `z ${fmtPlain(z, 0)}` }, svg);
          const vals = cats.map(([k]) => Math.max(0.2, R[k][w]));
          sv("line", { x1: x(Math.min(...vals)), x2: x(Math.max(...vals)), y1: cy, y2: cy, stroke: "var(--rule)", "stroke-width": 3, "stroke-linecap": "round" }, svg);
          cats.forEach(([k, label, color, ring], i) => {
            const v = R[k][w];
            sv("circle", { cx: x(Math.max(0.2, v)), cy, r: ring ? 5 : 5.5, fill: ring ? "var(--surface)" : color, stroke: ring ? color : "var(--surface)", "stroke-width": 2 }, svg);
            const hit = sv("circle", { cx: x(Math.max(0.2, v)), cy, r: 10, class: "hit" }, svg);
            bindTip(hit, `<b>${w}</b><br>${label}: ${v.toFixed(1)} per 10,000 words`);
          });
          y += rowH;
        }
      }
    });
  }

  /* ---------------------------------------------------------------- step 3: z histogram and HC curve */
  {
    const H3 = S.hc;
    chart("z-hist", (host, W) => {
      const H = 250, l = 40, r = 10, t = 12, b = 34;
      const svg = svgBox(host, W, H);
      const e = H3.hist_edges, c = H3.hist_counts;
      const x = lin(e[0], e[e.length - 1], l, W - r);
      const y = logs(0.7, 5000, H - b, t);
      for (const v of [1, 10, 100, 1000]) {
        sv("line", { x1: l, x2: W - r, y1: y(v), y2: y(v), class: "grid" }, svg);
        sv("text", { x: l - 6, y: y(v) + 4, "text-anchor": "end", text: v.toLocaleString() }, svg);
      }
      const bw = 0.5;
      c.forEach((n, i) => {
        if (!n) return;
        const mid = e[i] + bw / 2;
        const sel = Math.abs(mid) >= H3.z_threshold;
        const fill = sel ? (mid < 0 ? "var(--ai)" : "var(--human)") : "var(--muted)";
        const x0 = x(e[i]) + 1, x1 = x(e[i + 1]) - 1;
        sv("rect", { x: x0, y: y(n), width: Math.max(1, x1 - x0), height: y(0.7) - y(n), fill, opacity: sel ? 1 : 0.45, rx: 1.5 }, svg);
        const hit = sv("rect", { x: x(e[i]), y: t, width: x(e[i + 1]) - x(e[i]), height: H - b - t, class: "hit" }, svg);
        const range = i === 0 ? `z ≤ ${e[1]}` : i === c.length - 1 ? `z ≥ ${e[i]}` : `${e[i]} ≤ z < ${e[i + 1]}`;
        bindTip(hit, `${range}<br><b>${n.toLocaleString()}</b> words${sel ? " · selected" : ""}`);
      });
      // null: P * binwidth * phi(z)
      const pts = [];
      for (let z = -5.5; z <= 5.5; z += 0.1) {
        const d = H3.P * bw * Math.exp(-z * z / 2) / Math.sqrt(2 * Math.PI);
        if (d >= 0.7) pts.push(`${x(z).toFixed(1)},${y(d).toFixed(1)}`);
      }
      sv("polyline", { points: pts.join(" "), fill: "none", stroke: "var(--ink)", "stroke-width": 1.5, "stroke-dasharray": "4 3" }, svg);
      for (const v of [-H3.z_threshold, H3.z_threshold]) sv("line", { x1: x(v), x2: x(v), y1: t, y2: H - b, stroke: "var(--ink-2)", "stroke-width": 1 }, svg);
      sv("line", { x1: l, x2: W - r, y1: H - b, y2: H - b, class: "axis" }, svg);
      for (const v of [-12, -6, 0, 6, 12]) sv("text", { x: x(v), y: H - b + 16, "text-anchor": "middle", text: v === -12 ? "≤ −12" : v === 12 ? "≥ 12" : fmtPlain(v, 0) }, svg);
      sv("text", { x: (l + W - r) / 2, y: H - 2, "text-anchor": "middle", class: "t-ink2", text: "Welch z (negative = AI uses it more)" }, svg);
      sv("text", { x: x(-H3.z_threshold) - 4, y: t + 10, "text-anchor": "end", class: "t-ink2", text: `${H3.n_ai} AI-leaning` }, svg);
      sv("text", { x: W - r, y: t + 10, "text-anchor": "end", class: "t-ink2", text: `${H3.n_human} human-leaning` }, svg);
    });

    chart("hc-curve", (host, W) => {
      const H = 250, l = 40, r = 14, t = 12, b = 34;
      const svg = svgBox(host, W, H);
      const pts = H3.hc;
      const x = logs(1, 3500, l, W - r);
      const y = lin(0, 55, H - b, t);
      sv("rect", { x: l, y: t, width: x(H3.m_cap) - l, height: H - b - t, fill: "var(--surface-2)" }, svg);
      for (const v of [0, 10, 20, 30, 40, 50]) {
        sv("line", { x1: l, x2: W - r, y1: y(v), y2: y(v), class: "grid" }, svg);
        sv("text", { x: l - 6, y: y(v) + 4, "text-anchor": "end", text: v }, svg);
      }
      sv("polyline", { points: pts.map(([m, h]) => `${x(m).toFixed(1)},${y(Math.max(0, h)).toFixed(1)}`).join(" "), fill: "none", stroke: "var(--ink)", "stroke-width": 2, "stroke-linejoin": "round" }, svg);
      const star = pts.reduce((a, p) => (Math.abs(p[0] - H3.m_star) < Math.abs(a[0] - H3.m_star) ? p : a));
      const peak = pts.reduce((a, p) => (p[1] > a[1] ? p : a));
      sv("circle", { cx: x(star[0]), cy: y(star[1]), r: 5, fill: "var(--ai)", stroke: "var(--surface)", "stroke-width": 2 }, svg);
      sv("text", { x: x(star[0]) - 8, y: y(star[1]) - 8, "text-anchor": "end", class: "t-strong", text: `m* = ${H3.m_star}` }, svg);
      sv("circle", { cx: x(peak[0]), cy: y(peak[1]), r: 4, fill: "var(--surface)", stroke: "var(--ink-2)", "stroke-width": 1.5 }, svg);
      sv("text", { x: x(peak[0]), y: y(peak[1]) - 10, "text-anchor": "middle", class: "t-ink2", text: "uncapped peak" }, svg);
      sv("line", { x1: l, x2: W - r, y1: H - b, y2: H - b, class: "axis" }, svg);
      for (const v of [1, 10, 100, 1000]) sv("text", { x: x(v), y: H - b + 16, "text-anchor": "middle", text: v.toLocaleString() }, svg);
      sv("text", { x: (l + W - r) / 2, y: H - 2, "text-anchor": "middle", class: "t-ink2", text: "m, number of smallest p-values kept" }, svg);
      const hit = sv("rect", { x: l, y: t, width: W - r - l, height: H - b - t, class: "hit" }, svg);
      hit.addEventListener("pointermove", (ev) => {
        const box = svg.getBoundingClientRect();
        const px = ((ev.clientX - box.left) / box.width) * W;
        const p = pts.reduce((a, q) => (Math.abs(x(q[0]) - px) < Math.abs(x(a[0]) - px) ? q : a));
        showTip(`m = <b>${p[0].toLocaleString()}</b><br>HC(m) = <b>${p[1].toFixed(1)}</b>`, ev.clientX, ev.clientY);
      });
      hit.addEventListener("pointerleave", () => { tip.hidden = true; });
    });
  }

  /* ---------------------------------------------------------------- step 4: word wall */
  {
    const words = S.model.words;
    const ai = words.filter((w) => w[3] < 0).sort((a, b) => a[3] - b[3]);
    const hu = words.filter((w) => w[3] > 0).sort((a, b) => b[3] - a[3]);
    $("#wall-count").textContent = `${ai.length} AI-leaning and ${hu.length} human-leaning words were selected.`;
    let all = false;
    function fill() {
      const take = (list, n) => (all ? list : list.slice(0, n));
      for (const [id, list, side, n] of [["#wall-ai", ai, "ai", 90], ["#wall-human", hu, "human", 45]]) {
        $(id).replaceChildren(...take(list, n).map(([w, wt, , z]) => {
          const s = el("span", { class: "w " + side, style: `--a:${alphaFor(z)}`, text: w });
          bindTip(s, `<b>${w}</b><br>z = ${fmtPlain(z, 1)} · weight ${fmtPlain(wt, 0)}`);
          return s;
        }));
      }
      $("#wall-more").textContent = all ? "Show the strongest words only" : `Show all ${words.length} words`;
    }
    $("#wall-more").addEventListener("click", () => { all = !all; fill(); });
    fill();
  }

  /* ---------------------------------------------------------------- cross-validation (below the steps) */
  {
    const T = RES0.tuning, DEV = RES0.dev;
    const key = (r) => r.slice(0, 4).join("|");
    const top = new Set(DEV.map(key)), chosen = key(DEV[0]);
    const rowsDef = [[true, true, "Frequencies, standardized"], [true, false, "Frequencies, raw"], [false, true, "Counts, standardized"], [false, false, "Counts, raw"]];
    const alphas = [0.05, 0.1, 0.25, 0.5];
    legend("cv-legend", [["Chosen setting", "var(--ai)"], ["Other top five", "var(--ink)", "ring"], ["Other settings", "var(--muted)"]]);
    chart("cv-chart", (host, W) => {
      const l = W < 520 ? 120 : 160, r = 16, t = 8, rowH = 38, b = 34;
      const H = t + rowsDef.length * rowH + b;
      const svg = svgBox(host, W, H);
      const lo = Math.floor(Math.min(...T.map((d) => d[4])) * 50) / 50, hi = 0.8;
      const x = lin(lo, hi, l, W - r);
      for (let v = lo; v <= hi + 1e-9; v += 0.02) {
        sv("line", { x1: x(v), x2: x(v), y1: t, y2: H - b, class: "grid" }, svg);
        sv("text", { x: x(v), y: H - b + 16, "text-anchor": "middle", text: v.toFixed(2) }, svg);
      }
      sv("text", { x: (l + W - r) / 2, y: H - 2, "text-anchor": "middle", text: "mean AUROC over 5 folds" }, svg);
      rowsDef.forEach(([freq, std, label], i) => {
        const cy = t + i * rowH + rowH / 2;
        sv("text", { x: 0, y: cy + 4, class: "t-ink", text: label }, svg);
        T.filter((d) => d[2] === freq && d[3] === std).sort((a, b) => key(a) === chosen ? 1 : top.has(key(a)) - top.has(key(b))).forEach((d) => {
          const k = key(d), jitter = (alphas.indexOf(d[0]) - 1.5) * 4;
          const isChosen = k === chosen, isTop = top.has(k);
          sv("circle", { cx: x(d[4]), cy: cy + jitter, r: isChosen ? 7 : isTop ? 6 : 4.5,
            fill: isChosen ? "var(--ai)" : isTop ? "var(--surface)" : "var(--muted)", opacity: isChosen || isTop ? 1 : 0.55,
            stroke: isChosen ? "var(--surface)" : isTop ? "var(--ink)" : "none", "stroke-width": 2 }, svg);
          const hit = sv("circle", { cx: x(d[4]), cy: cy + jitter, r: 9, class: "hit" }, svg);
          bindTip(hit, `α₀ = ${d[0]}, min_df = ${d[1]}<br>${label.toLowerCase()}<br>CV AUROC <b>${d[4].toFixed(3)}</b> ± ${d[5].toFixed(3)}<br>about ${d[7].toLocaleString()} words selected`);
        });
      });
    });
    const tbl = $("#dev-table");
    tbl.append(el("tr", {}, ...["α₀", "min_df", "features", "words", "CV AUROC", "dev accuracy", "dev AUROC"].map((h) => el("th", { text: h }))));
    DEV.forEach((d, i) => tbl.append(el("tr", { style: i === 0 ? "font-weight:600" : "" },
      el("td", { text: String(d[0]) + (i === 0 ? " (chosen)" : "") }), el("td", { text: d[1] }),
      el("td", { text: `${d[2] ? "freq." : "counts"}, ${d[3] ? "std." : "raw"}` }), el("td", { text: d[7].toLocaleString() }),
      el("td", { text: d[4].toFixed(3) }), el("td", { text: d[5].toFixed(3) }), el("td", { text: d[6].toFixed(3) }))));
  }

  /* ---------------------------------------------------------------- step 5: score a whole article
     The scorer keeps its own article, separate from the game, drawn at random from the same test documents. */
  const detState = { item: Math.floor(Math.random() * S.guess.length), ex: "human", own: "Type or paste any English text here. Additionally, it is crucial to note that numerous significant factors, specifically those within the comprehensive framework, consistently shape the outcome." };
  const detInput = $("#det-input");
  function setExample(ex) {
    detState.ex = ex;
    $$("[data-ex]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.ex === ex)));
    const item = S.guess[detState.item];
    detInput.value = ex === "own" ? detState.own : ex === "ai" ? item.full_ai : item.full_human;
    $("#det-meta").textContent = ex === "own" ? "" :
      `${DOMAIN[item.domain]}, ${ex === "ai" ? `v${item.k} (${item.op}, ${item.coverage}% of sentences AI-edited by ${item.generator})` : "human original (v0)"} · ${(ex === "ai" ? item.words_ai : item.words_human).toLocaleString()} words`;
    updateDetector();
  }
  $("#det-new").addEventListener("click", () => {
    let next;
    do next = Math.floor(Math.random() * S.guess.length); while (next === detState.item && S.guess.length > 1);
    detState.item = next;
    setExample(detState.ex === "own" ? "human" : detState.ex);
  });
  let drawLine;
  function updateDetector() {
    const text = detInput.value;
    if (detState.ex === "own") detState.own = text;
    $("#det-colored").replaceChildren(colorize(text));
    const s = score(text);
    detState.last = s;
    const flagged = s.L < TAU;
    $("#det-breakdown").replaceChildren(
      el("div", {}, el("b", { text: fmt(s.ai) }), el("span", { text: "AI-leaning words" })),
      el("div", {}, el("b", { text: fmt(s.human) }), el("span", { text: "human-leaning words" })),
      el("div", {}, el("b", { text: fmt(s.base) }), el("span", { text: "baseline" })),
      el("div", { class: "total" }, el("b", { text: s.n ? fmtPlain(s.L) : "–" }), el("span", { text: s.n ? (flagged ? "L(d): flagged as AI" : "L(d): passes as human") : "no words yet" })));
    if (drawLine) drawLine();
  }
  drawLine = chart("det-line", (host, W) => {
    const s = detState.last || score(detInput.value);
    const H = 64, l = 8, r = 8, cy = 30;
    const svg = svgBox(host, W, H);
    const lo = -150, hi = 100;
    const x = lin(lo, hi, l, W - r);
    sv("rect", { x: l, y: cy - 7, width: x(TAU) - l, height: 14, rx: 7, fill: "color-mix(in srgb, var(--ai) var(--tint), transparent)" }, svg);
    sv("rect", { x: x(TAU), y: cy - 7, width: W - r - x(TAU), height: 14, rx: 7, fill: "color-mix(in srgb, var(--human) var(--tint), transparent)" }, svg);
    sv("line", { x1: x(TAU), x2: x(TAU), y1: cy - 14, y2: cy + 14, stroke: "var(--ink)", "stroke-width": 1.5 }, svg);
    sv("text", { x: x(TAU), y: cy + 28, "text-anchor": "middle", class: "t-ink2", text: "τ = −13.2" }, svg);
    sv("text", { x: l + 4, y: cy + 28, text: "← more AI-like" }, svg);
    sv("text", { x: W - r - 4, y: cy + 28, "text-anchor": "end", text: "more human-like →" }, svg);
    if (s.n) {
      const v = Math.max(lo, Math.min(hi, s.L));
      sv("circle", { cx: x(v), cy, r: 8, fill: s.L < TAU ? "var(--ai)" : "var(--human)", stroke: "var(--surface)", "stroke-width": 2.5 }, svg);
      const anchor = x(v) > W - 70 ? "end" : x(v) < 70 ? "start" : "middle";
      sv("text", { x: x(v), y: cy - 14, "text-anchor": anchor, class: "t-strong mono", text: (s.L < lo ? "< " : s.L > hi ? "> " : "") + "L = " + fmtPlain(s.L) }, svg);
    }
  });
  $$("[data-ex]").forEach((b) => b.addEventListener("click", () => setExample(b.dataset.ex)));
  detInput.addEventListener("input", () => {
    if (detState.ex !== "own") { detState.ex = "own"; $$("[data-ex]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.ex === "own"))); $("#det-meta").textContent = ""; }
    updateDetector();
  });
  setExample("human");

  /* ---------------------------------------------------------------- sentences */
  {
    const order = shuffle(S.sentences.map((_, i) => i));
    let pos = 0;
    const rows = [["base", "Original", "var(--ink)"], ["compress", "Compress", "var(--compress)"], ["paraphrase", "Paraphrase", "var(--paraphrase)"], ["expand", "Expand", "var(--expand)"]];
    function render() {
      const s = S.sentences[order[pos % order.length]];
      $("#sent-meta").textContent = `${DOMAIN[s.domain]} · sentence ${(pos % order.length) + 1} of ${order.length}`;
      const nBase = s.base.split(/\s+/).length;
      $("#versions").replaceChildren(...rows.map(([k, label, color]) => {
        const text = s[k];
        const n = text.split(/\s+/).length;
        const nAI = (text.toLowerCase().match(TOKEN) || []).filter((t) => MODEL.get(t) && MODEL.get(t).z < 0).length;
        return el("div", { class: "vcol" },
          el("div", { class: "op-name" }, el("span", { class: "dot", style: k === "base" ? "border:2px solid var(--ink)" : `background:${color}` }), label),
          el("div", { class: "doc" }, colorize(text, "ai")),
          el("div", { class: "count" }, el("b", { text: `${n} words` }), k === "base" ? "" : ` (${n >= nBase ? "+" : "−"}${Math.abs(n - nBase)})`,
            el("br"), `${nAI} AI-leaning word${nAI === 1 ? "" : "s"}`));
      }));
    }
    $("#sent-next").addEventListener("click", () => { pos++; render(); });
    render();

    const R = S.word_rates.rates;
    const aiWords = S.model.words.filter((w) => w[3] < 0).map((w) => w[0]);
    const per1k = (k) => aiWords.reduce((a, w) => a + (R[k][w] || 0), 0) / 10;
    const bars = rows.map(([k, label, color]) => [label, k === "base" ? per1k("abl_human") : per1k(k), color, k === "base"]);
    chart("vocab-bars", (host, W) => {
      const l = 92, r = 44, rowH = 40, t = 6;
      const H = t + bars.length * rowH + 4;
      const svg = svgBox(host, W, H);
      const max = Math.max(...bars.map((b) => b[1]));
      const x = lin(0, max * 1.05, l, W - r);
      bars.forEach(([label, v, color, ring], i) => {
        const y = t + i * rowH;
        sv("text", { x: 0, y: y + rowH / 2 + 4, class: "t-ink", text: label }, svg);
        sv("rect", { x: l, y: y + 9, width: Math.max(2, x(v) - l), height: rowH - 18, rx: 4, fill: ring ? "var(--surface-2)" : color, stroke: ring ? "var(--ink)" : "none", "stroke-width": ring ? 1.5 : 0 }, svg);
        sv("text", { x: x(v) + 6, y: y + rowH / 2 + 4, class: "t-ink mono", text: v.toFixed(1) }, svg);
        const hit = sv("rect", { x: l, y, width: W - l, height: rowH, class: "hit" }, svg);
        bindTip(hit, `${label}: <b>${v.toFixed(1)}</b> AI-leaning words per 1,000 words`);
      });
      sv("line", { x1: l, x2: l, y1: t, y2: H - 4, class: "axis" }, svg);
    });
  }

  /* ---------------------------------------------------------------- results */
  const RES = S.results;
  $("#r-acc").textContent = RES.overall.accuracy.toFixed(3);
  $("#sum-acc3").textContent = RES.accuracy["pooled-welch"][2][1].toFixed(3);
  $("#sum-acc4").textContent = RES.accuracy["pooled-welch"][3][1].toFixed(3);
  $("#r-auc").textContent = RES.overall.auroc.toFixed(3);

  // Q1: accuracy by version
  {
    const series = [["pooled-welch", "Pooled HC (trained on all versions)", "var(--ink)", ""], ["per-version-welch", "Per-version HC (trained on v0 vs. vk)", "var(--muted)", "4 3"]];
    legend("acc-legend", series.map(([, l, c]) => [l, c, "line"]));
    chart("acc-chart", (host, W) => {
      const H = 300, l = 44, r = 12, t = 14, b = 52;
      const svg = svgBox(host, W, H);
      const x = lin(0.6, 8.4, l, W - r);
      const y = lin(0.45, 0.92, H - b, t);
      sv("rect", { x: x(3.55), y: t, width: x(4.45) - x(3.55), height: H - b - t, fill: "color-mix(in srgb, var(--compress) 12%, transparent)" }, svg);
      for (const v of [0.5, 0.6, 0.7, 0.8, 0.9]) {
        sv("line", { x1: l, x2: W - r, y1: y(v), y2: y(v), class: "grid" }, svg);
        sv("text", { x: l - 6, y: y(v) + 4, "text-anchor": "end", text: v.toFixed(1) }, svg);
      }
      sv("text", { x: W - r, y: y(0.5) - 5, "text-anchor": "end", text: "chance" }, svg);
      for (let k = 1; k <= 8; k++) {
        sv("text", { x: x(k), y: H - b + 16, "text-anchor": "middle", class: k === 4 ? "t-strong" : "t-ink2", text: "v" + k }, svg);
        sv("text", { x: x(k), y: H - b + 30, "text-anchor": "middle", text: W < 520 ? SCHEDULE[k].slice(0, 4) : SCHEDULE[k] }, svg);
        sv("text", { x: x(k), y: H - b + 43, "text-anchor": "middle", text: COVERAGE[k] + "%" }, svg);
      }
      for (const [key, , color, dash] of series) {
        const pts = RES.accuracy[key];
        const band = pts.map(([k, a, h]) => `${x(k)},${y(a + h)}`).concat(pts.slice().reverse().map(([k, a, h]) => `${x(k)},${y(a - h)}`));
        sv("polygon", { points: band.join(" "), fill: color, opacity: 0.12 }, svg);
        sv("polyline", { points: pts.map(([k, a]) => `${x(k)},${y(a)}`).join(" "), fill: "none", stroke: color, "stroke-width": 2, "stroke-dasharray": dash }, svg);
        for (const [k, a, h] of pts) {
          sv("circle", { cx: x(k), cy: y(a), r: 4.5, fill: color, stroke: "var(--surface)", "stroke-width": 2 }, svg);
        }
      }
      for (let k = 1; k <= 8; k++) {
        const hit = sv("rect", { x: x(k - 0.5), y: t, width: x(k + 0.5) - x(k - 0.5), height: H - b - t, class: "hit" }, svg);
        const p = RES.accuracy["pooled-welch"][k - 1], q = RES.accuracy["per-version-welch"][k - 1];
        bindTip(hit, `v${k} · ${SCHEDULE[k]} · ${COVERAGE[k]}% AI<br>Pooled: <b>${p[1].toFixed(3)}</b><br>Per-version: <b>${q[1].toFixed(3)}</b>`);
      }
      const p3 = RES.accuracy["pooled-welch"][2][1], p4 = RES.accuracy["pooled-welch"][3][1];
      sv("text", { x: x(4), y: y(p4) + 22, "text-anchor": "middle", class: "t-strong", text: `${fmt((p4 - p3) * 100, 1)} pts` }, svg);
    });
  }

  // Q2a: ablation
  {
    let model = "main-trained";
    const colors = { compress: "var(--compress)", paraphrase: "var(--paraphrase)", expand: "var(--expand)" };
    const draw = chart("abl-chart", (host, W) => {
      const H = 280, l = 44, r = 86, t = 12, b = 40;
      const svg = svgBox(host, W, H);
      const x = lin(18, 82, l, W - r);
      const y = lin(0.45, 1.0, H - b, t);
      for (const v of [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]) {
        sv("line", { x1: l, x2: W - r, y1: y(v), y2: y(v), class: "grid" }, svg);
        sv("text", { x: l - 6, y: y(v) + 4, "text-anchor": "end", text: v.toFixed(1) }, svg);
      }
      for (const c of [25, 50, 75]) sv("text", { x: x(c), y: H - b + 16, "text-anchor": "middle", class: "t-ink2", text: c + "%" }, svg);
      sv("text", { x: (l + W - r) / 2, y: H - 4, "text-anchor": "middle", text: "share of sentences AI-edited" }, svg);
      const rows = RES.ablation[model];
      OPS.forEach((op, oi) => {
        const pts = rows.filter((r) => r[0] === op).sort((a, b) => a[1] - b[1]);
        const dx = (oi - 1) * 5;
        sv("polyline", { points: pts.map((p) => `${x(p[1]) + dx},${y(p[2])}`).join(" "), fill: "none", stroke: colors[op], "stroke-width": 2 }, svg);
        for (const [, cov, acc, lo, hi] of pts) {
          sv("line", { x1: x(cov) + dx, x2: x(cov) + dx, y1: y(lo), y2: y(hi), stroke: colors[op], "stroke-width": 2, opacity: 0.55 }, svg);
          sv("circle", { cx: x(cov) + dx, cy: y(acc), r: 5, fill: colors[op], stroke: "var(--surface)", "stroke-width": 2 }, svg);
          const hit = sv("circle", { cx: x(cov) + dx, cy: y(acc), r: 11, class: "hit" }, svg);
          bindTip(hit, `${op} · ${cov}%<br>accuracy <b>${acc.toFixed(3)}</b><br>95% CI ${lo.toFixed(3)}–${hi.toFixed(3)}`);
        }
        const last = pts[pts.length - 1];
        const ly = y(last[2]) + (op === "expand" ? -6 : op === "paraphrase" ? 10 : 4);
        sv("text", { x: x(last[1]) + 14, y: ly, class: "t-ink", text: op }, svg);
      });
    });
    $$("[data-model]").forEach((b) => b.addEventListener("click", () => {
      model = b.dataset.model;
      $$("[data-model]").forEach((o) => o.setAttribute("aria-pressed", String(o === b)));
      draw();
    }));
  }

  // Q2b: no-compress swap
  {
    let metric = "score";
    const runs = [["e5-small|compress", "v4 = compress (benchmark schedule)", "var(--compress)"], ["e5-small|no_compress", "v4 = paraphrase (our swap)", "var(--paraphrase)"]];
    legend("swap-legend", runs.map(([, l, c]) => [l, c, "line"]));
    const d = Object.fromEntries(RES.swap_diff.filter((r) => r.detector === "e5-small").map((r) => [`${r.metric}|${r.comparison}`, r]));
    const cap = () => {
      const k = metric === "score" ? "score" : "flag";
      const c = d[`${k}|compress`], n = d[`${k}|no_compress`], df = d[`${k}|no_compress minus compress`];
      const u = metric === "score" ? (v) => fmt(v, 3) : (v) => fmt(v * 100, 1) + " pts";
      $("#swap-cap").textContent = `Change from v3 to v4: ${u(c.v4_minus_v3)} with compression, ${u(n.v4_minus_v3)} with paraphrase. Difference ${u(df.v4_minus_v3)} (95% CI ${u(df.ci_low)} to ${u(df.ci_high)}), bootstrapped over articles.`;
    };
    const draw = chart("swap-chart", (host, W) => {
      const H = 260, l = 46, r = 12, t = 12, b = 40;
      const svg = svgBox(host, W, H);
      const idx = metric === "score" ? 2 : 1;
      const [lo, hi, ticks, f] = metric === "score" ? [0.54, 0.73, [0.55, 0.6, 0.65, 0.7], (v) => v.toFixed(2)] : [0.1, 0.32, [0.1, 0.15, 0.2, 0.25, 0.3], (v) => Math.round(v * 100) + "%"];
      const x = lin(-0.4, 8.4, l, W - r);
      const y = lin(lo, hi, H - b, t);
      sv("rect", { x: x(3.55), y: t, width: x(4.45) - x(3.55), height: H - b - t, fill: "color-mix(in srgb, var(--compress) 12%, transparent)" }, svg);
      for (const v of ticks) {
        sv("line", { x1: l, x2: W - r, y1: y(v), y2: y(v), class: "grid" }, svg);
        sv("text", { x: l - 6, y: y(v) + 4, "text-anchor": "end", text: f(v) }, svg);
      }
      for (let k = 0; k <= 8; k++) sv("text", { x: x(k), y: H - b + 16, "text-anchor": "middle", class: k === 4 ? "t-strong" : "t-ink2", text: "v" + k }, svg);
      sv("text", { x: (l + W - r) / 2, y: H - 4, "text-anchor": "middle", text: "version" }, svg);
      for (const [key, label, color] of runs) {
        const pts = RES.swap[key];
        sv("polyline", { points: pts.map((p) => `${x(p[0])},${y(p[idx])}`).join(" "), fill: "none", stroke: color, "stroke-width": 2 }, svg);
        for (const p of pts) {
          sv("circle", { cx: x(p[0]), cy: y(p[idx]), r: 4.5, fill: color, stroke: "var(--surface)", "stroke-width": 2 }, svg);
          const hit = sv("circle", { cx: x(p[0]), cy: y(p[idx]), r: 10, class: "hit" }, svg);
          bindTip(hit, `${label}<br>v${p[0]}: <b>${metric === "score" ? p[2].toFixed(3) : (p[1] * 100).toFixed(1) + "%"}</b>`);
        }
      }
    });
    cap();
    $$("[data-metric]").forEach((b) => b.addEventListener("click", () => {
      metric = b.dataset.metric;
      $$("[data-metric]").forEach((o) => o.setAttribute("aria-pressed", String(o === b)));
      draw(); cap();
    }));
  }

  // Q3: length matching
  {
    const rows = RES.length_match.filter((r) => /v[235]$/.test(r.comparison)).sort((a, b) => a.comparison.localeCompare(b.comparison));
    const order = ["v4 compress vs v3", "v4 compress vs v5", "v4 compress vs v2"];
    rows.sort((a, b) => order.indexOf(a.comparison) - order.indexOf(b.comparison));
    legend("len-legend", [["Raw gap", "var(--muted)", "ring"], ["Length-matched gap", "var(--compress)"], ["Originals' difference", "var(--muted)"]]);
    chart("len-chart", (host, W) => {
      const l = W < 520 ? 92 : 150, r = 16, t = 22, rowH = 56, b = 34;
      const H = t + rows.length * rowH + b;
      const svg = svgBox(host, W, H);
      const x = lin(-36, 6, l, W - r);
      for (const v of [-30, -20, -10, 0]) {
        sv("line", { x1: x(v), x2: x(v), y1: t - 6, y2: H - b, class: v === 0 ? "axis" : "grid" }, svg);
        sv("text", { x: x(v), y: H - b + 16, "text-anchor": "middle", text: v === 0 ? "0" : fmtPlain(v, 0) }, svg);
      }
      sv("text", { x: (l + W - r) / 2, y: H - 2, "text-anchor": "middle", text: "difference in share flagged (percentage points)" }, svg);
      rows.forEach((rw, i) => {
        const y0 = t + i * rowH + 12;
        const name = rw.comparison.replace(" compress", "");
        sv("text", { x: 0, y: y0 + 4, class: "t-ink", text: W < 520 ? name : `${name} (${Math.round(rw.length_treated)} words)` }, svg);
        const mm = rw.flagged_matched_diff * 100, lo = rw.flagged_matched_ci_low * 100, hi = rw.flagged_matched_ci_high * 100;
        const o = rw.flagged_v0_diff * 100, olo = rw.flagged_v0_ci_low * 100, ohi = rw.flagged_v0_ci_high * 100;
        sv("line", { x1: x(lo), x2: x(hi), y1: y0, y2: y0, stroke: "var(--compress)", "stroke-width": 3, "stroke-linecap": "round" }, svg);
        sv("circle", { cx: x(rw.flagged_raw_diff * 100), cy: y0, r: 6, fill: "var(--surface)", stroke: "var(--muted)", "stroke-width": 2 }, svg);
        sv("circle", { cx: x(mm), cy: y0, r: 5, fill: "var(--compress)", stroke: "var(--surface)", "stroke-width": 1.5 }, svg);
        sv("line", { x1: x(olo), x2: x(ohi), y1: y0 + 18, y2: y0 + 18, stroke: "var(--muted)", "stroke-width": 3, "stroke-linecap": "round" }, svg);
        sv("circle", { cx: x(o), cy: y0 + 18, r: 4.5, fill: "var(--muted)", stroke: "var(--surface)", "stroke-width": 1.5 }, svg);
        sv("text", { x: x(mm), y: y0 - 9, "text-anchor": "middle", class: "t-strong mono", text: fmtPlain(mm) }, svg);
        const hit = sv("rect", { x: l, y: y0 - 16, width: W - r - l, height: 40, class: "hit" }, svg);
        bindTip(hit, `${name}<br>raw gap <b>${fmt(rw.flagged_raw_diff * 100)}</b><br>length-matched <b>${fmt(mm)}</b> [${fmtPlain(lo)}, ${fmtPlain(hi)}]<br>originals <b>${fmt(o)}</b> [${fmtPlain(olo)}, ${fmtPlain(ohi)}]`);
      });
    });
  }

  /* ---------------------------------------------------------------- ruling out length */
  {
    const LEN = S.length;
    const med = (k) => LEN.words.find((w) => w[0] === k)[1];
    $("#len-v3").textContent = med(3);
    $("#len-v4").textContent = med(4);
    chart("len-words", (host, W) => {
      const H = 260, l = 44, r = 12, t = 22, b = 40;
      const svg = svgBox(host, W, H);
      const x = lin(-0.5, 8.5, l, W - r);
      const y = lin(200, 650, H - b, t);
      for (const v of [200, 300, 400, 500, 600]) {
        sv("line", { x1: l, x2: W - r, y1: y(v), y2: y(v), class: "grid" }, svg);
        sv("text", { x: l - 6, y: y(v) + 4, "text-anchor": "end", text: v }, svg);
      }
      for (const [k, m, q1, q3] of LEN.words) {
        const dip = k === 4;
        sv("line", { x1: x(k), x2: x(k), y1: y(q1), y2: y(q3), stroke: dip ? "var(--dip)" : "var(--muted)", "stroke-width": 8, "stroke-linecap": "round", opacity: 0.28 }, svg);
        sv("circle", { cx: x(k), cy: y(m), r: 5.5, fill: dip ? "var(--dip)" : "var(--ink)", stroke: "var(--surface)", "stroke-width": 2 }, svg);
        sv("text", { x: x(k), y: y(q3) - 8, "text-anchor": "middle", class: dip ? "t-strong mono" : "t-ink2 mono", text: m }, svg);
        sv("text", { x: x(k), y: H - b + 16, "text-anchor": "middle", class: dip ? "t-strong" : "t-ink2", text: "v" + k }, svg);
        sv("text", { x: x(k), y: H - b + 30, "text-anchor": "middle", text: k === 0 ? "human" : W < 560 ? SCHEDULE[k].slice(0, 4) : SCHEDULE[k] }, svg);
        const hit = sv("rect", { x: x(k - 0.5), y: t, width: x(k + 0.5) - x(k - 0.5), height: H - b - t, class: "hit" }, svg);
        bindTip(hit, `v${k} · ${k ? SCHEDULE[k] : "human original"}<br>median <b>${m}</b> words<br>middle half ${q1}–${q3}`);
      }
    });

    const ramp = [0.3, 0.45, 0.6, 0.8, 1];
    const names = ["Shortest fifth", "2nd fifth", "Middle fifth", "4th fifth", "Longest fifth"];
    legend("bins-legend", names.map((n, i) => [n, `color-mix(in srgb, var(--ink) ${ramp[i] * 100}%, transparent)`, "line"]));
    const drops = LEN.bins.map((pts) => (pts[4][1] - pts[3][1]) * 100);
    $("#bins-cap").textContent = `From v3 to v4 the share flagged falls by ${drops.map((d) => Math.abs(d).toFixed(0)).join(", ")} points, shortest fifth to longest. ` +
      `Medians of the fifths for news, for example: ${LEN.bin_words.news.map((w) => Math.round(w)).join(", ")} words.`;
    chart("len-bins", (host, W) => {
      const H = 280, l = 44, r = 12, t = 14, b = 40;
      const svg = svgBox(host, W, H);
      const x = lin(-0.4, 8.4, l, W - r);
      const y = lin(0, 1, H - b, t);
      sv("rect", { x: x(3.55), y: t, width: x(4.45) - x(3.55), height: H - b - t, fill: "color-mix(in srgb, var(--compress) 12%, transparent)" }, svg);
      for (const v of [0, 0.25, 0.5, 0.75, 1]) {
        sv("line", { x1: l, x2: W - r, y1: y(v), y2: y(v), class: v === 0 ? "axis" : "grid" }, svg);
        sv("text", { x: l - 6, y: y(v) + 4, "text-anchor": "end", text: Math.round(v * 100) + "%" }, svg);
      }
      for (let k = 0; k <= 8; k++) {
        sv("text", { x: x(k), y: H - b + 16, "text-anchor": "middle", class: k === 4 ? "t-strong" : "t-ink2", text: "v" + k }, svg);
        sv("text", { x: x(k), y: H - b + 30, "text-anchor": "middle", text: k === 0 ? "human" : W < 560 ? SCHEDULE[k].slice(0, 4) : SCHEDULE[k] }, svg);
      }
      LEN.bins.forEach((pts, i) => {
        const color = `color-mix(in srgb, var(--ink) ${ramp[i] * 100}%, transparent)`;
        sv("polyline", { points: pts.map(([k, f]) => `${x(k)},${y(f)}`).join(" "), fill: "none", stroke: color, "stroke-width": 2 }, svg);
        for (const [k, f] of pts) sv("circle", { cx: x(k), cy: y(f), r: 3.5, fill: color, stroke: "var(--surface)", "stroke-width": 1.5 }, svg);
      });
      for (let k = 0; k <= 8; k++) {
        const hit = sv("rect", { x: x(k - 0.5), y: t, width: x(k + 0.5) - x(k - 0.5), height: H - b - t, class: "hit" }, svg);
        bindTip(hit, `v${k} · ${k ? SCHEDULE[k] : "human original"}` + LEN.bins.map((pts, i) => `<br>${names[i]}: <b>${(pts[k][1] * 100).toFixed(1)}%</b>`).join(""));
      }
    });

    const [nd, nlo, nhi] = LEN.newsroom_e5;
    $("#nr-e5").textContent = `${fmt(nd * 100)} pts [${fmtPlain(nlo * 100)}, ${fmtPlain(nhi * 100)}]`;

    let cov = 50;
    const methods = [["native", "Original lengths"], ["prefix_exact_length", "Prefix cut to equal length"], ["random_tokens", "Random tokens (20 repeats)"], ["contiguous", "Random window (20 repeats)"]];
    const comps = [["paraphrase", "Paraphrase minus compress", "var(--paraphrase)"], ["expand", "Expand minus compress", "var(--expand)"]];
    legend("trunc-legend", comps.map(([, l, c]) => [l, c]));
    const drawTrunc = chart("trunc-chart", (host, W) => {
      const l = W < 560 ? 132 : 200, r = 40, t = 10, rowH = 50, b = 34;
      const H = t + methods.length * rowH + b;
      const svg = svgBox(host, W, H);
      const x = lin(0, 45, l, W - r);
      for (const v of [0, 10, 20, 30, 40]) {
        sv("line", { x1: x(v), x2: x(v), y1: t, y2: H - b, class: v === 0 ? "axis" : "grid" }, svg);
        sv("text", { x: x(v), y: H - b + 16, "text-anchor": "middle", text: v ? "+" + v : "0" }, svg);
      }
      sv("text", { x: (l + W - r) / 2, y: H - 2, "text-anchor": "middle", text: "accuracy advantage over compression (percentage points)" }, svg);
      methods.forEach(([m, label], i) => {
        const y0 = t + i * rowH + rowH / 2;
        if (i) sv("line", { x1: 0, x2: W - r, y1: y0 - rowH / 2, y2: y0 - rowH / 2, class: "grid" }, svg);
        sv("text", { x: 0, y: y0 + 4, class: "t-ink", text: W < 560 ? label.replace(" to equal length", "").replace(" (20 repeats)", "") : label }, svg);
        comps.forEach(([c, cl, color], ci) => {
          const row = LEN.truncation.find((d) => d[0] === cov && d[1] === c && d[2] === m);
          const yy = y0 + (ci ? 8 : -8);
          const [v, lo, hi] = row.slice(3).map((z) => z * 100);
          sv("line", { x1: x(lo), x2: x(hi), y1: yy, y2: yy, stroke: color, "stroke-width": 3, "stroke-linecap": "round", opacity: 0.55 }, svg);
          sv("circle", { cx: x(v), cy: yy, r: 5, fill: color, stroke: "var(--surface)", "stroke-width": 1.5 }, svg);
          sv("text", { x: x(hi) + 6, y: yy + 4, class: "mono", text: fmt(v) }, svg);
          const hit = sv("rect", { x: l, y: yy - 8, width: W - r - l, height: 16, class: "hit" }, svg);
          bindTip(hit, `${label}, ${cov}% coverage<br>${cl}: <b>${fmt(v)} pts</b><br>${m === "native" || m.startsWith("prefix") ? "95% CI" : "range"} ${fmtPlain(lo)} to ${fmtPlain(hi)}`);
        });
      });
    });
    $$("[data-cov]").forEach((b) => b.addEventListener("click", () => {
      cov = Number(b.dataset.cov);
      $$("[data-cov]").forEach((o) => o.setAttribute("aria-pressed", String(o === b)));
      drawTrunc();
    }));

    const N = LEN.negative;
    $("#neg-tokens").textContent = Math.round(N.tokens) + " tokens";
    $("#neg-repeats").textContent = N.repeats;
    $("#neg-full").textContent = (N.full * 100).toFixed(1) + "%";
    $("#neg-short").textContent = (N.short * 100).toFixed(1) + "%";
    $("#neg-range").textContent = `${(N.min * 100).toFixed(1)}–${(N.max * 100).toFixed(1)}%`;
  }

  // Q4: word contributions
  chart("contrib-chart", (host, W) => {
    const rows = RES.contrib.slice().sort((a, b) => b[2] - a[2]);
    const l = 112, r = 44, rowH = 22, t = 6, b = 30;
    const H = t + rows.length * rowH + b;
    const svg = svgBox(host, W, H);
    const x = lin(-0.6, 1.0, l, W - r);
    for (const v of [-0.5, 0, 0.5, 1.0]) {
      sv("line", { x1: x(v), x2: x(v), y1: t, y2: H - b, class: v === 0 ? "axis" : "grid" }, svg);
      sv("text", { x: x(v), y: H - b + 16, "text-anchor": "middle", text: fmtPlain(v, 1) }, svg);
    }
    rows.forEach(([w, side, v], i) => {
      const y = t + i * rowH;
      const ai = side.startsWith("AI");
      sv("text", { x: l - 8, y: y + rowH / 2 + 4, "text-anchor": "end", class: "t-ink", text: w }, svg);
      sv("rect", { x: Math.min(x(0), x(v)), y: y + 4, width: Math.abs(x(v) - x(0)), height: rowH - 8, rx: 3, fill: ai ? "var(--ai)" : "var(--human)" }, svg);
      sv("text", { x: v >= 0 ? x(v) + 5 : x(v) - 5, y: y + rowH / 2 + 4, "text-anchor": v >= 0 ? "start" : "end", class: "mono", text: fmt(v, 2) }, svg);
      const hit = sv("rect", { x: 0, y, width: W, height: rowH, class: "hit" }, svg);
      bindTip(hit, `<b>${w}</b> (${side})<br>mean contribution ${fmt(v, 3)} per document`);
    });
  });

  /* ---------------------------------------------------------------- tabs
     One page per tab, chosen by the URL hash (#intro, #game, #method, #edits). A hash that names an element
     inside a tab (e.g. #results) opens that tab and scrolls to it. Charts are redrawn when their tab opens,
     since a hidden chart has no width to measure. */
  const TABS = $$(".tab-panel").map((p) => p.dataset.panel);
  function route(scroll) {
    const hash = decodeURIComponent(location.hash.slice(1));
    const target = hash && !TABS.includes(hash) ? document.getElementById(hash) : null;
    const panel = target ? target.closest(".tab-panel") : null;
    const tab = TABS.includes(hash) ? hash : panel ? panel.dataset.panel : "intro";
    $$(".tab-panel").forEach((p) => { p.hidden = p.dataset.panel !== tab; });
    const group = $(`.tab-panel[data-panel="${tab}"]`).dataset.group || tab;
    $$(".tabs a").forEach((a) => (a.dataset.tab === group ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current")));
    $("#subtabs").hidden = group !== "results";
    $$("#subtabs a").forEach((a) => (a.dataset.sub === tab ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current")));
    tip.hidden = true;
    charts.forEach((c) => c());
    if (target) target.scrollIntoView();
    else if (scroll) window.scrollTo(0, 0);
  }
  window.addEventListener("hashchange", () => route(true));
  route(false);
})();
