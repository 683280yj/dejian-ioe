import io
import re
from pathlib import Path

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from ai_assist import demo_profile as P
from ai_assist import services
from ai_assist.models import DraftTask, Suggestion
from inventory.models import Inventory
from tenancy.models import Tenant

HOSTS = override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])


@HOSTS
class DemoFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_dejian', days=400, stdout=io.StringIO())
        cls.dj = Tenant.objects.get(code='dejian')
        cls.other = Tenant.objects.get(code='demo-other')
        U = get_user_model()
        cls.boss, cls.purchaser, cls.sales = (U.objects.get(username=n) for n in ('dj_boss', 'dj_purchase', 'dj_sales'))

    def _restock(self, tenant=None):
        return Suggestion.objects.filter(tenant=tenant or self.dj, workflow='replenish', status='pending', quantity__gt=0).order_by('-score').first()

    # ---- seed
    def test_no_context_without_tenant(self):
        from ai_assist import hints
        req = RequestFactory().get('/')
        req.tenant = None
        self.assertEqual(hints.index_context(req), {})
        self.assertEqual(hints.inventory_context(req), {})

    def test_seed_shape_and_idempotent(self):
        # 6 个成品 + 1 个基酒原料
        self.assertEqual(apps.get_model('inventory', 'Product').objects.filter(tenant=self.dj).count(), len(P.SKUS) + 1)
        self.assertTrue(Suggestion.objects.filter(tenant=self.dj, workflow='replenish').exists())
        self.assertTrue(Suggestion.objects.filter(tenant=self.dj, workflow='stock_alert').exists())
        out = io.StringIO()
        call_command('seed_dejian', stdout=out)
        self.assertIn('已存在', out.getvalue())

    # ---- helpers render
    def test_view_context_for_ioe_pages(self):
        self.client.force_login(self.purchaser)
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('库存提示', r.context['stock_alert']['title'])
        r = self.client.get('/inventory/')
        self.assertEqual(r.status_code, 200)
        rows = r.context['replenish_suggestions']
        self.assertTrue(0 < len(rows) <= 5)
        row = rows[0]
        self.assertEqual(set(row), {'pk', 'product', 'target_label', 'title', 'suggested_qty', 'basis', 'explain', 'anomalies', 'ai_source'})
        self.assertGreater(row['suggested_qty'], 0)
        self.assertEqual(row['product'].tenant_id, self.dj.pk)
        self.assertEqual(reverse('ai_assist:suggestion_adopt', args=[row['pk']]), f"/ai/suggestions/{row['pk']}/adopt/")

    def test_other_tenant_sees_own_context_only(self):
        self.client.force_login(get_user_model().objects.get(username='other_boss'))
        r = self.client.get('/inventory/')
        for row in r.context.get('replenish_suggestions', []):
            self.assertEqual(row['product'].tenant_id, self.other.pk)

    # ---- adopt / dismiss
    def test_adopt_creates_b2b_draft_without_touching_stock(self):
        sug = self._restock()
        stock_before = list(Inventory.objects.filter(tenant=self.dj).order_by('pk').values_list('quantity', flat=True))
        self.client.force_login(self.purchaser)
        r = self.client.post(f'/ai/restock/{sug.pk}/adopt/', {'next': '/inventory/'})
        self.assertEqual(r.status_code, 302)
        sug.refresh_from_db()
        self.assertEqual(sug.status, 'adopted')
        task = DraftTask.objects.get(suggestion=sug)
        self.assertTrue(task.external_ref)
        PO = apps.get_model('b2b', 'PurchaseOrder')
        po = PO.objects.get(number=task.external_ref)
        self.assertEqual((po.status, po.source, po.tenant_id), ('DRAFT', 'AI_DRAFT', self.dj.pk))
        self.assertIn(f'/b2b/purchase-orders/{po.pk}/', r['Location'])
        stock_after = list(Inventory.objects.filter(tenant=self.dj).order_by('pk').values_list('quantity', flat=True))
        self.assertEqual(stock_before, stock_after)
        r = self.client.post(f'/ai/restock/{sug.pk}/adopt/', {'next': '/inventory/'})
        self.assertEqual(DraftTask.objects.filter(suggestion=sug).count(), 1)

    def test_role_required(self):
        sug = self._restock()
        self.client.force_login(self.sales)
        self.client.post(f'/ai/restock/{sug.pk}/adopt/', {'next': '/inventory/'})
        sug.refresh_from_db()
        self.assertEqual(sug.status, 'pending')

    def test_dismiss(self):
        sug = self._restock()
        self.client.force_login(self.purchaser)
        r = self.client.post(f'/ai/restock/{sug.pk}/dismiss/', {'next': 'https://evil.example/'})
        self.assertEqual(r.status_code, 302)
        self.assertFalse(r['Location'].startswith('https://evil'))
        sug.refresh_from_db()
        self.assertEqual(sug.status, 'rejected')
        self.assertTrue(sug.reject_reason)

    def test_foreign_tenant_404(self):
        sug = self._restock()
        self.client.force_login(get_user_model().objects.get(username='other_boss'))
        self.assertEqual(self.client.post(f'/ai/restock/{sug.pk}/adopt/').status_code, 404)

    def test_get_not_allowed_and_login_required(self):
        sug = self._restock()
        r = self.client.post(f'/ai/restock/{sug.pk}/adopt/')
        self.assertEqual(r.status_code, 302)
        self.assertIn('login', r['Location'])
        self.client.force_login(self.boss)
        self.assertEqual(self.client.get(f'/ai/restock/{sug.pk}/adopt/').status_code, 405)

    def test_refresh(self):
        self.client.force_login(self.boss)
        n = Suggestion.objects.filter(tenant=self.dj).count()
        r = self.client.post('/ai/refresh/', {'next': '/'})
        self.assertEqual(r.status_code, 302)
        self.assertGreater(Suggestion.objects.filter(tenant=self.dj).count(), n)

    def test_refresh_supersedes_old_stock_alerts(self):
        old = set(Suggestion.objects.filter(tenant=self.dj, workflow='stock_alert', status='auto_done').values_list('pk', flat=True))
        self.assertTrue(old)
        services.run_workflow(self.dj, 'stock_alert', {}, user=self.boss)
        self.assertFalse(Suggestion.objects.filter(pk__in=old).exclude(status='superseded').exists())
        self.assertTrue(Suggestion.objects.filter(tenant=self.dj, workflow='stock_alert', status='auto_done').exists())

    def test_b2b_seed_states_consistent(self):
        if not apps.is_installed('b2b'):
            self.skipTest('b2b 未安装')
        PO = apps.get_model('b2b', 'PurchaseOrder')
        SO = apps.get_model('b2b', 'WholesaleOrder')
        Payable, Receivable = apps.get_model('b2b', 'Payable'), apps.get_model('b2b', 'Receivable')
        St, Cust = apps.get_model('b2b', 'SupplierStatement'), apps.get_model('b2b', 'Customer')
        from tenancy import importer
        self.assertEqual(Cust.objects.filter(tenant=self.dj).count(), len(importer.sample_rows('customers')))
        po_states = set(PO.objects.filter(tenant=self.dj).values_list('status', flat=True))
        self.assertTrue({'DRAFT', 'SUBMITTED', 'APPROVED', 'RECEIVED'} <= po_states)
        so_states = set(SO.objects.filter(tenant=self.dj).values_list('status', flat=True))
        self.assertTrue({'DRAFT', 'SUBMITTED', 'APPROVED', 'SHIPPED', 'COMPLETED'} <= so_states)
        # 只有已入库/已发货的单据有应收应付，且部分付款状态存在
        self.assertEqual(Payable.objects.filter(tenant=self.dj).count(),
                         PO.objects.filter(tenant=self.dj, status='RECEIVED').count())
        self.assertEqual(Receivable.objects.filter(tenant=self.dj).count(),
                         SO.objects.filter(tenant=self.dj, status__in=['SHIPPED', 'COMPLETED']).count())
        self.assertTrue(Payable.objects.filter(tenant=self.dj, status='PARTIAL').exists())
        self.assertTrue(Receivable.objects.filter(tenant=self.dj, status='PARTIAL').exists())
        self.assertTrue(St.objects.filter(tenant=self.dj, status='DRAFT').exists())
        # 另一企业：小而非空，且与德鉴互不串
        self.assertTrue(PO.objects.filter(tenant=self.other).exists())
        self.assertTrue(SO.objects.filter(tenant=self.other).exists())
        self.assertFalse(SO.objects.filter(tenant=self.other, customer__tenant=self.dj).exists())

    def test_workbook_orders_imported_as_is(self):
        from django.db.models import Sum
        from ai_assist import case_data as C
        from inventory.models import Sale, SaleItem
        tot = C.totals()
        sheet = Sale.objects.filter(tenant=self.dj, remark__startswith='批发出库 XS-20')
        self.assertEqual(sheet.count(), tot['sales_rows'])
        self.assertEqual(sheet.aggregate(s=Sum('final_amount'))['s'], tot['amount'])
        self.assertEqual(SaleItem.objects.filter(sale__in=sheet).aggregate(q=Sum('quantity'))['q'], tot['bottles'])
        SO, PO = apps.get_model('b2b', 'WholesaleOrder'), apps.get_model('b2b', 'PurchaseOrder')
        first = C.sales()[0]
        so = SO.objects.get(tenant=self.dj, number=first.id)
        self.assertEqual((so.created_at.date(), so.lines.get().quantity, so.lines.get().product.barcode),
                         (first.date, first.bottles, first.sku))
        self.assertEqual(PO.objects.filter(tenant=self.dj, number__startswith='CG-').count(), tot['purchase_rows'])
        # 工作簿说明列、数据来源标注都不进用户可见字段
        self.assertFalse(SO.objects.filter(tenant=self.dj, notes__contains='仿真').exists())
        self.assertFalse(PO.objects.filter(tenant=self.dj, notes__contains='仿真').exists())
        self.assertFalse(apps.get_model('inventory', 'Supplier').objects.filter(tenant=self.dj, name__contains='仿真').exists())

    def test_no_provenance_labels_in_seeded_text(self):
        """seed 后任何文本字段都不出现来源/演示标注（只允许出现在代码注释与文档里）。"""
        from django.db import models as djm
        banned = ('仿真', '演示补充数据', '演示数据', '演示案例', '演示商品', '（演示）', '示例', '生成', '补充')
        hits = []
        for m in apps.get_models():
            if m._meta.app_label not in ('inventory', 'b2b', 'tenancy', 'ai_assist', 'auth'):
                continue
            fields = [f.name for f in m._meta.concrete_fields if isinstance(f, (djm.CharField, djm.TextField))
                      and not f.choices and f.name not in ('password',)]
            for f in fields:
                for w in banned:
                    n = m._base_manager.filter(**{f'{f}__contains': w}).count()
                    if n:
                        hits.append((m._meta.label, f, w, n))
        self.assertEqual(hits, [])

    def test_product_images_and_raw_material_kept_out_of_ai(self):
        Product = apps.get_model('inventory', 'Product')
        for sku, *_ in P.SKUS:
            p = Product.objects.get(tenant=self.dj, barcode=sku)
            self.assertTrue(p.image and p.image.name.endswith(f'{sku}.jpg'), p.image.name)
            self.assertEqual(p.description, P.DESCRIPTIONS[sku])
        raw = Product.objects.get(tenant=self.dj, barcode=P.RAW['sku'])
        self.assertFalse(Suggestion.objects.filter(tenant=self.dj, product=raw).exists())

    def test_stock_alert_writes_native_alert(self):
        self.assertTrue(apps.get_model('inventory', 'StockAlert').objects.filter(tenant=self.dj, is_active=True).exists())

    # ---- safety
    def test_ai_code_never_calls_b2b_transitions(self):
        root = Path(__file__).resolve().parents[1]
        banned = re.compile(r'\b(transition_\w+|record_\w+|decide_statement|update_inventory)\s*\(')
        for p in root.rglob('*.py'):
            if 'tests' in p.parts or 'migrations' in p.parts:
                continue
            self.assertIsNone(banned.search(p.read_text()), p)

    def test_old_pages_removed(self):
        self.client.force_login(self.boss)
        for url in ('/ai/', '/ai/backtest/', '/ai/data-inventory/'):
            self.assertEqual(self.client.get(url).status_code, 404, url)

    # ---- commands
    def test_backtest_command(self):
        out = io.StringIO()
        call_command('ai_backtest', sim_days=60, stdout=out)
        s = out.getvalue()
        self.assertIn('演示数据', s)
        self.assertIn('缺货率', s)

    def test_refresh_command(self):
        out = io.StringIO()
        call_command('ai_refresh', tenant='dejian', stdout=out)
        self.assertIn('补货', out.getvalue())

    def test_user_can(self):
        m = self.purchaser.tenant_memberships.get(tenant=self.dj)
        self.assertTrue(services.user_can(self.purchaser, m, 'purchaser'))
        self.assertFalse(services.user_can(self.purchaser, m, 'warehouse'))
