import io

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from b2b.models import Customer
from inventory.models import Category, Inventory, InventoryTransaction, Product
from tenancy.models import Brand, Membership, Role, Tenant, Warehouse


def csv_file(text, name='data.csv'):
    return SimpleUploadedFile(name, text.encode('utf-8-sig'), content_type='text/csv')


@override_settings(ALLOWED_HOSTS=['testserver'])
class ImportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = Tenant.objects.create(name='甲酒业', code='a')
        cls.b = Tenant.objects.create(name='乙酒业', code='b')
        Brand.objects.create(tenant=cls.a, name='甲牌', code='BR1')
        Warehouse.objects.create(tenant=cls.a, name='一号仓', code='WH1')
        cls.boss = User.objects.create_user('boss', password='x')
        cls.sales = User.objects.create_user('sales', password='x')
        cls.other = User.objects.create_user('other', password='x')
        Membership.objects.create(user=cls.boss, tenant=cls.a, role=Role.BOSS, is_default=True)
        Membership.objects.create(user=cls.sales, tenant=cls.a, role=Role.SALES, is_default=True)
        Membership.objects.create(user=cls.other, tenant=cls.b, role=Role.BOSS, is_default=True)

    def _preview(self, kind, f):
        return self.client.post('/tenancy/import/', {'kind': kind, 'step': 'preview', 'file': f})

    def _confirm(self):
        return self.client.post('/tenancy/import/', {'step': 'confirm'})

    def test_templates_download(self):
        self.client.force_login(self.boss)
        r = self.client.get('/tenancy/import/template/products.csv')
        self.assertEqual(r.status_code, 200)
        self.assertIn('条码,商品名称,分类', r.content.decode('utf-8-sig'))
        r = self.client.get('/tenancy/import/template/customers.xlsx')
        from openpyxl import load_workbook
        ws = load_workbook(io.BytesIO(r.content)).active
        self.assertEqual(ws.cell(1, 1).value, '客户编码')

    def test_preview_does_not_write_then_confirm_writes_to_own_tenant(self):
        self.client.force_login(self.boss)
        f = csv_file('条码,商品名称,分类,品牌编码,规格,售价,成本价,箱规\n690001,甲酱香,自有,BR1,500ml,298,150,6\n')
        r = self._preview('products', f)
        self.assertTrue(r.context['can_confirm'])
        self.assertFalse(Product.objects.filter(barcode='690001').exists())
        self._confirm()
        p = Product.objects.get(barcode='690001')
        self.assertEqual((p.tenant, p.brand.code, p.case_size), (self.a, 'BR1', 6))
        self.assertEqual(Category.objects.get(name='自有').tenant, self.a)
        # 期初库存
        self._preview('stock', csv_file('条码,库存数量,预警数量,仓库编码\n690001,120,24,WH1\n'))
        self._confirm()
        inv = Inventory.objects.get(product=p)
        self.assertEqual((inv.quantity, inv.warning_level, inv.warehouse.code, inv.tenant), (120, 24, 'WH1', self.a))
        self.assertEqual(InventoryTransaction.objects.get(product=p).quantity, 120)
        # 再次导入同一数量不产生流水
        self._preview('stock', csv_file('条码,库存数量\n690001,120\n'))
        self._confirm()
        self.assertEqual(InventoryTransaction.objects.filter(product=p).count(), 1)

    def test_errors_block_confirm(self):
        self.client.force_login(self.boss)
        r = self._preview('products', csv_file('条码,商品名称,分类,售价,成本价\nX1,甲,自有,abc,1\nX1,乙,自有,1,1\n'))
        self.assertFalse(r.context['can_confirm'])
        self.assertEqual(r.context['error_count'], 2)
        self._confirm()
        self.assertFalse(Product.objects.filter(barcode='X1').exists())
        r = self._preview('products', csv_file('名称\n甲\n'))
        self.assertIsNone(r.context.get('preview'))

    def test_tenant_isolation(self):
        other_cat = Category.objects.create(tenant=self.b, name='乙类')
        Product.objects.create(tenant=self.b, barcode='B-1', name='乙酒', category=other_cat, price=1, cost=1)
        self.client.force_login(self.boss)
        r = self._preview('products', csv_file('条码,商品名称,分类,售价,成本价\nB-1,抢占,自有,1,1\n'))
        self.assertIn('条码已被其他企业使用', r.context['preview'][0]['errors'])
        r = self._preview('stock', csv_file('条码,库存数量\nB-1,5\n'))
        self.assertFalse(r.context['can_confirm'])
        self.assertEqual(Product.objects.unscoped().get(barcode='B-1').name, '乙酒')
        # 甲企业预览后切到乙企业确认：不应写入
        self._preview('customers', csv_file('客户编码,客户名称\nC1,甲客户\n'))
        self.client.force_login(self.other)
        self._confirm()
        self.assertFalse(Customer.objects.filter(code='C1').exists())

    def test_customers_xlsx_and_role_scope(self):
        from openpyxl import Workbook
        wb = Workbook()
        wb.active.append(['客户编码', '客户名称', '类型', '信用额度', '账期(天)'])
        wb.active.append(['C9', '甲经销商', '终端门店', 50000, 45])
        buf = io.BytesIO()
        wb.save(buf)
        self.client.force_login(self.sales)
        kinds = dict(self.client.get('/tenancy/import/').context['kinds'])
        self.assertEqual(list(kinds), ['customers', 'wholesale_orders'])
        self.assertEqual(self.client.get('/tenancy/import/template/products.csv').status_code, 404)
        self._preview('customers', SimpleUploadedFile('c.xlsx', buf.getvalue()))
        self._confirm()
        c = Customer.objects.get(code='C9')
        self.assertEqual((c.tenant, c.kind, c.credit_limit, c.payment_terms_days), (self.a, 'RETAILER', 50000, 45))
