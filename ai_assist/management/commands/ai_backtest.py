"""python manage.py ai_backtest [--tenant dejian] [--sim-days 180] [--service-level 0.95] [--json]

补货策略回测：逐日滚动仿真，比较人工基线与测算策略（演示数据 + 演示假设，非真实经营数据）。
"""
import json

from django.core.management.base import BaseCommand, CommandError

from ai_assist.backtest import run_backtest
from tenancy.models import Tenant


def _fmt(v, f):
    if v is None:
        return '-'
    return {'pct': f'{v:.2%}', 'days': f'{v:.1f} 天', 'money': f'¥{v / 10000:.2f} 万', 'int': f'{int(v)}'}.get(f, str(v))


class Command(BaseCommand):
    help = '补货策略回测（演示数据，仿真结果）'

    def add_arguments(self, parser):
        parser.add_argument('--tenant', default='dejian')
        parser.add_argument('--sim-days', type=int)
        parser.add_argument('--service-level', type=float)
        parser.add_argument('--json', action='store_true')

    def handle(self, *args, **opts):
        t = Tenant.objects.filter(code=opts['tenant']).first()
        if t is None:
            raise CommandError(f"企业 {opts['tenant']} 不存在（先运行 seed_dejian）")
        params = {k: opts[k] for k in ('sim_days', 'service_level') if opts.get(k) is not None}
        res = run_backtest(t, params)
        if opts['json']:
            self.stdout.write(json.dumps(res, ensure_ascii=False, default=str, indent=2))
            return
        self.stdout.write(f"【{res['label']}】{res.get('period', '')}")
        for row in res['headline']:
            ch = f"{row['变化']:+.1%}" if row.get('变化') is not None else ''
            self.stdout.write(f"  {row['指标']:<12} 人工 {_fmt(row['人工基线'], row['fmt']):>12}   测算 {_fmt(row['AI'], row['fmt']):>12}  {ch}")
