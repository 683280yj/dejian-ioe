"""Dark-mood variants (PALETTE_V2 「气质补充」): token swap over the light SVGs.
bg #211b18, card #2d2523, cream #fbf8f3 for ink, AI gold -> #e4b76f, wine -> #a43f45.
Tints are the accent blended over #2d2523 (no new hues)."""
import re, os
DARK_BG = '#211b18'; DARK_CARD = '#2d2523'

def _blend(fg, a, bg=DARK_CARD):
    f = [int(fg[i:i+2], 16) for i in (1, 3, 5)]; b = [int(bg[i:i+2], 16) for i in (1, 3, 5)]
    return '#' + ''.join(f'{round(b[i]+(f[i]-b[i])*a):02x}' for i in range(3))

SWAP = {
    '#fffdf9': DARK_CARD,             # card -> dark card
    '#241e1b': '#fbf8f3',             # ink -> cream
    '#fbf8f3': DARK_BG,               # paper used as shape fill / knock-out stroke -> dark bg
    '#e8dfd7': _blend('#fbf8f3', .14),# line fills -> faint cream
    '#7c716c': '#e8dfd7',             # muted text -> light line colour
    '#c99a57': '#e4b76f',             # AI gold -> dark-bg gold
    '#f5ebdc': _blend('#e4b76f', .16),
    '#6e1f2c': '#a43f45',             # wine -> wine-2 (legible on dark)
    '#f4e8e6': _blend('#a43f45', .22),
    '#e6eeea': _blend('#43685e', .40),
}

def to_dark(s):
    # background rect emitted by art_common.svg()
    s = re.sub(r'(<title>.*?</title>)<rect width="(\d+)" height="(\d+)" fill="#fbf8f3"/>',
               lambda m: f'{m.group(1)}<rect width="{m.group(2)}" height="{m.group(3)}" fill="{DARK_BG}"/>', s, count=1)
    s = s.replace('<g fill="#fbf8f3"', '<g fill="@CREAM@"')  # paper-coloured text stays cream
    s = re.sub(r'#[0-9a-fA-F]{6}', lambda m: SWAP.get(m.group(0).lower(), m.group(0)), s)
    s = s.replace('@CREAM@', '#fbf8f3')
    return s.replace('role="img" aria-label="', 'role="img" aria-label="（深色）')

def build(src_dir='../illustrations/', out_dir='../illustrations/dark/'):
    os.makedirs(out_dir, exist_ok=True); out = []
    for f in sorted(os.listdir(src_dir)):
        if f.endswith('.svg'):
            open(out_dir + f.replace('.svg', '-dark.svg'), 'w').write(to_dark(open(src_dir + f).read())); out.append(f)
    return out
if __name__ == '__main__': print(build())
