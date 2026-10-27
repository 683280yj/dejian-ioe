"""补货测算：(R, S) 周期盘点 + 安全库存 + EOQ 参考 + 预算/库容约束贪心分配。"""
from __future__ import annotations

import datetime as dt
import math

from .. import algorithms as A
from .. import data
from .base import Param, RunResult, Workflow, yuan


class Replenish(Workflow):
    key = 'replenish'
    label = '补货测算'
    cycle = 'week'
    role = 'purchaser'
    objective = '在目标服务水平下，使预算内的预计缺货损失最小、库存资金占用不超标'
    pain_point = '采购凭经验按“上月销量×1.2”下单，旺季断货、淡季压货；每周人工翻表测算约 3 小时'
    params = [
        Param('service_level', '目标服务水平(不缺货概率)', 'pct', 0.95, '目标', '决定安全库存的 z 值', 0.5, 0.999),
        Param('budget', '本期采购预算(元)', 'money', 300000, '约束', '超出时按“避免缺货毛利/资金”优先级裁剪', 0, 1e9),
        Param('max_cover_days', '单品最多备货天数', 'int', 60, '约束', '业务规则：防止压货占用资金', 7, 365),
        Param('respect_capacity', '遵守仓库库容', 'bool', True, '约束', '总在库+在途+本次补货 ≤ 各仓库容之和'),
        Param('review_days', '盘点/下单周期 R(天)', 'int', 7, '算法', '每 R 天测算一次', 1, 31),
        Param('forecast_window', '需求移动平均窗口(天)', 'int', 28, '算法', '', 7, 120),
        Param('use_seasonality', '使用季节指数(春节/中秋)', 'bool', True, '算法', '用去年同月日均/全年日均修正'),
        Param('season_shrink', '季节指数收缩系数', 'pct', 0.5, '算法', '1=完全采用历史季节指数，0=不用；小样本时取 0.5 更稳', 0, 1),
        Param('order_cost', '每次下单固定成本(元)', 'money', 300, '算法', 'EOQ 参考用：运费+人工', 0, 1e6),
        Param('holding_rate', '年库存持有费率', 'pct', 0.12, '算法', 'EOQ 参考用：资金成本+仓储', 0.01, 1),
    ]

    def run(self, ctx):
        p, tenant = ctx.params, ctx.tenant
        products = data.products_for(tenant, ctx.brand)
        pids = [x.id for x in products]
        hist = data.daily_demand(tenant, pids, ctx.as_of - dt.timedelta(days=1), 365)  # 截至昨日的完整日
        stock = data.on_hand(tenant, pids)
        terms = data.primary_terms(tenant, pids)
        transit = data.on_order(tenant)
        z = A.z_for_service_level(p['service_level'])
        R = p['review_days']
        rows, items = [], []
        for prod in products:
            term = terms.get(prod.id)
            if term is None:
                continue
            series = hist[prod.id]
            L = term.lead_time_days
            sL = float(term.lead_time_sd_days)
            ma = A.moving_average(series, p['forecast_window'])
            sigma = A.std_dev(series, max(p['forecast_window'], 56))
            target_month = (ctx.as_of + dt.timedelta(days=L)).month
            si = 1.0
            if p['use_seasonality']:
                monthly = data.monthly_daily_avg(series, ctx.as_of - dt.timedelta(days=1))
                si = A.seasonal_ratio(monthly, ctx.as_of.month, target_month, p['season_shrink'])
            dhat = ma * si
            sigma_lt = math.sqrt(L * sigma ** 2 + (dhat ** 2) * (sL ** 2))
            ss = z * sigma_lt
            rop = dhat * L + ss
            S = dhat * (L + R) + ss
            on_hand = stock.get(prod.id, 0)
            pos = on_hand + transit.get(prod.id, 0)
            cap_units = max(0, p['max_cover_days'] * dhat - pos)
            annual = sum(series)
            unit_cost = float(term.unit_cost)
            e = A.eoq(annual, p['order_cost'], unit_cost, p['holding_rate'])
            need = max(0.0, S - pos)
            raw = 0.0
            if pos < S:
                raw = min(max(need, e), cap_units)
            qty = A.round_up_to(raw, prod.case_size or 1, term.moq_units)
            cover_days = on_hand / dhat if dhat > 0 else None
            shortage = max(0.0, dhat * (L + R) - pos)
            margin = float(prod.price) - unit_cost
            row = dict(prod=prod, term=term, L=L, sL=sL, ma=ma, si=si, dhat=dhat, sigma=sigma, sigma_lt=sigma_lt,
                       ss=ss, rop=rop, S=S, on_hand=on_hand, transit=transit.get(prod.id, 0), pos=pos, eoq=e,
                       need=need, qty=qty, cover_days=cover_days, shortage=shortage, unit_cost=unit_cost, margin=margin,
                       cap_units=cap_units)
            rows.append(row)
            if qty > 0:
                items.append(A.KnapsackItem(key=str(prod.id), cost=qty * unit_cost,
                                            value=margin * (shortage + 0.1 * qty) + 1e-6, units=qty,
                                            min_units=max(term.moq_units, 0), step=prod.case_size or 1))
        capacity = None
        cap_total = data.warehouse_capacity(tenant)
        stock_total = data.total_stock(tenant) + sum(transit.values())
        if p['respect_capacity'] and cap_total:
            capacity = max(cap_total - stock_total, 0)
        alloc = A.budget_allocate(items, p['budget'], capacity)

        suggestions = []
        total_amount = 0.0
        cut_count = 0
        for r in rows:
            prod, term = r['prod'], r['term']
            approved = alloc.get(str(prod.id), 0)
            if r['qty'] == 0 and r['pos'] >= r['rop']:
                continue
            amount = approved * r['unit_cost']
            total_amount += amount
            cases = approved / (prod.case_size or 1)
            cut = approved < r['qty']
            cut_count += 1 if cut else 0
            risk_days = (r['pos'] / r['dhat']) if r['dhat'] > 0 else 999
            if approved > 0:
                title = (f"向 {term.supplier.name} 补 {prod.name} {approved} 瓶（{cases:.0f} 箱），"
                         f"预算占用 {yuan(amount)}")
                if cut:
                    title += f"（原测算 {r['qty']} 瓶，受{'预算' if p['budget'] else '库容'}约束裁剪）"
            else:
                title = (f"{prod.name} 应补 {r['qty']} 瓶但超出预算/库容：建议追加预算 {yuan(r['qty'] * r['unit_cost'])} "
                         f"或接受约 {r['shortage']:.0f} 瓶缺货风险")
            severity = 'high' if risk_days < r['L'] else ('medium' if r['pos'] < r['rop'] else 'low')
            rationale = (f"近 {p['forecast_window']} 天日均销量 {r['ma']:.2f} 瓶"
                         + (f"，季节修正 ×{r['si']:.2f}" if p['use_seasonality'] else '')
                         + f" → 预测日需求 {r['dhat']:.2f}；交期 {r['L']} 天(±{r['sL']:.0f})，"
                         f"安全库存 {r['ss']:.0f}，再订货点 {r['rop']:.0f}，目标库存 {r['S']:.0f}；"
                         f"当前在库 {r['on_hand']} + 在途 {r['transit']} = {r['pos']}，"
                         f"含在途可售约 {risk_days:.0f} 天；缺口 {r['need']:.0f}、经济批量 EOQ {r['eoq']:.0f}，取较大者，"
                         f"再按箱规 {prod.case_size}、起订量 {term.moq_units} 取整，"
                         f"并受单品最多 {p['max_cover_days']} 天备货上限约束。")
            suggestions.append(dict(
                title=title, target_label=f"{prod.barcode} {prod.name}", product_id=prod.id,
                quantity=approved, unit='瓶', amount=round(amount, 2), severity=severity,
                score=round(r['shortage'] * r['margin'] / 1000 + (10 if severity == 'high' else 0), 2),
                rationale=rationale,
                formula=('d̂ = MA(n) × 季节指数；σ_LT = √(L·σ_d² + d̂²·σ_L²)；SS = z·σ_LT；'
                         'ROP = d̂·L + SS；S = d̂·(L+R) + SS；Q = ⌈min(max(S − 库存位置, EOQ), 备货上限 − 库存位置)⌉箱规/起订量；'
                         'EOQ = √(2DK/h)；预算内按 毛利×缺口/资金 贪心分配'),
                inputs={'近期日销量(末14天)': [round(v, 1) for v in hist[prod.id][-14:]],
                        '在库': r['on_hand'], '在途': r['transit'], '交期天': r['L'], '交期波动天': r['sL'],
                        '采购价': r['unit_cost'], '售价': float(prod.price), '箱规': prod.case_size,
                        '起订量': term.moq_units, '供应商': term.supplier.name},
                values={'z': round(z, 3), 'MA': round(r['ma'], 3), '季节指数': round(r['si'], 3),
                        'd̂': round(r['dhat'], 3), 'σ_d': round(r['sigma'], 3), 'σ_LT': round(r['sigma_lt'], 2),
                        'SS': round(r['ss'], 1), 'ROP': round(r['rop'], 1), 'S': round(r['S'], 1),
                        '库存位置': r['pos'], 'EOQ': round(r['eoq'], 1), '测算量': r['qty'], '批准量': approved,
                        '预计缺口': round(r['shortage'], 1)},
                execution_mode='review', required_role='purchaser',
                draft_kind='purchase_draft',
                draft_payload={'supplier_id': term.supplier_id, 'supplier': term.supplier.name,
                               'lines': [{'product_id': prod.id, 'sku': prod.barcode, 'name': prod.name,
                                          'quantity': approved, 'unit_price': r['unit_cost']}] if approved else [],
                               'amount': round(amount, 2)},
            ))
        by_supplier = {}
        for s in suggestions:
            if s['quantity']:
                k = s['draft_payload']['supplier']
                by_supplier[k] = round(by_supplier.get(k, 0) + s['amount'], 2)
        summary = {
            '纳入测算 SKU': len(rows), '建议补货 SKU': sum(1 for s in suggestions if s['quantity']),
            '预算': p['budget'], '预算占用': round(total_amount, 2),
            '预算使用率': round(total_amount / p['budget'], 4) if p['budget'] else None,
            '受约束裁剪 SKU': cut_count, '剩余库容': capacity, '目标服务水平': p['service_level'],
            '按供应商汇总': by_supplier,
        }
        return RunResult(summary=summary, suggestions=suggestions)
