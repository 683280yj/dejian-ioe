"""To B 交易演示数据（合成）：供 seed_dejian 调用。

放在 b2b 而不在 ai_assist：所有状态推进都经 b2b.services 的流转函数、以演示账号身份执行，
AI 模块本身仍不调用任何流转函数（见 ai_assist 的安全测试）。
"""
import datetime as dt
from collections import defaultdict
from decimal import Decimal

from django.utils import timezone

from ai_assist import demo_profile as P
from inventory.models import Inventory, InventoryTransaction
from tenancy.context import use_tenant


class B2BSeedMixin:
    def _seed_b2b(self, tenant, users, sups, prods, sku_info):
        """To B 合成历史：全部经 b2b.services 的流转函数推进，状态/库存/应收应付保持一致；完成后回写历史日期。

        收货会加库存、发货会减库存：先把库存预扣/预加这部分差额，跑完后库存回到上面设定的目标值，
        这样 AI 补货/预警演示不受影响。
        """
        from b2b.models import Customer, WholesaleOrder
        recv, ship = defaultdict(int), defaultdict(int)
        for _d, _s, status, _n, lines, _r in P.B2B_PURCHASES:
            if status == 'RECEIVED':
                for sku, q in lines:
                    recv[sku] += q
        for _d, _c, status, _n, lines, _r, _t in P.B2B_WHOLESALE:
            if status in ('SHIPPED', 'COMPLETED'):
                for sku, q in lines:
                    ship[sku] += q
        target = {}
        for sku, p in prods.items():
            inv = Inventory.objects.unscoped().get(product=p)
            target[sku] = inv.quantity
            Inventory.objects.unscoped().filter(pk=inv.pk).update(quantity=inv.quantity - recv[sku] + ship[sku])
        # 客户/经销商走企业自助导入同一条路径（与导入页「示例数据」同源）
        from tenancy import importer
        importer.apply('customers', tenant, users['boss'], importer.sample_dicts('customers'))
        customers = [Customer._base_manager.get(tenant=tenant, code=c[0]) for c in P.B2B_CUSTOMERS]
        price = {sku: Decimal(sku_info[sku][4]) for sku in prods}
        cost = {sku: Decimal(sku_info[sku][5]) for sku in prods}
        boss = users['boss']
        with use_tenant(tenant):
            for i, (d, sup, status, note, lines, pay) in enumerate(P.B2B_PURCHASES, 1):
                self._b2b_po(tenant, sups[sup], d, i, status, note,
                             [(prods[s], q, cost[s]) for s, q in lines], pay, users['purchaser'], boss)
            for i, (d, ci, status, note, lines, ratio, total) in enumerate(P.B2B_WHOLESALE, 1):
                gross = sum(price[s] * q for s, q in lines)
                factor = (Decimal(total) / gross) if total else Decimal('0.985')
                self._b2b_so(tenant, customers[ci], d, i, status, note,
                             [(prods[s], q, (price[s] * factor).quantize(Decimal('0.01'))) for s, q in lines],
                             ratio, users['sales'], boss)
            for sup, start, end, status in P.B2B_STATEMENTS:
                self._b2b_statement(tenant, sups[sup], start, end, status, boss)
        for sku, p in prods.items():
            got = Inventory.objects.unscoped().get(product=p).quantity
            assert got == target[sku], (sku, got, target[sku])
        self.stdout.write(f"  To B：{len(customers)} 个经销商（另有工作簿客户见下），{len(P.B2B_PURCHASES)} 张习酒采购单，{len(P.B2B_WHOLESALE)} 张批发订单（生成）")

    def _seed_case_b2b(self, tenant, users, sups, prods, raw, orders):
        """工作簿流水 → 批发订单（德鉴三档）与基酒采购单：单号/日期/数量/金额原样，状态按日期直接落到终态。

        这些是历史单据的「导入」，不是现场操作：直接写终态、应收应付与收付款登记，不再逐笔调用流转函数；
        对应的库存流水（出库/入库）也一并写入，当前库存由上面的目标值决定。
        """
        from ai_assist import case_data as C
        from b2b.models import (Customer, Payable, PurchaseOrder, PurchaseOrderLine, Receivable, SettlementEntry,
                                WholesaleOrder, WholesaleOrderLine)
        tz = timezone.get_current_timezone()
        at = lambda d, h=10: dt.datetime.combine(d, dt.time(h), tzinfo=tz)  # noqa: E731
        boss, sales, wh = users['boss'], users['sales'], users['warehouse']
        today = timezone.localdate()
        cust = {c.code: c for c in Customer._base_manager.filter(tenant=tenant)}
        sos = []
        for o in orders:
            ts, done = at(o['date']), o['status'] in ('SHIPPED', 'COMPLETED')
            sos.append(WholesaleOrder(tenant=tenant, customer=cust[o['customer']], number=o['number'], status=o['status'],
                                      notes=o['scenario'], created_by=sales,
                                      submitted_by=sales, submitted_at=ts,
                                      approved_by=boss if done else None, approved_at=ts if done else None,
                                      shipped_by=wh if done else None, shipped_at=ts if done else None,
                                      completed_by=boss if o['status'] == 'COMPLETED' else None,
                                      completed_at=ts if o['status'] == 'COMPLETED' else None))
        WholesaleOrder.objects.bulk_create(sos)
        WholesaleOrderLine.objects.bulk_create([
            WholesaleOrderLine(order=so, product=prods[o['sku']], quantity=o['bottles'],
                               unit_price=(o['amount'] / o['bottles']).quantize(Decimal('0.01')))
            for so, o in zip(sos, orders)])
        recs, rec_meta, moves = [], [], []
        for so, o in zip(sos, orders):
            if o['status'] not in ('SHIPPED', 'COMPLETED'):
                continue
            amt = (o['amount'] / o['bottles']).quantize(Decimal('0.01')) * o['bottles']
            got = amt if o['status'] == 'COMPLETED' else (amt / 2).quantize(Decimal('0.01'))
            recs.append(Receivable(tenant=tenant, customer=so.customer, wholesale_order=so, amount=amt, received_amount=got,
                                   status='SETTLED' if got == amt else 'PARTIAL',
                                   due_date=o['date'] + dt.timedelta(days=so.customer.payment_terms_days)))
            rec_meta.append((o, got))
            moves.append(InventoryTransaction(tenant=tenant, product=prods[o['sku']], transaction_type='OUT',
                                              quantity=o['bottles'], operator=wh, notes=f"批发发货 {o['number']}"))
        Receivable.objects.bulk_create(recs)
        entries = SettlementEntry.objects.bulk_create([
            SettlementEntry(tenant=tenant, kind='COLLECT', receivable=r, amount=got, operator=boss,
                            reference=f"回款-{o['number']}") for r, (o, got) in zip(recs, rec_meta)])
        moves = InventoryTransaction.objects.bulk_create(moves)
        for objs, metas, days in ((recs, rec_meta, 0), (entries, rec_meta, 20), (moves, rec_meta, 0)):
            for obj, (o, _g) in zip(objs, metas):
                obj.created_at = at(o['date'] + dt.timedelta(days=days))
            type(objs[0])._base_manager.bulk_update(objs, ['created_at'], batch_size=1000) if objs else None
        for so, o in zip(sos, orders):
            so.created_at = at(o['date'], 9)
        WholesaleOrder._base_manager.bulk_update(sos, ['created_at'], batch_size=1000)

        pos, rows = [], C.purchases()
        for x in rows:
            pos.append(PurchaseOrder(tenant=tenant, supplier=sups[x.supplier], number=x.id, status='RECEIVED',
                                     expected_date=x.arrive_date, notes=x.purpose.replace('库存补充', '库存补货'),  # 表内用词统一为业务口径
                                     created_by=users['purchaser'], submitted_by=users['purchaser'], submitted_at=at(x.order_date),
                                     approved_by=boss, approved_at=at(x.order_date, 14), received_by=wh, received_at=at(x.arrive_date)))
        PurchaseOrder.objects.bulk_create(pos)
        PurchaseOrderLine.objects.bulk_create([
            PurchaseOrderLine(order=po, product=raw, quantity=x.jin, unit_price=x.price_per_jin, received_quantity=x.jin)
            for po, x in zip(pos, rows)])
        pays = []
        for po, x in zip(pos, rows):
            paid = x.amount if x.arrive_date <= today - dt.timedelta(days=60) else (x.amount / 2).quantize(Decimal('0.01'))
            pays.append(Payable(tenant=tenant, supplier=po.supplier, purchase_order=po, amount=x.amount, paid_amount=paid,
                                status='SETTLED' if paid == x.amount else 'PARTIAL', due_date=x.arrive_date + dt.timedelta(days=30)))
        Payable.objects.bulk_create(pays)
        pentries = SettlementEntry.objects.bulk_create([
            SettlementEntry(tenant=tenant, kind='PAY', payable=pa, amount=pa.paid_amount, operator=boss,
                            reference=f'转账-{x.id}') for pa, x in zip(pays, rows)])
        for objs, extra in ((pos, 0), (pays, 0), (pentries, 15)):
            for obj, x in zip(objs, rows):
                obj.created_at = at((x.order_date if objs is pos else x.arrive_date) + dt.timedelta(days=extra))
            type(objs[0])._base_manager.bulk_update(objs, ['created_at'], batch_size=1000)
        n_sheet = sum(o['source'] == 'sheet' for o in orders)
        self.stdout.write(f"  工作簿：{n_sheet} 张批发订单、{len(pos)} 张基酒采购单；生成补充批发订单 {len(orders) - n_sheet} 张")

    def _backdate(self, obj, day, fields, number_prefix=None, seq=1):
        tz = timezone.get_current_timezone()
        ts = dt.datetime.combine(dt.date.fromisoformat(day), dt.time(10), tzinfo=tz)
        upd = {f: ts for f in fields if getattr(obj, f, None) is not None}
        type(obj)._base_manager.filter(pk=obj.pk).update(created_at=ts, **upd)
        return ts

    def _b2b_po(self, tenant, supplier, day, seq, status, note, lines, pay_ratio, maker, boss):
        from b2b import services as B
        from b2b.models import Payable, PurchaseOrder
        po = B.create_purchase_draft(tenant, supplier, lines, user=maker, source='MANUAL', notes=note)
        number = f"PO-{day.replace('-', '')}-{seq:04d}"
        PurchaseOrder._base_manager.filter(pk=po.pk).update(number=number)
        po.refresh_from_db()
        steps = {'DRAFT': [], 'SUBMITTED': ['submit'], 'APPROVED': ['submit', 'approve'],
                 'RECEIVED': ['submit', 'approve', 'receive']}[status]
        for a in steps:
            po = B.transition_purchase_order(po, a, maker if a == 'submit' else boss)
        ts = self._backdate(po, day, ['submitted_at', 'approved_at', 'received_at'])
        if status == 'RECEIVED':
            InventoryTransaction.objects.unscoped().filter(tenant=tenant, notes__contains=number).update(created_at=ts)
            payable = Payable._base_manager.get(purchase_order=po)
            Payable._base_manager.filter(pk=payable.pk).update(created_at=ts, due_date=ts.date() + dt.timedelta(days=30))
            if pay_ratio:
                payable.refresh_from_db()
                B.record_payment(payable, (payable.amount * Decimal(str(pay_ratio))).quantize(Decimal('0.01')), boss,
                                 reference=f'转账-{number}')
        return po

    def _b2b_so(self, tenant, customer, day, seq, status, note, lines, ratio, maker, boss):
        from b2b import services as B
        from b2b.models import Receivable, WholesaleOrder, WholesaleOrderLine
        so = WholesaleOrder(tenant=tenant, customer=customer, notes=note, created_by=maker,
                            number=f"SO-{day.replace('-', '')}-{seq:04d}")
        so.save()
        WholesaleOrderLine.objects.bulk_create([WholesaleOrderLine(order=so, product=p, quantity=q, unit_price=u) for p, q, u in lines])
        steps = {'DRAFT': [], 'SUBMITTED': ['submit'], 'APPROVED': ['submit', 'approve'],
                 'SHIPPED': ['submit', 'approve', 'ship'], 'COMPLETED': ['submit', 'approve', 'ship', 'complete']}[status]
        for a in steps:
            so = B.transition_wholesale_order(so, a, maker if a == 'submit' else boss)
        ts = self._backdate(so, day, ['submitted_at', 'approved_at', 'shipped_at', 'completed_at'])
        if status in ('SHIPPED', 'COMPLETED'):
            InventoryTransaction.objects.unscoped().filter(tenant=tenant, notes__contains=so.number).update(created_at=ts)
            rec = Receivable._base_manager.get(wholesale_order=so)
            Receivable._base_manager.filter(pk=rec.pk).update(created_at=ts, due_date=ts.date() + dt.timedelta(days=customer.payment_terms_days))
            if ratio:
                rec.refresh_from_db()
                B.record_receipt(rec, (rec.amount * Decimal(str(ratio))).quantize(Decimal('0.01')), boss,
                                 reference=f'回款-{so.number}')
        return so

    def _b2b_statement(self, tenant, supplier, start, end, status, boss):
        from b2b import services as B
        from b2b.models import SupplierStatement
        st = SupplierStatement.objects.create(tenant=tenant, supplier=supplier, period_start=dt.date.fromisoformat(start),
                                              period_end=dt.date.fromisoformat(end), created_by=boss,
                                              notes='月度对账')
        B.refresh_statement_amount(st)
        st.refresh_from_db()
        st.supplier_amount = st.system_amount
        st.save(update_fields=['supplier_amount'])
        if status == 'CONFIRMED':
            B.decide_statement(st, 'confirm', boss)
        return st

