"""企业自助导入：商品 / 期初库存 / 客户经销商 / 批发订单 / 采购订单。

流程：下载模板（或示例模板）→ 上传 CSV/XLSX → parse_upload + validate 预览（不写库）→ 确认后 apply 在事务内写入 request.tenant。
所有查询显式按 tenant 过滤，条码与订单号全局唯一，被其他企业占用时报错而不是覆盖。
品牌编码/仓库编码/供应商名称在本企业不存在时自动新建。
"""
import csv
import io
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.apps import apps
from django.db import transaction
from django.utils import timezone

from .context import use_tenant
from .models import Brand, Warehouse

MAX_ROWS = 5000
SAMPLES_DIR = Path(__file__).resolve().parents[1] / 'ai_assist' / 'demo_assets' / 'import_samples'

WO_STATUS = {
    '草稿': 'DRAFT', '待审批': 'SUBMITTED', '已审批': 'APPROVED', '已发货': 'SHIPPED',
    '已签收': 'COMPLETED', '已完成': 'COMPLETED', '已取消': 'CANCELLED',
    'DRAFT': 'DRAFT', 'SUBMITTED': 'SUBMITTED', 'APPROVED': 'APPROVED',
    'SHIPPED': 'SHIPPED', 'COMPLETED': 'COMPLETED', 'CANCELLED': 'CANCELLED',
}
PO_STATUS = {
    '草稿': 'DRAFT', '待审批': 'SUBMITTED', '已审批': 'APPROVED', '已入库': 'RECEIVED',
    '已取消': 'CANCELLED',
    'DRAFT': 'DRAFT', 'SUBMITTED': 'SUBMITTED', 'APPROVED': 'APPROVED',
    'RECEIVED': 'RECEIVED', 'CANCELLED': 'CANCELLED',
}
WO_STATUS_LABEL = {'DRAFT': '草稿', 'SUBMITTED': '待审批', 'APPROVED': '已审批',
                   'SHIPPED': '已发货', 'COMPLETED': '已签收', 'CANCELLED': '已取消'}
PO_STATUS_LABEL = {'DRAFT': '草稿', 'SUBMITTED': '待审批', 'APPROVED': '已审批',
                   'RECEIVED': '已入库', 'CANCELLED': '已取消'}

KINDS = {
    'products': dict(label='商品', columns=[
        ('barcode', '条码', True), ('name', '商品名称', True), ('category', '分类', True),
        ('brand', '品牌编码', False), ('specification', '规格', False), ('price', '售价', True),
        ('cost', '成本价', True), ('case_size', '箱规', False)],
        sample=[['6900000000011', '酱香酒 53° 500ml', '自有品牌', 'BR1', '53° 500ml*6瓶/箱', '298', '150', '6']]),
    'stock': dict(label='期初库存', columns=[
        ('barcode', '条码', True), ('quantity', '库存数量', True), ('warning_level', '预警数量', False),
        ('warehouse', '仓库编码', False)],
        sample=[['6900000000011', '120', '24', 'WH1']]),
    'customers': dict(label='客户/经销商', columns=[
        ('code', '客户编码', True), ('name', '客户名称', True), ('kind', '类型', False),
        ('contact_person', '联系人', False), ('phone', '电话', False), ('region', '授权区域', False),
        ('address', '地址', False), ('credit_limit', '信用额度', False), ('payment_terms_days', '账期(天)', False)],
        sample=[['C001', '百川商贸有限公司', '经销商', '王经理', '', '贵阳', '', '50000', '30']]),
    'wholesale_orders': dict(label='批发订单', columns=[
        ('number', '单号', True), ('customer', '客户编码', True), ('date', '日期', True),
        ('status', '状态', False), ('barcode', '商品条码', True), ('quantity', '数量', True),
        ('unit_price', '单价', True), ('notes', '备注', False)],
        sample=[['SO-20261001-0001', 'C001', '2026-10-01', '已签收', '6900000000011', '60', '298', '团购订单']]),
    'purchase_orders': dict(label='采购订单', columns=[
        ('number', '单号', True), ('supplier', '供应商', True), ('date', '日期', True),
        ('status', '状态', False), ('barcode', '商品条码', True), ('quantity', '数量', True),
        ('unit_price', '单价', True), ('expected_date', '预计到货', False), ('notes', '备注', False)],
        sample=[['PO-20261001-0001', '仁怀酱酒坊', '2026-09-20', '已入库', '6900000000011', '120', '150', '2026-10-01', '秋季备货']]),
}
CUSTOMER_KINDS = {'经销商': 'DISTRIBUTOR', '企业客户': 'ENTERPRISE', '终端门店': 'RETAILER',
                  'DISTRIBUTOR': 'DISTRIBUTOR', 'ENTERPRISE': 'ENTERPRISE', 'RETAILER': 'RETAILER'}
CUSTOMER_KIND_LABELS = {'DISTRIBUTOR': '经销商', 'ENTERPRISE': '企业客户', 'RETAILER': '终端门店'}
SAMPLE_LABEL = '示例模板（已填写）'
FILE_STEM = {
    'products': '商品', 'stock': '期初库存', 'customers': '客户',
    'wholesale_orders': '批发订单', 'purchase_orders': '采购订单',
}


class ImportFileError(ValueError):
    pass


def headers(kind):
    return [h for _, h, _ in KINDS[kind]['columns']]


def _csv(kind, rows):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers(kind))
    w.writerows(rows)
    return '\ufeff' + buf.getvalue()


def _xlsx(kind, rows):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = KINDS[kind]['label'].replace('/', '_')[:31]
    ws.append(headers(kind))
    for r in rows:
        ws.append(list(r))
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def template_csv(kind):
    return _csv(kind, KINDS[kind]['sample'])


def template_xlsx(kind):
    return _xlsx(kind, KINDS[kind]['sample'])


def _read_sample_csv(path):
    text = path.read_text(encoding='utf-8-sig')
    rows = list(csv.reader(io.StringIO(text)))
    return [r for r in rows[1:] if any(c.strip() for c in r)]


def _generate_sample_rows(kind):
    """无落盘文件时按德鉴案例生成（与 seed 同源）。"""
    from ai_assist import case_data as C
    from ai_assist import demo_profile as P
    own = {b['code']: b['is_own'] for b in P.BRANDS}
    if kind == 'products':
        rows = [[sku, name, '自有品牌' if own[b] else '代理品牌', b, spec, str(price), str(cost), str(case)]
                for sku, b, name, spec, price, cost, _base, case, *_ in P.SKUS]
        r = P.RAW
        return rows + [[r['sku'], r['name'], r['category'], r['brand'], r['spec'], str(r['price']), str(r['cost']), '1']]
    if kind == 'stock':
        default_wh = next(w['code'] for w in P.WAREHOUSES if w['is_default'])
        rows = [[sku, str(int(round(base * cover))), str(max(6, int(base * 12))), default_wh]
                for sku, _b, _n, _s, _p, _c, base, _case, cover, *_ in P.SKUS]
        bal, per_day = C.raw_balance_jin()
        return rows + [[P.RAW['sku'], str(bal), str(int(per_day * 30)), default_wh]]
    if kind == 'customers':
        case = [[code, name, CUSTOMER_KIND_LABELS[k], '', '', '', '', '500000', '30']
                for code, (name, k, _ch) in C.customers().items()]
        return case + [[code, name, CUSTOMER_KIND_LABELS[k], contact, f'138-0000-{i + 1:04d}', region, addr, str(credit), str(terms)]
                       for i, (code, name, k, region, contact, credit, addr, terms) in enumerate(P.B2B_CUSTOMERS)]
    if kind == 'wholesale_orders':
        price_by = {s: price for s, _b, _n, _sp, price, *_ in P.SKUS}
        rows = []
        for r in C.sales():
            unit = (r.amount / r.bottles).quantize(Decimal('0.01'))
            rows.append([r.id, r.customer_code, r.date.isoformat(), '已签收', r.sku, str(r.bottles), str(unit), r.scenario])
        for i, (d, cust_i, status, note, lines, *_rest) in enumerate(P.B2B_WHOLESALE, 1):
            number = f'SO-{d.replace("-", "")}-{i:04d}'
            code = P.B2B_CUSTOMERS[cust_i][0]
            for sku, qty in lines:
                rows.append([number, code, d, WO_STATUS_LABEL.get(status, status), sku, str(qty), str(price_by[sku]), note])
        return rows
    if kind == 'purchase_orders':
        price_by = {s: cost for s, _b, _n, _sp, _p, cost, *_ in P.SKUS}
        rows = []
        for x in C.purchases():
            purpose = x.purpose.replace('库存补充', '库存补货')
            rows.append([x.id, x.supplier, x.arrive_date.isoformat(), '已入库', C.RAW_SKU,
                         str(x.jin), str(x.price), x.arrive_date.isoformat(), purpose])
        for i, (d, key, status, note, lines, *_rest) in enumerate(P.B2B_PURCHASES, 1):
            number = f'PO-{d.replace("-", "")}-{i:04d}'
            name = next(s['name'] for s in P.SUPPLIERS if s['key'] == key)
            for sku, qty in lines:
                rows.append([number, name, d, PO_STATUS_LABEL.get(status, status), sku, str(qty),
                             str(price_by[sku]), d, note])
        return rows
    raise KeyError(kind)


def sample_rows(kind):
    """优先读落盘示例；没有则按德鉴案例生成。"""
    path = SAMPLES_DIR / f'{FILE_STEM[kind]}.csv'
    if path.exists():
        return _read_sample_csv(path)
    return _generate_sample_rows(kind)


def sample_csv(kind):
    return _csv(kind, sample_rows(kind))


def sample_xlsx(kind):
    return _xlsx(kind, sample_rows(kind))


def sample_dicts(kind):
    fields = [f for f, _, _ in KINDS[kind]['columns']]
    return [dict(zip(fields, r)) for r in sample_rows(kind)]


def write_sample_files(rows_by_kind=None, extra_dirs=()):
    """把示例行写成 CSV/XLSX。rows_by_kind 缺省则生成。"""
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    dirs = [SAMPLES_DIR, *[Path(d) for d in extra_dirs]]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    out = {}
    for kind in KINDS:
        rows = (rows_by_kind or {}).get(kind)
        if rows is None:
            rows = _generate_sample_rows(kind)
        stem = FILE_STEM[kind]
        for d in dirs:
            (d / f'{stem}.csv').write_text(_csv(kind, rows), encoding='utf-8')
            (d / f'{stem}.xlsx').write_bytes(_xlsx(kind, rows))
        out[kind] = len(rows)
    return out


def export_tenant_rows(tenant):
    """从指定企业导出当前业务数据为导入行（无来源标注）。"""
    Product = apps.get_model('inventory', 'Product')
    Inventory = apps.get_model('inventory', 'Inventory')
    Customer = apps.get_model('b2b', 'Customer')
    WholesaleOrder = apps.get_model('b2b', 'WholesaleOrder')
    PurchaseOrder = apps.get_model('b2b', 'PurchaseOrder')
    products, stock = [], []
    for p in Product.objects.unscoped().filter(tenant=tenant).select_related('category', 'brand').order_by('barcode'):
        products.append([
            p.barcode, p.name, p.category.name if p.category else '',
            p.brand.code if p.brand else '', p.specification or '',
            str(p.price), str(p.cost), str(p.case_size or 1),
        ])
        inv = Inventory.objects.unscoped().filter(tenant=tenant, product=p).select_related('warehouse').first()
        if inv:
            stock.append([
                p.barcode, str(inv.quantity), str(inv.warning_level),
                inv.warehouse.code if inv.warehouse else '',
            ])
    customers = []
    for c in Customer._base_manager.filter(tenant=tenant).order_by('code'):
        customers.append([
            c.code, c.name, CUSTOMER_KIND_LABELS.get(c.kind, c.kind),
            c.contact_person or '', c.phone or '', c.region or '', c.address or '',
            str(c.credit_limit), str(c.payment_terms_days),
        ])
    wholesale = []
    for o in (WholesaleOrder.objects.filter(tenant=tenant)
              .select_related('customer').prefetch_related('lines__product').order_by('number', 'id')):
        for ln in o.lines.all():
            wholesale.append([
                o.number, o.customer.code, timezone.localtime(o.created_at).date().isoformat(),
                WO_STATUS_LABEL.get(o.status, o.status), ln.product.barcode,
                str(ln.quantity), str(ln.unit_price), o.notes or '',
            ])
    purchase = []
    for o in (PurchaseOrder.objects.filter(tenant=tenant)
              .select_related('supplier').prefetch_related('lines__product').order_by('number', 'id')):
        for ln in o.lines.all():
            purchase.append([
                o.number, o.supplier.name, timezone.localtime(o.created_at).date().isoformat(),
                PO_STATUS_LABEL.get(o.status, o.status), ln.product.barcode,
                str(ln.quantity), str(ln.unit_price),
                o.expected_date.isoformat() if o.expected_date else '',
                o.notes or '',
            ])
    return {
        'products': products, 'stock': stock, 'customers': customers,
        'wholesale_orders': wholesale, 'purchase_orders': purchase,
    }


def _cell(v):
    if v is None:
        return ''
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v).strip()


def parse_upload(kind, f):
    """返回 [{field: str}]；表头按中文名或字段名匹配。"""
    name = (getattr(f, 'name', '') or '').lower()
    if name.endswith('.xlsx'):
        from openpyxl import load_workbook
        try:
            ws = load_workbook(f, read_only=True, data_only=True).active
        except Exception as e:  # noqa: BLE001
            raise ImportFileError(f'无法读取 XLSX：{e}')
        rows = [[_cell(c) for c in r] for r in ws.iter_rows(values_only=True)]
    elif name.endswith('.csv'):
        raw = f.read()
        for enc in ('utf-8-sig', 'gbk'):
            try:
                text = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ImportFileError('CSV 编码无法识别，请用 UTF-8 保存')
        rows = [[c.strip() for c in r] for r in csv.reader(io.StringIO(text))]
    else:
        raise ImportFileError('只支持 .csv 或 .xlsx 文件')
    rows = [r for r in rows if any(r)]
    if not rows:
        raise ImportFileError('文件为空')
    head = rows[0]
    index = {}
    for field, label, required in KINDS[kind]['columns']:
        pos = next((i for i, h in enumerate(head) if h.rstrip('*') in (label, field)), None)
        if pos is None and required:
            raise ImportFileError(f'缺少必填列「{label}」，请使用下载的模板')
        index[field] = pos
    body = rows[1:]
    if len(body) > MAX_ROWS:
        raise ImportFileError(f'单次最多导入 {MAX_ROWS} 行')
    return [{f: (r[i] if i is not None and i < len(r) else '') for f, i in index.items()} for r in body]


def _dec(v, label, errs, default=None):
    if v == '' and default is not None:
        return default
    try:
        d = Decimal(v.replace(',', ''))
    except (InvalidOperation, AttributeError):
        errs.append(f'{label}不是数字')
        return None
    if d < 0:
        errs.append(f'{label}不能为负')
    return d


def _int(v, label, errs, default=None):
    if v == '' and default is not None:
        return default
    try:
        n = int(Decimal(v))
    except (InvalidOperation, ValueError):
        errs.append(f'{label}不是整数')
        return None
    if n < 0:
        errs.append(f'{label}不能为负')
    return n


def _parse_date(v, label, errs):
    if not v:
        return None
    for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d'):
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    errs.append(f'{label}格式应为 YYYY-MM-DD')
    return None


def validate(kind, tenant, rows):
    """逐行检查，返回 [{row, data, errors, action}]；不写库。"""
    Product = apps.get_model('inventory', 'Product')
    out, seen = [], set()
    order_meta = {}  # number -> (customer/supplier, date, status, notes)
    for n, data in enumerate(rows, start=2):
        errs, action = [], ''
        for field, label, required in KINDS[kind]['columns']:
            if required and not data.get(field):
                errs.append(f'「{label}」必填')
        if kind == 'products':
            key = data.get('barcode')
            _dec(data.get('price', ''), '售价', errs)
            _dec(data.get('cost', ''), '成本价', errs)
            _int(data.get('case_size', ''), '箱规', errs, default=1)
            existing = Product.objects.unscoped().filter(barcode=key).first() if key else None
            if existing and existing.tenant_id != tenant.pk:
                errs.append('条码已被其他企业使用')
            action = '更新' if existing else '新增'
            if data.get('brand') and not Brand.objects.filter(tenant=tenant, code=data['brand']).exists():
                action += f'（新建品牌 {data["brand"]}）'
            if key and key in seen:
                errs.append('文件内重复')
            seen.add(key)
        elif kind == 'stock':
            key = data.get('barcode')
            _int(data.get('quantity', ''), '库存数量', errs)
            _int(data.get('warning_level', ''), '预警数量', errs, default=10)
            if key and not Product.objects.unscoped().filter(tenant=tenant, barcode=key).exists():
                errs.append('本企业没有该条码的商品，请先导入商品')
            action = '设为期初'
            if data.get('warehouse') and not Warehouse.objects.filter(tenant=tenant, code=data['warehouse']).exists():
                action += f'（新建仓库 {data["warehouse"]}）'
            if key and key in seen:
                errs.append('文件内重复')
            seen.add(key)
        elif kind == 'customers':
            key = data.get('code')
            if data.get('kind') and data['kind'] not in CUSTOMER_KINDS:
                errs.append('类型应为 经销商/企业客户/终端门店')
            _dec(data.get('credit_limit', ''), '信用额度', errs, default=Decimal('0'))
            _int(data.get('payment_terms_days', ''), '账期', errs, default=30)
            Customer = apps.get_model('b2b', 'Customer')
            action = '更新' if Customer.objects.filter(tenant=tenant, code=key).exists() else '新增'
            if key and key in seen:
                errs.append('文件内重复')
            seen.add(key)
        elif kind == 'wholesale_orders':
            number, barcode = data.get('number'), data.get('barcode')
            key = (number, barcode)
            _parse_date(data.get('date', ''), '日期', errs)
            qty = _int(data.get('quantity', ''), '数量', errs)
            if qty is not None and qty == 0:
                errs.append('数量须大于 0')
            _dec(data.get('unit_price', ''), '单价', errs)
            st = data.get('status') or '已签收'
            if st not in WO_STATUS:
                errs.append('状态应为 草稿/待审批/已审批/已发货/已签收/已取消')
            Customer = apps.get_model('b2b', 'Customer')
            WholesaleOrder = apps.get_model('b2b', 'WholesaleOrder')
            if data.get('customer') and not Customer.objects.filter(tenant=tenant, code=data['customer']).exists():
                errs.append('本企业没有该客户编码，请先导入客户')
            if barcode and not Product.objects.unscoped().filter(tenant=tenant, barcode=barcode).exists():
                errs.append('本企业没有该条码的商品，请先导入商品')
            if number:
                other = WholesaleOrder.objects.filter(number=number).exclude(tenant=tenant).first()
                if other:
                    errs.append('单号已被其他企业使用')
                elif number in order_meta:
                    prev = order_meta[number]
                    if prev[0] != data.get('customer'):
                        errs.append('同一单号的客户编码不一致')
                    if prev[1] != data.get('date'):
                        errs.append('同一单号的日期不一致')
                    if (prev[2] or '已签收') != st:
                        errs.append('同一单号的状态不一致')
                else:
                    order_meta[number] = (data.get('customer'), data.get('date'), st, data.get('notes', ''))
                    existing = WholesaleOrder.objects.filter(tenant=tenant, number=number).first()
                    action = '更新订单' if existing else '新增订单'
            if key in seen:
                errs.append('文件内同一单号+条码重复')
            seen.add(key)
            if not action:
                action = '明细'
        elif kind == 'purchase_orders':
            number, barcode = data.get('number'), data.get('barcode')
            key = (number, barcode)
            _parse_date(data.get('date', ''), '日期', errs)
            if data.get('expected_date'):
                _parse_date(data['expected_date'], '预计到货', errs)
            qty = _int(data.get('quantity', ''), '数量', errs)
            if qty is not None and qty == 0:
                errs.append('数量须大于 0')
            _dec(data.get('unit_price', ''), '单价', errs)
            st = data.get('status') or '已入库'
            if st not in PO_STATUS:
                errs.append('状态应为 草稿/待审批/已审批/已入库/已取消')
            PurchaseOrder = apps.get_model('b2b', 'PurchaseOrder')
            if barcode and not Product.objects.unscoped().filter(tenant=tenant, barcode=barcode).exists():
                errs.append('本企业没有该条码的商品，请先导入商品')
            if number:
                other = PurchaseOrder.objects.filter(number=number).exclude(tenant=tenant).first()
                if other:
                    errs.append('单号已被其他企业使用')
                elif number in order_meta:
                    prev = order_meta[number]
                    if prev[0] != data.get('supplier'):
                        errs.append('同一单号的供应商不一致')
                    if prev[1] != data.get('date'):
                        errs.append('同一单号的日期不一致')
                    if (prev[2] or '已入库') != st:
                        errs.append('同一单号的状态不一致')
                else:
                    order_meta[number] = (data.get('supplier'), data.get('date'), st, data.get('notes', ''))
                    existing = PurchaseOrder.objects.filter(tenant=tenant, number=number).first()
                    action = '更新订单' if existing else '新增订单'
                    if data.get('supplier'):
                        Supplier = apps.get_model('inventory', 'Supplier')
                        if not Supplier.objects.filter(tenant=tenant, name=data['supplier']).exists():
                            action += f'（新建供应商 {data["supplier"]}）'
            if key in seen:
                errs.append('文件内同一单号+条码重复')
            seen.add(key)
            if not action:
                action = '明细'
        else:
            errs.append(f'未知导入类型 {kind}')
            key = None
        out.append({'row': n, 'data': data, 'errors': errs, 'action': action})
    return out


def _aware(d, hour=12):
    tz = timezone.get_current_timezone()
    return timezone.make_aware(datetime.combine(d, datetime.min.time().replace(hour=hour)), tz)


def _apply_wholesale(tenant, user, rows):
    Product = apps.get_model('inventory', 'Product')
    Customer = apps.get_model('b2b', 'Customer')
    WholesaleOrder = apps.get_model('b2b', 'WholesaleOrder')
    WholesaleOrderLine = apps.get_model('b2b', 'WholesaleOrderLine')
    groups = defaultdict(list)
    for d in rows:
        groups[d['number']].append(d)
    for number, lines in groups.items():
        head = lines[0]
        status = WO_STATUS[head.get('status') or '已签收']
        day = _parse_date(head['date'], '日期', [])
        cust = Customer.objects.get(tenant=tenant, code=head['customer'])
        existing = WholesaleOrder.objects.filter(tenant=tenant, number=number).first()
        if existing:
            existing.lines.all().delete()
            existing.customer = cust
            existing.notes = head.get('notes', '')
            existing.status = status
            existing.save()
            order = existing
        else:
            order = WholesaleOrder(
                tenant=tenant, number=number, customer=cust, status=status,
                notes=head.get('notes', ''), created_by=user)
            order.save()
        WholesaleOrderLine.objects.bulk_create([
            WholesaleOrderLine(
                order=order,
                product=Product.objects.unscoped().get(tenant=tenant, barcode=ln['barcode']),
                quantity=int(Decimal(ln['quantity'])),
                unit_price=Decimal(ln['unit_price'].replace(',', '')),
            ) for ln in lines
        ])
        if day:
            WholesaleOrder.objects.filter(pk=order.pk).update(created_at=_aware(day))


def _apply_purchase(tenant, user, rows):
    Product = apps.get_model('inventory', 'Product')
    Supplier = apps.get_model('inventory', 'Supplier')
    PurchaseOrder = apps.get_model('b2b', 'PurchaseOrder')
    PurchaseOrderLine = apps.get_model('b2b', 'PurchaseOrderLine')
    groups = defaultdict(list)
    for d in rows:
        groups[d['number']].append(d)
    for number, lines in groups.items():
        head = lines[0]
        status = PO_STATUS[head.get('status') or '已入库']
        day = _parse_date(head['date'], '日期', [])
        exp = _parse_date(head.get('expected_date') or '', '预计到货', [])
        sup, _ = Supplier.objects.get_or_create(tenant=tenant, name=head['supplier'])
        existing = PurchaseOrder.objects.filter(tenant=tenant, number=number).first()
        if existing:
            existing.lines.all().delete()
            existing.supplier = sup
            existing.notes = head.get('notes', '')
            existing.status = status
            existing.expected_date = exp
            existing.save()
            order = existing
        else:
            order = PurchaseOrder(
                tenant=tenant, number=number, supplier=sup, status=status,
                expected_date=exp, notes=head.get('notes', ''), created_by=user)
            order.save()
        PurchaseOrderLine.objects.bulk_create([
            PurchaseOrderLine(
                order=order,
                product=Product.objects.unscoped().get(tenant=tenant, barcode=ln['barcode']),
                quantity=int(Decimal(ln['quantity'])),
                unit_price=Decimal(ln['unit_price'].replace(',', '')),
                received_quantity=int(Decimal(ln['quantity'])) if status == 'RECEIVED' else 0,
            ) for ln in lines
        ])
        if day:
            PurchaseOrder.objects.filter(pk=order.pk).update(created_at=_aware(day))


def apply(kind, tenant, user, rows):
    """在事务内写入；调用前须先 validate 无错误。返回写入行数。"""
    checked = validate(kind, tenant, rows)
    if any(r['errors'] for r in checked):
        raise ImportFileError('数据有误，请重新预览')
    Product = apps.get_model('inventory', 'Product')
    Category = apps.get_model('inventory', 'Category')
    Inventory = apps.get_model('inventory', 'Inventory')
    with use_tenant(tenant), transaction.atomic():
        if kind == 'wholesale_orders':
            _apply_wholesale(tenant, user, rows)
            return len(rows)
        if kind == 'purchase_orders':
            _apply_purchase(tenant, user, rows)
            return len(rows)
        for d in rows:
            if kind == 'products':
                cat, _ = Category.objects.get_or_create(tenant=tenant, name=d['category'])
                brand = Brand.objects.get_or_create(tenant=tenant, code=d['brand'], defaults={'name': d['brand']})[0] if d.get('brand') else None
                Product.objects.update_or_create(barcode=d['barcode'], tenant=tenant, defaults=dict(
                    name=d['name'], category=cat, brand=brand, specification=d.get('specification', ''),
                    price=Decimal(d['price']), cost=Decimal(d['cost']), case_size=int(d.get('case_size') or 1)))
            elif kind == 'stock':
                from inventory.models import InventoryTransaction
                p = Product.objects.get(tenant=tenant, barcode=d['barcode'])
                qty = int(Decimal(d['quantity']))
                wh = Warehouse.objects.get_or_create(tenant=tenant, code=d['warehouse'], defaults={'name': d['warehouse']})[0] if d.get('warehouse') else None
                inv, _ = Inventory.objects.get_or_create(product=p, defaults={'tenant': tenant, 'quantity': 0})
                delta = qty - inv.quantity
                inv.quantity = qty
                inv.warning_level = int(Decimal(d['warning_level'])) if d.get('warning_level') else inv.warning_level
                if wh:
                    inv.warehouse = wh
                inv.save()
                if delta:
                    InventoryTransaction.objects.create(tenant=tenant, product=p, transaction_type='ADJUST',
                                                        quantity=abs(delta), operator=user,
                                                        notes=f'期初库存导入：设为 {qty}')
            elif kind == 'customers':
                Customer = apps.get_model('b2b', 'Customer')
                Customer.objects.update_or_create(tenant=tenant, code=d['code'], defaults=dict(
                    name=d['name'], kind=CUSTOMER_KINDS.get(d.get('kind') or '经销商', 'DISTRIBUTOR'),
                    contact_person=d.get('contact_person', ''), phone=d.get('phone', ''),
                    region=d.get('region', ''), address=d.get('address', ''),
                    credit_limit=Decimal((d.get('credit_limit') or '0').replace(',', '')),
                    payment_terms_days=int(Decimal(d.get('payment_terms_days') or 30))))
            else:
                raise ImportFileError(f'未知导入类型 {kind}')
    return len(rows)
