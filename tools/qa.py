"""Visual and technical check of the built site with Playwright (Chromium).

What it does:
  1. runs build.py;
  2. copies the publishable files into a temporary folder under a sub-path (as GitHub Pages serves a project
     site) and serves that folder locally, which proves that every URL is relative;
  3. loads the page and records console messages, page errors, failed requests and every request made;
  4. checks behaviour: in-page links, theme toggle, scroll-spy, lightbox, charts, reveal on scroll, images,
     the noindex tag and robots.txt, and that no block is still marked data-draft;
  5. checks for horizontal overflow at a list of widths;
  6. writes screenshots: every section in light and dark at 1440 x 900 (device scale factor 2), the whole page
     at 390 px, a few interaction states, and (with --tiles) one screenshot per screenful.

Usage (from the site folder):
  python3 tools/qa.py                 # everything except tiles, into _qa/
  python3 tools/qa.py --tiles         # also one tile per screenful
  python3 tools/qa.py --only checks   # no screenshots
Needs: pip install playwright && playwright install chromium
"""
import argparse
import functools
import http.server
import json
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

SITE = Path(__file__).resolve().parent.parent
SUBPATH = 'compII_presentation_fable'
PUBLISH = ['index.html', 'assets', 'robots.txt', '.nojekyll']
FONT_HOSTS = ('fonts.googleapis.com', 'fonts.gstatic.com')
WIDTHS = [320, 360, 390, 430, 600, 768, 900, 1024, 1100, 1280, 1440, 1920]
CHAPTERS = ['measure', 'improve', 'ground', 'reproduce', 'audit', 'plan']

ap = argparse.ArgumentParser()
ap.add_argument('--out', default=str(SITE / '_qa'))
ap.add_argument('--only', default='', help='comma list of: checks, sections, mobile, states, tiles')
ap.add_argument('--tiles', action='store_true', help='also write one screenshot per screenful (light and dark, 1440 and 390)')
ap.add_argument('--dsf', type=float, default=2, help='device scale factor for screenshots')
ap.add_argument('--no-build', action='store_true')
args = ap.parse_args()
want = set(args.only.split(',')) if args.only else {'checks', 'sections', 'mobile', 'states'}
if args.tiles:
    want.add('tiles')
out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)

if not args.no_build:
    subprocess.run([sys.executable, str(SITE / 'build.py')], check=True)

tmp = Path(tempfile.mkdtemp(prefix='c2-qa-'))
root = tmp / SUBPATH
root.mkdir()
for name in PUBLISH:
    src = SITE / name
    if src.is_dir():
        shutil.copytree(src, root / name)
    elif src.exists():
        shutil.copy2(src, root / name)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(tmp)))
port = httpd.server_address[1]
threading.Thread(target=httpd.serve_forever, daemon=True).start()
ORIGIN = f'http://127.0.0.1:{port}'
BASE = f'{ORIGIN}/{SUBPATH}/'

report = {'base_path': f'/{SUBPATH}/', 'console': [], 'page_errors': [], 'failed_requests': [], 'bad_status': [],
          'outside_subpath': [], 'external_hosts': {}, 'overflow': {}, 'behaviour': {}, 'screenshots': []}


def watch(page):
    page.on('console', lambda m: report['console'].append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
    page.on('pageerror', lambda e: report['page_errors'].append(str(e)))
    page.on('requestfailed', lambda r: report['failed_requests'].append(r.url.replace(ORIGIN, '')))

    def on_response(resp):
        url = resp.url
        if url.startswith(ORIGIN):
            path = url[len(ORIGIN):]
            if not path.startswith(f'/{SUBPATH}/'):
                report['outside_subpath'].append(path)
            if resp.status >= 400:
                report['bad_status'].append(f'{resp.status} {path}')
        elif url.startswith('http'):
            host = url.split('/')[2]
            report['external_hosts'][host] = report['external_hosts'].get(host, 0) + 1
    page.on('response', on_response)


def open_page(browser, width, height, theme, reduced=True, dsf=1.0, query=''):
    ctx = browser.new_context(viewport={'width': width, 'height': height}, device_scale_factor=dsf,
                              reduced_motion='reduce' if reduced else 'no-preference')
    if theme:
        ctx.add_init_script(f"try {{ if (!sessionStorage.getItem('qa')) {{ localStorage.setItem('c2-theme', '{theme}'); sessionStorage.setItem('qa', '1'); }} }} catch (e) {{}}")
    page = ctx.new_page()
    watch(page)
    page.goto(BASE + query, wait_until='networkidle')
    page.evaluate('document.fonts.ready')
    page.wait_for_timeout(500)
    return ctx, page


def jump(page, y):
    page.evaluate(f"window.scrollTo({{ top: {int(y)}, behavior: 'instant' }})")


def settle(page):
    """Scroll through the page once so lazy images load and every block has been revealed.
    Steps are shorter than a screen: reveal ignores the lowest 8% of the viewport, so a full-screen step could
    carry a short block past without ever showing it to the observer."""
    h = page.evaluate('document.documentElement.scrollHeight')
    vh = page.viewport_size['height']
    y = 0
    while y < h:
        jump(page, y)
        page.wait_for_timeout(120)
        y += int(vh * 0.6)
    jump(page, 0)
    page.wait_for_function('[...document.images].every(i => i.complete)', timeout=15000)
    page.wait_for_timeout(300)


def to(page, selector, dy=0):
    page.evaluate("([s, dy]) => { const r = document.querySelector(s).getBoundingClientRect();"
                  " window.scrollTo({ top: window.scrollY + r.top - 80 + dy, behavior: 'instant' }); }", [selector, dy])
    page.wait_for_timeout(250)


def shot(page, name, **kw):
    path = out / name
    path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(path), **kw)
    report['screenshots'].append(name)


with sync_playwright() as pw:
    browser = pw.chromium.launch()

    if 'checks' in want:
        beh = report['behaviour']
        # ---- behaviour, with motion on (the state a visitor gets)
        ctx, page = open_page(browser, 1440, 900, None, reduced=False)
        beh['default_theme'] = page.evaluate("document.documentElement.getAttribute('data-theme')")
        beh['robots_meta'] = page.evaluate("(document.querySelector('meta[name=robots]') || {}).content || ''")
        beh['robots_txt'] = page.evaluate("fetch('robots.txt').then(r => r.text())").strip().replace('\n', ' | ')
        beh['broken_in_page_links'] = page.evaluate(
            "[...document.querySelectorAll('a[href^=\"#\"]')].map(a => a.getAttribute('href')).filter(h => h.length > 1 && !document.getElementById(h.slice(1)))")
        beh['duplicate_ids'] = page.evaluate(
            "(() => { const seen = {}, dup = []; document.querySelectorAll('[id]').forEach(e => { if (seen[e.id]) dup.push(e.id); seen[e.id] = 1; }); return dup; })()")
        beh['external_links_without_noopener'] = page.evaluate(
            "[...document.querySelectorAll('a[target=_blank]')].filter(a => !/noopener/.test(a.rel)).map(a => a.href)")
        settle(page)
        beh['unrevealed_blocks'] = page.evaluate("document.querySelectorAll('[data-reveal]:not(.in)').length")
        beh['broken_images'] = page.evaluate("[...document.images].filter(i => i.hasAttribute('src') && !i.naturalWidth).map(i => i.getAttribute('src'))")
        beh['images_without_alt'] = page.evaluate("[...document.images].filter(i => !i.hasAttribute('alt')).length")
        beh['draft_markers'] = page.evaluate("document.querySelectorAll('[data-draft]').length")
        beh['charts'] = page.evaluate('''() => [...document.querySelectorAll('.chart[data-chart]')].map(c => {
          const spec = JSON.parse(c.querySelector('script[type="application/json"]').textContent);
          return { type: c.dataset.chart, rows: spec.rows.length, marks: c.querySelectorAll('svg .mk-rra, svg .bar').length,
                   tableRows: c.querySelectorAll('.chart-table tbody tr').length, shown: c.classList.contains('in') }; })''')
        spy = {}
        for cid in CHAPTERS:
            to(page, '#' + cid, 120)
            page.wait_for_timeout(150)
            spy[cid] = page.evaluate("[...document.querySelectorAll('.nav-links a.on')].map(a => a.getAttribute('href')).join(',')")
        beh['scroll_spy'] = spy
        jump(page, 0)
        page.click('.theme-toggle')
        clicked = page.evaluate("[document.documentElement.getAttribute('data-theme'), localStorage.getItem('c2-theme')]")
        page.reload(wait_until='networkidle')
        reloaded = page.evaluate("document.documentElement.getAttribute('data-theme')")
        page.click('.theme-toggle')
        clicked_again = page.evaluate("document.documentElement.getAttribute('data-theme')")
        beh['theme_toggle'] = {'after_click': clicked, 'after_reload': reloaded, 'after_second_click': clicked_again}
        to(page, '#measure .fig')
        page.click('#measure .fig img')
        page.wait_for_timeout(300)
        lb1 = page.evaluate("[document.getElementById('rb-lightbox').open, document.querySelector('#rb-lightbox img').getAttribute('src')]")
        page.keyboard.press('Escape')
        page.wait_for_timeout(200)
        beh['lightbox'] = {'opened': lb1[0], 'image': lb1[1], 'closed_by_escape': not page.evaluate("document.getElementById('rb-lightbox').open")}
        ctx.close()
        beh['ok'] = bool(
            beh['default_theme'] == 'light' and 'noindex' in beh['robots_meta'] and 'Disallow: /' in beh['robots_txt']
            and not beh['broken_in_page_links'] and not beh['duplicate_ids'] and not beh['external_links_without_noopener']
            and beh['unrevealed_blocks'] == 0 and not beh['broken_images'] and beh['images_without_alt'] == 0
            and beh['draft_markers'] == 0
            and all(c['marks'] >= c['rows'] and c['tableRows'] == c['rows'] and c['shown'] for c in beh['charts'])
            and all(spy[c] == '#' + c for c in CHAPTERS)
            and clicked == ['dark', 'dark'] and reloaded == 'dark' and clicked_again == 'light'
            and lb1[0] and beh['lightbox']['closed_by_escape'])

        # ---- horizontal overflow
        for w in WIDTHS:
            ctx, page = open_page(browser, w, 900, 'light')
            settle(page)
            res = page.evaluate('''() => {
              const vw = document.documentElement.clientWidth, sw = document.documentElement.scrollWidth, bad = [];
              for (const el of document.querySelectorAll('body *')) {
                if (el.closest('svg') && el.tagName.toLowerCase() !== 'svg') continue;
                const cs = getComputedStyle(el);
                if (cs.position === 'fixed' || cs.display === 'none' || cs.visibility === 'hidden') continue;
                const r = el.getBoundingClientRect();
                if (!r.width || !r.height) continue;
                if (r.right > vw + 1 || r.left < -1) {
                  let p = el.parentElement, clipped = false;
                  while (p && p !== document.body) {
                    const o = getComputedStyle(p);
                    if (/(hidden|auto|scroll|clip)/.test(o.overflowX)) { clipped = true; break; }
                    p = p.parentElement;
                  }
                  if (!clipped) bad.push((el.id ? '#' + el.id : el.tagName.toLowerCase() + '.' + String(el.className).split(' ').join('.')) + ' [' + Math.round(r.left) + ',' + Math.round(r.right) + ']');
                }
              }
              return { vw, sw, bad: bad.slice(0, 12) };
            }''')
            if res['sw'] > res['vw'] or res['bad']:
                report['overflow'][str(w)] = res
            ctx.close()

    themes = ('light', 'dark')
    if 'sections' in want:
        for theme in themes:
            ctx, page = open_page(browser, 1440, 900, theme, dsf=args.dsf)
            settle(page)
            # the fixed bar and the side rail would be stitched into the middle of tall sections
            page.add_style_tag(content='nav.top { position: absolute !important; } .rail { display: none !important; }')
            ids = page.evaluate('''() => [...document.querySelectorAll('header.hero, main > section, main > aside, footer.foot')].map((el, i) => {
              if (!el.id) el.id = el.tagName.toLowerCase() === 'footer' ? 'footer' : 'part-' + i;
              return el.id; })''')
            for i, sid in enumerate(ids):
                name = f'sections-{theme}-1440/{i:02d}-{sid}.png'
                (out / name).parent.mkdir(parents=True, exist_ok=True)
                page.locator(f'#{sid}').screenshot(path=str(out / name))
                report['screenshots'].append(name)
            ctx.close()
        ctx, page = open_page(browser, 1440, 900, 'light', reduced=False)   # motion on: the hero draw-in must settle
        page.wait_for_timeout(4200)
        shot(page, 'hero-after-animation-1440.png')
        ctx.close()

    if 'mobile' in want:
        for theme in themes:
            ctx, page = open_page(browser, 390, 844, theme, dsf=args.dsf)
            settle(page)
            shot(page, f'mobile-390-{theme}-fullpage.png', full_page=True)
            ctx.close()

    if 'states' in want:
        ctx, page = open_page(browser, 1440, 900, 'light', dsf=1)
        settle(page)
        to(page, '#improve .chart-card')
        page.hover('#improve .chart .row-hit >> nth=1')
        page.wait_for_timeout(300)
        shot(page, 'states/chart-tooltip.png')
        page.mouse.move(5, 5)
        page.click('#improve .chart-table summary')
        to(page, '#improve .chart-card', 160)
        shot(page, 'states/chart-data-table-open.png')
        to(page, '#ground .fig')
        page.click('#ground .fig img')
        page.wait_for_timeout(400)
        shot(page, 'states/figure-lightbox.png')
        page.keyboard.press('Escape')
        to(page, '#thread .road', -40)
        page.hover('#thread .road-stop:nth-child(1) .road-card')
        page.wait_for_timeout(700)
        shot(page, 'states/roadmap-card-hover.png')
        to(page, '#audit .sub-row')
        page.mouse.move(5, 5)
        page.hover('.rail')
        page.wait_for_timeout(600)
        shot(page, 'states/side-rail-expanded.png')
        to(page, '#bridge-2', 60)
        page.mouse.move(5, 5)
        page.wait_for_timeout(500)
        shot(page, 'states/bridge.png')
        ctx.close()
        ctx, page = open_page(browser, 390, 844, 'light', dsf=2)                # phone: a figure opened in the lightbox
        settle(page)
        to(page, '#measure .fig')
        page.click('#measure .fig img')
        page.wait_for_timeout(400)
        shot(page, 'states/figure-lightbox-390.png')
        ctx.close()
        for w, hgt in ((1024, 900), (768, 1024)):
            ctx, page = open_page(browser, w, hgt, 'light', dsf=1)
            settle(page)
            shot(page, f'states/fullpage-{w}.png', full_page=True)
            ctx.close()
        ctx = browser.new_context(viewport={'width': 1440, 'height': 900}, java_script_enabled=False,
                                  reduced_motion='reduce')                            # without JavaScript
        page = ctx.new_page()
        page.goto(BASE, wait_until='networkidle')
        page.mouse.move(700, 450)
        for _ in range(70):                                                         # wheel down so lazy images load
            page.mouse.wheel(0, 600)
            page.wait_for_timeout(60)
        page.wait_for_timeout(600)
        shot(page, 'states/no-javascript-fullpage.png', full_page=True)
        ctx.close()

    if 'tiles' in want:
        for theme in themes:
            for (w, hgt) in ((1440, 900), (390, 844)):
                ctx, page = open_page(browser, w, hgt, theme, dsf=1 if w > 600 else 2)
                settle(page)
                total = page.evaluate('document.documentElement.scrollHeight')
                y, i = 0, 0
                step = hgt - (60 if w > 600 else 56)
                while y < total:
                    jump(page, y)
                    page.wait_for_timeout(150)
                    shot(page, f'tiles-{theme}-{w}/{i:02d}.png')
                    y += step
                    i += 1
                ctx.close()

    browser.close()

httpd.shutdown()
shutil.rmtree(tmp, ignore_errors=True)

for k in ('console', 'page_errors', 'failed_requests', 'bad_status', 'outside_subpath'):
    report[k] = sorted(set(report[k]))
report['external_hosts_not_fonts'] = sorted(h for h in report['external_hosts'] if h not in FONT_HOSTS)
ok = not (report['console'] or report['page_errors'] or report['failed_requests'] or report['bad_status']
          or report['outside_subpath'] or report['overflow'] or report['external_hosts_not_fonts'])
if 'checks' in want:
    ok = ok and report['behaviour'].get('ok', False)
report['ok'] = ok
(out / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k != 'screenshots'}, indent=2))
print(f"{len(report['screenshots'])} screenshots in {out.name}/")
sys.exit(0 if ok else 1)
