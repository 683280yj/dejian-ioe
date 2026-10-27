"""演示案例企业（德鉴）业务流水：从企业提供的工作簿读取，作为 seed 的唯一订单来源。

源文件：ai_assist/demo_assets/dejian_case.xlsx（企业填报的「AI 数据需求清单」工作簿副本）。
读取三张流水表（表头在第 4 行）：
  - 仿真销售流水：每行 = 一笔批发出库（三档包装成品），日期/箱数/金额原样使用；
  - 仿真采购流水：每行 = 一笔「基酒原料（待包装）」采购，吨→斤，单价元/斤；
  - 仿真加工质检流水：每行 = 一批成品入库（箱）。
表内「数据属性」列不写入任何用户可见字段。
"""
from __future__ import annotations

import datetime as dt
import statistics
from collections import defaultdict
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache
from pathlib import Path

SOURCE = Path(__file__).resolve().parent / 'demo_assets' / 'dejian_case.xlsx'
JIN_PER_TON = 2000

# 产品档位 → 德鉴自有品牌 SKU
TIER_SKU = {'低端': 'DJ-53-500-NF', '中端': 'DJ-53-500-ZC', '高端': 'DJ-53-500-LH'}
# 销售渠道 → 系统渠道编码
CHANNEL_CODE = {'乡镇流通/零售/经销': 'DEALER', '团购/经销/零售': 'GROUP', '企事业团购/节庆礼赠': 'GROUP'}
CHANNEL_KIND = {'乡镇流通/零售/经销': 'DISTRIBUTOR', '团购/经销/零售': 'DISTRIBUTOR', '企事业团购/节庆礼赠': 'ENTERPRISE'}
RAW_SKU = 'DJ-RAW-BASE'


def _clean(name: str) -> str:
    """去掉表内「（仿真编号）」「（匿名/模拟）」一类说明后缀。"""
    for tag in ('（仿真编号）', '（匿名/模拟）', '（模拟）', '（仿真）'):
        name = name.replace(tag, '')
    return name.strip()


@dataclass(frozen=True)
class SaleRow:
    id: str
    quarter: str
    date: dt.date
    scenario: str
    customer_group: str
    product_name: str
    tier: str
    channel: str
    boxes: int
    per_box: int
    amount: Decimal

    @property
    def bottles(self) -> int:
        return self.boxes * self.per_box

    @property
    def sku(self) -> str:
        return TIER_SKU[self.tier]

    @property
    def customer_code(self) -> str:
        return f"CASE-{CHANNEL_CODE[self.channel]}-{list(CHANNEL_KIND).index(self.channel) + 1:02d}"

    @property
    def customer_name(self) -> str:
        return f'{self.customer_group}·{self.channel}'


@dataclass(frozen=True)
class PurchaseRow:
    id: str
    quarter: str
    order_date: dt.date
    arrive_date: dt.date
    supplier: str
    material: str
    tons: Decimal
    price_per_jin: Decimal
    purpose: str

    @property
    def jin(self) -> int:
        return int((self.tons * JIN_PER_TON).to_integral_value(ROUND_HALF_UP))

    @property
    def amount(self) -> Decimal:
        return (self.jin * self.price_per_jin).quantize(Decimal('0.01'))


@dataclass(frozen=True)
class BatchRow:
    id: str
    quarter: str
    done_date: dt.date
    boxes: int
    rate_ton_per_box: Decimal
    mode: str


def _d(v):
    return v.date() if isinstance(v, dt.datetime) else v


def _rows(ws):
    return [r for r in ws.iter_rows(min_row=5, values_only=True) if r and r[0]]


@lru_cache(maxsize=1)
def load():
    from openpyxl import load_workbook
    wb = load_workbook(SOURCE, data_only=True, read_only=True)
    sales = [SaleRow(r[0], r[1], _d(r[2]), r[3], r[4], r[5], r[6], r[7], int(r[8]), int(r[9]), Decimal(str(r[10])))
             for r in _rows(wb['仿真销售流水'])]
    purchases = [PurchaseRow(r[0], r[1], _d(r[2]), _d(r[3]), _clean(r[4]), r[5], Decimal(str(r[6])), Decimal(str(r[7])), r[9] or '')
                 for r in _rows(wb['仿真采购流水'])]
    batches = [BatchRow(r[0], r[1], _d(r[4]), int(r[5]), Decimal(str(r[7])), r[8] or '') for r in _rows(wb['仿真加工质检流水'])]
    wb.close()
    return sales, purchases, batches


def sales():
    return load()[0]


def purchases():
    return load()[1]


def batches():
    return load()[2]


def tier_price(tier: str) -> Decimal:
    """档位售价 = 各笔「销售额 ÷ 瓶数」的中位数（元/瓶）。"""
    vals = [r.amount / r.bottles for r in sales() if r.tier == tier]
    return Decimal(str(statistics.median(vals))).quantize(Decimal('0.01'))


def per_box(tier: str) -> int:
    return statistics.mode(r.per_box for r in sales() if r.tier == tier)


def tier_label(tier: str) -> str:
    return next(r.product_name for r in sales() if r.tier == tier)


def base_price_per_jin() -> Decimal:
    return Decimal(str(statistics.median(p.price_per_jin for p in purchases())))


def base_cost_per_bottle(tier: str) -> Decimal:
    """基酒折算成本（元/瓶）= 消耗率(吨/箱) × 2000 斤/吨 × 采购单价(元/斤) ÷ 瓶/箱。"""
    rate = Decimal(str(statistics.median(b.rate_ton_per_box for b in batches())))
    return (rate * JIN_PER_TON * base_price_per_jin() / per_box(tier)).quantize(Decimal('0.01'))


def daily_bottles_last_year(tier: str) -> float:
    """最近 365 天（以表内最后一笔为止）日均出库瓶数。"""
    last = max(r.date for r in sales())
    start = last - dt.timedelta(days=364)
    return sum(r.bottles for r in sales() if r.tier == tier and r.date >= start) / 365


def customers():
    seen = {}
    for r in sales():
        seen.setdefault(r.customer_code, (r.customer_name, CHANNEL_KIND[r.channel], r.channel))
    return seen


def totals():
    s, p = sales(), purchases()
    by_tier = defaultdict(lambda: [0, Decimal('0')])
    for r in s:
        by_tier[r.tier][0] += r.boxes
        by_tier[r.tier][1] += r.amount
    return dict(sales_rows=len(s), boxes=sum(r.boxes for r in s), bottles=sum(r.bottles for r in s),
                amount=sum((r.amount for r in s), Decimal('0')), by_tier=dict(by_tier),
                purchase_rows=len(p), tons=sum((x.tons for x in p), Decimal('0')),
                purchase_amount=sum((x.amount for x in p), Decimal('0')),
                batches=len(batches()), batch_boxes=sum(b.boxes for b in batches()),
                first=min(r.date for r in s), last=max(r.date for r in s))


def raw_balance_jin():
    """基酒原料结存（斤）= 累计采购 − 累计加工消耗；以及近一年日均消耗（斤/天）。"""
    bought = sum(p.jin for p in purchases())
    used = sum(b.boxes * b.rate_ton_per_box * JIN_PER_TON for b in batches())
    last = max(b.done_date for b in batches())
    yr = sum(b.boxes * b.rate_ton_per_box * JIN_PER_TON for b in batches() if b.done_date > last - dt.timedelta(days=365))
    return int(bought - used), float(yr) / 365
