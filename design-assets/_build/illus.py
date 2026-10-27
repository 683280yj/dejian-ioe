from art_common import *
from icons import CUSTOM
OUT='../illustrations/'
W,H=320,240

def floor(y=208, x1=24, x2=296): return line(x1,y,x2,y,INK,1,0.25)

def jar(x, y, s=1.0):
    # x,y = top-left of a 100x130 jar box
    g = (f'<g transform="translate({x} {y}) scale({s})" stroke="{INK}" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round">'
         f'<path d="M22 28C22 14 36 6 50 6s28 8 28 22" fill="{STONE}"/>'
         f'<path d="M18 28h64" fill="none"/>'
         f'<path d="M27 28C10 38 2 56 2 76c0 28 16 50 34 50h28c18 0 34-22 34-50 0-20-8-38-25-48" fill="{SHEET}"/>'
         f'<path d="M30 34h40" fill="none" stroke="{CORAL}" stroke-width="3"/>'
         f'<path d="M62 30l10 14M66 30l4 16" fill="none" stroke="{CORAL}" stroke-width="2"/>'
         f'<path d="M50 56l20 20-20 20-20-20z" fill="{PAPER}"/>'
         f'<path d="M10 112h80" fill="none" stroke-opacity="0.35"/></g>')
    g += T('酒', x+50*s, y+76*s+16*s*0.36, 16*s, 'serif', INK, 'middle')
    return g

def bottle(x, y, s=1.0):
    return (f'<g transform="translate({x} {y}) scale({s})" stroke="{INK}" stroke-width="1.5" stroke-linejoin="round" fill="{SHEET}">'
            f'<rect x="12" y="0" width="12" height="9" fill="{INK}" stroke="{INK}"/>'
            f'<path d="M13.5 9v8c0 3-2 5-4.5 6.5C4 26.5 1 30 1 35v42a3 3 0 0 0 3 3h28a3 3 0 0 0 3-3V35c0-5-3-8.5-8-11.5-2.5-1.5-4.5-3.5-4.5-6.5V9"/>'
            f'<rect x="7" y="40" width="22" height="26" fill="{PAPER}"/>'
            f'<path d="M18 45v16" stroke="{CORAL}" stroke-width="2"/></g>')

def ledger(x, y, w=120, h=96, ticks=True):
    s = (f'<path d="M{x} {y+6}L{x+w/2} {y}L{x+w} {y+6}V{y+h}L{x+w/2} {y+h-6}L{x} {y+h}Z" fill="{SHEET}" stroke="{INK}" stroke-width="1.5" stroke-linejoin="round"/>'
         f'<path d="M{x+w/2} {y}V{y+h-6}" stroke="{INK}" stroke-width="1.5"/>')
    for i in range(5):
        yy = y+20+i*14
        s += line(x+10, yy+(0 if True else 0), x+w/2-10, yy, INK, 1, 0.3)
        s += line(x+w/2+10, yy, x+w-28, yy, INK, 1, 0.3)
        if ticks and i < 4:
            s += f'<path d="M{x+w-22} {yy-3}l3 3 6-6" fill="none" stroke="{AI}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
    return s

def empty_no_todo():
    b = floor()
    b += box(112, 44, 104, 150, SHEET, INK, 1.5, 1)
    b += box(140, 36, 48, 16, STONE, INK, 1.5, 1)
    for i in range(4):
        yy = 78 + i*26
        b += f'<rect x="128" y="{yy-8}" width="12" height="12" fill="none" stroke="{INK}" stroke-opacity=".5" stroke-width="1.2"/>'
        b += f'<path d="M130 {yy-2}l3 3 6-7" fill="none" stroke="{WINE}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
        b += line(150, yy-2, 200, yy-2, INK, 1, 0.25)
    # seal imprint
    b += f'<g transform="rotate(-8 230 168)"><rect x="210" y="146" width="40" height="40" fill="none" stroke="{WINE}" stroke-width="2"/>' + T('毕', 230, 166+22*0.36, 22, 'serif', WINE, 'middle') + '</g>'
    b += T('Nil.', 40, 112, 40, 'displayi', INK)
    b += label('NO PENDING', 42, 132, CORAL, 9)
    b += label('DECISIONS', 42, 145, CORAL, 9)
    b += f'<rect x="276" y="200" width="6" height="6" fill="{CORAL}"/>'
    return svg(W, H, b, '空状态：无待办（没有需要你拍板的事项）')

def empty_no_anomaly():
    b = floor()
    b += box(64, 52, 150, 134, SHEET, INK, 1.5, 1)
    b += box(64, 52, 150, 20, STONE, INK, 1.5, 1)
    for i in range(6):
        yy = 88 + i*16
        b += line(74, yy, 128, yy, INK, 1, 0.3) + line(150, yy, 202, yy, INK, 1, 0.3)
    # magnifier
    b += f'<circle cx="196" cy="118" r="38" fill="{AI_T}" fill-opacity=".85" stroke="{AI}" stroke-width="2"/>'
    b += f'<path d="M223 145l30 30" stroke="{AI}" stroke-width="5" stroke-linecap="square"/>'
    b += f'<path d="M180 118l11 11 21-22" fill="none" stroke="{AI}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
    b += sparkle(252, 64, 9, AI, AI_T)
    b += label('0 ANOMALIES', 64, 36, AI, 10)
    b += T('AI 已筛完，暂无异常订单', 64, 228, 11, 'sans', INK, opacity=0.7)
    b += f'<rect x="282" y="200" width="6" height="6" fill="{CORAL}"/>'
    return svg(W, H, b, '空状态：无异常（AI 已筛查完毕）')

def login_hero():
    w, h = 480, 360
    b = aura(16, 16, w-32, h-32, 18)
    b += line(40, 300, 440, 300, INK, 1, 0.3)
    b += jar(46, 152, 1.15)
    b += bottle(190, 206, 1.15)
    b += ledger(262, 200, 170, 100)
    b += f'<g transform="rotate(-6 372 150)">{box(318, 128, 108, 46, SHEET, INK, 1.2, 0.6)}' + label('DJ-53-500', 328, 146, INK, 9) + T('¥ 演示价', 328, 166, 16, 'display', INK) + '</g>'
    b += sparkle(420, 100, 11, AI, AI_T) + sparkle(400, 80, 5, AI, AI)
    b += label('01 / LEDGER & LIQUOR', 40, 52, CORAL, 10)
    b += T('Ledger,', 40, 96, 40, 'displayi', INK)
    b += T('not guesswork.', 40, 132, 40, 'display', INK)
    return svg(w, h, b, '登录页主视觉：酒坛 + 账本')

def ai_human_flow():
    w, h = 480, 240
    b = floor(206, 24, 456)
    # AI card
    b += box(28, 60, 130, 110, AI_T, AI, 1.5, 1)
    b += sparkle(50, 82, 9, AI, PAPER)
    b += label('AI 起草', 66, 86, AI, 10)
    for i,(ww) in enumerate([88, 70, 96]):
        b += f'<rect x="42" y="{106+i*14}" width="{ww}" height="5" fill="{AI}" fill-opacity="{0.8-i*0.2:.1f}"/>'
    b += T('补货建议', 42, 160, 13, 'sansb', AI)
    b += arrow(166, 115, 204, 115)
    # person + seal
    b += f'<circle cx="240" cy="84" r="16" fill="{SHEET}" stroke="{INK}" stroke-width="1.5"/>'
    b += f'<path d="M210 152v-12a30 30 0 0 1 60 0v12" fill="{SHEET}" stroke="{INK}" stroke-width="1.5"/>'
    b += icon(CUSTOM['approve-seal'], 262, 58, 30, WINE, 1.6)
    b += label('你拍板', 216, 180, WINE, 10)
    b += arrow(300, 115, 338, 115)
    # draft doc
    b += box(346, 60, 106, 120, SHEET, INK, 1.5, 0.7, '5 4')
    b += label('DRAFT', 358, 74, INK, 9)
    b += T('草稿采购单', 358, 96, 14, 'serif', INK)
    for i in range(4): b += line(358, 114+i*14, 438, 114+i*14, INK, 1, 0.3)
    b += f'<rect x="430" y="166" width="6" height="6" fill="{CORAL}"/>'
    b += label('01', 28, 46, CORAL, 10) + label('02', 214, 46, CORAL, 10) + label('03', 346, 46, CORAL, 10)
    return svg(w, h, b, 'AI 起草 → 人拍板 → 生成草稿')

def backtest_compare():
    w, h = 480, 240
    x0, y0, x1, y1 = 56, 44, 452, 186
    b = line(x0, y1, x1, y1, INK, 1.2, 0.6) + line(x0, y0, x0, y1, INK, 1.2, 0.6)
    bt, bb = y1-92, y1-56   # target band of 可售天数
    b += f'<rect x="{x0}" y="{bt}" width="{x1-x0}" height="{bb-bt}" fill="{GREEN_T}"/>'
    b += T('目标区间', x0+8, bt+14, 10, 'sans', GREEN)
    import math
    xs = [x0+16+i*34 for i in range(12)]
    base = [y1-74-52*math.sin(i*1.05+0.3) for i in range(12)]
    base = [min(y1-4, max(y0+6, v)) for v in base]
    aiv = [y1-74-9*math.sin(i*0.8) for i in range(12)]
    for x, v in zip(xs, base):
        if v > y1-30:
            b += f'<rect x="{x-5}" y="{y1-14}" width="10" height="14" fill="{CORAL}"/>'
    b += '<path d="M' + ' L'.join(f'{x:.0f} {y:.1f}' for x,y in zip(xs, base)) + f'" fill="none" stroke="{INK}" stroke-width="1.6" stroke-dasharray="5 4"/>'
    b += '<path d="M' + ' L'.join(f'{x:.0f} {y:.1f}' for x,y in zip(xs, aiv)) + f'" fill="none" stroke="{AI}" stroke-width="2.4"/>'
    b += f'<circle cx="{xs[-1]}" cy="{aiv[-1]:.1f}" r="4" fill="{AI}"/>'
    b += label('BACKTEST · 可售天数 · 演示假设', x0, 26, CORAL, 10)
    b += T('压货', x0-8, y0+12, 10, 'sans', INK, 'end', opacity=0.6) + T('断货', x0-8, y1-4, 10, 'sans', INK, 'end', opacity=0.6)
    b += line(x0, 212, x0+22, 212, INK, 1.6, 1, '5 4') + T('人工基线', x0+28, 216, 11, 'sans', INK)
    b += line(x0+100, 212, x0+122, 212, AI, 2.4, 1) + T('AI 建议', x0+128, 216, 11, 'sans', AI)
    b += f'<rect x="{x0+196}" y="206" width="10" height="10" fill="{CORAL}"/>' + T('缺货周', x0+212, 215, 11, 'sans', INK)
    b += label('W01', x0+6, y1+14, INK, 9) + label('W12', x1-26, y1+14, INK, 9)
    return svg(w, h, b, '回测对比：AI 建议 vs 人工基线')

def multi_brand():
    w, h = 480, 280
    b = ''
    # enterprise
    b += box(190, 24, 100, 56, INK, INK, 1, 1)
    b += icon('<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4M10 10h4M10 14h4M10 18h4"/>', 200, 40, 24, PAPER)
    b += T('企业', 232, 52, 14, 'serif', PAPER) + label('TENANT', 232, 68, CORAL, 8.5)
    brands = [('A', '品牌 A', 70), ('B', '品牌 B', 240), ('C', '品牌 C', 410)]
    for k, n, cx in brands:
        b += f'<path d="M240 80V100H{cx}V120" fill="none" stroke="{INK}" stroke-opacity=".45" stroke-width="1.2"/>'
        b += f'<rect x="{cx-44+4}" y="124" width="88" height="48" fill="{CORAL}"/>'
        b += box(cx-44, 120, 88, 48, SHEET, INK, 1.5, 1)
        b += f'<rect x="{cx-36}" y="130" width="16" height="28" fill="{STONE}" stroke="{INK}" stroke-width="1"/>' + T(k, cx-28, 150, 14, 'display', INK, 'middle')
        b += T(n, cx-12, 145, 13, 'serif', INK) + label('BRAND', cx-12, 160, CORAL, 8)
        for j, dx in enumerate((-30, 30)):
            wx = cx+dx
            b += f'<path d="M{cx} 168V186H{wx}V204" fill="none" stroke="{INK}" stroke-opacity=".35" stroke-width="1"/>'
            if j == 0:
                b += icon(open('lucide/warehouse.svg').read().split('>',1)[1].split('<svg',1)[-1].split('>',1)[1].rsplit('</svg>',1)[0], wx-14, 208, 28, INK)
            else:
                b += icon(open('lucide/store.svg').read().split('>',1)[1].split('<svg',1)[-1].split('>',1)[1].rsplit('</svg>',1)[0], wx-14, 208, 28, INK)
    b += label('仓库 WAREHOUSE', 24, 262, INK, 9) + label('渠道 CHANNEL', 456, 262, INK, 9, 'end')
    b += line(24, 248, 456, 248, INK, 1, 0.15)
    return svg(w, h, b, '多品牌结构：企业 → 品牌 → 仓库 / 渠道')

def build():
    import os; os.makedirs(OUT, exist_ok=True)
    files = {'empty-no-todo.svg': empty_no_todo(), 'empty-no-anomaly.svg': empty_no_anomaly(),
             'login-hero.svg': login_hero(), 'ai-human-flow.svg': ai_human_flow(),
             'backtest-compare.svg': backtest_compare(), 'multi-brand.svg': multi_brand()}
    for k, v in files.items(): open(OUT+k, 'w').write(v)
    return files
if __name__ == '__main__': print(len(build()))
