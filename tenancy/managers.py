from django.db import models

from .context import get_current_tenant


class TenantQuerySet(models.QuerySet):
    def for_tenant(self, tenant):
        if tenant is None:
            return self
        return self.filter(tenant=tenant)


class TenantManager(models.Manager.from_queryset(TenantQuerySet)):
    """默认管理器：存在当前租户时只返回该租户的数据。

    - 无当前租户（管理命令、测试、未加入任何企业的平台管理员）→ 不过滤；
    - 关联访问（product.category 等）走 _base_manager，不受影响。
    """

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = get_current_tenant()
        if tenant is not None:
            qs = qs.filter(tenant=tenant)
        return qs

    def unscoped(self):
        return TenantQuerySet(self.model, using=self._db)
