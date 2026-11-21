"""Draws assets/img/audit/audit-view-schematic.png: the stand-in for the audit screenshot.

A synthetic three-pane wireframe (source document, claim graph, inspector) in the site's palette. It shows no
real paper, judgment, result or identifier. The middle pane carries the words "schematic · not yet evaluated", so the
picture cannot pass for a screenshot when it is seen without its caption. Drawn at 2x and downscaled to 2400 x 1004.

Usage (from the site folder):
  python3 tools/make_audit_schematic.py --sans GoogleSansFlex.ttf --mono GoogleSansCode.ttf
Both fonts are optional: without them Pillow's built-in font is used (the labels then look plainer).
Needs: pip install pillow
"""
import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser()
ap.add_argument('--out', default=str(Path(__file__).resolve().parent.parent / 'assets/img/audit/audit-view-schematic.png'))
ap.add_argument('--sans', default='', help='path to the Google Sans Flex variable font (.ttf)')
ap.add_argument('--mono', default='', help='path to the Google Sans Code variable font (.ttf)')
args = ap.parse_args()
out, SANS, MONO = args.out, args.sans, args.mono

S = 2                                   # supersampling
W, H = 2400 * S, 1004 * S
BG = (247, 249, 250); PANE = (255, 255, 255); LINE = (223, 230, 233); LINE2 = (203, 213, 219)
INK = (29, 43, 53); INK2 = (62, 82, 96); INK3 = (94, 113, 131); BAR = (232, 238, 242); BAR2 = (223, 230, 233)
GREEN = (47, 143, 107); GREEN_T = (226, 240, 233); GREEN_INK = (44, 115, 96)
GOLD = (188, 138, 53); GOLD_T = (255, 240, 211)
RED = (196, 111, 98)
PANEL = (242, 245, 246)


def font(path, size, weight):
    if not path:
        return ImageFont.load_default(size * S)
    f = ImageFont.truetype(path, size * S)
    try:
        axes = f.get_variation_axes()
        vals = []
        for a in axes:
            name = a['name'].decode() if isinstance(a['name'], bytes) else a['name']
            vals.append(weight if name == 'Weight' else a['default'])
        f.set_variation_by_axes(vals)
    except Exception:
        pass
    return f


def px(v):
    return int(round(v * S))


im = Image.new('RGB', (W, H), BG)
d = ImageDraw.Draw(im)
random.seed(7)


def rrect(box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle([px(box[0]), px(box[1]), px(box[2]), px(box[3])], radius=px(r), fill=fill, outline=outline, width=px(width) if outline else 0)


def text(xy, s, f, fill, anchor='la', tracking=0):
    if not tracking:
        d.text((px(xy[0]), px(xy[1])), s, font=f, fill=fill, anchor=anchor)
        return
    x = px(xy[0])
    for ch in s:
        d.text((x, px(xy[1])), ch, font=f, fill=fill, anchor='la')
        x += d.textlength(ch, font=f) + px(tracking)


M = 20                                  # outer margin
GAP = 16
inner = 2400 - 2 * M - 2 * GAP
wl, wm = round(inner * .27), round(inner * .40)
wr = inner - wl - wm
panes = {
    'left': (M, M, M + wl, 1004 - M),
    'mid': (M + wl + GAP, M, M + wl + GAP + wm, 1004 - M),
    'right': (M + wl + GAP + wm + GAP, M, 2400 - M, 1004 - M),
}
for box in panes.values():
    rrect(box, 18, fill=PANE, outline=LINE, width=2)

f_label = font(MONO, 17, 600)
f_small = font(SANS, 19, 400)
f_head = font(SANS, 21, 600)
f_chip = font(SANS, 20, 600)
f_mono_s = font(MONO, 15, 600)


def pane_label(box, s, right=None):
    text((box[0] + 28, box[1] + 26), s, f_label, INK3, tracking=2.2)
    if right:
        d.text((px(box[2] - 28), px(box[1] + 26)), right, font=f_small, fill=INK3, anchor='ra')
    d.line([px(box[0] + 1), px(box[1] + 66), px(box[2] - 1), px(box[1] + 66)], fill=LINE, width=px(2))


# ---- left: source document with located claims ---------------------------------------------
x0, y0, x1, y1 = panes['left']
pane_label(panes['left'], 'SOURCE DOCUMENT', 'page 0 / 00')
pg = (x0 + 44, y0 + 96, x1 - 44, y1 - 34)
rrect(pg, 6, fill=(255, 255, 255), outline=LINE, width=2)
colw = (pg[2] - pg[0] - 96) / 2
for c in range(2):
    cx = pg[0] + 32 + c * (colw + 32)
    y = pg[1] + 44
    while y < pg[3] - 40:
        w = colw if random.random() > 0.18 else colw * random.uniform(0.35, 0.8)
        r = random.random()
        if r < 0.10:        # a located claim
            rrect((cx - 5, y - 6, cx + w + 5, y + 16), 5, fill=GOLD_T, outline=GOLD, width=2)
        elif r < 0.20:      # an evidence statement
            rrect((cx - 5, y - 6, cx + w + 5, y + 16), 5, fill=GREEN_T, outline=GREEN, width=2)
        rrect((cx, y, cx + w, y + 10), 5, fill=BAR)
        y += 28
        if random.random() < 0.06:
            y += 28

# ---- middle: claim-evidence graph -----------------------------------------------------------
x0, y0, x1, y1 = panes['mid']
pane_label(panes['mid'], 'CLAIMS · GRAPH', 'schematic · not yet evaluated')


def node(cx, cy, w, h, head=None, dots=(GREEN, GREEN, GOLD)):
    bx = [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2]
    rrect(bx, 12, fill=(255, 255, 255), outline=INK if head else LINE2, width=3 if head else 2)
    if head:
        rrect((bx[0], bx[1], bx[2], bx[1] + 38), 12, fill=INK)
        d.rectangle([px(bx[0] + 1), px(bx[1] + 22), px(bx[2] - 1), px(bx[1] + 38)], fill=INK)
        text((bx[0] + 16, bx[1] + 9), head, f_mono_s, (255, 255, 255), tracking=1.6)
    ty = bx[1] + (56 if head else 22)
    rrect((bx[0] + 18, ty, bx[2] - 30, ty + 11), 5.5, fill=BAR)
    rrect((bx[0] + 18, ty + 24, bx[2] - 100, ty + 35), 5.5, fill=BAR)
    for i, col in enumerate(dots):
        d.ellipse([px(bx[0] + 18 + i * 24), px(bx[3] - 29), px(bx[0] + 32 + i * 24), px(bx[3] - 15)], fill=col)
    return bx


def arrow(p, q, col=GREEN, width=3.2):
    d.line([px(p[0]), px(p[1]), px(q[0]), px(q[1] + 10)], fill=col, width=px(width))
    x, y = q
    d.polygon([(px(x - 10), px(y + 17)), (px(x + 10), px(y + 17)), (px(x), px(y))], fill=col)


cx = (x0 + x1) / 2
top = [node(cx - 196, y0 + 190, 356, 136, 'CORE CLAIM A'), node(cx + 196, y0 + 190, 356, 136, 'CORE CLAIM B', dots=(GREEN, GOLD, RED))]
mids = [node(cx - 300, y0 + 420, 264, 106), node(cx, y0 + 420, 264, 106, dots=(GREEN, GREEN)), node(cx + 300, y0 + 420, 264, 106, dots=(GOLD, RED))]
bots = [node(cx - 180, y0 + 632, 278, 106, dots=(GREEN,)), node(cx + 160, y0 + 632, 278, 106, dots=(GREEN, GOLD))]
arrow((mids[0][0] + 132, mids[0][1]), (top[0][0] + 100, top[0][3]))
arrow((mids[1][0] + 100, mids[1][1]), (top[0][0] + 262, top[0][3]))
arrow((mids[1][0] + 164, mids[1][1]), (top[1][0] + 100, top[1][3]))
arrow((mids[2][0] + 132, mids[2][1]), (top[1][0] + 262, top[1][3]), col=RED)
arrow((bots[0][0] + 139, bots[0][1]), (mids[1][0] + 90, mids[1][3]))
arrow((bots[1][0] + 139, bots[1][1]), (mids[1][0] + 176, mids[1][3]))
lg_y = y1 - 62
lx = x0 + 34
for col, name in ((GREEN, 'supported'), (RED, 'contradicted'), (GOLD, 'insufficient evidence')):
    d.ellipse([px(lx), px(lg_y), px(lx + 18), px(lg_y + 18)], fill=col)
    d.text((px(lx + 30), px(lg_y + 9)), name, font=f_small, fill=INK2, anchor='lm')
    lx += 30 + d.textlength(name, font=f_small) / S + 44

# ---- right: inspector -------------------------------------------------------------------------
x0, y0, x1, y1 = panes['right']
pane_label(panes['right'], 'INSPECTOR', 'core claim B')
y = y0 + 104
for w in (0.94, 0.86, 0.9, 0.52):
    rrect((x0 + 32, y, x0 + 32 + (x1 - x0 - 64) * w, y + 15), 7.5, fill=BAR2)
    y += 36
y += 16
d.line([px(x0 + 32), px(y), px(x1 - 32), px(y)], fill=LINE, width=px(2))
y += 30
text((x0 + 32, y), 'Judgment', f_head, INK)
y += 44
chip = 'supported  ·  why'
cw = d.textlength(chip, font=f_chip) / S + 44
rrect((x0 + 32, y, x0 + 32 + cw, y + 46), 23, fill=GREEN_T, outline=GREEN, width=2)
d.text((px(x0 + 32 + cw / 2), px(y + 23)), chip, font=f_chip, fill=GREEN_INK, anchor='mm')
y += 84
text((x0 + 32, y), 'Evidence compared', f_head, INK)
y += 46
for row in ('claim in the text', 'table / figure value', 'code and configuration', 're-run or recomputation'):
    rrect((x0 + 32, y, x1 - 32, y + 56), 12, fill=PANEL, outline=LINE, width=2)
    d.text((px(x0 + 54), px(y + 28)), row, font=f_small, fill=INK3, anchor='lm')
    y += 70
y += 6
for w in (0.9, 0.7):
    rrect((x0 + 32, y, x0 + 32 + (x1 - x0 - 64) * w, y + 13), 6.5, fill=BAR)
    y += 30

im = im.resize((W // S, H // S), Image.LANCZOS)
im.save(out, optimize=True)
print('ok', im.size)
