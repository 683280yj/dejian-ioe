"""python manage.py ai_refresh [--tenant CODE]

重新计算补货建议与库存提示（可放 cron 每日跑一次）。
"""
from django.core.management.base import BaseCommand, CommandError

from ai_assist import services
from ai_assist.workflows import WORKFLOWS
from tenancy.models import Tenant


class Command(BaseCommand):
    help = '重新计算补货建议与库存提示'

    def add_arguments(self, parser):
        parser.add_argument('--tenant', help='企业 code，不填则全部企业')

    def handle(self, *args, **opts):
        qs = Tenant.objects.all()
        if opts['tenant']:
            qs = qs.filter(code=opts['tenant'])
            if not qs.exists():
                raise CommandError(f"企业 {opts['tenant']} 不存在")
        for t in qs:
            for key, wf in WORKFLOWS.items():
                run = services.run_workflow(t, key, {})
                self.stdout.write(f"{t.code} {wf.label}: {run.suggestions.count()} 条")
