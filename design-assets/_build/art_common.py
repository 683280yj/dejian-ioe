from textlib import T, width, MODE
# Palette V2 (docs/PALETTE_V2.md): AI = gold, human decision = wine, ok/improvement = green
PAPER='#fbf8f3'; SHEET='#fffdf9'; INK='#241e1b'; MUTED='#7c716c'; LINEC='#e8dfd7'
STONE=LINEC                      # panel fill (was stone)
AI='#c99a57'; AI_DARK='#e4b76f'  # AI outputs; AI_DARK on ink backgrounds
WINE='#6e1f2c'; WINE2='#a43f45'; GREEN='#43685e'
CORAL=WINE2                      # legacy name: accent labels / dots / hard shadows now use wine-2
AI_T='#f5ebdc'; WINE_T='#f4e8e6'; GREEN_T='#e6eeea'   # 15-20% tints of gold / wine / green on paper
LINE='stroke="#241e1b" stroke-opacity="0.15"'

def svg(w, h, body, title, bg=PAPER):
    bgr = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{title}">'
            f'<title>{title}</title>{bgr}{body}</svg>\n')

def aura(x, y, w, h, L=14, sw=1.5, dot=True, color=INK):
    p = (f'M{x} {y+L}V{y}H{x+L} M{x+w-L} {y}H{x+w}V{y+L} M{x+w} {y+h-L}V{y+h}H{x+w-L} M{x+L} {y+h}H{x}V{y+h-L}')
    s = f'<path d="{p}" fill="none" stroke="{color}" stroke-width="{sw}"/>'
    if dot: s += f'<rect x="{x+w-L-9}" y="{y+h-9}" width="6" height="6" fill="{CORAL}"/>'
    return s

def box(x, y, w, h, fill=SHEET, stroke=INK, sw=1, op=0.15, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-opacity="{op}" stroke-width="{sw}"{d}/>'

def line(x1, y1, x2, y2, color=INK, sw=1, op=0.15, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-opacity="{op}" stroke-width="{sw}"{d}/>'

def arrow(x1, y1, x2, y2, color=INK, sw=1.5, op=0.7, head=7, dash=None):
    import math
    a = math.atan2(y2-y1, x2-x1)
    hx1 = x2 - head*math.cos(a-0.45); hy1 = y2 - head*math.sin(a-0.45)
    hx2 = x2 - head*math.cos(a+0.45); hy2 = y2 - head*math.sin(a+0.45)
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<g stroke="{color}" stroke-opacity="{op}" stroke-width="{sw}" fill="none" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="M{x1:.1f} {y1:.1f}L{x2:.1f} {y2:.1f}"{d}/><path d="M{hx1:.1f} {hy1:.1f}L{x2:.1f} {y2:.1f}L{hx2:.1f} {hy2:.1f}"/></g>')

def icon(body, x, y, size=24, color=INK, sw=1.5):
    s = size/24
    return (f'<g transform="translate({x} {y}) scale({s:.4f})" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round">{body}</g>')

def sparkle(cx, cy, r, color=AI, fill='none', sw=1.5):
    k = r*0.28
    d = f'M{cx} {cy-r}L{cx+k} {cy-k}L{cx+r} {cy}L{cx+k} {cy+k}L{cx} {cy+r}L{cx-k} {cy+k}L{cx-r} {cy}L{cx-k} {cy-k}Z'
    return f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{sw}" stroke-linejoin="round"/>'

def label(s, x, y, color=CORAL, size=11, anchor='start'):
    return T(s, x, y, size, 'mono', color, anchor, track=0.14)

def chip(s, x, y, fg, bg, size=13, padx=10, h=26, font='sans', stroke=None):
    w = width(s, size, font) + padx*2
    st = f' stroke="{stroke}" stroke-width="1"' if stroke else ''
    return f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" fill="{bg}"{st}/>' + T(s, x+padx, y+h/2+size*0.36, size, font, fg), w
