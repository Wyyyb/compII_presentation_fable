# Towards Grounded, Reproducible, and Auditable Autonomous Research

Companion page for Yubo Wang's PhD Comprehensive II talk (research proposal), David R. Cheriton School of Computer
Science, University of Waterloo, 26 November 2026.

The page follows the talk. It asks one question, "What would it take to trust research done by AI?", and splits
it into five smaller ones, one chapter each:

| Chapter | Question | Work |
| --- | --- | --- |
| 01 Measure | Can we measure what the model can really do? | MMLU-Pro (NeurIPS 2024 Datasets and Benchmarks, Spotlight) |
| 02 Improve | Can we make it reason better? | Critique Fine-Tuning (COLM 2025) and One-Shot CFT (EMNLP 2025) |
| 03 Ground | Is what it writes tied to real sources? | ScholarCopilot (COLM 2025) |
| 04 Reproduce | Do its experiments re-run? | ReproBridge (arXiv preprint, 2026) |
| 05 Audit | Do its claims follow from its evidence? | Proposed research, in progress |

Between two chapters a **bridge** says what we have, what is still open, and the next question. The page ends
with the plan and the list of papers.

The audit chapter is proposed work. It is written in the future tense, it reports no result, and its picture is
a schematic drawing (see "Replacing the audit schematic").

The page is one static file in the style of the ReproBridge project page: white ground, ink text, one green
accent, mono-caps labels, hairline cards, big numerals. There is no framework, no bundler and nothing to
install. The only external request is Google Fonts (Google Sans Flex, Google Sans Code).

## Build

```bash
python3 build.py                  # src/ -> index.html
python3 -m http.server 8000       # then open http://localhost:8000/
python3 build.py --only hero,measure --out .preview-x.html   # preview a few sections (the file is git-ignored)
python3 build.py --strict         # also fails while a block is still marked data-draft
python3 tools/qa.py               # Playwright check and screenshots into _qa/ (see "Checking")
```

`build.py` uses the Python standard library only. It joins `src/head.html`, every `src/partials/NN-<id>.html` in
file-name order and `src/tail.html` into `index.html`. It links `assets/css/base.css`, `kit.css` and `talk.css`,
then `assets/css/<id>.css` for each partial that has one, and the scripts in the same way. Each asset URL gets a
content hash. HTML comments in partials are author notes and are left out of `index.html`.

`index.html` is generated. Do not edit it by hand; commit it together with the sources.

## Publishing

- GitHub Pages can serve the folder as it is (a `.nojekyll` file is present).
- Every URL is relative, so the page works from a project sub-path without a base setting. `build.py` stops if it
  finds a root-relative URL, an absolute file path, or an external resource other than Google Fonts. Links to
  papers are allowed in `<a href>` only.
- The page is a talk companion and asks not to be indexed: `src/head.html` sets
  `<meta name="robots" content="noindex">` and `robots.txt` disallows everything. Crawlers read `robots.txt` only
  at the root of a host, so on a project sub-path the meta tag is the one that counts.
- `_qa/` holds check screenshots. It is git-ignored and is not part of the site.
- No analytics, no counters, no API calls.

## Files

| Path | What it is |
| --- | --- |
| `build.py` | The build script. |
| `index.html` | The page (generated). |
| `src/head.html`, `src/tail.html` | `<head>` (title, description, `noindex`, favicon, fonts, theme bootstrap) and the page tail (tooltip node, figure lightbox, script slot). |
| `src/partials/` | One file per section, see the table below. |
| `assets/css/base.css` | The design system of the ReproBridge page: light and dark tokens, layout, type roles, nav and side rail, buttons, tags, cards, stats, figures and lightbox, tables, chart chrome, reveal on scroll. |
| `assets/css/kit.css` | Component recipes from the ReproBridge page under neutral `.k-*` names (icon cards, step lists, window frame, pipeline, quote, ...). |
| `assets/css/talk.css` | What this page adds and more than one section uses: the chapter template, the question card, the five-node rail, the bridge band, chart marks. |
| `assets/css/<id>.css` | Section styles, each scoped under `#<id>`. |
| `assets/js/site.js` | Theme toggle (stored under `c2-theme`), scroll-spy for the top bar and the side rail, reveal on scroll, lightbox. |
| `assets/js/charts.js`, `assets/js/plots.js` | SVG helpers (scales, tooltip, resize hooks) and the two chart types drawn from a JSON block. |
| `assets/img/fig/` | Figures from the published papers (WebP). A `-stacked` file is the phone version of a wide figure. |
| `assets/img/audit/` | The schematic drawing of the audit chapter. |
| `tools/qa.py` | The Playwright check (see "Checking"). |
| `tools/make_audit_schematic.py` | Draws the audit schematic with Pillow. |
| `robots.txt`, `.nojekyll`, `.gitignore` | Publishing files. |

### Sections

| Partial | Anchor | Content |
| --- | --- | --- |
| `00-nav.html` | | Top bar (mark, six links, theme toggle) and the side rail shown on wide screens. Both highlight the section in view. |
| `01-hero.html` | `#top` | Title, author, lede, and a drawing of the five questions on one thread. |
| `02-thread.html` | `#thread` | The question of the talk, the three conditions, the thesis direction, and the roadmap of five question cards. |
| `03-measure.html` | `#measure` | Chapter 01, MMLU-Pro. |
| `03b-bridge-1.html` | `#bridge-1` | Bridge: Measure to Improve. |
| `04-improve.html` | `#improve` | Chapter 02, Critique Fine-Tuning and One-Shot CFT. |
| `04b-bridge-2.html` | `#bridge-2` | Bridge: Improve to Ground. It has one more row ("So"). |
| `05-ground.html` | `#ground` | Chapter 03, ScholarCopilot. |
| `05b-bridge-3.html` | `#bridge-3` | Bridge: Ground to Reproduce. |
| `06-reproduce.html` | `#reproduce` | Chapter 04, ReproBridge. |
| `06b-bridge-4.html` | `#bridge-4` | Bridge: Reproduce to Audit. The Audit node is drawn in progress. |
| `07-audit.html` | `#audit` | Chapter 05, proposed research: the loop of four stages, the schematic, two research questions, two planned studies. |
| `08-plan.html` | `#plan` | Timeline, risks, three expected contributions, the closing line. |
| `09-publications.html` | `#publications` | The five papers. |
| `99-footer.html` | | One-line footer. |

A partial is named `NN-<id>.html`. One lowercase letter may follow the number (`03b-...`), so a bridge can sit
between two chapters. To add a section: create the partial with `<section class="sec" id="<id>">`, add its link
to the top bar and the side rail in `00-nav.html`, put section-only styles in `assets/css/<id>.css` (scoped under
`#<id>`), and rebuild.

## Editing

Open the partial, change the text, run `python3 build.py`. Each partial starts with a comment that names its
blocks and the wording rules that apply to it. Rules that hold everywhere:

- A headline is a claim in sentence case, ten words at most, with no final period. A lede is short, 45 words at
  most, with the key terms and numbers in `<b>`. No paragraph runs over 60 words.
- Every number names its basis in a dashed `.tag-note` or in the `.caveat` line below it.
- Author lists are shown as printed. ReproBridge's venue label is "arXiv preprint, 2026".
- ReproBridge's component is always "the execution Auditor". The proposed one in the audit chapter is "the
  auditor". Its three judgments are "supported", "contradicted" and "insufficient evidence".
- The audit chapter states plans, not results: future tense, and no audit performance number.
- Do not write that Critique Fine-Tuning produced a critic. The critiques came from a stronger teacher, and the
  gain is measured in solving.
- Add `data-reveal` to a block that should fade up when it scrolls into view.
- While a block holds content that is not final, mark it with `data-draft="..."`. `build.py` counts these markers,
  `build.py --strict` fails while one is left, and `index.html?drafts=1` outlines them. The published page has none.

### Chapter template (`03-measure.html` is the reference)

```html
<section class="sec chapter" id="measure" aria-labelledby="measure-title">
  <div class="wrap">
    <div class="sec-head" data-reveal>
      <p class="ch-label"><span class="sec-no">01 · Measure</span><span class="ch-q">The chapter's question</span></p>
      <h2 id="measure-title">The claim, in ten words at most</h2>
      <p class="lede">Two or three sentences with <b>key terms</b> and <b>numbers</b> in bold.</p>
    </div>
    <div class="papers"> <article class="paper">…</article> </div>        <!-- class="papers two" for two cards -->
    <h3 class="sub">The gap: …</h3> <p class="sub-lede">…</p>
    <h3 class="sub">The idea: …</h3> <p class="sub-lede">…</p>
    <figure class="fig"> <div class="fig-frame pad"><img … data-zoom="…" data-title="…"><button class="zoom-btn" …>Zoom</button></div> <figcaption><b>Title.</b> …</figcaption> </figure>
    <div class="chart-card"> … <div class="chart" data-chart="bars">…JSON…</div> </div>
    <div class="stats k-stats"> <div class="stat">…</div> … </div> <p class="caveat">…</p>
    <div class="takeaway"><span class="takeaway-k">Take-away</span><p>One sentence.</p></div>
    <h3 class="sub">Still open: …</h3> <p class="sub-lede">…</p>          <!-- leads into the bridge -->
  </div>
</section>
```

- **Paper card** `.paper`: `.paper-top` (icon, mono kicker, `.paper-tags` with the venue), `h3` title,
  `.paper-authors`, optional `.paper-note`, `.paper-links` with `<a class="btn btn-sm ext">`. Venue tags:
  `tag rra` (green) for a published venue, plain `tag` for a preprint, `tag gold wip` for work in progress.
- **Figure**: the image and the Zoom button both carry `data-zoom` (the file the lightbox opens) and `data-title`.
  Give `width` and `height` in pixels and a real `alt`. A wide figure can have a second cut for phones:
  `<picture><source media="(max-width: 640px)" srcset="…-stacked.webp" width="…" height="…"><img …></picture>`.
- **Question card** `figure.fig.qcard`: one exam question with its options as text (`ol.qcard-opts`); `li.is-model`
  marks the answer a model gave, `li.is-key` the answer key.
- **Stats row**: one `.stat` per number. `.n` is the numeral; `<span class="from">76.4% →</span>` before it is the
  baseline in small blue; `<small>` is a unit; `.l` says what is measured; the dashed `.tag-note` names the data
  basis. Use two or three cells and put the limits in the `.caveat` line below.
- **Take-away**: one sentence, key words in `<b>`. For planned work use `class="takeaway is-wip"` and the label
  "Proposed": the block turns gold and dashed.

### Charts

A chart is a `<div class="chart" data-chart="…" aria-label="…">` with one JSON block inside. Edit the JSON only.
`plots.js` draws the SVG, a legend, a tooltip per row and a collapsed data table, and redraws on resize.

```html
<div class="chart" data-chart="dumbbell" aria-label="What the chart shows, in one sentence.">
  <script type="application/json">
  { "domain": [0, 100], "unit": "%", "axis": "Accuracy (%)",
    "from": "Baseline", "to": "Ours", "gainUnit": "pp",
    "rows": [ { "label": "Model A", "from": 40, "to": 55 } ] }
  </script>
</div>
```

| Field | Charts | Meaning |
| --- | --- | --- |
| `data-chart` | | `dumbbell` (before and after per row) or `bars` (one bar per row). |
| `domain` | both | `[min, max]` of the value axis. Bars should start at 0. |
| `unit`, `axis` | both | Unit appended to values in tooltips and the table; axis title. |
| `decimals` | both | Decimals to print (default: 1 if any value has a fraction, else 0). |
| `rows[].label`, `rows[].note` | both | Row label; optional note shown in the tooltip. |
| `from`, `to` | dumbbell | Legend names of the two marks. |
| `rows[].from`, `rows[].to` | dumbbell | Before (hollow blue ring) and after (filled green dot). |
| `gainUnit`, `gains` | dumbbell | Unit of the change pill at the row end (`pp`, `%`, ...). A decrease turns the pill red. `"gains": false` leaves the change out of the chart, the tooltip and the table, so only the numbers in the JSON are printed. |
| `rows[].value`, `rows[].kind` | bars | Bar length; `kind` is `base` (blue outline, the baseline), `ours` (solid green), `neutral` (grey), `flag` (red) or `gold`. |
| `kinds` | bars | Optional legend, for example `{ "base": "Baseline", "ours": "Ours" }`. |
| `legend`, `table` | both | Set to `false` to omit the legend or the data table. |

Baseline and ours are never told apart by colour alone: the baseline is hollow or outlined, ours is filled.
Keep the `<noscript>` line inside the chart: it gives the same numbers as text when JavaScript is off.

### Bridges (`03b-bridge-1.html` is the reference)

A bridge is the web form of a transition slide of the talk: a full-width soft band with the question of the
talk as its label, the five-node rail, and three rows. Edit only the `<dd>` lines. Keep them short and without
a final period.

```html
<aside class="bridge" id="bridge-1" aria-labelledby="bridge-1-q">
  <div class="wrap">
    <div class="br-head"> <p class="br-eyebrow">…What would it take to trust research done by AI?</p> <p class="br-route"><b>Measure</b> → <b>Improve</b></p> </div>
    <ol class="rail5">
      <li class="is-done is-from"><i></i><span><b>01</b> Measure</span></li>   <!-- covered; is-from draws the gold arch -->
      <li class="is-next"><i></i><span><b>02</b> Improve</span></li>           <!-- the next question -->
      <li><i></i><span><b>03</b> Ground</span></li>                            <!-- still ahead -->
      …
    </ol>
    <dl class="br-lines">
      <div class="br-line is-have"><dt>We have</dt><dd>…</dd></div>
      <div class="br-line is-open"><dt>Still open</dt><dd>…</dd></div>
      <div class="br-line is-next"><dt>Next question</dt><dd id="bridge-1-q">The question, key words in <em>…</em></dd></div>
    </dl>
    <a class="cue br-cue" href="#improve">…</a>
  </div>
</aside>
```

The next question is the question of the chapter that follows, word for word. Bridge 2 has a fourth row,
`<div class="br-line is-so">`, styled in `assets/css/bridge-2.css`. On bridge 4 the next node carries
`class="is-next is-wip"` (a gold dashed ring, `assets/css/bridge-4.css`), because the audit is not finished.

### Other components

| Component | Where | Markup in short |
| --- | --- | --- |
| Roadmap | `02-thread.html` | `.road` > two `.road-grp` (bracket label + `ol.road-stops`) > `li.road-stop` (`is-done`, `is-wip`, `to-wip`) > `a.road-card` (verb, question, work, chips). |
| Gap cases | `05-ground.html` | `.gap-cases` > two `article.gap-case` (label, `h4`, `.code` block with the wrong span in `<mark class="err">`, `.gap-fix` note). |
| Loop of four stages | `07-audit.html` | `figure.loop-fig` > `.loop` > four `.loop-box` (`data-s="1"` to `"4"`) with arrows between them. |
| Audit view | `07-audit.html` | `.audit-view` > `ol.steps3` (three numbered headers sized to the three panes) + `figure.audit-shot` (window frame, image, `SCHEMATIC` caption). |
| Research-question card | `07-audit.html` | `article.rq` > `.rq-top` (`.rq-no` pill + kicker), `h4`, `p`, `.rq-foot`. |
| Study card | `07-audit.html` | `article.study` (dashed: planned) > `.study-top`, `h4`, `p`, `ul.study-well`, `.hyp` (hypothesis), `dl.facts3` (planning targets with a `TARGET` tag), `p.study-fine`, `.rq-foot`. Keep these eight children in this order: the two cards share their rows. |
| Hand-over strip | `07-audit.html` | `.synth` > four `a.synth-cell` (index + work, role tag, what it hands over, arrow to the research question). |
| Timeline | `08-plan.html` | `ol.tl` > `li.tl-stop` (`is-now` carries the TODAY tag, `is-end` is the last stop) > `.tl-when`, `.tl-node`, `.tl-what`. |
| Contribution cards | `08-plan.html` | `.grid3` > `article.k-icard.contrib` (icon tile, kicker, `h4`, `p`). |
| Publication list | `09-publications.html` | `ol.pubs` > `li.pub` > `.pub-venue`, `.pub-main` (`h3`, `p`), `.pub-links`. |

## Replacing the audit schematic

The audit chapter shows a stand-in, labelled `SCHEMATIC`: a three-pane drawing made by
`tools/make_audit_schematic.py`. It shows no real paper, judgment or result.

To draw it again (the two fonts are optional):

```bash
pip install pillow
python3 tools/make_audit_schematic.py --sans GoogleSansFlex.ttf --mono GoogleSansCode.ttf
```

To put another picture in its place:

1. Save it as `assets/img/audit/audit-view-schematic.png`, or change the three paths in `07-audit.html` (`src` and
   the two `data-zoom` attributes).
2. Keep an aspect ratio between 2.0:1 and 2.4:1, and set `width` and `height` to the new pixel size.
3. Write a new `alt` text and a new caption. The three step headers above the picture are sized to panes of
   27%, 39% and 33% of its width; change `grid-template-columns` of `#audit .steps3` in `assets/css/audit.css` if
   the panes differ.
4. If the picture is a real screenshot, remove the `SCHEMATIC` tag and the words "stand-in drawing". Keep the
   sentence that says whether what it shows has been evaluated.
5. Run `python3 build.py` and `python3 tools/qa.py`.

## Design rules

- Colour carries meaning. Green: this work, the point, the active state. Blue: the baseline, always hollow.
  Violet: whoever judges (a teacher, an answer key, an auditor). Gold: not yet established (in progress, still
  open, a hypothesis, a target). Red: an error or a contradiction. One hue keeps one meaning on the whole page.
- Structure comes from whitespace, hairlines and 22px rounded cards, not from shadows or coloured grounds. The
  bridges are the only soft bands.
- Mono capitals are for labels, tags and data bases. Body text is never set in mono.
- Light is the default and the page ignores the system setting. The dark theme is the toggle in the top bar.
- Motion is slow and one-directional, and everything honours `prefers-reduced-motion`.

## Checking

`python3 tools/qa.py` needs Playwright (`pip install playwright`, then `playwright install chromium`). It builds
the page, serves a copy of the publishable files from a sub-path, and loads it in Chromium. It fails on:

- console errors or warnings, page errors, failed or missing files;
- a request outside the sub-path (a URL that is not relative) or to a host other than Google Fonts;
- horizontal overflow at twelve widths from 320 to 1920 px;
- behaviour: a broken in-page link or duplicate id, the theme toggle not switching or not persisting, the top bar
  not highlighting the chapter in view, the lightbox not opening or closing, a chart without its marks or data
  table, a block that never reveals, a broken image or one without `alt`, a block still marked `data-draft`,
  a missing `noindex` tag or `robots.txt` rule.

It writes into `_qa/`: every section in light and dark at 1440 x 900 (device scale factor 2), the whole page at
390 px in both themes, the hero after its entrance animation, `states/` (chart tooltip, open data table, figure
lightbox at 1440 and 390 px, card hover, side rail, a bridge, the full page at 1024 and 768 px, the page without
JavaScript) and `report.json`. Add `--tiles` for one screenshot per screenful; `--only checks` skips screenshots.
