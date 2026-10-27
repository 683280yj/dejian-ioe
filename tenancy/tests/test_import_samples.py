"""导入页「参考模板（已填写）」：下载 → 预览 → 确认，导入一个全新的企业，条数与示例一致。

商品条码与订单号全局唯一，所以这里的新企业所在库里没有德鉴租户（真实库里德鉴已占用，
其他企业应换成自己的条码/单号）。
"""
import io

from django.apps import apps
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from b2b.models import Customer, PurchaseOrder, WholesaleOrder
from inventory.models import Inventory, Product
from tenancy import importer
from tenancy.models import Brand, Membership, Role, Tenant, Warehouse


@override_settings(ALLOWED_HOSTS=['testserver'])
class ImportSampleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.t = Tenant.objects.create(name='新开通酒企', code='fresh')
        cls.boss = User.objects.create_user('fresh_boss', password='x')
        Membership.objects.create(user=cls.boss, tenant=cls.t, role=Role.BOSS, is_default=True)

    def _roundtrip(self, kind, fmt):
        r = self.client.get(f'/tenancy/import/sample/{kind}.{fmt}')
        self.assertEqual(r.status_code, 200)
        self.assertIn('filled', r['Content-Disposition'])
        f = SimpleUploadedFile(f'{kind}.{fmt}', r.content)
        r = self.client.post('/tenancy/import/', {'kind': kind, 'step': 'preview', 'file': f})
        self.assertTrue(r.context['can_confirm'], [x for x in r.context['preview'] if x['errors']])
        self.client.post('/tenancy/import/', {'step': 'confirm'})

    def _check_all(self, fmt):
        self.client.force_login(self.boss)
        for kind in ('products', 'stock', 'customers', 'purchase_orders', 'wholesale_orders'):
            self._roundtrip(kind, fmt)
        self.assertEqual(Product.objects.unscoped().filter(tenant=self.t).count(),
                         len(importer.sample_rows('products')))
        self.assertEqual(Inventory.objects.unscoped().filter(tenant=self.t).count(),
                         len(importer.sample_rows('stock')))
        self.assertEqual(Customer._base_manager.filter(tenant=self.t).count(),
                         len(importer.sample_rows('customers')))
        wo_rows = importer.sample_rows('wholesale_orders')
        po_rows = importer.sample_rows('purchase_orders')
        self.assertEqual(WholesaleOrder.objects.filter(tenant=self.t).count(),
                         len({r[0] for r in wo_rows}))
        self.assertEqual(PurchaseOrder.objects.filter(tenant=self.t).count(),
                         len({r[0] for r in po_rows}))
        self.assertEqual(sum(o.lines.count() for o in WholesaleOrder.objects.filter(tenant=self.t)),
                         len(wo_rows))
        self.assertEqual(sum(o.lines.count() for o in PurchaseOrder.objects.filter(tenant=self.t)),
                         len(po_rows))
        self.assertTrue(Brand.objects.filter(tenant=self.t, code='RY').exists())
        self.assertTrue(Warehouse.objects.filter(tenant=self.t, code='GY').exists())
        for barcode, qty, *_ in importer.sample_rows('stock'):
            self.assertEqual(Inventory.objects.unscoped().get(product__barcode=barcode).quantity, int(qty))

    def test_csv_samples_import_into_fresh_tenant(self):
        self._check_all('csv')

    def test_xlsx_samples_import_into_fresh_tenant(self):
        self._check_all('xlsx')

    def test_sample_columns_match_importer_and_page_labels(self):
        from openpyxl import load_workbook
        for kind, spec in importer.KINDS.items():
            ws = load_workbook(io.BytesIO(importer.sample_xlsx(kind))).active
            self.assertEqual([c.value for c in ws[1]], [label for _f, label, _r in spec['columns']])
            self.assertTrue(all(len(r) == len(spec['columns']) for r in importer.sample_rows(kind)))
        self.client.force_login(self.boss)
        html = self.client.get('/tenancy/import/').content.decode()
        self.assertIn('参考模板（已填写）', html)
        self.assertNotIn('演示', html)
        self.assertIn('下载后可直接上传', html)
        for label in ('商品', '期初库存', '客户/经销商', '批发订单', '采购订单'):
            self.assertIn(label, html)

    def test_samples_come_from_workbook(self):
        from ai_assist import case_data as C
        rows = {r[0]: r for r in importer.sample_rows('products')}
        for tier, sku in C.TIER_SKU.items():
            self.assertEqual(rows[sku][5], str(C.tier_price(tier)))
            self.assertIn(C.tier_label(tier), rows[sku][4])
        codes = {r[0] for r in importer.sample_rows('customers')}
        self.assertTrue(set(C.customers()) <= codes)
        wo_numbers = {r[0] for r in importer.sample_rows('wholesale_orders')}
        self.assertTrue({r.id for r in C.sales()} <= wo_numbers)
        po_numbers = {r[0] for r in importer.sample_rows('purchase_orders')}
        self.assertTrue({r.id for r in C.purchases()} <= po_numbers)
