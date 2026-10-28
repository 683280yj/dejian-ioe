"""python manage.py seed_dejian [--reset] [--no-ai] [--days N]

生成演示案例企业「德鉴」租户（平台对所有酒企通用，德鉴只是给评委看的案例）：
  - 来自企业工作簿（ai_assist/demo_assets/dejian_case.xlsx，见 ai_assist/case_data.py）：
    德鉴三档成品的全部批发出库单、基酒原料采购单、加工成品入库，日期/数量/金额/单号原样导入；
  - 生成的演示数据（固定随机种子，按工作簿的价格、同比、季节性推算）：
    习酒代理三款的销售历史与具名经销商订单、表内最后一笔之后到今天的德鉴补充订单、当前库存。
另建一个小的「示例酒行」用于演示数据隔离。
"""
from __future__ import annotations

import datetime as dt
import math
import random
from collections import defaultdict
from decimal import Decimal

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import ProtectedError
from django.utils import timezone

from ai_assist import case_data as C
from ai_assist import demo_profile as P
from ai_assist.models import SupplyTerm
from inventory.models import (Category, Inventory, InventoryTransaction, Member, MemberLevel, Product, Sale,
                              SaleItem, Supplier)
from b2b.demo_seed import B2BSeedMixin
from tenancy.context import use_tenant
from tenancy.models import Brand, Channel, Membership, Tenant, Warehouse

SEED = 20261027


def _poisson(rng, lam):
    if lam <= 0:
        return 0
    if lam > 30:
        return max(0, int(round(rng.gauss(lam, math.sqrt(lam)))))
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


def wipe_tenant(tenant):
    """删除某企业的全部数据（按依赖顺序，多轮重试 PROTECT）。"""
    SaleItem.objects.filter(sale__tenant=tenant).delete()
    models = [m for m in apps.get_models()
              if m._meta.app_label != 'tenancy' and any(f.name == 'tenant' and f.related_model is Tenant for f in m._meta.fields)]
    for _ in range(6):
        left = []
        for m in models:
            mgr = getattr(m, '_base_manager')
            try:
                mgr.filter(tenant=tenant).delete()
            except ProtectedError:
                left.append(m)
        models = left
        if not models:
            break
    tenant.delete()


class Command(B2BSeedMixin, BaseCommand):
    help = '生成演示案例企业「德鉴」：工作簿业务流水 + 生成的补充演示数据'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='已存在时先删除再重建')
        parser.add_argument('--no-ai', action='store_true', help='不自动跑一遍 AI 测算')
        parser.add_argument('--days', type=int, default=P.HISTORY_DAYS)

    def handle(self, *args, **opts):
        existing = Tenant.objects.filter(code=P.TENANT['code']).first()
        if existing and not opts['reset']:
            self.stdout.write(self.style.WARNING('德鉴酒业演示数据已存在（如需重建请加 --reset）'))
            self._ensure_users(existing)
            return
        with transaction.atomic():
            if existing:
                wipe_tenant(existing)
            other = Tenant.objects.filter(code='demo-other').first()
            if other:
                wipe_tenant(other)
            self.rng = random.Random(SEED)
            self.today = timezone.localdate()
            tenant = self._seed_dejian(opts['days'])
            self._seed_other()
        if not opts['no_ai']:
            self._run_ai(tenant)
        self.stdout.write(self.style.SUCCESS(
            f"完成：{tenant.name}；账号 {', '.join(u for u, *_ in P.USERS)} / admin,sales,warehouse / other_boss。演示密码由 DEMO_PASSWORD 环境变量提供，未设置时随机生成。"))

    # ------------------------------------------------------------------ users
    def _ensure_users(self, tenant):
        User = get_user_model()
        out = {}
        for i, (username, role, name, title) in enumerate(P.USERS):
            u, created = User.objects.get_or_create(username=username, defaults={'first_name': name})
            if created:
                u.set_password(P.DEMO_PASSWORD)
            u.first_name = name
            u.is_staff = role == 'boss'
            u.is_superuser = role == 'boss'  # 演示：老板可进入 IOE 全部原有功能
            u.save()
            Membership.objects.update_or_create(user=u, tenant=tenant, defaults={'role': role, 'title': title, 'is_default': True})
            out[role] = u
        # 演示登录别名（同人同权，方便一键填入）
        aliases = {'admin': 'boss', 'sales': 'sales', 'warehouse': 'warehouse'}
        for alias, role in aliases.items():
            src = out.get(role)
            if src is None:
                continue
            u, created = User.objects.get_or_create(username=alias, defaults={'first_name': src.first_name})
            if created:
                u.set_password(P.DEMO_PASSWORD)
            u.first_name = src.first_name
            u.is_staff = src.is_staff
            u.is_superuser = src.is_superuser
            u.save()
            Membership.objects.update_or_create(user=u, tenant=tenant, defaults={
                'role': role, 'title': Membership.objects.filter(user=src, tenant=tenant).values_list('title', flat=True).first() or '',
                'is_default': True})
        return out

    # ----------------------------------------------------------------- dejian
    def _seed_dejian(self, days):
        rng, today = self.rng, self.today
        tenant = Tenant.objects.create(**P.TENANT)
        brands = {b['code']: Brand.objects.create(tenant=tenant, **b) for b in P.BRANDS}
        whs = {w['code']: Warehouse.objects.create(tenant=tenant, **w) for w in P.WAREHOUSES}
        chans = {c['code']: Channel.objects.create(tenant=tenant, name=c['name'], code=c['code'], kind=c['kind'],
                                                    min_price_ratio=Decimal(str(c['min_price_ratio']))) for c in P.CHANNELS}
        users = self._ensure_users(tenant)
        cats = {'JX': Category.objects.create(tenant=tenant, name='代理品牌'),
                'RY': Category.objects.create(tenant=tenant, name='自有品牌')}
        sups = {s['key']: Supplier.objects.create(tenant=tenant, name=s['name'], contact_person=s['contact_person'],
                                                  phone=s['phone'], remarks='') for s in P.SUPPLIERS}
        for name in sorted({x.supplier for x in C.purchases()}):
            sups[name] = Supplier.objects.create(tenant=tenant, name=name, remarks='')
        sup_cfg = {s['key']: s for s in P.SUPPLIERS}
        # 商品走企业自助导入同一条路径（与导入页「示例数据」同源），证明导入链路可用
        from tenancy import importer
        importer.apply('products', tenant, users['boss'], importer.sample_dicts('products'))
        prods = {}
        for sku, b, name, spec, price, cost, base, case, cover, dn_name in P.SKUS:
            prods[sku] = Product.objects.unscoped().get(tenant=tenant, barcode=sku)
            Product.objects.unscoped().filter(pk=prods[sku].pk).update(
                manufacturer=sups[b].name, description=P.DESCRIPTIONS[sku])
            self._attach_image(prods[sku])
            c = sup_cfg[b]
            SupplyTerm.objects.create(tenant=tenant, product=prods[sku], supplier=sups[b], lead_time_days=c['lead'],
                                      lead_time_sd_days=Decimal(str(c['lead_sd'])), moq_units=c['moq'],
                                      unit_cost=Decimal(cost), is_primary=True)
        raw = Product.objects.unscoped().get(tenant=tenant, barcode=P.RAW['sku'])
        Product.objects.unscoped().filter(pk=raw.pk).update(manufacturer='供应商S01', description=P.RAW['description'])
        leads = sorted((x.arrive_date - x.order_date).days for x in C.purchases())
        SupplyTerm.objects.create(tenant=tenant, product=raw, supplier=sups['供应商S01'], lead_time_days=leads[len(leads) // 2],
                                  moq_units=0, unit_cost=P.RAW['cost'], is_primary=True)
        lv_a = MemberLevel.objects.create(tenant=tenant, name='A级经销商', discount=Decimal('1.00'), points_threshold=0)
        lv_b = MemberLevel.objects.create(tenant=tenant, name='B级经销商', discount=Decimal('1.00'), points_threshold=0)
        lv_g = MemberLevel.objects.create(tenant=tenant, name='企业团购', discount=Decimal('1.00'), points_threshold=0)
        lv_r = MemberLevel.objects.create(tenant=tenant, name='门店会员', discount=Decimal('1.00'), points_threshold=0, is_default=True)
        dealers = [Member.objects.create(tenant=tenant, name=d['name'], phone=d['phone'], level=lv_a if d['level'] == 'A' else lv_b,
                                         notes='经销商') for d in P.DEALERS]
        groups = [Member.objects.create(tenant=tenant, name=g['name'], phone=g['phone'], level=lv_g, notes='团购客户') for g in P.GROUP_BUYERS]
        retail = [Member.objects.create(tenant=tenant, name=f'门店会员{i:02d}', phone=f'1990000{i:04d}', level=lv_r) for i in range(100, 130)]

        # ---- 订单级销售历史：习酒代理三款为生成数据（工作簿没有代理款）；德鉴三档见下方 _case_orders
        start = today - dt.timedelta(days=days)
        tz = timezone.get_current_timezone()
        weights = [(sku, base) for sku, b, _n, _s, _p, _c, base, *_ in P.SKUS if b == 'JX']
        sku_info = {s[0]: s for s in P.SKUS}
        sales, lines = [], []  # lines: (sale_index, sku, qty, std, actual)
        slow_cut = today - dt.timedelta(days=75)
        for i in range((today - start).days):
            day = start + dt.timedelta(days=i)
            trend = 1 + 0.08 * (i / 365)
            f = P.SEASON[day.month] * P.WEEKDAY[day.weekday()] * trend
            w = [(s, b if not (s == P.SLOW_SKU and day >= slow_cut) else 0) for s, b in weights]
            tot_w = sum(b for _, b in w)
            for ch in P.CHANNELS:
                lot_lo, lot_hi = ch['lot']
                mean_lot = (lot_lo + lot_hi) / 2
                expected_units = tot_w * f * ch['share']
                n = _poisson(rng, expected_units / mean_lot)
                for _ in range(n):
                    k = rng.choice([1, 1, 2, 3]) if ch['code'] in ('DEALER', 'GROUP') else rng.choice([1, 1, 1, 2])
                    picks = []  # 用 list 保序：set 迭代顺序受 hash 随机化影响，会让演示数据不可复现
                    for _j in range(k):
                        r, acc = rng.random() * tot_w, 0
                        for s, b in w:
                            acc += b
                            if r <= acc and b > 0:
                                if s not in picks:
                                    picks.append(s)
                                break
                    if not picks:
                        continue
                    hour = rng.randint(9, 17) if ch['code'] == 'DEALER' else rng.randint(8, 22)
                    ts = dt.datetime.combine(day, dt.time(hour, rng.randint(0, 59), rng.randint(0, 59)), tzinfo=tz)
                    if ch['code'] == 'DEALER':
                        member = rng.choice(dealers)
                    elif ch['code'] == 'GROUP':
                        member = rng.choice(groups)
                    elif ch['code'] == 'STORE' and rng.random() < 0.3:
                        member = rng.choice(retail)
                    else:
                        member = None
                    idx = len(sales)
                    sales.append(dict(ts=ts, channel=ch['code'], member=member, pay='card' if ch['code'] in ('DEALER', 'GROUP') else rng.choice(['wechat', 'card', 'cash'])))
                    for s in picks:
                        case = sku_info[s][7]
                        q = max(1, int(round(rng.uniform(lot_lo, lot_hi) / len(picks))))
                        if ch['code'] in ('DEALER', 'GROUP'):
                            q = max(case, int(math.ceil(q / case) * case))
                        std = Decimal(sku_info[s][4])
                        act = (std * Decimal(str(ch['discount']))).quantize(Decimal('1'))
                        lines.append((idx, s, q, std, act))
        n_generated_pos = len(sales)
        self.case_orders = self._case_orders()
        for o in self.case_orders:
            if o['status'] not in ('SHIPPED', 'COMPLETED'):
                continue
            idx = len(sales)
            sales.append(dict(ts=dt.datetime.combine(o['date'], dt.time(10), tzinfo=tz), channel=C.CHANNEL_CODE[o['channel']],
                              member=None, pay='card', total=o['amount'],
                              note=f"批发出库 {o['number']} · {o['scenario']}"))
            lines.append((idx, o['sku'], o['bottles'], Decimal(sku_info[o['sku']][4]),
                          (o['amount'] / o['bottles']).quantize(Decimal('0.01')), o['amount']))
        self._bulk_sales(tenant, sales, lines, prods, chans, users)

        # ---- 当前库存 & 历史入库流水
        recent = defaultdict(float)
        cut28 = today - dt.timedelta(days=28)
        monthly = defaultdict(lambda: defaultdict(int))
        for idx, s, q, *_ in lines:
            d = sales[idx]['ts'].date()
            if d >= cut28:
                recent[s] += q / 28
            if sku_info[s][1] == 'JX':
                monthly[s][(d.year, d.month)] += q
        for sku, b, *_rest in P.SKUS:
            cover = sku_info[sku][8]
            qty = P.SLOW_STOCK if cover is None else int(round(recent[sku] * cover))
            Inventory.objects.create(tenant=tenant, product=prods[sku], quantity=qty, warehouse=whs['GY'],
                                     warning_level=max(6, int(recent[sku] * 12)))
        bal, per_day = C.raw_balance_jin()
        Inventory.objects.create(tenant=tenant, product=raw, quantity=bal, warehouse=whs['GY'], warning_level=int(per_day * 30))
        txs = []
        for sku, months in monthly.items():
            for (y, m), q in sorted(months.items()):
                txs.append(InventoryTransaction(tenant=tenant, product=prods[sku], transaction_type='IN', quantity=q,
                                                operator=users['warehouse'], notes=f'{y}-{m:02d} 月度到货汇总'))
        InventoryTransaction.objects.bulk_create(txs)
        objs = list(InventoryTransaction.objects.filter(tenant=tenant))
        keys = [(k, ym) for k, months in monthly.items() for ym in sorted(months)]
        for o, (_k, (y, m)) in zip(objs, keys):
            o.created_at = dt.datetime(y, m, 2, 10, 0, tzinfo=tz)
        InventoryTransaction.objects.bulk_update(objs, ['created_at'])
        self._case_stock_moves(tenant, users, prods, raw)

        if apps.is_installed('b2b'):
            self._seed_b2b(tenant, users, sups, prods, sku_info)
            self._seed_case_b2b(tenant, users, sups, prods, raw, self.case_orders)

        n_sheet = sum(o['source'] == 'sheet' for o in self.case_orders)
        self.stdout.write(f"德鉴：{len(prods) + 1} 个商品；销售单 {len(sales)} 张 = 工作簿 {n_sheet} + 生成补充 "
                          f"{len(sales) - n_generated_pos - n_sheet} + 习酒代理款生成 {n_generated_pos}；习酒历史 {days} 天")
        return tenant

    # ------------------------------------------------------------ case data
    def _case_orders(self):
        """德鉴三档批发出库：工作簿每行一单（原样）；表内最后一笔之后到今天，按上年同期 × 同比生成补充单。"""
        today = self.today
        out = []
        for r in C.sales():
            out.append(dict(source='sheet', number=r.id, date=r.date, scenario=r.scenario, tier=r.tier,
                            channel=r.channel, sku=r.sku, boxes=r.boxes, bottles=r.bottles, amount=r.amount,
                            customer=r.customer_code, status='COMPLETED' if r.date <= today - dt.timedelta(days=60) else 'SHIPPED'))
        last = max(r.date for r in C.sales())
        lq = C.sales()[-1].quarter  # e.g. 2026Q3
        prev_q = f'{int(lq[:4]) - 1}{lq[4:]}'
        seq = defaultdict(int)
        for r in C.sales():
            nd = r.date.replace(year=r.date.year + 1)
            if not (last < nd <= today):
                continue
            seq[(nd, r.sku)] += 1
            cur = sum(x.boxes for x in C.sales() if x.tier == r.tier and x.quarter == lq)
            prev = sum(x.boxes for x in C.sales() if x.tier == r.tier and x.quarter == prev_q) or cur
            boxes = max(1, int(round(r.boxes * cur / prev)))
            bottles = boxes * r.per_box
            status = 'SUBMITTED' if nd > today - dt.timedelta(days=3) else 'SHIPPED'
            out.append(dict(source='generated', number=f'XS-BC-{nd:%Y%m%d}-{r.sku[-2:]}-{seq[(nd, r.sku)]:02d}', date=nd,
                            scenario=r.scenario, tier=r.tier, channel=r.channel, sku=r.sku, boxes=boxes, bottles=bottles,
                            amount=(C.tier_price(r.tier) * bottles).quantize(Decimal('0.01')), customer=r.customer_code,
                            status=status))
        return out

    def _case_stock_moves(self, tenant, users, prods, raw):
        """库存流水：原料采购入库、加工消耗原料、成品入库（工作簿）；批发出库流水在 _seed_case_b2b 里写。"""
        tz = timezone.get_current_timezone()
        rows = []  # (date, product, type, qty, note)
        for x in C.purchases():
            rows.append((x.arrive_date, raw, 'IN', x.jin, f'采购入库 {x.id}'))
        share = defaultdict(lambda: defaultdict(int))
        for r in C.sales():
            share[r.quarter][r.sku] += r.boxes
        for b in C.batches():
            rows.append((b.done_date, raw, 'OUT', int(b.boxes * b.rate_ton_per_box * C.JIN_PER_TON), f'{b.id} 加工领用基酒'))
            tot = sum(share[b.quarter].values())
            for sku, n in share[b.quarter].items():
                q = int(round(b.boxes * n / tot)) * 6
                if q:
                    rows.append((b.done_date, prods[sku], 'IN', q, f'{b.id} 成品入库·{b.mode}'))
        objs = InventoryTransaction.objects.bulk_create([
            InventoryTransaction(tenant=tenant, product=p, transaction_type=k, quantity=q, operator=users['warehouse'], notes=n)
            for _d, p, k, q, n in rows])
        for o, (d, *_r) in zip(objs, rows):
            o.created_at = dt.datetime.combine(d, dt.time(9), tzinfo=tz)
        InventoryTransaction.objects.bulk_update(objs, ['created_at'], batch_size=1000)

    def _attach_image(self, product):
        from pathlib import Path
        from django.core.files import File
        src = Path(__file__).resolve().parents[2] / 'demo_assets' / 'products' / f'{product.barcode}.jpg'
        if src.exists():
            name = f'products/{product.barcode}.jpg'
            if product.image.storage.exists(name):  # 重建时覆盖同名文件，避免 _abc123 后缀堆积
                product.image.storage.delete(name)
            with src.open('rb') as fh:
                product.image.save(f'{product.barcode}.jpg', File(fh), save=False)
            Product.objects.unscoped().filter(pk=product.pk).update(image=product.image.name)

    def _bulk_sales(self, tenant, sales, lines, prods, chans, users):
        by_sale = defaultdict(list)
        for ln in lines:
            by_sale[ln[0]].append(ln)
        objs = []
        for i, s in enumerate(sales):
            total = s.get('total') or sum(Decimal(ln[2]) * ln[4] for ln in by_sale[i])
            objs.append(Sale(tenant=tenant, channel=chans[s['channel']], member=s['member'], total_amount=total,
                             discount_amount=Decimal(0), final_amount=total, payment_method=s['pay'], status='COMPLETED',
                             operator=users['sales'], remark=s.get('note') or ''))
        Sale.objects.bulk_create(objs, batch_size=1000)
        for o, s in zip(objs, sales):
            o.created_at = s['ts']
        Sale.objects.bulk_update(objs, ['created_at'], batch_size=1000)
        # 第 6 项（可选）= 原样小计（工作簿金额），避免「单价四舍五入 × 数量」与表内金额差几分
        items = [SaleItem(sale=objs[ln[0]], product=prods[ln[1]], quantity=ln[2], price=ln[3], actual_price=ln[4],
                          subtotal=ln[5] if len(ln) > 5 else ln[4] * ln[2]) for ln in lines]
        SaleItem.objects.bulk_create(items, batch_size=2000)

    # ------------------------------------------------------------------ other
    def _seed_other(self):
        User = get_user_model()
        t = Tenant.objects.create(code='demo-other', name='黔北酱香酒行', short_name='黔北酒行', industry='酒类零售', is_demo=True,
                                  description='')
        b = Brand.objects.create(tenant=t, code='OT', name='黔北酱香', is_own=True)
        Warehouse.objects.create(tenant=t, code='MAIN', name='主仓', capacity_units=1000, is_default=True)
        ch = Channel.objects.create(tenant=t, code='STORE', name='门店', kind='STORE')
        cat = Category.objects.create(tenant=t, name='酱香型白酒')
        u, created = User.objects.get_or_create(username='other_boss', defaults={'first_name': '周总'})
        if created:
            u.set_password(P.DEMO_PASSWORD)
            u.save()
        Membership.objects.update_or_create(user=u, tenant=t, defaults={'role': 'boss', 'is_default': True})
        sup = Supplier.objects.create(tenant=t, name='仁怀酱酒坊')
        tz = timezone.get_current_timezone()
        prods = {}
        for code, name, price, cost in (('OT-53-500-A', '黔北酱香·窖藏', 399, 200), ('OT-53-500-B', '黔北酱香·光瓶', 199, 90)):
            p = Product.objects.create(tenant=t, barcode=code, name=name, category=cat, brand=b, price=price, cost=cost, case_size=6)
            Inventory.objects.create(tenant=t, product=p, quantity=50)
            SupplyTerm.objects.create(tenant=t, product=p, supplier=sup, unit_cost=cost, lead_time_days=5)
            for i in range(60):
                d = self.today - dt.timedelta(days=60 - i)
                q = self.rng.randint(0, 3)
                if not q:
                    continue
                s = Sale.objects.create(tenant=t, channel=ch, total_amount=price * q, final_amount=price * q, status='COMPLETED', remark='')
                Sale.objects.filter(pk=s.pk).update(created_at=dt.datetime.combine(d, dt.time(12), tzinfo=tz))
                SaleItem.objects.bulk_create([SaleItem(sale=s, product=p, quantity=q, price=price, actual_price=price, subtotal=price * q)])
            prods[code] = p
        if apps.is_installed('b2b'):
            from b2b.models import Customer
            u = get_user_model().objects.get(pk=u.pk)  # 刷新权限缓存（角色组刚同步）
            cust = Customer.objects.create(tenant=t, code='C-001', name='遵义百川商贸有限公司', kind='ENTERPRISE', region='遵义',
                                           contact_person='陈经理', credit_limit=Decimal(50000))
            with use_tenant(t):
                self._b2b_po(t, sup, '2026-10-05', 1, 'RECEIVED', '秋季备货',
                             [(prods['OT-53-500-A'], 30, Decimal(200))], 0, u, u)
                self._b2b_so(t, cust, '2026-10-12', 1, 'SHIPPED', '团购订单',
                             [(prods['OT-53-500-A'], 12, Decimal(360))], 0.5, u, u)

    def _run_ai(self, tenant):
        from ai_assist import services
        from ai_assist.workflows import WORKFLOWS
        boss = get_user_model().objects.get(username='dj_boss')
        for key in WORKFLOWS:
            run = services.run_workflow(tenant, key, {}, user=boss)
            self.stdout.write(f"  测算 {WORKFLOWS[key].label}: {run.suggestions.count()} 条建议")
