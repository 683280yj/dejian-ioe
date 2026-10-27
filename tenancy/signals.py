"""保存业务数据时自动带上当前租户（只在请求上下文中，且字段为空时）。"""
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .context import get_current_tenant


@receiver(pre_save)
def fill_tenant(sender, instance, raw=False, **kwargs):
    if raw:
        return
    if not hasattr(instance, 'tenant_id') or sender._meta.app_label == 'tenancy':
        return
    if instance.tenant_id is None:
        tenant = get_current_tenant()
        if tenant is not None:
            instance.tenant = tenant


def _sync_roles(sender, instance, **kwargs):
    from .roles import sync_user_groups
    sync_user_groups(instance.user)


def connect_membership_signals():
    from django.db.models.signals import post_delete, post_save
    from .models import Membership
    post_save.connect(_sync_roles, sender=Membership, dispatch_uid='tenancy_membership_roles_save')
    post_delete.connect(_sync_roles, sender=Membership, dispatch_uid='tenancy_membership_roles_delete')
