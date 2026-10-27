from art_common import *
from icons import CUSTOM, lucide_body
import textlib
W, H = 1600, 900
FOOT = '德鉴 × IOE 二开 · 2026 iCAN 精创杯 AI 智能决策挑战赛 · 带「演示假设」的数字均未经德鉴核实'

def wrap(s, maxw, size, font='sans'):
    import re
    toks = re.findall(r'[A-Za-z0-9_.%¥,/+\-]+|\s|.', s)
    lines, cur = [], ''
    for tk in toks:
        if width(cur+tk, size, font) > maxw and cur.strip():
            lines.append(cur.rstrip()); cur = tk.lstrip()
        else: cur += tk
    if cur.strip(): lines.append(cur.rstrip())
    return lines

def para(s, x, y, maxw, size=14, font='sans', fill=INK, lh=1.6, opacity=None):
    out = ''
    for i, ln in enumerate(wrap(s, maxw, size, font)):
        out += T(ln, x, y+i*size*lh, size, font, fill, opacity=opacity)
    return out, len(wrap(s, maxw, size, font))

def frame(no, title, sub):
    b = aura(24, 24, W-48, H-48, 22)
    b += label(f'DIAGRAM {no}', 72, 84, CORAL, 13)
    b += T(title, 72, 136, 40, 'serif', INK)
    b += T(sub, 72, 172, 17, 'sans', INK, opacity=0.7)
    b += line(72, 196, W-72, 196, INK, 1, 0.2)
    b += label(FOOT, 72, H-52, INK, 10.5)
    return b

LU = {n: lucide_body(n) for n in ['warehouse','package-plus','truck','building-2','scan-search','file-pen-line','database','zap','shield-alert','calendar-sync','sliders-horizontal','book-open-text','users','store','layout-dashboard','server','clipboard-check']}
IC = {**LU, **CUSTOM}

# ---------- D1 业务流程：人工现状 vs AI 赋能 ----------
def d1():
    b = frame('01', '业务流程：人工现状 vs AI 赋能', '同一条链路，AI 接手算数、对表、筛异常、起草；每一步的决定仍由人来拍板。')
    steps = [
      ('库存盯盘', 'stock-alert', '仓管翻台账看库存，固定预警数量不随销量变化', '每周约 12 小时盯库存/发货台账「演示假设」',
       '库存预警：按销量与交期动态算安全库存', '每日 · 自动执行', '你确认是否触发补货'),
      ('补货测算', 'replenish', '凭经验按“上月销量×1.2”下单，旺季断货、淡季压货', '缺货 3 次/月 · 周转 4.2 次/年「演示假设」',
       '补货测算：向供应商补 N 箱，预算占用 ¥X，受预算/库容/起订量约束', '每周 · 人工复核', '采购审批 → 生成草稿采购单'),
      ('入库对单', 'inbound-match', '拿送货单、采购单、发票逐行手工核对，品名不统一易漏差异', '约 15 分钟/单「演示假设」',
       '入库对单：数量、单价、品名差异逐行标出', '到货即算 · 差异自动标记', '仓管确认入库'),
      ('订单处理', 'scan-search', '微信/纸质接单，低价窜货、录错、重复单常在发货后才发现', '订货准备 40 分钟/单 · 差错率 5.5%「演示假设」',
       '订单异常筛查：超信用、重复单、低于渠道底价', '实时 · 人工复核', '销售复核后发货'),
      ('对账结算', 'reconcile', '月底导流水在 Excel 里 VLOOKUP，手续费、跨日到账造成假差异', '耗时与差异笔数待跟岗计时【待核实】',
       '对账：差异金额 + 疑似差异单据清单', '每日 · 人工复核', '财务确认或发起争议'),
      ('经营日报', 'file-pen-line', '内勤每天导数、做表、写文字汇报', '约 40 分钟/天「演示假设」',
       '日报起草：销量、库存、异常、待拍板事项', '每日 · 自动执行', '老板阅读并批示'),
    ]
    x0, colw, gap = 206, 206, 12
    yT, hT = 236, 236     # 人工 lane
    yA, hA = 520, 300     # AI lane
    b += f'<rect x="72" y="{yT}" width="{W-144}" height="{hT}" fill="{STONE}" fill-opacity=".55"/>'
    b += f'<rect x="72" y="{yA}" width="{W-144}" height="{hA}" fill="{AI_T}" fill-opacity=".45"/>'
    b += label('A / 人工现状', 88, yT+30, INK, 12)
    b += T('靠经验', 88, yT+62, 15, 'serif', INK) + T('靠台账', 88, yT+86, 15, 'serif', INK) + T('靠加班', 88, yT+110, 15, 'serif', INK)
    b += label('B / AI 赋能', 88, yA+30, AI, 12)
    b += T('AI 起草', 88, yA+62, 15, 'serif', AI) + T('人拍板', 88, yA+86, 15, 'serif', WINE)
    b += f'<rect x="88" y="{yA+hA-74}" width="10" height="10" fill="{AI}"/>' + T('AI 产出', 104, yA+hA-65, 12, 'sans', INK)
    b += f'<rect x="88" y="{yA+hA-50}" width="10" height="10" fill="{WINE}"/>' + T('人的决定', 104, yA+hA-41, 12, 'sans', INK)
    for i, (name, ic, now, pain, ai, cyc, human) in enumerate(steps):
        x = x0 + i*(colw+gap)
        # 人工
        b += box(x, yT+16, colw, hT-32, SHEET, INK, 1, 0.2)
        b += label(f'{i+1:02d}', x+14, yT+40, CORAL, 11)
        b += T(name, x+44, yT+42, 19, 'serif', INK)
        b += para(now, x+14, yT+74, colw-28, 13, 'sans', INK, 1.6, 0.8)[0]
        b += line(x+14, yT+hT-74, x+colw-14, yT+hT-74, INK, 1, 0.15)
        b += f'<rect x="{x+14}" y="{yT+hT-62}" width="6" height="6" fill="{CORAL}"/>'
        b += para(pain, x+28, yT+hT-54, colw-42, 12, 'sans', INK, 1.5)[0]
        if i < 5: b += arrow(x+colw+1, yT+hT/2, x+colw+gap-1, yT+hT/2, INK, 1.2, 0.5, 5)
        # 下沉箭头
        b += arrow(x+colw/2, yT+hT-14, x+colw/2, yA+14, INK, 1.2, 0.35, 6, '3 4')
        # AI
        b += box(x, yA+16, colw, 170, SHEET, AI, 1.4, 1)
        b += icon(IC[ic], x+14, yA+30, 22, AI)
        b += T(name, x+44, yA+48, 17, 'serif', AI)
        b += para(ai, x+14, yA+78, colw-28, 13, 'sans', INK, 1.6)[0]
        b += label(cyc, x+14, yA+176, AI, 10.5)
        # human
        b += f'<rect x="{x}" y="{yA+198}" width="{colw}" height="84" fill="{WINE_T}"/>'
        b += f'<rect x="{x}" y="{yA+198}" width="4" height="84" fill="{WINE}"/>'
        b += icon(CUSTOM['approve-seal'], x+16, yA+212, 20, WINE)
        b += label('你拍板', x+44, yA+227, WINE, 10.5)
        b += para(human, x+16, yA+256, colw-28, 14, 'sansb', WINE)[0]
        if i < 5: b += arrow(x+colw+1, yA+101, x+colw+gap-1, yA+101, AI, 1.2, 0.6, 5)
    return b

# ---------- D2 数据流 / 数据清单 ----------
def d2():
    b = frame('02', '数据流与数据清单', '15 类数据从台账走到决策：先清洗、对齐、脱敏，再进系统；完备性不达标的不参与测算。')
    cols = [(72, '01 / 来源', INK), (392, '02 / 处理', INK), (712, '03 / 系统数据集', INK), (1072, '04 / AI 六环节', AI), (1352, '05 / 效能指标', INK)]
    for x, t, c in cols: b += label(t, x, 232, c if c != INK else CORAL, 12)
    src = ['销售台账 · 微信/纸质订单', '仓库台账 · 期初盘点', '采购合同 · 送货单', '供应商对账单（PDF/Excel）', '收付款登记 · 凭证', '驻厂跟岗计时 · 访谈', '公开行情（规划）']
    for i, s in enumerate(src):
        y = 256 + i*76
        b += box(72, y, 260, 60, SHEET, INK, 1, 0.2)
        b += T(s, 88, y+36, 15, 'sans', INK)
        b += arrow(334, y+30, 386, 520 if False else y+30, INK, 1, 0.35, 5)
    proc = [('采集', '系统内操作自然产生；历史 Excel 按固定列模板导入'), ('清洗', '去空格/全半角、日期统一、瓶↔箱换算、去重'),
            ('对齐', '以单号串联：采购→入库→应付→对账；批发→出库→应收'), ('脱敏', '对外只用「演示酒业」；电话、银行账号不进演示库'),
            ('完备性', '关键字段非空率 = 非空记录 ÷ 总记录'), ('补齐', '人工补录 → 规则推导 → 补不了标“数据不足”')]
    b += f'<rect x="392" y="256" width="280" height="{len(proc)*88+6}" fill="{STONE}" fill-opacity=".6"/>'
    for i, (k, v) in enumerate(proc):
        y = 256 + i*88
        b += label(f'{i+1:02d}', 408, y+30, CORAL, 11) + T(k, 440, y+32, 17, 'serif', INK)
        b += para(v, 408, y+56, 248, 12.5, 'sans', INK, 1.5, 0.8)[0]
    b += arrow(674, 520, 706, 520, INK, 1.5, 0.6, 7)
    groups = [('主数据', 'D01 经销商/企业客户 · D02 酒品 SKU · D03 供应商'), ('单据', 'D04 采购单 · D06 批发单 · D11 供应商对账单'),
              ('流水', 'D05 入库 · D07 出库 · D12 操作日志'), ('快照与结算', 'D08 库存快照 · D09 应付 · D10 应收'),
              ('基线', 'D13 人工耗时（当前全为演示假设）'), ('规划', 'D14 外部行情 · D15 一物一码（本期不做）')]
    for i, (k, v) in enumerate(groups):
        y = 256 + i*88
        dash = '4 4' if k == '规划' else None
        b += box(712, y, 320, 74, SHEET, INK, 1, 0.25, dash)
        b += icon(IC['database'], 726, y+14, 18, INK)
        b += T(k, 752, y+30, 16, 'serif', INK)
        b += para(v, 726, y+54, 296, 12.5, 'sans', INK, 1.5, 0.8)[0]
    b += label('TENANT 隔离 · 每条记录带 企业/品牌/仓库', 712, 800, INK, 10)
    b += arrow(1034, 520, 1066, 520, AI, 1.5, 0.8, 7)
    six = [('补货测算', 'replenish', '每周'), ('入库对单', 'inbound-match', '实时'), ('订单异常筛查', 'scan-search', '实时'),
           ('库存预警', 'stock-alert', '每日'), ('对账', 'reconcile', '每日'), ('日报起草', 'file-pen-line', '每日')]
    for i, (k, ic, cyc) in enumerate(six):
        y = 256 + i*88
        b += box(1072, y, 250, 74, AI_T, AI, 1.2, 1)
        b += icon(IC[ic], 1086, y+16, 22, AI)
        b += T(k, 1118, y+34, 16, 'serif', AI)
        b += label(f'更新周期 · {cyc}', 1118, y+58, AI, 10)
        b += arrow(1324, y+37, 1348, y+37, INK, 1, 0.35, 5)
    kpis = ['采购决策耗时 · 缺货次数 · 库存周转 · 预算占用', '入库差错率 · 到货—入库时长', '订货准备耗时 · 订单差错率 · 超信用单数',
            '库存可售天数 · 缺货率', '对账耗时 · 差异笔数 · 账龄', '人工节省工时 · 采纳率 / 人工改量率']
    for i, k in enumerate(kpis):
        y = 256 + i*88
        b += line(1352, y, 1352, y+74, CORAL, 2, 1)
        b += para(k, 1364, y+26, 168, 13, 'sans', INK, 1.55)[0]
    return b

# ---------- D3 人机协同分工 ----------
def d3():
    b = frame('03', '人机协同分工：自动执行 vs 人工复核', 'AI 只给备选方案；低风险、可撤回的动作自动执行，涉及钱、货、单据的一律由人拍板。')
    # left AI
    b += f'<rect x="72" y="232" width="440" height="520" fill="{AI_T}"/>'
    b += icon(IC['zap'], 96, 256, 28, AI) + T('自动执行', 136, 280, 26, 'serif', AI)
    b += label('LOW RISK · REVERSIBLE · 可撤回', 96, 312, AI, 11)
    autos = [('ai-stock-alert', 'stock-alert', '生成库存预警'), ('', 'file-pen-line', '起草经营日报'), ('', 'replenish', '计算补货建议（不下单）'),
             ('', 'scan-search', '标记异常订单（不拦截）'), ('', 'inbound-match', '生成入库差异表'), ('', 'reconcile', '生成对账差异清单')]
    for i, (_, ic, t) in enumerate(autos):
        y = 340 + i*64
        b += box(96, y, 392, 52, SHEET, AI, 1, 0.5)
        b += icon(IC[ic], 110, y+14, 24, AI) + T(t, 148, y+33, 16, 'sans', INK)
    # right human
    b += f'<rect x="1088" y="232" width="440" height="520" fill="{WINE_T}"/>'
    b += icon(CUSTOM['approve-seal'], 1112, 256, 28, WINE) + T('人工复核确认', 1152, 280, 26, 'serif', WINE)
    b += label('MONEY · GOODS · DOCUMENTS · 人拍板', 1112, 312, WINE, 11)
    hums = [('purchase', '审批采购单', '采购 / 老板'), ('inventory-warehouse', '确认入库', '仓库'), ('wholesale', '确认发货', '仓库 / 销售'),
            ('reconcile', '确认对账或发起争议', '财务'), ('roles', '登记收付款', '财务'), ('params', '修改约束与目标、重新测算', '老板 / 采购')]
    icmap = {'purchase': LU['package-plus'], 'inventory-warehouse': LU['warehouse'], 'wholesale': LU['truck'], 'reconcile': CUSTOM['reconcile'],
             'roles': lucide_body('shield-user'), 'params': LU['sliders-horizontal']}
    for i, (ic, t, who) in enumerate(hums):
        y = 340 + i*64
        b += box(1112, y, 392, 52, SHEET, WINE, 1, 0.5)
        b += icon(icmap[ic], 1126, y+14, 24, WINE) + T(t, 1164, y+33, 16, 'sansb', WINE)
        b += label(who, 1490, y+32, INK, 10, 'end')
    # middle: suggestion card
    cx = 560; cw = 480
    b += label('建议卡 · 一条 AI 建议长这样（示例 · 演示假设）', cx, 250, CORAL, 11)
    b += f'<rect x="{cx+6}" y="270" width="{cw}" height="330" fill="{CORAL}"/>'
    b += box(cx, 264, cw, 330, SHEET, INK, 1.5, 1)
    b += sparkle(cx+28, 296, 10, AI, AI_T) + label('AI · 补货测算 · 每周', cx+48, 301, AI, 11)
    b += T('向 供应商 A 补 120 箱', cx+24, 344, 24, 'serif', INK)
    b += T('预算占用 ¥4.3 万 · 建议 11/05 前到货', cx+24, 374, 16, 'sans', INK, opacity=0.8)
    rows = [('依据', '近 8 周日均出库 × 交期 + 安全库存 − 在途 − 现有'), ('约束', '周预算上限 · 仓容 · 最小起订量 · 箱规取整'), ('输入', 'D02 SKU · D07 出库 · D08 库存快照 · D04 在途')]
    for i, (k, v) in enumerate(rows):
        y = 404 + i*36
        b += line(cx+24, y, cx+cw-24, y, INK, 1, 0.12)
        b += label(k, cx+24, y+24, AI, 11) + T(v, cx+84, y+24, 13.5, 'sans', INK)
    b += line(cx+24, 512, cx+cw-24, 512, INK, 1, 0.12)
    b += box(cx+24, 530, 150, 44, SHEET, INK, 1, 0.5) + icon(LU['sliders-horizontal'], cx+36, 541, 20, INK) + T('改参数 · 重算', cx+64, 557, 14, 'sans', INK)
    b += f'<rect x="{cx+cw-204}" y="530" width="180" height="44" fill="{WINE}"/>' + T('采纳 → 生成草稿', cx+cw-114, 558, 15, 'sansb', PAPER, 'middle')
    b += arrow(512, 430, 552, 430, AI, 1.6, 0.9)
    b += arrow(cx+cw+8, 552, 1080, 552, WINE, 1.6, 0.9)
    # feedback loop
    b += f'<path d="M1300 752V790H300V760" fill="none" stroke="{INK}" stroke-opacity=".4" stroke-width="1.2" stroke-dasharray="4 4"/>'
    b += arrow(300, 772, 300, 756, INK, 1.2, 0.5, 6)
    b += T('回流复盘：采纳率、人工改量率、失效样本 → 每月调参', 800, 784, 13.5, 'sans', INK, 'middle', opacity=0.75)
    # red line
    b += f'<rect x="{cx}" y="624" width="{cw}" height="100" fill="{INK}"/>'
    b += label('红线 · NEVER AUTOMATED', cx+24, 652, AI_DARK, 11)
    b += T('AI 不自动审批、不自动下单、', cx+24, 684, 17, 'serif', PAPER)
    b += T('不改库存、不发货、不付款。', cx+24, 710, 17, 'serif', PAPER)
    return b

# ---------- D4 系统架构 ----------
def d4():
    b = frame('04', '系统架构：多品牌底座 + ai_assist 六环节', '基于开源 IOE（Django · MIT）二开：企业 → 品牌 → 仓库/渠道 层层隔离，AI 服务只读数据、只出建议。')
    L = 72; R = 1320; Wd = R-L
    def band(y, h, tag, title, fill=SHEET, color=INK, op=0.2):
        s = box(L, y, Wd, h, fill, color, 1, op)
        s += label(tag, L+16, y+26, CORAL if color == INK else color, 10.5)
        s += T(title, L+16, y+52, 17, 'serif', color)
        return s
    # roles
    y = 222
    b += label('角色', L, y+24, INK, 11)
    x = L+60
    for r in ['老板', '采购', '销售', '仓库', '财务', '稽核']:
        c, w = chip(r, x, y+6, INK, STONE, 14); b += c; x += w+10
    b += T('按 Membership 授权，只看到本企业数据', x+12, y+24, 13, 'sans', INK, opacity=0.65)
    # presentation
    y = 270
    b += band(y, 96, 'L1 / PRESENTATION', '表现层 · Django 模板 · 编辑风 UI')
    x = L+340
    for t in ['AI 工作台', '数据清单', '回测对比', '业务单据', '经营看板']:
        c, w = chip(t, x, y+34, INK, PAPER, 14, stroke=LINEC); b += c; x += w+12
    # application
    y = 382
    b += band(y, 230, 'L2 / APPLICATION', '应用层')
    blocks = [('inventory', 'IOE 原有能力', ['商品', '库存', '盘点', '收银', '会员', '报表'], INK, SHEET),
              ('b2b', 'To B 交易（新）', ['采购单', '批发单', '经销商', '应收应付', '对账单'], INK, SHEET)]
    bx = L+16
    for name, sub, items, c, f in blocks:
        b += box(bx, y+72, 300, 142, f, c, 1, 0.3)
        b += T(name, bx+16, y+102, 18, 'mono', INK) + T(sub, bx+16, y+126, 13, 'sans', INK, opacity=0.7)
        xx, yy = bx+16, y+144
        for it in items:
            cc, w = chip(it, xx, yy, INK, STONE, 12.5, 8, 24)
            if xx + w > bx+290: xx = bx+16; yy += 30; cc, w = chip(it, xx, yy, INK, STONE, 12.5, 8, 24)
            b += cc; xx += w+6
        bx += 316
    # ai_assist
    ax = bx; aw = R-16-ax
    b += box(ax, y+72, aw, 142, AI_T, AI, 1.4, 1)
    b += sparkle(ax+24, y+96, 9, AI, PAPER) + T('ai_assist', ax+42, y+102, 18, 'mono', AI) + T('规则/统计算法为主 · 可选 LLM 起草（无 key 降级模板）', ax+150, y+101, 12.5, 'sans', INK, opacity=0.75)
    six = [('补货测算', 'replenish', '周'), ('入库对单', 'inbound-match', '实时'), ('订单异常', 'scan-search', '实时'), ('库存预警', 'stock-alert', '日'), ('对账', 'reconcile', '日'), ('日报起草', 'file-pen-line', '日')]
    cw = (aw-32-5*8)/6
    for i, (k, ic, cyc) in enumerate(six):
        xx = ax+16+i*(cw+8)
        b += box(xx, y+120, cw, 82, SHEET, AI, 1, 0.6)
        b += icon(IC[ic], xx+cw/2-11, y+130, 22, AI)
        b += T(k, xx+cw/2, y+172, 13, 'sansb', AI, 'middle')
        b += label(cyc, xx+cw/2, y+192, AI, 9.5, 'middle')
    # tenancy
    y = 628
    b += band(y, 120, 'L3 / TENANCY', '多租户底座 · tenancy')
    nodes = [('企业 Tenant', '德鉴酒业 · 首批体验企业'), ('品牌 Brand', '多品牌并行'), ('仓库 Warehouse', '多仓库存'), ('渠道 Channel', '经销商 / 团购 / 门店 / 电商')]
    nx = L+300
    for i, (k, v) in enumerate(nodes):
        b += f'<rect x="{nx+4}" y="{y+30}" width="200" height="66" fill="{CORAL}"/>' if i == 0 else ''
        b += box(nx, y+26, 200, 66, SHEET if i else INK, INK, 1, 0.4)
        fg = PAPER if i == 0 else INK
        b += T(k, nx+14, y+52, 15, 'serif', fg) + T(v, nx+14, y+76, 12, 'sans', fg, opacity=0.8)
        if i < 3: b += arrow(nx+202, y+59, nx+236, y+59, INK, 1.3, 0.6, 6)
        nx += 240
    # data
    y = 764
    b += box(L, y, Wd, 52, STONE, INK, 1, 0.2)
    b += label('L4 / DATA', L+16, y+32, CORAL, 10.5)
    b += T('数据库 · 操作日志 OperationLog · seed_dejian 演示数据（对外以「演示酒业」脱敏）', L+120, y+32, 14, 'sans', INK)
    # right rail: boundary
    rx = 1344; rw = 184
    b += f'<rect x="{rx}" y="222" width="{rw}" height="594" fill="{INK}"/>'
    b += label('人机边界', rx+16, 252, AI_DARK, 11)
    steps = [('AI 读数据', AI_DARK), ('出建议 + 依据', AI_DARK), ('人改参数 · 重算', PAPER), ('人拍板', CORAL), ('生成草稿单据', PAPER), ('人确认执行', CORAL)]
    for i, (t, c) in enumerate(steps):
        yy = 296 + i*80
        b += f'<rect x="{rx+16}" y="{yy-14}" width="8" height="8" fill="{c if c != PAPER else MUTED}"/>'
        b += T(t, rx+34, yy-5, 15, 'sans', PAPER)
        if i < 5: b += line(rx+20, yy+2, rx+20, yy+56, PAPER, 1, 0.35)
    b += T('AI 不写库存', rx+16, 790, 13, 'sansb', AI_DARK)
    return b

def build(outline=True):
    import os
    textlib.MODE['outline'] = outline
    d = '../diagrams/' if outline else '../diagrams/editable/'
    os.makedirs(d, exist_ok=True)
    names = {'01-business-flow.svg': (d1, '业务流程：人工现状 vs AI 赋能'), '02-data-flow.svg': (d2, '数据流与数据清单'),
             '03-human-ai-split.svg': (d3, '人机协同分工'), '04-architecture.svg': (d4, '系统架构')}
    for k, (fn, t) in names.items(): open(d+k, 'w').write(svg(W, H, fn(), t))
    textlib.MODE['outline'] = True
    return names
if __name__ == '__main__':
    build(True); build(False); print('ok')
