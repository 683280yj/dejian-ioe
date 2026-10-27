"""python manage.py reset_showcase [--snapshot PATH] [--save-snapshot] [--no-refresh]

体验实例专用：把体验库整体还原成干净快照（访客点过的单据、日志全部清掉），再重算补货建议。
可放 cron 每晚跑一次。只在 settings 里设了 SHOWCASE_SNAPSHOT（或传 --snapshot）时工作，
并且拒绝对主库 db/db.sqlite3 动手。

  --save-snapshot  把当前体验库存成快照（重建体验库后跑一次）
"""
import os
import sqlite3
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connections


class Command(BaseCommand):
    help = '把体验库还原为干净快照并重算补货建议'

    def add_arguments(self, parser):
        parser.add_argument('--snapshot', default=getattr(settings, 'SHOWCASE_SNAPSHOT', '') or '')
        parser.add_argument('--save-snapshot', action='store_true')
        parser.add_argument('--no-refresh', action='store_true')

    def handle(self, *args, **opts):
        db = Path(str(settings.DATABASES['default']['NAME'])).resolve()
        main_db = (Path(settings.BASE_DIR) / 'db' / 'db.sqlite3').resolve()
        if 'sqlite3' not in settings.DATABASES['default']['ENGINE'] or db == main_db:
            raise CommandError(f'拒绝执行：{db} 不是体验库（请用 showcase_settings）')
        snap = Path(opts['snapshot']).resolve() if opts['snapshot'] else None
        if snap is None:
            raise CommandError('未配置快照路径：设 SHOWCASE_SNAPSHOT 或传 --snapshot')
        if snap in (db, main_db):
            raise CommandError('快照路径不能是体验库或主库本身')
        connections.close_all()
        if opts['save_snapshot']:
            self._copy(db, snap)
            os.chmod(snap, 0o600)
            self.stdout.write(f'已保存快照 {snap}')
            return
        if not snap.exists():
            raise CommandError(f'快照不存在：{snap}')
        self._copy(snap, db)
        self.stdout.write(f'体验库已还原自 {snap}')
        if not opts['no_refresh']:
            call_command('ai_refresh', stdout=self.stdout)

    @staticmethod
    def _copy(src, dst):
        # sqlite 在线备份：目标库被 gunicorn 打开时也能安全整体替换
        s = sqlite3.connect(f'file:{src}?mode=ro', uri=True)
        d = sqlite3.connect(str(dst))
        try:
            s.backup(d)
        finally:
            d.close()
            s.close()
