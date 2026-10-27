"""库存预警：可售天数 vs 交期+安全天数；积压天数；滞销。自动生成预警（低风险），处理由人决定。"""
from __future__ import annotations

import datetime as dt

from .. import algorithms as A
from .. import data
from .base import Param, RunResult, Workflow, yuan


class StockAlertFlow(Workflow):
    key = 'stock_alert'
    label = '库存预警'
    cycle = 'day'
    role = 'warehouse'
    objective = '断货前至少提前一个交期发出预警；积压/滞销资金每日可见'
    pain_point = 'IOE 原预警只看固定“预警数量”，不随销量和交期变化；旺季预警太晚、淡季误报多'
    params = [
        Param('service_level', '安全库存服务水平', 'pct', 0.95, '目标', '', 0.5, 0.999),
        Param('forecast_window', '需求移动平均窗口(天)', 'int', 28, '算法', '', 7, 120),
        Param('overstock_days', '积压阈值(可售天数)', 'int', 120, '约束', '超过即提示积压', 30, 720),
        Param('slow_days', '滞销阈值(连续无销售天数)', 'int', 45, '约束', '', 7, 365),
        Param('write_alerts', '自动写入库存预警表', 'bool', True, '约束', '低风险自动动作：只生成预警，不改库存'),
    ]

    def run(self, ctx):
        p, tenant = ctx.params, ctx.tenant
        products = data.products_for(tenant, ctx.brand)
        pids = [x.id for x in products]
        hist = data.daily_demand(tenant, pids, ctx.as_of - dt.timedelta(days=1), 120)  # 截至昨日
        stock = data.on_hand(tenant, pids)
        terms = data.primary_terms(tenant, pids)
        z = A.z_for_service_level(p['service_level'])
        out, counts = [], {'low_stock': 0, 'overstock': 0, 'slow': 0}
        for prod in products:
            s = hist[prod.id]
            dhat = A.moving_average(s, p['forecast_window'])
            sigma = A.std_dev(s, 56)
            term = terms.get(prod.id)
            L = term.lead_time_days if term else 10
            ss = A.safety_stock(z, sigma, L)
            q = stock.get(prod.id, 0)
            cover = q / dhat if dhat > 0 else None
            threshold_days = L + (ss / dhat if dhat > 0 else 0)
            last_sale = next((i for i in range(len(s) - 1, -1, -1) if s[i] > 0), None)
            idle = (len(s) - 1 - last_sale) if last_sale is not None else len(s)
            cost = float(term.unit_cost) if term else float(prod.cost)
            common = dict(target_label=f"{prod.barcode} {prod.name}", product_id=prod.id, unit='瓶',
                          formula='可售天数 = 在库 ÷ d̂；预警线 = 交期 L + SS/d̂，SS = z·σ_d·√L',
                          inputs={'在库': q, '近28天日均': round(dhat, 2), 'σ_d': round(sigma, 2), '交期': L},
                          execution_mode='auto', required_role='warehouse', draft_kind='stock_alert')
            if dhat > 0 and q < dhat * threshold_days:
                counts['low_stock'] += 1
                stockout = ctx.as_of + dt.timedelta(days=int(cover or 0))
                sev = 'high' if (cover or 0) < L else 'medium'
                out.append(dict(common, title=f"低库存预警：{prod.name} 在库 {q} 瓶，约可售 {cover:.1f} 天（预计 {stockout:%m-%d} 断货），低于预警线 {threshold_days:.1f} 天",
                                quantity=q, severity=sev, score=100 - min(cover or 0, 99),
                                rationale=f"日均 {dhat:.2f} 瓶，交期 {L} 天，安全库存 {ss:.0f} 瓶；可在商品页查看补货建议",
                                values={'可售天数': round(cover or 0, 1), '预警线天数': round(threshold_days, 1), 'SS': round(ss, 1)},
                                alert_type='low_stock', draft_payload={'product_id': prod.id, 'type': 'low_stock'}))
            elif cover is not None and cover > p['overstock_days']:
                counts['overstock'] += 1
                excess = q - dhat * p['overstock_days']
                out.append(dict(common, title=f"积压提示：{prod.name} 可售 {cover:.0f} 天 > {p['overstock_days']} 天，超额约 {excess:.0f} 瓶，占用资金 {yuan(excess * cost)}",
                                quantity=round(excess), amount=round(excess * cost, 2), severity='medium', score=min(cover / 10, 60),
                                rationale='建议暂停该品采购、评估渠道调拨或促销（由老板/销售决定）',
                                values={'可售天数': round(cover, 1), '超额瓶数': round(excess)}, alert_type='overstock',
                                draft_payload={'product_id': prod.id, 'type': 'overstock'}))
            if q > 0 and idle >= p['slow_days']:
                counts['slow'] += 1
                out.append(dict(common, title=f"滞销提示：{prod.name} 已 {idle} 天无销售，在库 {q} 瓶，占用资金 {yuan(q * cost)}",
                                quantity=q, amount=round(q * cost, 2), severity='low', score=idle / 10,
                                rationale='连续无销售；建议核实是否下架/换渠道', values={'无销售天数': idle},
                                alert_type='overstock', draft_payload={'product_id': prod.id, 'type': 'slow'}))
        summary = {'检查 SKU': len(products), '低库存': counts['low_stock'], '积压': counts['overstock'], '滞销': counts['slow']}
        return RunResult(summary=summary, suggestions=out)
