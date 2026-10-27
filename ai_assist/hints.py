"""IOE 原页面里的两个小提示：库存页「补货建议」、首页「库存提示」（由视图放进 context）。

数据来自最近一次 replenish / stock_alert 测算（seed_dejian 或 `python manage.py ai_refresh` 生成）。
"""
from .models import DecisionRun, Suggestion


def latest_run(tenant, workflow):
    if tenant is None:
        return None
    return DecisionRun.objects.filter(tenant=tenant, workflow=workflow, parent__isnull=True).order_by('-created_at', '-pk').first()


def restock_suggestions(tenant, product=None, limit=5):
    run = latest_run(tenant, 'replenish')
    if run is None:
        return run, []
    qs = Suggestion.objects.filter(run=run, status='pending', quantity__gt=0)
    if product is not None:
        qs = qs.filter(product_id=product.pk)
    return run, list(qs.order_by('-score', 'pk')[:limit])


def stock_hints(tenant, limit=3):
    run = latest_run(tenant, 'stock_alert')
    if run is None:
        return run, [], {}
    items = list(Suggestion.objects.filter(run=run).order_by('-score', 'pk'))
    counts = {k: run.summary.get(k, 0) for k in ('低库存', '积压', '滞销')}
    return run, items[:limit], counts


# ---- 给 IOE 原视图用的可选上下文（lane-b 模板约定：index.stock_alert / inventory_list.replenish_suggestions）
def index_context(request):
    """首页：stock_alert={title, detail}；无测算数据时不提供（模板回退到原有低库存统计）。"""
    run, items, counts = stock_hints(getattr(request, 'tenant', None))
    total = sum(counts.values()) if counts else 0
    if not total:
        return {}
    title = f"库存提示：低库存 {counts['低库存']} 种，积压 {counts['积压']} 种，滞销 {counts['滞销']} 种"
    detail = '；'.join(s.title for s in items) + f"（{run.as_of:%m-%d} 按近期销量和交期测算）"
    return {'stock_alert': {'title': title, 'detail': detail}}


def inventory_context(request, limit=5):
    """库存列表：replenish_suggestions=[{pk, product, target_label, title, suggested_qty, basis, explain, anomalies, ai_source}]。"""
    run, items = restock_suggestions(getattr(request, 'tenant', None), limit=limit)
    if not items:
        return {}
    from inventory.models import Product
    prods = Product.objects.in_bulk([s.product_id for s in items if s.product_id])
    from . import explain as _explain
    rows = []
    for s in items:
        if not s.ai_explanation:
            # 页面侧只用规则即时补齐（不调 LLM，不阻塞页面）；LLM 版在测算时生成
            _explain.ensure_explanation(s, allow_llm=False, persist=False)
        rows.append({'pk': s.pk, 'product': prods.get(s.product_id), 'target_label': s.target_label, 'title': s.title,
                     'suggested_qty': int(s.quantity) if s.quantity is not None else None, 'basis': s.rationale,
                     'short': _explain.short_line(s),
                     'explain': s.ai_explanation, 'anomalies': s.ai_anomalies or [], 'ai_source': s.ai_source})
    return {'replenish_suggestions': rows}
