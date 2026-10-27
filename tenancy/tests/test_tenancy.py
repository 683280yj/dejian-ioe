from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from inventory.models import Category
from tenancy.context import get_current_tenant, use_tenant
from tenancy.models import Brand, Membership, Role, Tenant


@override_settings(ALLOWED_HOSTS=['testserver'])
class TenancyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = Tenant.objects.create(name='A 酒业', code='a')
        cls.b = Tenant.objects.create(name='B 酒业', code='b')
        cls.ba = Brand.objects.create(tenant=cls.a, name='A1', code='A1')
        cls.bb = Brand.objects.create(tenant=cls.b, name='B1', code='B1')
        cls.u = User.objects.create_user('u', password='x')
        Membership.objects.create(user=cls.u, tenant=cls.a, role=Role.BOSS, is_default=True)
        Membership.objects.create(user=cls.u, tenant=cls.b, role=Role.FINANCE)

    def test_manager_filters_by_current_tenant(self):
        Category.objects.create(name='甲', tenant=self.a)
        Category.objects.create(name='乙', tenant=self.b)
        self.assertEqual(Category.objects.count(), 2)  # 无上下文不过滤
        with use_tenant(self.a):
            self.assertEqual(list(Category.objects.values_list('name', flat=True)), ['甲'])
        self.assertIsNone(get_current_tenant())

    def test_pre_save_fills_tenant(self):
        with use_tenant(self.b):
            c = Category.objects.create(name='自动带租户')
        self.assertEqual(c.tenant_id, self.b.pk)

    def test_middleware_default_and_switch(self):
        self.client.force_login(self.u)
        r = self.client.get('/tenancy/')
        self.assertEqual(r.context['current_tenant'], self.a)
        self.assertEqual(r.context['current_role'], Role.BOSS)
        self.client.post('/tenancy/switch/', {'tenant_id': self.b.pk, 'next': '/tenancy/'})
        r = self.client.get('/tenancy/')
        self.assertEqual(r.context['current_tenant'], self.b)
        self.assertEqual(r.context['current_role'], Role.FINANCE)

    def test_cannot_switch_to_foreign_tenant_or_brand(self):
        c = Tenant.objects.create(name='C', code='c')
        self.client.force_login(self.u)
        self.client.post('/tenancy/switch/', {'tenant_id': c.pk})
        self.assertEqual(self.client.get('/tenancy/').context['current_tenant'], self.a)
        self.client.post('/tenancy/switch/', {'brand_id': self.bb.pk})
        self.assertIsNone(self.client.get('/tenancy/').context['current_brand'])
        self.client.post('/tenancy/switch/', {'brand_id': self.ba.pk})
        self.assertEqual(self.client.get('/tenancy/').context['current_brand'], self.ba)

    def test_open_redirect_blocked(self):
        self.client.force_login(self.u)
        r = self.client.post('/tenancy/switch/', {'tenant_id': self.a.pk, 'next': 'https://evil.example/'})
        self.assertEqual(r.url, '/')

    def test_role_groups_synced(self):
        names = set(self.u.groups.values_list('name', flat=True))
        self.assertIn(f'角色:{Role.BOSS.label}', names)
        self.assertIn(f'角色:{Role.FINANCE.label}', names)
