/* plots.js: two inline-SVG charts drawn from a JSON block, on top of the RBCharts helpers (charts.js).
 *
 *   <div class="chart" data-chart="dumbbell" aria-label="what the chart shows">
 *     <script type="application/json">{ ...spec... }</script>
 *   </div>
 *
 * data-chart="dumbbell"   before -> after, one row per item. Before is a hollow blue ring, after a filled green
 *                         dot, joined by a dashed connector; a pill at the row end carries the change.
 *   { "domain": [0, 100], "unit": "%", "axis": "Accuracy (%)", "from": "Baseline", "to": "Ours",
 *     "gainUnit": "pp", "decimals": 1, "rows": [ { "label": "Model A", "from": 40, "to": 55, "note": "optional" } ] }
 *   "gains": false leaves the change out everywhere (pill, tooltip, table): the chart then prints only the
 *   numbers that the JSON holds.
 *
 * data-chart="bars"       one horizontal bar per row. "kind" sets the mark: "base" (blue outline, the baseline),
 *                         "ours" (solid green), "neutral" (grey), "flag" (red), "gold". "kinds" names them in a legend.
 *   { "domain": [0, 50], "unit": "%", "axis": "Share (%)", "kinds": { "base": "Baseline", "ours": "Ours" },
 *     "rows": [ { "label": "Faulty reasoning", "value": 39, "kind": "flag" } ] }
 *
 * Optional in both: "decimals" (default: as many as the data needs, at most 1), "legend": false, "table": false.
 * Every chart also gets a collapsed data table, redraws when its width changes, and follows the theme because
 * all colours come from CSS classes (base.css, talk.css). */
(function () {
  'use strict';
  var C = window.RBCharts;
  if (!C) return;
  var svg = C.svg, h = C.h;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var MINUS = '−';

  function readSpec(el) {
    var s = el.querySelector('script[type="application/json"]');
    if (!s) return null;
    try { return JSON.parse(s.textContent); } catch (e) { console.error('plots.js: invalid chart JSON', e, el); return null; }
  }
  function decimalsOf(spec, values) {
    if (typeof spec.decimals === 'number') return spec.decimals;
    return values.some(function (v) { return Math.abs(v - Math.round(v)) > 1e-9; }) ? 1 : 0;
  }
  function fmt(v, d, unit) { return (v < 0 ? MINUS : '') + Math.abs(v).toFixed(d) + (unit || ''); }
  function signed(v, d, unit) { return (v > 0 ? '+' : v < 0 ? MINUS : '') + Math.abs(v).toFixed(d) + (unit ? ' ' + unit : ''); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  /* widest text of a list, measured in the chart's own font */
  function measure(root, cls, strings) {
    var t = svg('text', { class: cls, x: -9999, y: -9999 }, root), w = 0;
    strings.forEach(function (s) { t.textContent = s; w = Math.max(w, t.getComputedTextLength()); });
    root.removeChild(t);
    return Math.ceil(w);
  }
  function domainOf(spec, values) {
    if (spec.domain && spec.domain.length === 2) return [Number(spec.domain[0]), Number(spec.domain[1])];
    var lo = Math.min.apply(null, values.concat(0)), hi = Math.max.apply(null, values);
    return [lo, hi + (hi - lo) * 0.12];
  }
  function axis(root, x, y0, y1, title, cx) {
    var grid = svg('g', { class: 'grid', 'aria-hidden': 'true' }, root), ticks = svg('g', { class: 'tick', 'aria-hidden': 'true' }, root);
    x.ticks(5).forEach(function (t) {
      svg('line', { x1: x(t), x2: x(t), y1: y0, y2: y1 }, grid);
      svg('text', { x: x(t), y: y1 + 18, 'text-anchor': 'middle', text: String(t) }, ticks);
    });
    svg('line', { class: 'axis-line', x1: x.range[0], x2: x.range[1], y1: y1, y2: y1 }, root);
    if (title) svg('text', { class: 'axis-title', x: cx, y: y1 + 40, 'text-anchor': 'middle', text: title, 'aria-hidden': 'true' }, root);
  }
  /* one focusable hit area per row, with the shared tooltip */
  function hit(root, x, y, w, hgt, label, tipHtml) {
    var r = svg('rect', { class: 'row-hit', x: x, y: y, width: w, height: hgt, tabindex: 0, role: 'img', 'aria-label': label }, root);
    svg('rect', { class: 'row-bg', x: x, y: y + 3, width: w, height: hgt - 6, rx: 10 }, root);
    C.bindTip(r, tipHtml);
    return r;
  }

  /* ---------------------------------------------------------------- dumbbell */
  function dumbbell(el, spec, stage) {
    var rows = spec.rows || [], W = stage.clientWidth, narrow = W < 560;
    var vals = []; rows.forEach(function (r) { vals.push(r.from, r.to); });
    var d = decimalsOf(spec, vals), unit = spec.unit || '', gu = spec.gainUnit === undefined ? unit : spec.gainUnit;
    var showGain = spec.gains !== false;
    var dom = domainOf(spec, vals);
    var pitch = narrow ? (showGain ? 68 : 62) : 60, top = 6, H = top + rows.length * pitch + 48;
    var root = svg('svg', { viewBox: '0 0 ' + W + ' ' + H, width: W, height: H, role: 'group', 'aria-label': el.getAttribute('aria-label') || spec.axis || 'Chart' });
    stage.appendChild(root);
    var labelW = measure(root, 'lbl', rows.map(function (r) { return r.label; }));
    var gains = rows.map(function (r) { return signed(r.to - r.from, d, gu); });
    var pillW = showGain ? measure(root, 'gain', gains) + 22 : 0;
    var valW = measure(root, 'val', vals.map(function (v) { return fmt(v, d); }));
    var left = narrow ? 40 : Math.min(labelW + 28, Math.round(W * 0.34)), right = showGain ? (narrow ? 44 : pillW + 62) : valW + 26;
    var x = C.linear(dom[0], dom[1], left, W - right);
    axis(root, x, top, top + rows.length * pitch, spec.axis, (left + W - right) / 2);
    rows.forEach(function (r, i) {
      var y0 = top + i * pitch, cy = y0 + (narrow ? pitch - 22 : pitch / 2), xa = x(r.from), xb = x(r.to), up = r.to >= r.from;
      var tip = '<div class="tt">' + esc(r.label) + '</div>' +
        '<div class="row"><span><i class="sw raw"></i>' + esc(spec.from || 'Before') + '</span><b>' + fmt(r.from, d, unit) + '</b></div>' +
        '<div class="row"><span><i class="sw rra"></i>' + esc(spec.to || 'After') + '</span><b>' + fmt(r.to, d, unit) + '</b></div>' +
        (showGain ? '<div class="sub">' + gains[i] + (r.note ? ' · ' + esc(r.note) : '') + '</div>' : r.note ? '<div class="sub">' + esc(r.note) + '</div>' : '');
      hit(root, 0, y0, W, pitch, r.label + ': ' + fmt(r.from, d, unit) + ' to ' + fmt(r.to, d, unit) + (showGain ? ', ' + gains[i] : ''), tip);
      var g = svg('g', { 'aria-hidden': 'true', style: '--i:' + i, 'pointer-events': 'none' }, root);
      svg('text', { class: 'lbl', x: narrow ? 2 : 0, y: narrow ? y0 + 20 : cy + 5, text: r.label }, g);
      if (Math.abs(xb - xa) > 15) svg('line', { class: 'conn', x1: xa + (up ? 8 : -8), x2: xb + (up ? -9 : 9), y1: cy, y2: cy, style: '--i:' + i }, g);
      svg('circle', { class: 'mk-raw', cx: xa, cy: cy, r: 6.5 }, g);
      svg('text', { class: 'val raw', x: xa + (up ? -13 : 13), y: cy + 4.5, 'text-anchor': up ? 'end' : 'start', text: fmt(r.from, d) }, g);
      var to = svg('g', { class: 'dumb-to', style: '--i:' + i + ';--dx:' + (xa - xb).toFixed(1) + 'px' }, g);
      svg('circle', { class: 'mk-rra', cx: xb, cy: cy, r: 7 }, to);
      svg('text', { class: 'val rra', x: xb + (up ? 13 : -13), y: cy + 4.5, 'text-anchor': up ? 'start' : 'end', text: fmt(r.to, d) }, to);
      if (!showGain) return;
      var pg = svg('g', { class: 'gain-g', style: '--i:' + i }, g), neg = r.to < r.from ? ' neg' : '';
      var px = W - pillW, py = narrow ? y0 + 6 : cy - 12;
      svg('rect', { class: 'gain-bg' + neg, x: px, y: py, width: pillW, height: 24, rx: 12 }, pg);
      svg('text', { class: 'gain' + neg, x: px + pillW / 2, y: py + 16.3, 'text-anchor': 'middle', text: gains[i] }, pg);
    });
  }

  /* ---------------------------------------------------------------- bars */
  function bars(el, spec, stage) {
    var rows = spec.rows || [], W = stage.clientWidth, narrow = W < 560;
    var vals = rows.map(function (r) { return r.value; });
    var d = decimalsOf(spec, vals), unit = spec.unit || '';
    var dom = domainOf(spec, vals);
    var pitch = narrow ? 54 : 38, bh = 16, top = 6, H = top + rows.length * pitch + 48;
    var root = svg('svg', { viewBox: '0 0 ' + W + ' ' + H, width: W, height: H, role: 'group', 'aria-label': el.getAttribute('aria-label') || spec.axis || 'Chart' });
    stage.appendChild(root);
    var labelW = measure(root, 'lbl', rows.map(function (r) { return r.label; }));
    var valW = measure(root, 'val', vals.map(function (v) { return fmt(v, d, unit); }));
    var left = narrow ? 2 : Math.min(labelW + 28, Math.round(W * 0.36)), right = valW + 22;
    var x = C.linear(dom[0], dom[1], left, W - right);
    axis(root, x, top, top + rows.length * pitch, spec.axis, (left + W - right) / 2);
    rows.forEach(function (r, i) {
      var kind = r.kind || 'ours', y0 = top + i * pitch, cy = y0 + (narrow ? pitch - 17 : pitch / 2);
      var x0 = x(Math.max(dom[0], 0)), x1 = x(r.value), w = Math.max(0, x1 - x0), rad = Math.min(4, w / 2), ty = cy - bh / 2;
      var tip = '<div class="tt">' + esc(r.label) + '</div><div class="row"><span>' + esc(spec.axis || 'Value') + '</span><b>' + fmt(r.value, d, unit) + '</b></div>' +
        (r.note ? '<div class="sub">' + esc(r.note) + '</div>' : '');
      hit(root, 0, y0, W, pitch, r.label + ': ' + fmt(r.value, d, unit), tip);
      var g = svg('g', { 'aria-hidden': 'true', 'pointer-events': 'none' }, root);
      svg('text', { class: 'lbl', x: narrow ? 2 : 0, y: narrow ? y0 + 18 : cy + 5, text: r.label }, g);
      /* square at the axis, rounded at the far end */
      svg('path', { class: 'bar ' + kind, style: '--i:' + i,
        d: 'M' + x0 + ' ' + ty + 'H' + (x1 - rad) + 'Q' + x1 + ' ' + ty + ' ' + x1 + ' ' + (ty + rad) + 'V' + (ty + bh - rad) + 'Q' + x1 + ' ' + (ty + bh) + ' ' + (x1 - rad) + ' ' + (ty + bh) + 'H' + x0 + 'Z' }, g);
      svg('text', { class: 'val bar-val ' + (kind === 'base' ? 'raw' : kind === 'ours' ? 'rra' : kind), style: '--i:' + i, x: x1 + 9, y: cy + 4.5, text: fmt(r.value, d, unit) }, g);
    });
  }

  /* ---------------------------------------------------------------- legend + data table */
  function legend(el, spec, type) {
    if (spec.legend === false) return null;
    var items = [];
    if (type === 'dumbbell') items = [['raw', spec.from || 'Before'], ['rra', spec.to || 'After']];
    else if (spec.kinds) items = Object.keys(spec.kinds).map(function (k) { return [k === 'base' ? 'raw' : k === 'ours' ? 'rra' : k, spec.kinds[k]]; });
    if (!items.length) return null;
    return h('div', { class: 'legend chart-legend' }, items.map(function (it) { return h('span', {}, [h('i', { class: 'sw ' + it[0], 'aria-hidden': 'true' }), it[1]]); }));
  }
  function table(spec, type) {
    if (spec.table === false) return null;
    var rows = spec.rows || [], unit = spec.unit || '', vals = [];
    rows.forEach(function (r) { if (type === 'dumbbell') vals.push(r.from, r.to); else vals.push(r.value); });
    var d = decimalsOf(spec, vals), gu = spec.gainUnit === undefined ? unit : spec.gainUnit, showGain = spec.gains !== false;
    var head = type === 'dumbbell' ? ['', spec.from || 'Before', spec.to || 'After'].concat(showGain ? ['Change'] : []) : ['', spec.axis || 'Value'];
    var thead = h('thead', {}, [h('tr', {}, head.map(function (t, i) { return h('th', { scope: 'col', class: i ? 'n' + (i === 2 ? ' rra-col' : '') : '' }, [t]); }))]);
    var tbody = h('tbody', {}, rows.map(function (r) {
      var cells = type === 'dumbbell'
        ? [h('td', { class: 'n' }, [fmt(r.from, d, unit)]), h('td', { class: 'n rra-col' }, [fmt(r.to, d, unit)])].concat(showGain ? [h('td', { class: 'n' }, [signed(r.to - r.from, d, gu)])] : [])
        : [h('td', { class: 'n' }, [fmt(r.value, d, unit)])];
      return h('tr', {}, [h('th', { scope: 'row' }, [r.label])].concat(cells));
    }));
    return h('details', { class: 'chart-table' }, [h('summary', {}, ['Data table']), h('div', { class: 'tbl-scroll' }, [h('table', { class: 'tbl' }, [thead, tbody])])]);
  }

  /* ---------------------------------------------------------------- mount */
  function mount(el) {
    var spec = readSpec(el), type = el.getAttribute('data-chart') || (spec && spec.type);
    if (!spec || (type !== 'dumbbell' && type !== 'bars')) return;
    var lg = legend(el, spec, type), stage = h('div', { class: 'chart-stage' }), tb = table(spec, type);
    if (lg) el.appendChild(lg);
    el.appendChild(stage);
    if (tb) el.appendChild(tb);
    function draw() {
      stage.innerHTML = '';
      if (stage.clientWidth < 40) return;
      (type === 'dumbbell' ? dumbbell : bars)(el, spec, stage);
    }
    draw();
    C.onResize(stage, draw);
    el._redraw = draw;
    if (reduce || !('IntersectionObserver' in window)) { el.classList.add('in'); return; }
    var io = new IntersectionObserver(function (es) {
      if (es.some(function (e) { return e.isIntersecting; })) { io.disconnect(); el.classList.add('in'); }
    }, { threshold: 0.25 });
    io.observe(el);
  }
  var charts = [].slice.call(document.querySelectorAll('.chart[data-chart]'));
  charts.forEach(mount);
  /* label widths depend on the web fonts: draw again once they have loaded */
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { charts.forEach(function (el) { if (el._redraw) el._redraw(); }); });
  C.plots = { mount: mount };
})();
