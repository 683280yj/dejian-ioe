import re, os
import os
LUCIDE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lucide') + '/'
OUT = '../icons/'
HEAD = ('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" role="img" aria-label="{label}">'
        '<title>{label}</title>')

# (file, 中文, 语义色 ink|ai|wine, source, body-or-lucide-name)
CUSTOM = {
 'liquor-bottle': '<path d="M10 2h4v2.5h-4z"/><path d="M10.5 4.5V7c0 .9-.6 1.5-1.4 2C7.9 9.8 7 11 7 12.6V20a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-7.4c0-1.6-.9-2.8-2.1-3.6-.8-.5-1.4-1.1-1.4-2V4.5"/><path d="M9.5 13h5v5.5h-5z"/><path d="M12 14.6v2.3"/>',
 'liquor-jar': '<path d="M7 6.2C7 4.6 9.2 3 12 3s5 1.6 5 3.2"/><path d="M6.5 6.2h11"/><path d="M8.6 6.2c-2.6 1.4-4.6 4-4.6 7.3C4 17.6 6.4 21 9.5 21h5c3.1 0 5.5-3.4 5.5-7.5 0-3.3-2-5.9-4.6-7.3"/><path d="M12 10.5l2.5 2.5-2.5 2.5-2.5-2.5z"/><path d="M7 19.5h10"/>',
 'reconcile': '<rect x="2.5" y="3" width="8" height="11" rx="1"/><rect x="13.5" y="10" width="8" height="11" rx="1"/><path d="M5 6.5h3M5 9.5h3M16 13.5h3M16 16.5h3"/><path d="M13 4.5h3.5a2 2 0 0 1 2 2V8"/><path d="M16.8 6.5l1.7 1.6 1.7-1.6"/><path d="M11 19.5H7.5a2 2 0 0 1-2-2V16"/><path d="M7.2 17.5l-1.7-1.6-1.7 1.6"/>',
 'replenish': '<rect x="2.5" y="10" width="12" height="11" rx="1"/><path d="M2.5 14h12"/><path d="M7 10v4M10 10v4"/><path d="M19 21V5"/><path d="M16 8l3-3 3 3"/><path d="M6 17.5h5"/>',
 'inbound-match': '<path d="M12 9V4a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h4"/><path d="M6 6.5h3M6 9.5h3M6 12.5h2"/><rect x="11" y="12" width="10" height="9" rx="1"/><path d="M11 15h10"/><path d="M13.8 18.1l1.5 1.4 2.9-2.9"/><path d="M14.5 6.5h4.5v3"/><path d="M17.3 8l1.7 1.7 1.7-1.7"/>',
 'stock-alert': '<path d="M2.5 21V9.2a1 1 0 0 1 .6-.9l8.5-4.2a1 1 0 0 1 .8 0l8.5 4.2a1 1 0 0 1 .6.9V21"/><path d="M1.5 21h21"/><path d="M12 10v5"/><path d="M12 18h.01"/>',
 'backtest': '<path d="M3 3v17a1 1 0 0 0 1 1h17"/><path d="M7 13l3.5-4 3 2.5L19 6"/><path d="M19 6v2.8M19 6h-2.8"/><path d="M7 17.5l4-1.5 3.5 1 4.5-2" stroke-dasharray="1.2 2.6"/>',
 'ai-workbench': '<rect x="2" y="3.5" width="20" height="13.5" rx="1"/><path d="M8 21h8M12 17v4"/><path d="M12 6.5l1.1 2.6 2.6 1.1-2.6 1.1-1.1 2.6-1.1-2.6-2.6-1.1 2.6-1.1z"/><path d="M18 6.5v.01"/>',
 'approve-seal': '<circle cx="12" cy="4.8" r="2.3"/><path d="M10.6 6.6L9.6 11h4.8l-1-4.4"/><path d="M4 12a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v3H4z"/><path d="M4 18.5h16"/><path d="M8 21.5h8"/>',
 'ai-handoff': '<path d="M6 7l1.1 2.6 2.6 1.1-2.6 1.1L6 14.4l-1.1-2.6-2.6-1.1 2.6-1.1z"/><path d="M10.8 10.7h4"/><path d="M13 8.7l2 2-2 2"/><circle cx="19" cy="7.5" r="2.2"/><path d="M15.8 16.5v-.8a3.2 3.2 0 0 1 6.4 0v.8"/><path d="M2.5 20h19"/><path d="M15.5 20v-1.5M22 20v-1.5" stroke-opacity="0"/>',
}
ICONS = [
 ('product-liquor', '商品 / 白酒瓶', 'ink', 'custom', 'liquor-bottle'),
 ('liquor-jar', '酒坛（品牌/窖藏）', 'ink', 'custom', 'liquor-jar'),
 ('inventory-warehouse', '库存 / 仓库', 'ink', 'lucide', 'warehouse'),
 ('purchase', '采购', 'ink', 'lucide', 'package-plus'),
 ('wholesale', '销售 / 批发', 'ink', 'lucide', 'truck'),
 ('customer-b2b', '经销商 / 企业客户', 'ink', 'lucide', 'building-2'),
 ('reconcile', '对账', 'ink', 'custom', 'reconcile'),
 ('stocktake', '盘点', 'ink', 'lucide', 'clipboard-check'),
 ('report', '报表', 'ink', 'lucide', 'chart-column'),
 ('brand-switch', '品牌切换 / 多品牌', 'ink', 'lucide', 'layers'),
 ('roles', '角色权限', 'ink', 'lucide', 'shield-user'),
 ('ai-workbench', 'AI 工作台', 'ai', 'custom', 'ai-workbench'),
 ('ai-replenish', '补货测算', 'ai', 'custom', 'replenish'),
 ('ai-inbound-match', '入库对单', 'ai', 'custom', 'inbound-match'),
 ('ai-anomaly', '异常筛查', 'ai', 'lucide', 'scan-search'),
 ('ai-stock-alert', '库存预警', 'ai', 'custom', 'stock-alert'),
 ('ai-daily-report', '日报起草', 'ai', 'lucide', 'file-pen-line'),
 ('data-catalog', '数据清单', 'ink', 'lucide', 'database'),
 ('backtest', '回测 / 仿真', 'ai', 'custom', 'backtest'),
 ('params-recalc', '参数调整 / 重算', 'ink', 'lucide', 'sliders-horizontal'),
 ('auto-exec', '自动执行（低风险）', 'ai', 'lucide', 'zap'),
 ('human-approve', '人工复核 / 拍板', 'wine', 'custom', 'approve-seal'),
 ('ai-to-human', 'AI → 人 交接', 'wine', 'custom', 'ai-handoff'),
 ('explain-basis', '依据 / 可解释', 'ai', 'lucide', 'book-open-text'),
 ('update-cycle', '更新周期', 'ink', 'lucide', 'calendar-sync'),
 ('risk-boundary', '风险 / 适用边界', 'ink', 'lucide', 'shield-alert'),
]

def lucide_body(name):
    s = open(LUCIDE + name + '.svg').read()
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    body = re.search(r'<svg[^>]*>(.*)</svg>', s, re.S).group(1)
    return re.sub(r'\s+', ' ', body).strip()

def build():
    os.makedirs(OUT, exist_ok=True)
    out = []
    for fn, label, role, src, key in ICONS:
        body = CUSTOM[key] if src == 'custom' else lucide_body(key)
        body = body.replace('<path d="M15.5 20v-1.5M22 20v-1.5" stroke-opacity="0"/>', '')
        svg = HEAD.format(label=label) + body + '</svg>\n'
        if src == 'lucide':
            svg = '<!-- Based on Lucide "%s" (ISC License, lucide.dev); stroke-width adjusted to 1.5 -->\n' % key + svg
        else:
            svg = '<!-- 德鉴 design-assets · original icon (MIT, same as project) -->\n' + svg
        open(OUT + fn + '.svg', 'w').write(svg)
        out.append((fn, label, role, src, key, body))
    return out

if __name__ == '__main__':
    print(len(build()))
