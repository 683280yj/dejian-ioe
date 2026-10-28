from decimal import Decimal

from django.test import TestCase

from inventory.models import Member, MemberLevel, RechargeRecord
from inventory.services.report_service import ReportService
from tenancy.models import Tenant


class RechargeTenantIsolationTests(TestCase):
    def test_recharge_totals_are_scoped_to_requested_tenant(self):
        first = Tenant.objects.create(name='甲企业', code='tenant-a')
        second = Tenant.objects.create(name='乙企业', code='tenant-b')
        for tenant, suffix, amount in ((first, '1', '100'), (second, '2', '900')):
            level = MemberLevel.objects.create(tenant=tenant, name='普通', discount=Decimal('1'), points_threshold=0)
            member = Member.objects.create(tenant=tenant, level=level, name='测试会员', phone='1380000000' + suffix)
            RechargeRecord.objects.create(member=member, amount=amount, actual_amount=amount, payment_method='cash')

        self.assertEqual(ReportService.get_recharge_report(tenant=first)['summary']['total_recharge_amount'], Decimal('100'))
        self.assertEqual(ReportService.get_recharge_report(tenant=second)['summary']['total_recharge_amount'], Decimal('900'))
        self.assertEqual(ReportService.get_recharge_report()['summary']['total_recharge_amount'], 0)
