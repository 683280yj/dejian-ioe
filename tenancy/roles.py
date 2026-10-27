"""角色 → Django 权限映射（按 lane-c 在 COORDINATION.md 中给出的 b2b 权限码）。

Django 权限是全局的，这里取用户在所有企业中角色的并集，同步到名为「角色:xxx」的用户组。
真正的数据隔离仍靠 tenant 过滤；权限只决定“能不能点某个流转按钮”。
"""
from django.apps import apps
from django.contrib.auth.models import Group, Permission

from .models import Role

B2B_ALL = ['approve_purchaseorder', 'receive_purchaseorder', 'approve_wholesaleorder', 'ship_wholesaleorder',
           'record_payment', 'record_receipt', 'confirm_supplierstatement']

ROLE_PERMISSIONS = {
    Role.BOSS: [('b2b', c) for c in B2B_ALL],
    Role.PURCHASER: [],  # 提交采购单无需额外权限
    Role.SALES: [],      # 提交批发单无需额外权限
    Role.WAREHOUSE: [('b2b', 'receive_purchaseorder'), ('b2b', 'ship_wholesaleorder')],
    Role.FINANCE: [('b2b', 'record_payment'), ('b2b', 'record_receipt'), ('b2b', 'confirm_supplierstatement')],
    Role.AUDITOR: [],    # 只读
}


def group_for(role):
    group, _ = Group.objects.get_or_create(name=f'角色:{Role(role).label}')
    perms = []
    for app_label, codename in ROLE_PERMISSIONS.get(role, []):
        if not apps.is_installed(app_label):
            continue
        p = Permission.objects.filter(content_type__app_label=app_label, codename=codename).first()
        if p:
            perms.append(p)
    group.permissions.set(perms)
    return group


def sync_user_groups(user):
    from .models import Membership
    roles = set(Membership.objects.filter(user=user).values_list('role', flat=True))
    role_groups = Group.objects.filter(name__startswith='角色:')
    user.groups.remove(*role_groups.exclude(name__in=[f'角色:{Role(r).label}' for r in roles]))
    for r in roles:
        user.groups.add(group_for(r))
