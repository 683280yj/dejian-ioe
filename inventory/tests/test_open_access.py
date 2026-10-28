from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from tenancy.models import Membership, Role, Tenant


@override_settings(ALLOWED_HOSTS=['testserver'])
class OpenAccessLoginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.create(name='德鉴酒业', short_name='德鉴', code='dejian')
        cls.boss = User.objects.create_user('dj_boss', password='secret-in-db')
        Membership.objects.create(user=cls.boss, tenant=cls.tenant, role=Role.BOSS, is_default=True)

    @override_settings(DEJIAN_OPEN_ACCESS=True, DEJIAN_OPEN_ACCESS_USER='dj_boss')
    def test_login_page_shows_enter_button_without_password(self):
        html = self.client.get(reverse('login')).content.decode()
        self.assertIn('进入系统', html)
        self.assertNotIn('id_password', html)
        self.assertNotIn('ChangeMe', html)
        self.assertIn(reverse('open_enter'), html)

    @override_settings(DEJIAN_OPEN_ACCESS=True, DEJIAN_OPEN_ACCESS_USER='dj_boss')
    def test_post_enter_logs_in_without_password(self):
        r = self.client.post(reverse('open_enter'), {'next': '/'}, follow=False)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r['Location'], '/')
        # session authenticated
        r2 = self.client.get('/')
        self.assertEqual(r2.status_code, 200)
        self.assertTrue(r2.wsgi_request.user.is_authenticated)
        self.assertEqual(r2.wsgi_request.user.username, 'dj_boss')

    @override_settings(DEJIAN_OPEN_ACCESS=True, DEJIAN_OPEN_ACCESS_USER='dj_boss')
    def test_get_enter_auto_form_then_post(self):
        html = self.client.get(reverse('open_enter')).content.decode()
        self.assertIn('enter-form', html)
        self.assertIn('csrfmiddlewaretoken', html)
        r = self.client.post(reverse('open_enter'), follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.wsgi_request.user.is_authenticated)

    @override_settings(DEJIAN_OPEN_ACCESS=False)
    def test_closed_access_requires_password(self):
        html = self.client.get(reverse('login')).content.decode()
        self.assertIn('id_password', html)
        self.assertNotIn('进入系统', html)
        # /enter/ redirects to login
        r = self.client.get(reverse('open_enter'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])
        # POST enter does not authenticate
        r = self.client.post(reverse('open_enter'))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(self.client.session.get('_auth_user_id'))
        # normal password login still works
        ok = self.client.login(username='dj_boss', password='secret-in-db')
        self.assertTrue(ok)

    @override_settings(DEJIAN_OPEN_ACCESS=True, DEJIAN_OPEN_ACCESS_USER='dj_boss')
    def test_enter_lands_in_dejian_tenant(self):
        self.client.post(reverse('open_enter'))
        html = self.client.get('/tenancy/').content.decode()
        self.assertIn('德鉴', html)

    @override_settings(DEJIAN_OPEN_ACCESS=True, DEJIAN_OPEN_ACCESS_USER='dj_boss')
    def test_external_next_is_rejected_on_get_and_post(self):
        html = self.client.get(reverse('open_enter') + '?next=https://attacker.example/').content.decode()
        self.assertNotIn('attacker.example', html)
        response = self.client.post(reverse('open_enter'), {'next': '//attacker.example/'})
        self.assertEqual(response['Location'], '/')
