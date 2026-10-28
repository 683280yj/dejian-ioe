"""筹策助手工具层（function calling）。

只读查询工具在服务端直接执行、结果回喂给模型；
写操作工具不直接写库：统一返回待确认动作（与既有采纳入口一致），
由前端走 POST + CSRF + 权限校验真正执行，模型永不自作主张。
"""
import json
from decimal import Decimal

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


def _tool_create_product(tenant, args):
    """写操作：只做校验并返回待确认动作，不写库；用户确认后由视图调 create_product 落库。"""
    from decimal import InvalidOperation
    name = (args.get('name') or '').strip()
    if not name:
        return {'error': '缺少商品名称'}
    try:
        price = Decimal(str(args.get('price')))
        cost = Decimal(str(args.get('cost')))
    except (InvalidOperation, TypeError, ValueError):
        return {'error': '售价/成本价必须是数字'}
    if price < 0 or cost < 0:
        return {'error': '售价与成本价不能为负数'}
    Product = apps.get_model('inventory', 'Product')
    if Product.objects.filter(tenant=tenant, name=name, is_active=True).exists():
        return {'error': f'已存在同名启用商品「{name}」，如需更新请走商品管理页'}
    return {'__action__': {'create_product': {
        'name': name, 'price': str(price), 'cost': str(cost),
        'category': (args.get('category') or '').strip() or '未分类',
        'specification': (args.get('specification') or '').strip(),
        'barcode': (args.get('barcode') or '').strip(),
        'case_size': int(args.get('case_size') or 1),
    }},
        '待录入': name, '售价': str(price), '成本价': str(cost),
        '说明': '已收到录入请求，等用户在对话里确认后执行。请告诉用户回「好」确认。'}


def create_product(tenant, spec):
    """用户确认后真正落库：条码缺省自动生成，分类缺省建「未分类」。"""
    import secrets
    Product = apps.get_model('inventory', 'Product')
    Category = apps.get_model('inventory', 'Category')
    cat, _ = Category.objects.get_or_create(
        tenant=tenant, name=spec.get('category') or '未分类', defaults={'is_active': True})
    barcode = (spec.get('barcode') or '').strip()
    while not barcode or Product.objects.filter(barcode=barcode).exists():
        barcode = 'AI' + secrets.token_hex(5)
    case = int(spec.get('case_size') or 1)
    p = Product.objects.create(
        tenant=tenant, name=spec['name'], category=cat, barcode=barcode,
        price=Decimal(spec['price']), cost=Decimal(spec['cost']),
        specification=spec.get('specification') or '', case_size=max(case, 1))
    return p


# name -> (执行函数, 是否写操作)
TOOLBOX = {
    'query_restock_suggestions': (_tool_query_restock_suggestions, False),
    'query_stock': (_tool_query_stock, False),
    'query_sales_summary': (_tool_query_sales_summary, False),
    'query_pending_drafts': (_tool_query_pending_drafts, False),
    'adopt_suggestions': (_tool_adopt_suggestions, True),
    'create_product': (_tool_create_product, True),
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
    {'type': 'function', 'function': {
        'name': 'create_product',
        'description': '录入新商品。仅当用户在对话中明确要求录入/新增商品并给出名称、售价、成本价后才可调用；'
                       '调用后先向用户展示录入清单，用户再次确认才真正创建。条码留空则自动生成，分类留空归入「未分类」',
        'parameters': {'type': 'object', 'properties': {
            'name': {'type': 'string', 'description': '商品名称（必填）'},
            'price': {'type': 'number', 'description': '售价（必填）'},
            'cost': {'type': 'number', 'description': '成本价（必填）'},
            'category': {'type': 'string', 'description': '商品分类名称，可留空'},
            'specification': {'type': 'string', 'description': '规格，如 53度/500ml'},
            'barcode': {'type': 'string', 'description': '商品条码，留空自动生成'},
            'case_size': {'type': 'integer', 'description': '箱规(瓶/箱)，默认1'}},
            'required': ['name', 'price', 'cost']}}},
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
