"""Run isolated tests: python manage.py test --settings=inventory.test_settings"""

import atexit
import os
from pathlib import Path
from tempfile import TemporaryDirectory

# 测试专用密钥：仅当环境未提供 SECRET_KEY 时兜底，生产部署不受影响
if not os.environ.get('SECRET_KEY'):
    os.environ['SECRET_KEY'] = 'test-only-insecure-secret-key'

from inventory.settings import *

_test_storage = TemporaryDirectory(prefix='ioe-tests-')
atexit.register(_test_storage.cleanup)
_test_root = Path(_test_storage.name)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _test_root / 'db.sqlite3',
        'TEST': {'NAME': _test_root / 'test.sqlite3'},
    },
}
MEDIA_ROOT = _test_root / 'media'
BACKUP_ROOT = _test_root / 'backups'
TEMP_DIR = _test_root / 'temp'
STATIC_ROOT = _test_root / 'staticfiles'
