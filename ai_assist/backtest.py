"""回测 / 仿真：AI 策略 vs 人工基线（演示数据 + 演示假设）。

库存部分是逐日滚动仿真（walk-forward）：每天只用“截至前一天”的历史做决策，避免看到未来。
  · 两种策略面对同一条真实（演示）需求序列、同一组随机交期、同一个期初库存；
  · 缺货 = 当天需求 > 在库，缺口按损失销售计（白酒客户多半转买别家）；
  · 人工基线：每 30 天按“上月销量 × 1.2”补到目标；可售 < 7 天且无在途时紧急补半个月；
  · AI 策略：每 R 天 (R,S) 补到 S = d̂(L+R) + z·σ_LT，d̂ = 28 日均 × 季节指数。
仅后端/命令行使用：python manage.py ai_backtest
"""
from __future__ import annotations

import datetime as dt
import math
import random
import statistics

from . import algorithms as A
from . import data
from .demo_profile import BASELINE

DEFAULTS = {
    'sim_days': 180, 'service_level': 0.95, 'review_days': 7, 'forecast_window': 28,
    'max_cover_days': 60, 'manual_reorder_factor': BASELINE['manual_reorder_factor'],
    'manual_review_days': BASELINE['manual_review_days'], 'manual_emergency_cover_days': BASELINE['manual_emergency_cover_days'],
}
PARAM_LABELS = {
    'sim_days': '回测天数', 'service_level': 'AI 目标服务水平', 'review_days': 'AI 盘点周期 R(天)',
    'forecast_window': 'AI 移动平均窗口(天)', 'max_cover_days': '单品最多备货天数',
    'manual_reorder_factor': '人工：上月销量 × 系数', 'manual_review_days': '人工：下单间隔(天)',
    'manual_emergency_cover_days': '人工：紧急补货触发(可售天数)',
}


def _clean(series):
    """清洗：单日销量 > Q3 + 6·IQR（且 > 3 倍中位数）视为录错/异常大单，替换为中位数。返回(序列, 剔除数)。"""
    nz = [v for v in series if v > 0]
    if len(nz) < 20:
        return list(series), 0
    q = statistics.quantiles(nz, n=4)
    med = statistics.median(nz)
    cap = max(q[2] + 6 * (q[2] - q[0]), 3 * med)
    out, n = [], 0
    for v in series:
        if v > cap:
            out.append(med)
            n += 1
        else:
            out.append(v)
    return out, n


def _round(qty, case, moq):
    return A.round_up_to(qty, case or 1, moq or 0)


def _simulate(sku, demand, warm, lead_draws, policy, P, z):
    """demand: 全序列(含 warm 天预热)；从 index=warm 开始仿真。返回指标 dict。"""
    L, case, moq, cost, price = sku['L'], sku['case'], sku['moq'], sku['cost'], sku['price']
    n = len(demand)
    first = demand[warm - 28:warm]
    stock = round(sum(first) / 28 * 30)  # 期初：30 天可售（两种策略相同）
    pipeline = []  # (到货日 index, 数量)
    last_order_day = -10 ** 9
    lost = served = dem_total = 0.0
    stockout_days = orders = 0
    inv_value_sum = 0.0
    k_order = 0
    for t in range(warm, n):
        arrived = sum(q for d, q in pipeline if d == t)
        pipeline = [(d, q) for d, q in pipeline if d != t]
        stock += arrived
        dem = demand[t]
        sold = min(stock, dem)
        stock -= sold
        served += sold
        dem_total += dem
        if dem > sold:
            lost += dem - sold
            stockout_days += 1
        inv_value_sum += stock * cost
        hist = demand[:t + 1]  # 收盘后决策：只用到今天为止的数据
        pos = stock + sum(q for _, q in pipeline)
        qty = 0
        if policy == 'manual':
            last30 = sum(hist[-30:])
            avg = last30 / 30
            if t - last_order_day >= P['manual_review_days']:
                target = last30 * P['manual_reorder_factor'] + avg * L * 0  # 经验做法：不显式考虑交期
                qty = max(0.0, target - pos) if target > pos else 0
                if qty > 0 or t - last_order_day >= P['manual_review_days']:
                    last_order_day = t
            elif avg > 0 and stock / avg < P['manual_emergency_cover_days'] and not pipeline:
                qty = avg * 15
        else:
            if (t - warm) % P['review_days'] == 0:
                ma = A.moving_average(hist, P['forecast_window'])
                sigma = A.std_dev(hist, max(P['forecast_window'], 56))
                si = 1.0
                if len(hist) >= 365:
                    day = sku['end'] - dt.timedelta(days=n - 1 - t)
                    monthly = data.monthly_daily_avg(hist[-365:], day)
                    si = A.seasonal_ratio(monthly, day.month, (day + dt.timedelta(days=L)).month)
                dhat = ma * si
                sig_lt = math.sqrt(L * sigma ** 2 + dhat ** 2 * sku['sL'] ** 2)
                S = dhat * (L + P['review_days']) + z * sig_lt
                cap = P['max_cover_days'] * dhat
                if pos < S:
                    qty = min(S - pos, max(0.0, cap - pos))
        q = _round(qty, case, moq) if qty > 0 else 0
        if q > 0:
            lt = lead_draws[k_order % len(lead_draws)]
            k_order += 1
            pipeline.append((t + lt, q))
            orders += 1
    days = n - warm
    avg_inv_value = inv_value_sum / days
    cogs_daily = served * cost / days
    return {
        'demand': dem_total, 'served': served, 'lost': lost, 'stockout_days': stockout_days, 'days': days,
        'orders': orders, 'avg_inv_value': avg_inv_value, 'cogs_daily': cogs_daily,
        'lost_margin': lost * (price - cost), 'end_stock': stock,
    }


def run_backtest(tenant, params: dict | None = None, as_of: dt.date | None = None) -> dict:
    P = dict(DEFAULTS)
    for k, v in (params or {}).items():
        if k in P and v not in (None, ''):
            P[k] = type(DEFAULTS[k])(v)
    P['sim_days'] = int(min(max(P['sim_days'], 30), 180))
    as_of = as_of or data.today()
    end = as_of - dt.timedelta(days=1)
    products = data.products_for(tenant)
    pids = [p.id for p in products]
    terms = data.primary_terms(tenant, pids)
    total_days = P['sim_days'] + 365
    warm = total_days - P['sim_days']
    series = data.daily_demand(tenant, pids, end, total_days)
    z = A.z_for_service_level(P['service_level'])
    per_sku, cleaned_total = [], 0
    agg = {'manual': {}, 'ai': {}}
    for prod in products:
        term = terms.get(prod.id)
        if term is None:
            continue
        dem, ncl = _clean(series[prod.id])
        cleaned_total += ncl
        if sum(dem[warm:]) <= 0:
            continue
        rng = random.Random(f"{prod.barcode}-lead")
        draws = [max(1, round(rng.gauss(term.lead_time_days, float(term.lead_time_sd_days)))) for _ in range(200)]
        sku = {'L': term.lead_time_days, 'sL': float(term.lead_time_sd_days), 'case': prod.case_size, 'moq': term.moq_units,
               'cost': float(term.unit_cost), 'price': float(prod.price), 'end': end}
        res = {pol: _simulate(sku, dem, warm, draws, pol, P, z) for pol in ('manual', 'ai')}
        per_sku.append({'sku': prod.barcode, 'name': prod.name, 'manual': _metrics(res['manual']), 'ai': _metrics(res['ai'])})
        for pol in res:
            for k, v in res[pol].items():
                agg[pol][k] = agg[pol].get(k, 0) + v
    inv = {pol: _metrics(agg[pol], n_sku=len(per_sku)) for pol in agg}
    headline = _headline(inv)
    return {
        'label': '回测/仿真（演示数据 + 演示假设，非真实经营数据）',
        'as_of': str(as_of), 'period': f"{end - dt.timedelta(days=P['sim_days'] - 1)} ~ {end}",
        'params': P, 'param_labels': PARAM_LABELS, 'sku_count': len(per_sku), 'cleaned_points': cleaned_total,
        'inventory': inv, 'per_sku': per_sku, 'headline': headline,
        'method': [
            '逐日滚动仿真：每天只用截至当天收盘的历史决定是否下单，第二天起才看到新需求（无未来信息）。',
            '两种策略共用：同一需求序列（已清洗）、同一组交期随机抽样（按供应商交期均值/标准差，固定种子）、同一期初库存(30天可售)。',
            '人工基线（演示假设）：每 %d 天下单，补到“近30天销量×%.1f”；可售<%d 天且无在途时紧急补 15 天量。' % (
                P['manual_review_days'], P['manual_reorder_factor'], P['manual_emergency_cover_days']),
            'AI 策略：每 %d 天 (R,S) 补到 S = d̂·(L+R) + z·√(L·σ²+d̂²·σ_L²)，z=%.2f（服务水平 %.0f%%），d̂ = %d日均×季节指数，单品备货≤%d天。' % (
                P['review_days'], z, P['service_level'] * 100, P['forecast_window'], P['max_cover_days']),
            '缺货率 = 损失销量 / 总需求；资金占用 = 日均在库成本；周转天数 = 日均在库成本 / 日均销货成本。',
        ],
    }


def _metrics(r, n_sku=1):
    dem = r.get('demand', 0) or 0
    return {
        '缺货率': round(r['lost'] / dem, 4) if dem else 0.0,
        '满足率': round(r['served'] / dem, 4) if dem else 1.0,
        '缺货天数占比': round(r['stockout_days'] / (r['days'] or 1), 4),
        '平均资金占用': round(r['avg_inv_value'], 0),
        '库存周转天数': round(r['avg_inv_value'] / r['cogs_daily'], 1) if r['cogs_daily'] else None,
        '下单次数': int(r['orders']),
        '损失毛利': round(r['lost_margin'], 0),
        '总需求': int(dem), '损失销量': int(r['lost']),
    }


def _headline(inv):
    m, a = inv['manual'], inv['ai']
    h = [
        {'指标': '缺货率', '人工基线': m['缺货率'], 'AI': a['缺货率'], 'fmt': 'pct', '更好': 'lower'},
        {'指标': '库存周转天数', '人工基线': m['库存周转天数'], 'AI': a['库存周转天数'], 'fmt': 'days', '更好': 'lower'},
        {'指标': '平均资金占用(元)', '人工基线': m['平均资金占用'], 'AI': a['平均资金占用'], 'fmt': 'money', '更好': 'lower'},
        {'指标': '损失毛利(元)', '人工基线': m['损失毛利'], 'AI': a['损失毛利'], 'fmt': 'money', '更好': 'lower'},
    ]
    h.append({'指标': '下单次数', '人工基线': m['下单次数'], 'AI': a['下单次数'], 'fmt': 'int', '更好': None})
    for row in h:
        b, x = row['人工基线'], row['AI']
        row['变化'] = round((x - b) / b, 3) if b not in (None, 0) and x is not None else None
    return h
