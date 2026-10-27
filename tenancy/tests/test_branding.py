from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from tenancy.models import Membership, Role, Tenant


@override_settings(ALLOWED_HOSTS=['testserver'])
class BrandingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = Tenant.objects.create(name='甲酒业有限公司', short_name='甲酒业', code='a')
        cls.b = Tenant.objects.create(name='乙酒业有限公司', short_name='乙酒业', code='b')
        cls.boss = User.objects.create_user('boss', password='x')
        cls.clerk = User.objects.create_user('clerk', password='x')
        cls.other = User.objects.create_user('other', password='x')
        Membership.objects.create(user=cls.boss, tenant=cls.a, role=Role.BOSS, is_default=True)
        Membership.objects.create(user=cls.clerk, tenant=cls.a, role=Role.SALES, is_default=True)
        Membership.objects.create(user=cls.other, tenant=cls.b, role=Role.BOSS, is_default=True)

    def test_wordmark_and_color_render_from_tenant(self):
        self.client.force_login(self.boss)
        r = self.client.post('/tenancy/branding/', {'name': '甲酒业有限公司', 'short_name': '甲酒业',
                                                    'display_name': '甲字标', 'primary_color': '#123456'})
        self.assertRedirects(r, '/tenancy/branding/')
        html = self.client.get('/tenancy/').content.decode()
        self.assertIn('<span class="dejian-wordmark">甲字标</span>', html)
        self.assertIn('--bs-primary: #123456', html)
        self.assertIn('--bs-primary-rgb: 18, 52, 86', html)
        # 另一企业不受影响
        self.client.force_login(self.other)
        html = self.client.get('/tenancy/').content.decode()
        self.assertIn('<span class="dejian-wordmark">乙酒业</span>', html)
        self.assertNotIn('#123456', html)

    def test_only_boss_can_edit(self):
        self.client.force_login(self.clerk)
        self.assertEqual(self.client.get('/tenancy/branding/').status_code, 403)
        self.assertNotIn('/tenancy/branding/', self.client.get('/tenancy/').content.decode())

    def test_invalid_color_rejected(self):
        self.client.force_login(self.boss)
        r = self.client.post('/tenancy/branding/', {'name': 'x', 'display_name': '', 'primary_color': 'red'})
        self.assertEqual(r.status_code, 200)
        self.a.refresh_from_db()
        self.assertEqual(self.a.name, '甲酒业有限公司')

    def test_login_page_generic_or_tenant_by_code(self):
        html = self.client.get('/accounts/login/').content.decode()
        self.assertIn('筹策工作台', html)
        self.assertNotIn('德鉴', html)
        html = self.client.get('/accounts/login/?t=b').content.decode()
        self.assertIn('欢迎回到乙酒业', html)
