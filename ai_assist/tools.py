"""筹策助手工具层（function calling）。

只读查询工具在服务端直接执行、结果回喂给模型；
写操作工具不直接写库：统一返回待确认动作（与既有采纳入口一致），
由前端走 POST + CSRF + 权限校验真正执行，模型永不自作主张。
"""
import json

from django.apps import apps

from . import data
from .models import DraftTask, Suggestion


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _tool_query_restock_suggestions(tenant, args):
    rows = (Suggestion.objects.filter(tenant=tenant, workflow='replenish', status='pending')
            .select_related('product').order_by('-score', 'id')[:20])
    out = []
    for i, s in enumerate(rows, 1):
        out.append({
            '序号': i, '编号': s.pk, '对象': s.target_label or s.title,
            '建议数量': str(s.quantity), '单位': s.unit,
            '优先级分': round(s.score, 1), '严重度': s.severity,
            '依据': (s.rationale or '')[:200],
        })
    return {'待处理补货建议数': len(out), '建议列表': out}


def _tool_query_stock(tenant, args):
    Product = apps.get_model('inventory', 'Product')
    Inventory = apps.get_model('inventory', 'Inventory')
    kw = (args.get('keyword') or '').strip()
    qs = Product.objects.filter(tenant=tenant, is_active=True).select_related('category')
    if kw:
        qs = qs.filter(name__icontains=kw)
    prods = list(qs[:10])
    if not prods:
        return {'匹配商品数': 0}
    invs = {i.product_id: i for i in Inventory.objects.filter(product__in=prods)}
    out = []
    for p in prods:
        inv = invs.get(p.pk)
        out.append({
            '商品': p.name, '售价': str(p.price), '成本价': str(p.cost),
            '库存数量': inv.quantity if inv else 0,
            '预警水位': inv.warning_level if inv else 0,
            '库存告急': bool(inv and inv.quantity <= inv.warning_level),
        })
    return {'匹配商品数': len(prods), '库存列表': out}


def _tool_query_sales_summary(tenant, args):
    Sale = apps.get_model('inventory', 'Sale')
    SaleItem = apps.get_model('inventory', 'SaleItem')
    days = min(max(int(args.get('days') or 28), 1), 365)
    import datetime as dt
    from django.db.models import Sum
    from django.utils import timezone
    start = timezone.localdate() - dt.timedelta(days=days - 1)
    qs = SaleItem.objects.filter(sale__tenant=tenant, sale__status='COMPLETED',
                                 sale__created_at__date__gte=start)
    total = qs.aggregate(q=Sum('quantity'), amt=Sum('line_amount'))
    top = list(qs.values('product__name').annotate(q=Sum('quantity'), amt=Sum('line_amount'))
               .order_by('-amt')[:5])
    return {
        '统计天数': days,
        '总销量': float(total['q'] or 0),
        '总销售额': float(total['amt'] or 0),
        '销量Top5': [{'商品': r['product__name'], '销量': float(r['q'] or 0),
                     '销售额': float(r['amt'] or 0)} for r in top],
    }


def _tool_query_pending_drafts(tenant, args):
    rows = (DraftTask.objects.filter(tenant=tenant, status='open')
            .select_related('suggestion').order_by('-created_at')[:20])
    return {'待处理草稿数': len(rows), '草稿列表': [
        {'编号': t.pk, '标题': t.title, '类型': t.kind,
         '关联单据': t.external_ref, '创建时间': t.created_at.strftime('%m-%d %H:%M')}
        for t in rows]}


def _tool_adopt_suggestions(tenant, args):
    """写操作：不执行，返回待确认动作（前端走既有采纳入口，带权限与 CSRF）。"""
    pks = [int(pk) for pk in (args.get('ids') or [])]
    valid = set(Suggestion.objects.filter(tenant=tenant, workflow='replenish',
                                          status='pending', pk__in=pks)
                .values_list('pk', flat=True))
    return {'__action__': {'adopt_pks': sorted(valid)},
            '确认生成': len(valid), '无效编号': [pk for pk in pks if pk not in valid]}


# name -> (执行函数, 是否写操作)
TOOLBOX = {
    'query_restock_suggestions': (_tool_query_restock_suggestions, False),
    'query_stock': (_tool_query_stock, False),
    'query_sales_summary': (_tool_query_sales_summary, False),
    'query_pending_drafts': (_tool_query_pending_drafts, False),
    'adopt_suggestions': (_tool_adopt_suggestions, True),
}

TOOL_SPECS = [
    {'type': 'function', 'function': {
        'name': 'query_restock_suggestions',
        'description': '查询当前企业所有待处理的补货建议（含序号、建议数量、优先级与依据）',
        'parameters': {'type': 'object', 'properties': {}, 'required': []}}},
    {'type': 'function', 'function': {
        'name': 'query_stock',
        'description': '按商品名称关键词查询当前库存数量、预警水位与售价成本',
        'parameters': {'type': 'object', 'properties': {
            'keyword': {'type': 'string', 'description': '商品名称关键词，可留空查前10个商品'}},
            'required': []}}},
    {'type': 'function', 'function': {
        'name': 'query_sales_summary',
        'description': '查询最近 N 天已完成销售单的汇总：总销量、总销售额与销量Top5商品',
        'parameters': {'type': 'object', 'properties': {
            'days': {'type': 'integer', 'description': '统计天数，默认28'}},
            'required': []}}},
    {'type': 'function', 'function': {
        'name': 'query_pending_drafts',
        'description': '查询当前企业待处理的采购草稿/待办列表',
        'parameters': {'type': 'object', 'properties': {}, 'required': []}}},
    {'type': 'function', 'function': {
        'name': 'adopt_suggestions',
        'description': '为指定的补货建议生成采购草稿。仅当用户在对话中明确说「生成草稿」「确认」等之后才可调用；'
                       '调用后会先向用户展示清单，用户再次确认才真正执行',
        'parameters': {'type': 'object', 'properties': {
            'ids': {'type': 'array', 'items': {'type': 'integer'},
                    'description': '补货建议编号列表（来自 query_restock_suggestions 的编号字段）'}},
            'required': ['ids']}}},
]


def execute(name, args, tenant):
    """执行工具；未知工具返回错误。返回 dict（写操作返回带 __action__ 的确认信息）。"""
    entry = TOOLBOX.get(name)
    if entry is None:
        return {'error': f'未知工具 {name}'}
    fn, _is_write = entry
    try:
        return fn(tenant, args or {})
    except Exception as exc:  # 工具失败不拖垮对话，回喂错误让模型换个说法
        return {'error': f'{type(exc).__name__}: {exc}'}


def tool_result_text(result):
    return json.dumps(result, ensure_ascii=False, default=str)[:4000]
