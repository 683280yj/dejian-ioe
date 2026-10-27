from django.apps import AppConfig


class TenancyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tenancy'
    verbose_name = '企业 / 品牌 / 仓库（多租户）'

    def ready(self):
        from . import signals
        signals.connect_membership_signals()
