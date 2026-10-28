from django.contrib.auth import get_user_model
from django.test import TestCase


class ReadOnlyGuestTests(TestCase):
    def test_guest_cannot_write_even_without_view_permissions(self):
        guest = get_user_model().objects.create_user('chouce_guest', password='local-test-only')
        self.client.force_login(guest)
        response = self.client.post('/products/create/', {'name': '不应保存'}, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 403)
        response = self.client.get('/admin/', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 403)
