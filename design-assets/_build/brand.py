from art_common import *
OUT='../brand/'

def seal(chars, fill, fg=PAPER, w=76, h=132, shadow=False, x=0, y=0, size=50):
    s = ''
    if shadow: s += f'<rect x="{x+6}" y="{y+6}" width="{w}" height="{h}" fill="{CORAL}"/>'
    s += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>'
    s += f'<rect x="{x+5}" y="{y+5}" width="{w-10}" height="{h-10}" fill="none" stroke="{fg}" stroke-width="1.6"/>'
    # two characters stacked, optically centred
    cy1 = y + h*0.25 + size*0.36 + 2; cy2 = y + h*0.75 + size*0.36 - 2
    s += T(chars[0], x+w/2, cy1, size, 'serif', fg, 'middle')
    s += T(chars[1], x+w/2, cy2, size, 'serif', fg, 'middle')
    s += line(x+12, y+h/2, x+w-12, y+h/2, fg, 1, 0.55)
    return s

def lockup(chars, name, sub, fill):
    b = seal(chars, fill, w=46, h=80, size=25, x=2, y=2)
    b += T(name, 66, 46, 34, 'serif', INK)
    b += label(sub, 67, 72, CORAL, 10.5)
    return b

def build():
    import os; os.makedirs(OUT, exist_ok=True)
    files = {
     'dejian-seal.svg': svg(88, 144, seal('德鉴', WINE, shadow=True, x=2, y=2), '德鉴 印章标', bg=None),
     'dejian-seal-flat.svg': svg(76, 132, seal('德鉴', WINE), '德鉴 印章标（无投影）', bg=None),
     'dejian-favicon.svg': svg(64, 64, f'<rect width="64" height="64" fill="{WINE}"/><rect x="4" y="4" width="56" height="56" fill="none" stroke="{PAPER}" stroke-width="1.6"/>' + T('鉴', 32, 32+40*0.36, 40, 'serif', PAPER, 'middle'), '德鉴 favicon', bg=None),
     'dejian-lockup.svg': svg(300, 86, lockup('德鉴', '德鉴酒业', 'DEJIAN · 首批体验企业', WINE), '德鉴酒业 组合标', bg=None),
     'demo-seal.svg': svg(88, 144, seal('演示', INK, shadow=True, x=2, y=2), '演示酒业 印章标', bg=None),
     'demo-favicon.svg': svg(64, 64, f'<rect width="64" height="64" fill="{INK}"/><rect x="4" y="4" width="56" height="56" fill="none" stroke="{PAPER}" stroke-width="1.6"/>' + T('演', 32, 32+40*0.36, 40, 'serif', PAPER, 'middle'), '演示酒业 favicon', bg=None),
     'demo-lockup.svg': svg(300, 86, lockup('演示', '演示酒业', 'DEMO LIQUOR · 演示数据', INK), '演示酒业 组合标', bg=None),
    }
    for k, v in files.items(): open(OUT+k, 'w').write(v)
    return files
if __name__ == '__main__': print(len(build()))

# ---- dark-mood lockups (for #211b18 / #2d2523 hero, login, sidebar) ----
DARK_BG = '#211b18'
def lockup_dark(chars, name, sub, fill, fg):
    b = seal(chars, fill, fg=fg, w=46, h=80, size=25, x=2, y=2)
    b += T(name, 66, 46, 34, 'serif', PAPER)
    b += label(sub, 67, 72, AI_DARK, 10.5)
    return b
def build_dark():
    files = {
     'dejian-lockup-dark.svg': svg(300, 86, lockup_dark('德鉴', '德鉴酒业', 'DEJIAN · 首批体验企业', WINE2, PAPER), '德鉴酒业 组合标（深底）', bg=None),
     'demo-lockup-dark.svg': svg(300, 86, lockup_dark('演示', '演示酒业', 'DEMO LIQUOR · 演示数据', PAPER, DARK_BG), '演示酒业 组合标（深底）', bg=None),
     'dejian-favicon-dark.svg': svg(64, 64, f'<rect width="64" height="64" fill="{WINE2}"/><rect x="4" y="4" width="56" height="56" fill="none" stroke="{PAPER}" stroke-width="1.6"/>' + T('鉴', 32, 32+40*0.36, 40, 'serif', PAPER, 'middle'), '德鉴 favicon（深底）', bg=None),
    }
    for k, v in files.items(): open(OUT+k, 'w').write(v)
    return files
