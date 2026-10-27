"""Text helpers: outline text to SVG paths (portable) or emit live <text> (editable)."""
from fontTools.ttLib import TTFont, TTCollection
from fontTools.pens.svgPathPen import SVGPathPen
from xml.sax.saxutils import escape

def _ttc(path, family):
    for f in TTCollection(path).fonts:
        if f['name'].getDebugName(1) and f['name'].getDebugName(1).startswith(family):
            return f
    raise RuntimeError(family)

G = '/usr/share/fonts/truetype/sand-box/google/'
FONTS = {}
def _load():
    FONTS['serif'] = _ttc('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc', 'Noto Serif CJK SC')
    FONTS['serifr'] = _ttc('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc', 'Noto Serif CJK SC')
    FONTS['sans'] = _ttc('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 'Noto Sans CJK SC')
    FONTS['sansb'] = _ttc('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 'Noto Sans CJK SC')
    FONTS['mono'] = TTFont(G + 'IBM Plex Mono/IBMPlexMono-Medium.ttf')
    FONTS['display'] = TTFont(G + 'Instrument Serif/InstrumentSerif-Regular.ttf')
    FONTS['displayi'] = TTFont(G + 'Instrument Serif/InstrumentSerif-Italic.ttf')
_load()
FALLBACK = {'mono': 'sans', 'display': 'serifr', 'displayi': 'serifr'}
CSS = {
    'serif': ("'Noto Serif SC','Noto Serif CJK SC',serif", 700, 'normal'),
    'serifr': ("'Noto Serif SC','Noto Serif CJK SC',serif", 400, 'normal'),
    'sans': ("'Noto Sans SC','Noto Sans CJK SC',sans-serif", 400, 'normal'),
    'sansb': ("'Noto Sans SC','Noto Sans CJK SC',sans-serif", 700, 'normal'),
    'mono': ("'IBM Plex Mono','Noto Sans Mono CJK SC',monospace", 500, 'normal'),
    'display': ("'Instrument Serif','Noto Serif SC',serif", 400, 'normal'),
    'displayi': ("'Instrument Serif','Noto Serif SC',serif", 400, 'italic'),
}
_cache = {}
MODE = {'outline': True}

def _glyph(fk, ch):
    key = (fk, ch)
    if key in _cache: return _cache[key]
    f = FONTS[fk]
    cmap = f.getBestCmap()
    if ord(ch) not in cmap:
        r = _glyph(FALLBACK.get(fk, 'sans'), ch) if fk in FALLBACK else None
        if r is None:
            r = _glyph('sans', ch) if fk != 'sans' else ('', 500, 1000)
        _cache[key] = r; return r
    gs = f.getGlyphSet(); gn = cmap[ord(ch)]
    pen = SVGPathPen(gs); gs[gn].draw(pen)
    upm = f['head'].unitsPerEm
    r = (pen.getCommands(), gs[gn].width, upm)
    _cache[key] = r; return r

def width(s, size, font='sans', track=0.0):
    w = 0
    for ch in s:
        _, adv, upm = _glyph(font, ch)
        w += adv / upm * size + track * size
    return w - (track * size if s else 0)

def T(s, x, y, size=14, font='sans', fill='#241e1b', anchor='start', track=0.0, opacity=None):
    """Draw text with baseline at y."""
    w = width(s, size, font, track)
    x0 = x - (w / 2 if anchor == 'middle' else w if anchor == 'end' else 0)
    op = f' fill-opacity="{opacity}"' if opacity is not None else ''
    if not MODE['outline']:
        fam, wt, st = CSS[font]
        if font == 'mono' and any(ord(c) > 127 for c in s):
            fam = "'Noto Sans Mono CJK SC','IBM Plex Mono',monospace"
        ta = {'start': 'start', 'middle': 'middle', 'end': 'end'}[anchor]
        ls = f' letter-spacing="{track*size:.2f}"' if track else ''
        return (f'<text x="{x:.2f}" y="{y:.2f}" font-family="{escape(fam, {chr(39):"&apos;"})}" font-size="{size}" '
                f'font-weight="{wt}" font-style="{st}" text-anchor="{ta}" fill="{fill}"{op}{ls}>{escape(s)}</text>')
    out = [f'<g fill="{fill}"{op} aria-label="{escape(s)}">']
    cx = x0
    for ch in s:
        d, adv, upm = _glyph(font, ch)
        sc = size / upm
        if d:
            out.append(f'<path transform="matrix({sc:.5f} 0 0 {-sc:.5f} {cx:.2f} {y:.2f})" d="{d}"/>')
        cx += adv * sc + track * size
    out.append('</g>')
    return ''.join(out)
