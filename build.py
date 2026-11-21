"""Assemble index.html from src/head.html, src/partials/NN-<id>.html (in filename order) and src/tail.html.

Same approach as the build script of the ReproBridge project page: no framework, no bundler, standard library
only. Differences, all small:
  * shared assets are lists whose missing files are skipped (SHARED_CSS, SHARED_JS);
  * a partial may carry one lowercase letter after its number (03b-bridge-1.html), so a bridge can sit between
    two chapters without renumbering them;
  * HTML comments in partials are author notes and are removed from index.html;
  * the build counts draft markers (data-draft="...") and checks the output for absolute filesystem paths,
    root-relative URLs and external resources other than Google Fonts.

CSS and JS tags are generated:
  CSS  assets/css/base.css (required), then every SHARED_CSS file that exists, then assets/css/<id>.css for every
       partial that has one.
  JS   every SHARED_JS file that exists, then assets/js/<id>.js for every partial that has one.
Each URL gets a content hash (?v=...) so GitHub Pages caches never serve stale assets. Every URL is relative, so the
site works from any sub-path.

Usage:
  python3 build.py                         # writes index.html
  python3 build.py --only hero,measure     # preview with nav + selected partials + footer
  python3 build.py --out .preview-x.html   # alternate output (gitignored .preview-*.html)
  python3 build.py --strict                # also fail while draft markers remain (use before publishing)
"""
import argparse
import hashlib
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHARED_CSS = ['assets/css/kit.css', 'assets/css/talk.css']                       # after base.css; skipped when missing
SHARED_JS = ['assets/js/data.js', 'assets/js/charts.js', 'assets/js/plots.js', 'assets/js/site.js']
FONT_HOSTS = {'fonts.googleapis.com', 'fonts.gstatic.com'}                        # the only external resources allowed
TEXT_ASSETS = {'.css', '.js', '.svg', '.json', '.txt', '.html', '.md'}

ap = argparse.ArgumentParser()
ap.add_argument('--out', default='index.html')
ap.add_argument('--only', default='', help='comma-separated partial ids to include (nav and footer are always kept)')
ap.add_argument('--strict', action='store_true', help='fail while data-draft markers remain')
ap.add_argument('--no-lint', action='store_true', help='skip the path and URL checks')
args = ap.parse_args()

partials = sorted((ROOT / 'src/partials').glob('*.html'))
if not partials:
    sys.exit('no partials in src/partials')
ids = []
for p in partials:
    m = re.fullmatch(r'(\d\d[a-z]?)-([a-z0-9-]+)\.html', p.name)
    if not m:
        sys.exit(f'bad partial name {p.name} (expected NN-id.html or NNx-id.html)')
    ids.append(m.group(2))
if len(set(ids)) != len(ids):
    sys.exit('duplicate partial ids')
keep = None
if args.only:
    keep = set(x.strip() for x in args.only.split(',') if x.strip()) | {'nav', 'footer'}
    missing = keep - set(ids)
    if missing:
        sys.exit(f'unknown partial ids: {sorted(missing)}')


def ver(rel):
    return hashlib.sha1((ROOT / rel).read_bytes()).hexdigest()[:10]


def existing(rels):
    return [rel for rel in rels if (ROOT / rel).exists()]


def unique(rels):
    return list(dict.fromkeys(rels))     # a partial named like a shared file must not link it twice


def clean(text):
    """Drop author comments and the blank lines they leave behind."""
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    return re.sub(r'\n[ \t]*\n+', '\n', text).strip()


used = [(i, p) for i, p in zip(ids, partials) if keep is None or i in keep]
if not (ROOT / 'assets/css/base.css').exists():
    sys.exit('missing asset assets/css/base.css')
css = unique(['assets/css/base.css'] + existing(SHARED_CSS) + existing(f'assets/css/{i}.css' for i, _ in used))
js = unique(existing(SHARED_JS) + existing(f'assets/js/{i}.js' for i, _ in used))
css_tags = '\n'.join(f'<link rel="stylesheet" href="{rel}?v={ver(rel)}">' for rel in css)
js_tags = '\n'.join(f'<script src="{rel}?v={ver(rel)}"></script>' for rel in js)

head = (ROOT / 'src/head.html').read_text(encoding='utf-8')
tail = (ROOT / 'src/tail.html').read_text(encoding='utf-8')
if '<!--CSS-->' not in head or '<!--JS-->' not in tail:
    sys.exit('src/head.html needs <!--CSS--> and src/tail.html needs <!--JS-->')
sources = [(p.name, clean(p.read_text(encoding='utf-8'))) for _, p in used]
body = '\n'.join(f'<!-- ===== {name} ===== -->\n{text}\n' for name, text in sources)
html = head.replace('<!--CSS-->', css_tags) + '\n' + body + tail.replace('<!--JS-->', js_tags)

# ---------------------------------------------------------------- checks
ABS_PATH = re.compile(r'(?<![\w:/.\-])/(?:[A-Za-z0-9_.\-]+/){2,}[A-Za-z0-9_.\-]+|file:/')
ROOT_REL = re.compile(r'(?:\b(?:src|href|poster|action|data-zoom|data-src)\s*=\s*["\']|url\(\s*["\']?)(/[^"\')\s]*)')
LOADS = re.compile(r'(?:\bsrc\s*=\s*["\']|<link\b[^>]*?\bhref\s*=\s*["\']|url\(\s*["\']?|@import\s+["\'])(https?:)?//([^/"\')\s]+)', re.I)
ANCHORS = re.compile(r'<a\b[^>]*?\bhref\s*=\s*["\']https?://([^/"\']+)', re.I)

problems = []


def lint(name, text):
    for m in ABS_PATH.finditer(text):
        problems.append(f'{name}: absolute filesystem path "{m.group(0)[:80]}"')
    for m in ROOT_REL.finditer(text):
        if not m.group(1).startswith('//'):
            problems.append(f'{name}: root-relative URL "{m.group(1)[:60]}" (use a relative URL)')
    for m in LOADS.finditer(text):
        if m.group(2).lower() not in FONT_HOSTS:
            problems.append(f'{name}: external resource from "{m.group(2)}" (only Google Fonts may be loaded)')


if not args.no_lint:
    lint(args.out, html)
    for path in sorted((ROOT / 'assets').rglob('*')):
        if path.is_file() and path.suffix.lower() in TEXT_ASSETS:
            lint(str(path.relative_to(ROOT)), path.read_text(encoding='utf-8', errors='replace'))
    for path in (ROOT / 'src/head.html', ROOT / 'src/tail.html', *[p for _, p in used]):
        lint(str(path.relative_to(ROOT)), path.read_text(encoding='utf-8'))
    if problems:
        sys.exit('build stopped, fix these first:\n  ' + '\n  '.join(dict.fromkeys(problems)))

drafts = [(name, len(re.findall(r'\bdata-draft\b', text))) for name, text in sources]
drafts = [(name, n) for name, n in drafts if n]
total_drafts = sum(n for _, n in drafts)
if args.strict and total_drafts:
    sys.exit('build stopped (--strict): draft markers remain in ' + ', '.join(f'{name} ({n})' for name, n in drafts))

out = ROOT / args.out
fd, tmp = tempfile.mkstemp(dir=str(ROOT), prefix='.build-', suffix='.tmp')
with os.fdopen(fd, 'w', encoding='utf-8') as f:
    f.write(html)
os.chmod(tmp, 0o644)
os.replace(tmp, out)
print(f'wrote {out.name}: {len(used)} partials, {len(css)} css, {len(js)} js, {len(html):,} bytes')
hosts = sorted(set(h.lower() for h in ANCHORS.findall(html)))
if hosts:
    print('outbound links: ' + ', '.join(hosts))
if total_drafts:
    print(f'draft markers: {total_drafts} remain -> ' + ', '.join(f'{name} ({n})' for name, n in drafts))
    print('  open the page with ?drafts=1 to outline them; remove data-draft once the block holds final content')
