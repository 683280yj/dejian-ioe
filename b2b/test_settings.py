"""b2b 测试设置（兼容旧命令）：tenancy 与 b2b 已在 inventory.settings 中正式注册。

python manage.py test b2b --settings=b2b.test_settings
等价于 python manage.py test b2b --settings=inventory.test_settings
"""
from inventory.test_settings import *  # noqa: F401,F403
