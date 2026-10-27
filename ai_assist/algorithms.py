"""纯函数算法库（不依赖 Django，可单测、可在 PPT 里逐条讲清）。

全部是确定性统计 / 运筹方法：移动平均 + 季节指数、安全库存、EOQ、
预算约束下的贪心背包。
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

# 服务水平 → 标准正态分位数 z（常用取值表，避免引入 scipy）
_Z_TABLE = [(0.50, 0.0), (0.80, 0.8416), (0.85, 1.0364), (0.90, 1.2816), (0.95, 1.6449),
            (0.97, 1.8808), (0.98, 2.0537), (0.99, 2.3263), (0.995, 2.5758), (0.999, 3.0902)]


def z_for_service_level(p: float) -> float:
    p = min(max(p, 0.5), 0.999)
    for (p0, z0), (p1, z1) in zip(_Z_TABLE, _Z_TABLE[1:]):
        if p0 <= p <= p1:
            return z0 + (z1 - z0) * (p - p0) / (p1 - p0)
    return _Z_TABLE[-1][1]


def moving_average(series: list[float], window: int) -> float:
    if not series:
        return 0.0
    tail = series[-window:] if window > 0 else series
    return sum(tail) / len(tail)


def std_dev(series: list[float], window: int) -> float:
    tail = series[-window:] if window > 0 else series
    return statistics.pstdev(tail) if len(tail) > 1 else 0.0


def seasonal_index(monthly_totals: dict[int, float], month: int) -> float:
    """月度季节指数 = 该月历史日均 / 全年日均；数据不足返回 1。"""
    vals = [v for v in monthly_totals.values() if v > 0]
    if len(vals) < 6 or month not in monthly_totals or monthly_totals[month] <= 0:
        return 1.0
    avg = sum(vals) / len(vals)
    return monthly_totals[month] / avg if avg else 1.0


def seasonal_ratio(monthly: dict[int, float], cur_month: int, target_month: int, shrink: float = 0.5,
                   lo: float = 0.5, hi: float = 2.5) -> float:
    """季节修正系数 = 目标月指数 / 当前月指数，向 1 收缩(shrink)以抑制小样本噪声，并限制在 [lo, hi]。

    当前 28 日均已经反映了“当前月”的水平，所以只乘“目标月相对当前月”的比值。
    """
    tgt = seasonal_index(monthly, target_month)
    cur = seasonal_index(monthly, cur_month)
    raw = tgt / cur if cur > 0 else tgt
    return min(max(1 + shrink * (raw - 1), lo), hi)


def safety_stock(z: float, sigma_daily: float, lead_time_days: float) -> float:
    """SS = z × σ_d × √L"""
    return z * sigma_daily * math.sqrt(max(lead_time_days, 0))


def reorder_point(daily_forecast: float, lead_time_days: float, ss: float) -> float:
    """ROP = d̂ × L + SS"""
    return daily_forecast * lead_time_days + ss


def eoq(annual_demand: float, order_cost: float, unit_cost: float, holding_rate: float) -> float:
    """EOQ = √(2DK / h)，h = 单位成本 × 年持有费率"""
    h = unit_cost * holding_rate
    if annual_demand <= 0 or h <= 0 or order_cost <= 0:
        return 0.0
    return math.sqrt(2 * annual_demand * order_cost / h)


def round_up_to(qty: float, multiple: int, minimum: int = 0) -> int:
    if qty <= 0:
        return 0
    multiple = max(int(multiple or 1), 1)
    q = int(math.ceil(qty / multiple) * multiple)
    if minimum and q < minimum:
        q = int(math.ceil(minimum / multiple) * multiple)
    return q


@dataclass
class KnapsackItem:
    key: str
    cost: float          # 资金占用
    value: float         # 优先级价值（避免缺货的毛利）
    units: int
    min_units: int = 0   # 可缩减到的最小量（MOQ），0 表示可整单放弃
    step: int = 1        # 缩减步长（箱规）


def budget_allocate(items: list[KnapsackItem], budget: float, capacity_units: float | None = None):
    """预算 + 库容约束下的贪心分配（按 价值/资金 排序，必要时按箱规缩量）。

    返回 {key: 批准数量}；被裁掉的为 0。贪心对分数背包是最优的，对整箱近似。
    """
    remaining = budget if budget and budget > 0 else float('inf')
    cap = capacity_units if capacity_units and capacity_units > 0 else float('inf')
    order = sorted(items, key=lambda it: (it.value / it.cost) if it.cost else 0, reverse=True)
    result = {}
    for it in order:
        unit_cost = it.cost / it.units if it.units else 0
        q = it.units
        while q > 0 and (q * unit_cost > remaining + 1e-6 or q > cap):
            q -= max(it.step, 1)
        if q < it.min_units:
            q = 0
        q = max(q, 0)
        result[it.key] = q
        remaining -= q * unit_cost
        cap -= q
    return result
