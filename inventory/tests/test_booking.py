import json

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from inventory.models import BookingLead

VALID_PHONE = '139' + '0000' + '0000'


@override_settings(BOOKING_SUBMISSION_TOKEN='local-test-token')
class BookingSubmissionTests(TestCase):
    def post_booking(self, data=None, token='local-test-token'):
        payload = data or {'phone': VALID_PHONE, 'category': '白酒批发', 'consent': True}
        return self.client.post(
            reverse('submit_booking'),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_BOOKING_TOKEN=token,
        )

    def test_valid_booking_is_saved_once(self):
        self.assertEqual(self.post_booking().status_code, 200)
        self.assertEqual(self.post_booking().status_code, 200)
        self.assertEqual(BookingLead.objects.count(), 1)
        self.assertEqual(BookingLead.objects.get().category, '白酒批发')

    def test_rejects_untrusted_or_invalid_submissions(self):
        self.assertEqual(self.post_booking(token='wrong').status_code, 403)
        self.assertEqual(self.post_booking({'phone': '测试', 'category': '白酒批发', 'consent': True}).status_code, 400)
        self.assertEqual(self.post_booking({'phone': VALID_PHONE, 'category': '白酒批发', 'consent': False}).status_code, 400)
        self.assertEqual(BookingLead.objects.count(), 0)

    def test_honeypot_does_not_store_data(self):
        response = self.post_booking({'phone': VALID_PHONE, 'category': '白酒批发', 'consent': True, 'website': 'spam'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(BookingLead.objects.count(), 0)

    def test_only_superuser_can_view_booking_admin(self):
        url = reverse('admin:inventory_bookinglead_changelist')
        user = get_user_model().objects.create_user('ordinary', password='local-test-only')
        self.client.force_login(user)
        self.assertNotEqual(self.client.get(url).status_code, 200)
        user.is_superuser = True
        user.is_staff = True
        user.save(update_fields=['is_superuser', 'is_staff'])
        self.assertEqual(self.client.get(url).status_code, 200)
