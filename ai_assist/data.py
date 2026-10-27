"""从 IOE 业务表读取 AI 测算所需的输入（全部按租户过滤）。"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict
from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from inventory.models import Inventory, Product, Sale, SaleItem

from .models import DraftTask, SupplyTerm


def today():
    return timezone.localdate()


RAW_MATERIAL_CATEGORY = '原料'  # 原料按采购/加工管理，不参与成品销量预测与补货测算


def products_for(tenant, brand=None):
    qs = (Product.objects.filter(tenant=tenant, is_active=True).exclude(category__name=RAW_MATERIAL_CATEGORY)
          .select_related('brand', 'category'))
    if brand is not None:
        qs = qs.filter(brand=brand)
    return list(qs.order_by('brand_id', 'id'))


def daily_demand(tenant, product_ids, end: dt.date, days: int) -> dict[int, list[float]]:
    """每个商品 [end-days+1, end] 的日销量序列（已完成销售单）。"""
    start = end - dt.timedelta(days=days - 1)
    rows = (SaleItem.objects
            .filter(sale__tenant=tenant, sale__status='COMPLETED', product_id__in=product_ids,
                    sale__created_at__date__gte=start, sale__created_at__date__lte=end)
            .annotate(d=TruncDate('sale__created_at'))
            .values('product_id', 'd').annotate(q=Sum('quantity')))
    out = {pid: [0.0] * days for pid in product_ids}
    for r in rows:
        idx = (r['d'] - start).days
        if 0 <= idx < days:
            out[r['product_id']][idx] += float(r['q'])
    return out


def monthly_daily_avg(series: list[float], end: dt.date) -> dict[int, float]:
    """把日序列(结束于 end)按自然月聚合成 {月: 日均销量}。"""
    n = len(series)
    sums, cnt = defaultdict(float), defaultdict(int)
    for i, v in enumerate(series):
        d = end - dt.timedelta(days=n - 1 - i)
        sums[d.month] += v
        cnt[d.month] += 1
    return {m: sums[m] / cnt[m] for m in sums if cnt[m] >= 20}


def on_hand(tenant, product_ids) -> dict[int, int]:
    return dict(Inventory.objects.filter(tenant=tenant, product_id__in=product_ids).values_list('product_id', 'quantity'))


def primary_terms(tenant, product_ids) -> dict[int, SupplyTerm]:
    out = {}
    for t in SupplyTerm.objects.filter(tenant=tenant, product_id__in=product_ids).select_related('supplier').order_by('-is_primary', 'lead_time_days'):
        out.setdefault(t.product_id, t)
    return out


def on_order(tenant) -> dict[int, int]:
    """在途量：已采纳但未关闭的采购草稿 + （若安装 b2b）已审批未入库的采购单。"""
    out = defaultdict(int)
    # 已关联 b2b 采购单的草稿以 b2b 单据为准，避免重复计算
    for d in DraftTask.objects.filter(tenant=tenant, kind='purchase_draft', status='open', external_ref=''):
        for line in d.payload.get('lines', []):
            out[int(line['product_id'])] += int(line['quantity'])
    try:
        from django.apps import apps
        if apps.is_installed('b2b'):
            PurchaseOrderLine = apps.get_model('b2b', 'PurchaseOrderLine')
            for pid, q, r in PurchaseOrderLine.objects.filter(order__tenant=tenant, order__status__in=['DRAFT', 'SUBMITTED', 'APPROVED']).values_list('product_id', 'quantity', 'received_quantity'):
                out[pid] += max(int(q) - int(r), 0)
    except Exception:  # b2b 模型结构变化时不影响补货测算
        pass
    return dict(out)


def warehouse_capacity(tenant) -> int:
    return sum(w.capacity_units for w in tenant.warehouses.filter(is_active=True))


def total_stock(tenant) -> int:
    return int(Inventory.objects.filter(tenant=tenant).aggregate(s=Sum('quantity'))['s'] or 0)


def sales_in_range(tenant, start: dt.date, end: dt.date, brand=None):
    qs = Sale.objects.filter(tenant=tenant, status='COMPLETED', created_at__date__gte=start, created_at__date__lte=end)
    if brand is not None:
        qs = qs.filter(items__product__brand=brand).distinct()
    return qs


def d(x) -> float:
    return float(x) if isinstance(x, Decimal) else float(x or 0)
