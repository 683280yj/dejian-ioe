"""演示案例企业档案：贵州德鉴酒业（集团）有限公司。

平台面向任意酒企；本档案仅作评委展示用的首个案例租户数据。
全部销量/价格/库存天数均为「演示假设」，不代表真实经营数据。
商品名称对齐公开产品线称谓（习酒窖藏1988/金钻/银质；德鉴酱香珍藏15/年份窖藏10/柔雅双支礼盒）。
"""
import os
import secrets

TENANT = dict(code='dejian', name='贵州德鉴酒业（集团）有限公司', short_name='德鉴酒业',
              industry='白酒 · 酱香', region='贵州省遵义市习水县杉王街道希望社区红城佳园3-3-1号', is_demo=True,
              description='法定代表人：蔡艺。经营：代理贵州习酒 + 自有德鉴酒。')

BRANDS = [
    dict(code='JX', name='贵州习酒', is_own=False, positioning='代理品牌'),
    dict(code='RY', name='德鉴酒', is_own=True, positioning='自有品牌'),
]

WAREHOUSES = [
    dict(code='GY', name='习水总仓', address='贵州省遵义市习水县', capacity_units=9000, is_default=True),
    dict(code='CQ', name='贵阳前置仓', address='贵阳市观山湖区', capacity_units=3000, is_default=False),
]

# kind, 名称, 最低成交价比例(渠道限价), 实际成交折扣, 份额, 每单瓶数范围
CHANNELS = [
    dict(code='DEALER', name='经销商', kind='DEALER', min_price_ratio=0.70, discount=0.78, share=0.40, lot=(12, 60)),
    dict(code='GROUP', name='团购企业', kind='GROUP', min_price_ratio=0.85, discount=0.90, share=0.20, lot=(6, 24)),
    dict(code='STORE', name='直营门店', kind='STORE', min_price_ratio=0.95, discount=1.00, share=0.25, lot=(1, 4)),
    dict(code='ONLINE', name='电商旗舰店', kind='ONLINE', min_price_ratio=0.88, discount=0.92, share=0.15, lot=(1, 3)),
]

SUPPLIERS = [
    dict(key='JX', name='黔北星禾酒类供应链有限公司', contact_person='王经理', phone='0851-0000001', lead=12, lead_sd=3, moq=120),
    dict(key='RY', name='德鉴酒业灌装车间', contact_person='李主管', phone='0851-0000002', lead=7, lead_sd=1.5, moq=60),
]

# sku, 品牌, 名称, 规格, 售价, 成本, 日均基线(瓶), 箱规, 当前可售天数, 送货单写法
# 德鉴自有三款 = 企业工作簿三档包装成品（见 ai_assist/case_data.py）：售价取表内各笔「销售额÷瓶数」中位数，
# 箱规取表内「瓶/箱」，成本 = 基酒折算成本（消耗率×采购单价），日均基线 = 表内最近 365 天日均出库瓶数。
# 习酒代理三款：表内没有，沿用演示目录价格，历史为生成的演示数据。
from ai_assist import case_data as _C  # noqa: E402


def _dj(sku, name, tier, cover, dn):
    n = _C.per_box(tier)
    return (sku, 'RY', name, f'{_C.tier_label(tier)} · 53° 500ml*{n}瓶/箱', _C.tier_price(tier), _C.base_cost_per_bottle(tier),
            round(_C.daily_bottles_last_year(tier), 1), n, cover, dn)


SKUS = [
    ('XJ-53-500-1988', 'JX', '贵州习酒·窖藏1988', '53° 500ml*6瓶/箱', 568, 485, 8.0, 6, 9, '习酒窖藏1988 53度'),
    ('XJ-53-500-JZ', 'JX', '贵州习酒·金钻习酒', '53° 500ml*6瓶/箱', 268, 220, 14.0, 6, 26, '金钻习酒 53度'),
    ('XJ-53-500-YZ', 'JX', '贵州习酒·银质习酒', '53° 500ml*6瓶/箱', 168, 136, 10.0, 6, 5, '银质习酒 53度'),
    _dj('DJ-53-500-ZC', '德鉴·酱香珍藏15', '中端', 30, '德鉴酱香珍藏15'),
    _dj('DJ-53-500-NF', '德鉴·年份窖藏10', '低端', 7, '德鉴年份窖藏10'),
    _dj('DJ-53-500-LH', '德鉴·柔雅双支礼盒', '高端', 40, '德鉴柔雅双支礼盒'),
]
DESCRIPTIONS = {
    'XJ-53-500-1988': '习酒窖藏系列经典款，53度酱香型，商务宴请主力。',
    'XJ-53-500-JZ': '金钻习酒，53度酱香型，宴席与团购常用。',
    'XJ-53-500-YZ': '银质习酒，53度酱香型，日常流通款。',
    'DJ-53-500-ZC': '德鉴自有品牌·中端标准款（包装款），53度酱香型，团购与经销主力。',
    'DJ-53-500-NF': '德鉴自有品牌·低端流通款（光瓶），53度酱香型，乡镇流通与日常复购。',
    'DJ-53-500-LH': '德鉴自有品牌·高端礼盒款（包装款），53度酱香型，企事业团购与节庆礼赠。',
}
# 采购端原料：基酒原料（待包装），库存计量单位为「斤」（1 吨 = 2000 斤）
RAW = dict(sku=_C.RAW_SKU, brand='RY', name='基酒原料（待包装）', category='原料', spec='散装基酒 · 计量单位：斤',
           price=_C.base_price_per_jin(), cost=_C.base_price_per_jin(),
           description='采购端统一原料，经加工、灌装、包装后形成三档成品。')
SLOW_SKU = None                 # 演示目录无滞销款；不再人为制造滞销样例
SLOW_STOCK = 180

# 白酒季节性：春节(1–2月)、中秋国庆(9–10月)旺季
SEASON = {1: 1.6, 2: 1.3, 3: 0.7, 4: 0.75, 5: 0.8, 6: 0.8, 7: 0.7, 8: 0.85, 9: 1.35, 10: 1.2, 11: 0.9, 12: 1.15}
WEEKDAY = {0: 0.9, 1: 0.9, 2: 0.95, 3: 1.0, 4: 1.2, 5: 1.25, 6: 0.8}
HISTORY_DAYS = 550  # 约 18 个月：回测 180 天前仍有完整一年用于季节指数

DEALERS = [
    dict(name='贵阳云酒商贸', phone='19900000001', level='A'),
    dict(name='重庆山城酒行', phone='19900000002', level='B'),
    dict(name='成都蓉城名酒坊', phone='19900000003', level='B'),
]
GROUP_BUYERS = [
    dict(name='黔城建工集团', phone='19900000011'),
    dict(name='筑城律师事务所', phone='19900000012'),
]

# 登录名保持 dj_*（测试依赖）；展示名按案例企业岗位（蔡艺/张业务/李仓管）
USERS = [
    ('dj_boss', 'boss', '蔡艺', '系统管理员'),
    ('dj_purchase', 'purchaser', '采购·陈', '采购主管'),
    ('dj_sales', 'sales', '张业务', '团购与习酒运营经理'),
    ('dj_warehouse', 'warehouse', '李仓管', '习水总仓主管'),
    ('dj_finance', 'finance', '财务·周', '会计'),
    ('dj_audit', 'auditor', '稽核·吴', '内审'),
]
DEMO_PASSWORD = os.environ.get('DEMO_PASSWORD') or secrets.token_urlsafe(24)

# 人工现状基线（演示假设，需企业访谈后替换）
BASELINE = {  # 人工补货基线（演示假设），供 backtest 对照
    'manual_reorder_factor': 1.2,        # 上月销量×1.2
    'manual_review_days': 30,            # 每月下一次常规补货单
    'manual_emergency_cover_days': 7,    # 低于 7 天可售时紧急补货
}


# ---------------------------------------------------------------- To B 交易（合成演示数据）
# 具名经销商为生成的演示数据（工作簿只有匿名客户分组）；电话为演示占位号。
B2B_CUSTOMERS = [
    # code, name, kind, region, contact, credit_limit, address, 账期(天)
    ('DL-GY-001', '贵阳黔汇名酒供应链有限公司', 'DISTRIBUTOR', '贵州·贵阳', '王经理', 500000, '贵阳市观山湖区', 30),
    ('DL-ZY-002', '遵义星河名烟名酒连锁', 'DISTRIBUTOR', '贵州·遵义', '周经理', 350000, '遵义市汇川区', 30),
    ('DL-CQ-003', '重庆山城国韵酒业商贸', 'DISTRIBUTOR', '重庆·渝中', '陈总', 200000, '重庆市渝中区', 45),
    ('DL-CD-004', '成都锦城政企团购中心', 'ENTERPRISE', '四川·成都', '刘经理', 400000, '成都市锦江区', 45),
    ('DL-XS-005', '习水鰼部名酒荟', 'RETAILER', '贵州·遵义习水', '杨店长', 250000, '习水县杉王街道', 30),
    ('DL-KM-006', '昆明滇池名品酒业', 'DISTRIBUTOR', '云南·昆明', '赵经理', 300000, '昆明市西山区', 30),
]

# 以下具名经销商订单为生成的演示数据（工作簿里没有习酒代理款），只含习酒三款；德鉴三档订单全部来自工作簿。
# date, 客户序号, 目标状态, 备注, 明细[(sku, qty)], 回款比例（仅已发货/已签收有应收）, 折让后总额(None=按 1.5% 折让)
B2B_WHOLESALE = [
    ('2025-03-18', 0, 'COMPLETED', '春季品鉴团购', [('XJ-53-500-1988', 120), ('XJ-53-500-JZ', 60)], 1, None),
    ('2025-07-09', 1, 'SHIPPED', '遵义团购补货', [('XJ-53-500-JZ', 180), ('XJ-53-500-YZ', 60)], 0.5, None),
    ('2025-11-21', 2, 'APPROVED', '重庆政企团购，按账期结算', [('XJ-53-500-1988', 240), ('XJ-53-500-JZ', 90)], 0, None),
    ('2026-02-12', 3, 'APPROVED', '成都春节团购', [('XJ-53-500-1988', 120), ('XJ-53-500-YZ', 60)], 0, None),
    ('2026-10-16', 4, 'SUBMITTED', '习水本地品鉴会备货', [('XJ-53-500-JZ', 96), ('XJ-53-500-YZ', 48)], 0, None),
    ('2026-10-24', 5, 'DRAFT', '昆明年末团购方案', [('XJ-53-500-JZ', 72), ('XJ-53-500-1988', 24)], 0, None),
]

# date, 供应商 key, 目标状态, 备注, 明细[(sku, qty)]（单价=成本价）, 付款比例（仅已入库有应付）
# 未入库的单据会计入 AI 在途量，所以只放在可售天数充足的 SKU 上，避免冲掉补货演示。
B2B_PURCHASES = [  # 习酒代理款进货（生成的演示数据）；德鉴原料采购来自工作簿
    ('2026-08-20', 'JX', 'RECEIVED', '中秋前备货', [('XJ-53-500-1988', 120), ('XJ-53-500-JZ', 180)], 0.5),
    ('2026-10-10', 'JX', 'RECEIVED', '银质补货', [('XJ-53-500-YZ', 120)], 0),
    ('2026-10-22', 'JX', 'APPROVED', '窖藏1988 年末备货', [('XJ-53-500-1988', 60)], 0),
    ('2026-10-25', 'JX', 'SUBMITTED', '银质补货（待审批）', [('XJ-53-500-YZ', 60)], 0),
    ('2026-10-26', 'JX', 'DRAFT', '金钻补货草稿（人工）', [('XJ-53-500-JZ', 60)], 0),
]
# 待对账：JX 10 月（含 10-10 入库单）；基酒供应商 S01 2026 年 8 月已确认
B2B_STATEMENTS = [
    ('JX', '2026-10-01', '2026-10-31', 'DRAFT'),
    ('供应商S01', '2026-08-01', '2026-08-31', 'CONFIRMED'),
]
