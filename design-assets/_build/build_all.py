"""Rebuild every asset + PNG exports + preview.png.  Run: python build_all.py (needs cairosvg, fonttools)."""
import os, re, glob, cairosvg
import icons, brand, illus, diagrams, dark, hero, io, base64
from PIL import Image
from art_common import *
os.chdir(os.path.dirname(os.path.abspath(__file__)))
ic = icons.build(); brand.build(); brand.build_dark(); illus.build(); dark.build();
diagrams.build(True); diagrams.build(False)
if not os.path.exists('../hero/ledger-flatlay-1920.webp'): hero.build()

# PNG exports (2x)
for d in ['../diagrams', '../illustrations', '../illustrations/dark', '../brand']:
    os.makedirs(d + '/png', exist_ok=True)
    for f in sorted(glob.glob(d + '/*.svg')):
        cairosvg.svg2png(url=f, write_to=d + '/png/' + os.path.basename(f)[:-4] + '@2x.png', scale=2)
# verify every svg renders
bad = []
for f in glob.glob('../**/*.svg', recursive=True):
    try: cairosvg.svg2png(url=f, scale=1)
    except Exception as e: bad.append((f, e))
print('render failures:', bad)

def inner(path):
    s = open(path).read()
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    m = re.search(r'<svg[^>]*viewBox="([^"]+)"[^>]*>(.*)</svg>', s, re.S)
    return m.group(1), m.group(2)

def place(path, x, y, w=None, h=None):
    vb, body = inner(path)
    vw, vh = map(float, vb.split()[2:])
    if w and not h: h = w*vh/vw
    if h and not w: w = h*vw/vh
    return f'<svg x="{x}" y="{y}" width="{w:.1f}" height="{h:.1f}" viewBox="{vb}">{body}</svg>', w, h

PW = 2400; b = ''; y = 90
b += label('德鉴 DESIGN ASSETS · CONTACT SHEET', 90, y, CORAL, 16); y += 70
b += T('德鉴 × IOE 视觉资产总览', 90, y, 56, 'serif', INK); y += 46
b += T('金 = AI 产出 · 酒红 = 人的决定 · 绿 = 达标/改善 · 配色 V2', 90, y, 22, 'sans', INK, opacity=0.7); y += 40
sw = [(PAPER,'paper #fbf8f3'),(SHEET,'card #fffdf9'),(INK,'ink #241e1b'),(MUTED,'muted #7c716c'),(LINEC,'line #e8dfd7'),(WINE,'wine #6e1f2c'),(WINE2,'wine-2 #a43f45'),(AI,'gold/AI #c99a57'),(GREEN,'green #43685e')]
for i,(c,n) in enumerate(sw):
    x = 90+i*250; b += f'<rect x="{x}" y="{y}" width="60" height="60" fill="{c}" stroke="#241e1b" stroke-opacity=".2"/>' + label(n, x+72, y+36, INK, 13)
y += 110
b += line(90, y, PW-90, y, INK, 1, .2); y += 50
b += label('01 / ICONS · 24px · 1.5 stroke · currentColor', 90, y, CORAL, 15); y += 30
cols = 9; cw = (PW-180)/cols
for i, (fn, lab, role, src, key, body) in enumerate(ic):
    cx = 90 + (i % cols)*cw; cy = y + (i//cols)*170
    col = {'ink': INK, 'ai': AI, 'wine': WINE}[role]
    b += box(cx, cy, cw-16, 154, SHEET, INK, 1, .12)
    b += icon(body, cx+(cw-16)/2-28, cy+20, 56, col)
    b += T(lab, cx+(cw-16)/2, cy+110, 17, 'sans', INK, 'middle')
    b += label(fn + ('' if src == 'custom' else ' · lucide'), cx+(cw-16)/2, cy+136, INK if src=='custom' else MUTED, 10.5, 'middle')
y += ((len(ic)+cols-1)//cols)*170 + 40
b += label('02 / BRAND MARKS · 原创印章标（德鉴 / 演示酒业）', 90, y, CORAL, 15); y += 30
x = 90
for f, h in [('dejian-seal', 220), ('dejian-favicon', 100), ('dejian-lockup', 120), ('demo-seal', 220), ('demo-favicon', 100), ('demo-lockup', 120)]:
    s_, w_, h_ = place(f'../brand/{f}.svg', x, y, h=h); b += s_
    b += label(f + '.svg', x, y+240, INK, 11); x += w_ + 70
y += 290
b += label('03 / SPOT ILLUSTRATIONS', 90, y, CORAL, 15); y += 30
x = 90; rowh = 0
for f in ['empty-no-todo', 'empty-no-anomaly', 'login-hero', 'ai-human-flow', 'backtest-compare', 'multi-brand']:
    s_, w_, h_ = place(f'../illustrations/{f}.svg', 0, 0, h=300)
    if x + w_ > PW-90: x = 90; y += rowh + 50; rowh = 0
    s_, w_, h_ = place(f'../illustrations/{f}.svg', x, y, h=300)
    b += box(x, y, w_, h_, 'none', INK, 1, .2) + s_ + label(f + '.svg', x, y+h_+24, INK, 11)
    x += w_ + 40; rowh = max(rowh, h_)
y += rowh + 70
b += label('04 / DIAGRAMS · 1600×900 · 路演 PPT', 90, y, CORAL, 15); y += 30
dw = (PW-180-40)/2
for i, f in enumerate(sorted(glob.glob('../diagrams/0*.svg'))):
    x = 90 + (i % 2)*(dw+40); yy = y + (i//2)*(dw*9/16+60)
    s_, w_, h_ = place(f, x, yy, w=dw); b += box(x, yy, w_, h_, 'none', INK, 1, .25) + s_ + label(os.path.basename(f), x, yy+h_+26, INK, 11)
y += 2*(dw*9/16+60) + 40

# ---------- 05 dark mood ----------
DB, DC, CREAM = '#211b18', '#2d2523', '#fbf8f3'
def img(path, x, y, w, h=None, q=82):
    im = Image.open(path).convert('RGB'); 
    if h is None: h = w*im.height/im.width
    im = im.resize((int(w), int(h)), Image.LANCZOS); bio = io.BytesIO(); im.save(bio, 'JPEG', quality=q)
    return f'<image x="{x}" y="{y}" width="{w:.0f}" height="{h:.0f}" href="data:image/jpeg;base64,{base64.b64encode(bio.getvalue()).decode()}"/>', h
y0 = y; d = ''; y += 90
d += label('05 / DARK MOOD · 酱香 · 厚重感 · hero #211b18 / card #2d2523', 90, y, AI_DARK, 15); y += 30
# key-visual mock: hero image + headline composition (layout reference for lane-b)
mw = PW-180; s_, mh = img('../hero/desk-bottle-dejian-1920.png', 90, y, mw); d += s_
d += f'<defs><linearGradient id="hg" x1="0" x2="1"><stop offset="0" stop-color="{DB}" stop-opacity=".7"/><stop offset=".45" stop-color="{DB}" stop-opacity=".35"/><stop offset=".7" stop-color="{DB}" stop-opacity="0"/></linearGradient></defs><rect x="90" y="{y}" width="{mw:.0f}" height="{mh:.0f}" fill="url(#hg)"/>'
d += label('BAIJIU OPERATING SYSTEM · 德鉴 × IOE', 170, y+200, AI_DARK, 18)
d += T('一套会推演的', 170, y+300, 76, 'serif', CREAM)
d += T('采购—销售决策系统', 170, y+400, 76, 'serif', WINE2)
d += T('AI 逐步计算需求、订货、库存与渠道；人负责设定边界并批准动作。', 170, y+470, 26, 'sans', CREAM, opacity=.8)
d += f'<rect x="170" y="{y+520}" width="200" height="56" rx="28" fill="{WINE}"/>' + T('进入沙盘', 270, y+557, 22, 'sansb', CREAM, 'middle')
d += f'<rect x="392" y="{y+520}" width="220" height="56" rx="28" fill="none" stroke="{CREAM}" stroke-opacity=".45"/>' + T('查看数据目录', 502, y+557, 22, 'sans', CREAM, 'middle')
d += label('hero/desk-bottle-dejian-1920.webp · 版式示意（交 lane-b 实现）', 90, y+mh+28, CREAM, 11); y += mh + 60
tw = (PW-180-2*40)/3
for i, f in enumerate(['desk-bottle', 'cellar-jars', 'ledger-flatlay']):
    s_, th = img(f'../hero/{f}-1920.png', 90+i*(tw+40), y, tw); d += s_
    d += label(f'hero/{f}-1920 · -1280 · -crop-1280x960', 90+i*(tw+40), y+th+26, CREAM, 11)
y += th + 70
# icons on dark
d += label('ICONS ON DARK · cream #fbf8f3 / AI #e4b76f / 决定 #a43f45', 90, y, AI_DARK, 13); y += 24
cols2 = 13; cw2 = (PW-180)/cols2
for i, (fn, lab, role, src, key, body) in enumerate(ic):
    cx = 90 + (i % cols2)*cw2; cy = y + (i//cols2)*130
    col = {'ink': CREAM, 'ai': AI_DARK, 'wine': WINE2}[role]
    d += f'<rect x="{cx}" y="{cy}" width="{cw2-14:.1f}" height="116" fill="{DC}"/>'
    d += icon(body, cx+(cw2-14)/2-24, cy+18, 48, col)
    d += T(lab, cx+(cw2-14)/2, cy+96, 15, 'sans', CREAM, 'middle', opacity=.85)
y += 2*130 + 40
x = 90
for f, h in [('dejian-lockup-dark', 110), ('demo-lockup-dark', 110), ('dejian-favicon-dark', 96), ('dejian-seal', 170)]:
    s_, w_, h_ = place(f'../brand/{f}.svg', x, y, h=h); d += s_ + label(f + '.svg', x, y+190, CREAM, 11); x += max(w_, 300) + 90
y += 230
d += label('ILLUSTRATIONS · DARK VARIANTS (illustrations/dark/*-dark.svg)', 90, y, AI_DARK, 13); y += 24
x = 90; rowh = 0
for f in ['empty-no-todo', 'empty-no-anomaly', 'login-hero', 'ai-human-flow', 'backtest-compare', 'multi-brand']:
    s_, w_, h_ = place(f'../illustrations/dark/{f}-dark.svg', 0, 0, h=300)
    if x + w_ > PW-90: x = 90; y += rowh + 50; rowh = 0
    s_, w_, h_ = place(f'../illustrations/dark/{f}-dark.svg', x, y, h=300)
    d += s_ + label(f + '-dark.svg', x, y+h_+24, CREAM, 11)
    x += w_ + 40; rowh = max(rowh, h_)
y += rowh + 90
b += f'<rect x="0" y="{y0}" width="{PW}" height="{y-y0:.0f}" fill="{DB}"/>' + d
PH = int(y)
sheet = svg(PW, PH, b, '德鉴设计资产总览')
open('/tmp/preview.svg', 'w').write(sheet)
cairosvg.svg2png(bytestring=sheet.encode(), write_to='../preview.png', scale=1)
print('preview', PW, PH)
