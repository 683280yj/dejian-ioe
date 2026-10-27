from decimal import Decimal
from datetime import timedelta

from django.contrib.auth.models import Permission, User
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from inventory.models import Category, Inventory, InventoryTransaction, Product, Supplier
from b2b import services
from b2b.models import (
    Customer, Payable, PurchaseOrder, PurchaseOrderLine, Receivable, SettlementEntry,
    SupplierStatement, WholesaleOrder, WholesaleOrderLine,
)
from b2b.services import InvalidTransition


class Base(TestCase):
    def setUp(self):
        self.boss = User.objects.create_superuser('boss', 'b@x.cn', 'pw')
        self.clerk = User.objects.create_user('clerk', 'c@x.cn', 'pw')
        cat = Category.objects.create(name='白酒')
        self.product = Product.objects.create(barcode='DJ-53-500-2021', name='演示酱香 53度 500ml',
                                              category=cat, price=Decimal('1288'), cost=Decimal('600'))
        self.supplier = Supplier.objects.create(name='演示酒厂')
        self.customer = Customer.objects.create(code='D001', name='演示经销商', payment_terms_days=45)

    def stock(self):
        inv = Inventory.objects.filter(product=self.product).first()
        return inv.quantity if inv else 0

    def make_po(self, qty=10, price='600'):
        po = PurchaseOrder.objects.create(supplier=self.supplier, created_by=self.clerk)
        PurchaseOrderLine.objects.create(order=po, product=self.product, quantity=qty, unit_price=Decimal(price))
        return po

    def make_so(self, qty=4, price='1000'):
        so = WholesaleOrder.objects.create(customer=self.customer, created_by=self.clerk)
        WholesaleOrderLine.objects.create(order=so, product=self.product, quantity=qty, unit_price=Decimal(price))
        return so

    def refresh(self, obj):
        obj.refresh_from_db()
        return obj


class PurchaseOrderFlowTests(Base):
    def test_created_as_draft_and_nothing_auto_advances(self):
        po = self.make_po()
        self.assertEqual(po.status, 'DRAFT')
        self.assertTrue(po.number.startswith('PO-'))
        po.notes = 'edit'
        po.save()
        self.assertEqual(self.refresh(po).status, 'DRAFT')
        self.assertEqual(self.stock(), 0)
        self.assertFalse(Payable.objects.exists())
        self.assertFalse(InventoryTransaction.objects.exists())

    def test_full_human_flow_stocks_in_and_creates_payable(self):
        po = self.make_po(qty=10, price='600')
        for action in ('submit', 'approve'):
            services.transition_purchase_order(po, action, self.boss)
            self.assertEqual(self.stock(), 0, 'approve must not touch stock')
        self.assertFalse(Payable.objects.exists())
        services.transition_purchase_order(po, 'receive', self.boss)
        po = self.refresh(po)
        self.assertEqual(po.status, 'RECEIVED')
        self.assertEqual(po.received_by, self.boss)
        self.assertEqual(self.stock(), 10)
        payable = po.payable
        self.assertEqual(payable.amount, Decimal('6000'))
        self.assertEqual(payable.status, 'OPEN')
        self.assertEqual(payable.paid_amount, 0)

    def test_invalid_transitions_rejected(self):
        po = self.make_po()
        for action in ('approve', 'receive'):
            with self.assertRaises(InvalidTransition):
                services.transition_purchase_order(po, action, self.boss)
        services.transition_purchase_order(po, 'submit', self.boss)
        with self.assertRaises(InvalidTransition):
            services.transition_purchase_order(po, 'receive', self.boss)  # 跳过审批
        with self.assertRaises(InvalidTransition):
            services.transition_purchase_order(po, 'submit', self.boss)
        services.transition_purchase_order(po, 'approve', self.boss)
        services.transition_purchase_order(po, 'receive', self.boss)
        for action in ('receive', 'cancel', 'approve'):
            with self.assertRaises(InvalidTransition):
                services.transition_purchase_order(po, action, self.boss)
        self.assertEqual(self.stock(), 10, 'double receive must not double stock')
        with self.assertRaises(InvalidTransition):
            services.transition_purchase_order(po, 'auto_approve', self.boss)

    def test_empty_order_cannot_be_submitted(self):
        po = PurchaseOrder.objects.create(supplier=self.supplier)
        with self.assertRaises(InvalidTransition):
            services.transition_purchase_order(po, 'submit', self.boss)

    def test_requires_human_actor(self):
        po = self.make_po()
        with self.assertRaises(PermissionDenied):
            services.transition_purchase_order(po, 'submit', None)
        inactive = User.objects.create_user('bot', password='pw', is_active=False)
        with self.assertRaises(PermissionDenied):
            services.transition_purchase_order(po, 'submit', inactive)
        self.assertEqual(self.refresh(po).status, 'DRAFT')

    def test_approve_requires_permission(self):
        po = self.make_po()
        services.transition_purchase_order(po, 'submit', self.clerk)
        with self.assertRaises(PermissionDenied):
            services.transition_purchase_order(po, 'approve', self.clerk)
        self.clerk.user_permissions.add(Permission.objects.get(codename='approve_purchaseorder'))
        self.clerk = User.objects.get(pk=self.clerk.pk)
        services.transition_purchase_order(po, 'approve', self.clerk)
        with self.assertRaises(PermissionDenied):
            services.transition_purchase_order(po, 'receive', self.clerk)
        self.assertEqual(self.refresh(po).status, 'APPROVED')


class WholesaleOrderFlowTests(Base):
    def setUp(self):
        super().setUp()
        po = self.make_po(qty=10)
        for a in ('submit', 'approve', 'receive'):
            services.transition_purchase_order(po, a, self.boss)

    def test_full_human_flow_ships_and_creates_receivable(self):
        so = self.make_so(qty=4, price='1000')
        self.assertEqual(so.status, 'DRAFT')
        services.transition_wholesale_order(so, 'submit', self.boss)
        services.transition_wholesale_order(so, 'approve', self.boss)
        self.assertEqual(self.stock(), 10, 'approve must not ship')
        self.assertFalse(Receivable.objects.exists())
        services.transition_wholesale_order(so, 'ship', self.boss)
        self.assertEqual(self.stock(), 6)
        rec = self.refresh(so).receivable
        self.assertEqual(rec.amount, Decimal('4000'))
        self.assertEqual(rec.due_date, timezone.localdate() + timedelta(days=45))
        services.transition_wholesale_order(so, 'complete', self.boss)
        self.assertEqual(self.refresh(so).status, 'COMPLETED')
        self.assertEqual(self.refresh(rec).status, 'OPEN', 'sign-off must not auto-collect')

    def test_invalid_transitions_rejected(self):
        so = self.make_so()
        with self.assertRaises(InvalidTransition):
            services.transition_wholesale_order(so, 'ship', self.boss)
        services.transition_wholesale_order(so, 'submit', self.boss)
        with self.assertRaises(InvalidTransition):
            services.transition_wholesale_order(so, 'ship', self.boss)
        with self.assertRaises(InvalidTransition):
            services.transition_wholesale_order(so, 'complete', self.boss)
        services.transition_wholesale_order(so, 'approve', self.boss)
        services.transition_wholesale_order(so, 'ship', self.boss)
        with self.assertRaises(InvalidTransition):
            services.transition_wholesale_order(so, 'ship', self.boss)
        with self.assertRaises(InvalidTransition):
            services.transition_wholesale_order(so, 'cancel', self.boss)
        self.assertEqual(self.stock(), 6)

    def test_insufficient_stock_rolls_back(self):
        so = self.make_so(qty=50)
        services.transition_wholesale_order(so, 'submit', self.boss)
        services.transition_wholesale_order(so, 'approve', self.boss)
        with self.assertRaises(InvalidTransition):
            services.transition_wholesale_order(so, 'ship', self.boss)
        self.assertEqual(self.refresh(so).status, 'APPROVED')
        self.assertEqual(self.stock(), 10)
        self.assertFalse(Receivable.objects.exists())

    def test_ship_requires_permission(self):
        so = self.make_so()
        services.transition_wholesale_order(so, 'submit', self.clerk)
        services.transition_wholesale_order(so, 'approve', self.boss)
        with self.assertRaises(PermissionDenied):
            services.transition_wholesale_order(so, 'ship', self.clerk)
        self.assertEqual(self.stock(), 10)


class SettlementTests(Base):
    def setUp(self):
        super().setUp()
        po = self.make_po(qty=10, price='600')
        for a in ('submit', 'approve', 'receive'):
            services.transition_purchase_order(po, a, self.boss)
        self.payable = po.payable

    def test_partial_then_full_payment(self):
        services.record_payment(self.payable, '1000', self.boss, 'TX1')
        p = self.refresh(self.payable)
        self.assertEqual((p.status, p.paid_amount), ('PARTIAL', Decimal('1000')))
        services.record_payment(p, '5000', self.boss, 'TX2')
        p = self.refresh(p)
        self.assertEqual(p.status, 'SETTLED')
        self.assertEqual(SettlementEntry.objects.filter(kind='PAY').count(), 2)
        with self.assertRaises(InvalidTransition):
            services.record_payment(p, '1', self.boss)

    def test_overpay_and_bad_amount_rejected(self):
        for amt in ('7000', '0', '-5'):
            with self.assertRaises(InvalidTransition):
                services.record_payment(self.payable, amt, self.boss)
        self.assertEqual(self.refresh(self.payable).paid_amount, 0)

    def test_payment_requires_permission_and_human(self):
        with self.assertRaises(PermissionDenied):
            services.record_payment(self.payable, '10', self.clerk)
        with self.assertRaises(PermissionDenied):
            services.record_payment(self.payable, '10', None)

    def test_receipt(self):
        so = self.make_so(qty=2, price='1000')
        for a in ('submit', 'approve', 'ship'):
            services.transition_wholesale_order(so, a, self.boss)
        rec = self.refresh(so).receivable
        services.record_receipt(rec, '2000', self.boss, 'BANK1')
        self.assertEqual(self.refresh(rec).status, 'SETTLED')
        self.assertEqual(self.customer.outstanding, 0)


class StatementTests(Base):
    def setUp(self):
        super().setUp()
        po = self.make_po(qty=10, price='600')
        for a in ('submit', 'approve', 'receive'):
            services.transition_purchase_order(po, a, self.boss)
        today = timezone.localdate()
        self.st = SupplierStatement.objects.create(supplier=self.supplier, period_start=today - timedelta(days=30), period_end=today)
        services.refresh_statement_amount(self.st)

    def test_system_amount_and_no_auto_confirm(self):
        st = self.refresh(self.st)
        self.assertEqual(st.system_amount, Decimal('6000'))
        self.assertEqual(st.status, 'DRAFT')

    def test_confirm_requires_matching_amount(self):
        with self.assertRaises(InvalidTransition):
            services.decide_statement(self.st, 'confirm', self.boss)  # 未录入
        self.st.supplier_amount = Decimal('6100')
        self.st.save()
        with self.assertRaises(InvalidTransition):
            services.decide_statement(self.st, 'confirm', self.boss)  # 有差异
        services.decide_statement(self.st, 'dispute', self.boss)
        st = self.refresh(self.st)
        self.assertEqual(st.status, 'DISPUTED')
        with self.assertRaises(InvalidTransition):
            services.decide_statement(st, 'confirm', self.boss)

    def test_confirm_matching(self):
        self.st.supplier_amount = Decimal('6000')
        self.st.save()
        with self.assertRaises(PermissionDenied):
            services.decide_statement(self.st, 'confirm', self.clerk)
        services.decide_statement(self.st, 'confirm', self.boss)
        st = self.refresh(self.st)
        self.assertEqual((st.status, st.decided_by), ('CONFIRMED', self.boss))
        with self.assertRaises(InvalidTransition):
            services.refresh_statement_amount(st)


class ViewTests(Base):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.boss)

    def test_pages_render(self):
        po, so = self.make_po(), self.make_so()
        today = timezone.localdate()
        st = SupplierStatement.objects.create(supplier=self.supplier, period_start=today, period_end=today)
        for name, args in [('dashboard', []), ('customer_list', []), ('customer_create', []),
                           ('customer_edit', [self.customer.pk]), ('po_list', []), ('po_create', []),
                           ('po_detail', [po.pk]), ('so_list', []), ('so_create', []), ('so_detail', [so.pk]),
                           ('statement_list', []), ('statement_create', []), ('statement_detail', [st.pk]),
                           ('payable_list', []), ('receivable_list', [])]:
            resp = self.client.get(reverse(f'b2b:{name}', args=args))
            self.assertEqual(resp.status_code, 200, name)

    def test_login_required(self):
        self.client.logout()
        resp = self.client.get(reverse('b2b:po_list'))
        self.assertEqual(resp.status_code, 302)
        po = self.make_po()
        self.client.post(reverse('b2b:po_transition', args=[po.pk, 'submit']))
        self.assertEqual(self.refresh(po).status, 'DRAFT')

    def test_transition_get_not_allowed(self):
        po = self.make_po()
        resp = self.client.get(reverse('b2b:po_transition', args=[po.pk, 'submit']))
        self.assertEqual(resp.status_code, 405)
        self.assertEqual(self.refresh(po).status, 'DRAFT')

    def test_unknown_action_404(self):
        po = self.make_po()
        resp = self.client.post(reverse('b2b:po_transition', args=[po.pk, 'autoapprove']))
        self.assertEqual(resp.status_code, 404)

    def test_create_po_via_view_is_draft_then_human_posts(self):
        resp = self.client.post(reverse('b2b:po_create'), {'supplier': self.supplier.pk, 'notes': 'x'})
        po = PurchaseOrder.objects.get()
        self.assertRedirects(resp, reverse('b2b:po_detail', args=[po.pk]))
        self.assertEqual(po.status, 'DRAFT')
        self.client.post(reverse('b2b:po_detail', args=[po.pk]),
                         {'product': self.product.pk, 'quantity': 3, 'unit_price': '500'})
        self.assertEqual(po.lines.count(), 1)
        for a in ('submit', 'approve', 'receive'):
            self.client.post(reverse('b2b:po_transition', args=[po.pk, a]))
        self.assertEqual(self.refresh(po).status, 'RECEIVED')
        self.assertEqual(self.stock(), 3)

    def test_invalid_transition_via_view_shows_error(self):
        po = self.make_po()
        resp = self.client.post(reverse('b2b:po_transition', args=[po.pk, 'receive']), follow=True)
        self.assertContains(resp, '不能执行')
        self.assertEqual(self.refresh(po).status, 'DRAFT')
        self.assertEqual(self.stock(), 0)

    def test_view_permission_denied(self):
        po = self.make_po()
        services.transition_purchase_order(po, 'submit', self.boss)
        self.client.force_login(self.clerk)
        resp = self.client.post(reverse('b2b:po_transition', args=[po.pk, 'approve']))
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(self.refresh(po).status, 'SUBMITTED')

    def test_payment_via_view(self):
        po = self.make_po(qty=1, price='100')
        for a in ('submit', 'approve', 'receive'):
            services.transition_purchase_order(po, a, self.boss)
        self.client.post(reverse('b2b:payable_pay', args=[po.payable.pk]), {'amount': '100', 'reference': 'T'})
        self.assertEqual(self.refresh(po.payable).status, 'SETTLED')

    def test_cannot_add_line_after_submit(self):
        po = self.make_po()
        services.transition_purchase_order(po, 'submit', self.boss)
        resp = self.client.post(reverse('b2b:po_detail', args=[po.pk]),
                                {'product': self.product.pk, 'quantity': 1, 'unit_price': '1'})
        self.assertEqual(resp.status_code, 403)


class TenantScopeTests(Base):
    """lane-a 中间件设置 request.tenant 后，跨租户访问应 404。"""

    def test_cross_tenant_404(self):
        from django.apps import apps
        Tenant = apps.get_model('tenancy', 'Tenant')
        t1 = Tenant.objects.create(name='德鉴')
        t2 = Tenant.objects.create(name='其他')
        po = self.make_po()
        po.tenant = t2
        po.save()
        from django.test import RequestFactory
        from b2b import views
        req = RequestFactory().get('/')
        req.user, req.tenant = self.boss, t1
        from django.http import Http404
        with self.assertRaises(Http404):
            views.get_scoped(req, PurchaseOrder, po.pk)
        req.tenant = t2
        self.assertEqual(views.get_scoped(req, PurchaseOrder, po.pk), po)


class NoAutomationTests(TestCase):
    """守住铁律：b2b 不注册任何会自动推进状态的信号接收器。"""

    def test_no_b2b_signal_receivers(self):
        from django.db.models import signals
        from b2b import models as m
        for sig in (signals.post_save, signals.pre_save):
            for model in (m.PurchaseOrder, m.WholesaleOrder, m.Payable, m.Receivable, m.SupplierStatement,
                          m.PurchaseOrderLine, m.WholesaleOrderLine):
                receivers = [r for r in sig._live_receivers(model)]
                receivers = receivers[0] if receivers and isinstance(receivers[0], list) else receivers
                mods = [getattr(r, '__module__', '') for r in receivers]
                self.assertFalse([x for x in mods if x.startswith('b2b')], f'{sig} {model}')

    def test_status_not_form_editable(self):
        from b2b.forms import PurchaseOrderForm, WholesaleOrderForm, SupplierAmountForm
        for f in (PurchaseOrderForm, WholesaleOrderForm, SupplierAmountForm):
            self.assertNotIn('status', f.base_fields)


class AIDraftTests(Base):
    def test_create_purchase_draft_is_only_a_draft(self):
        po = services.create_purchase_draft(None, self.supplier, [(self.product, 12, '580')], user=None)
        po = self.refresh(po)
        self.assertEqual((po.status, po.source), ('DRAFT', 'AI_DRAFT'))
        self.assertIsNone(po.submitted_by)
        self.assertIsNone(po.approved_by)
        self.assertEqual(po.total_amount, Decimal('6960'))
        self.assertEqual(self.stock(), 0)
        self.assertFalse(Payable.objects.exists())
        # 只能由人继续推进
        with self.assertRaises(PermissionDenied):
            services.transition_purchase_order(po, 'submit', None)

    def test_create_purchase_draft_validates(self):
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            services.create_purchase_draft(None, self.supplier, [])
        with self.assertRaises(ValidationError):
            services.create_purchase_draft(None, self.supplier, [{'product': self.product, 'quantity': 0, 'unit_price': 1}])
        with self.assertRaises(ValueError):
            services.create_purchase_draft(None, self.supplier, [(self.product, 1, 1)], source='APPROVED')
