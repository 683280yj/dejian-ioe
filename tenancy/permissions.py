from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import Role


def has_role(request, *roles):
    """老板拥有全部角色；没有企业成员身份的超级管理员也放行。"""
    if request.user.is_superuser and getattr(request, 'membership', None) is None:
        return True
    role = getattr(request, 'role', None)
    return role is not None and (role == Role.BOSS or role in roles)


def role_required(*roles):
    def deco(view):
        @login_required
        @wraps(view)
        def wrapper(request, *a, **kw):
            if not has_role(request, *roles):
                raise PermissionDenied('当前角色无权执行此操作')
            return view(request, *a, **kw)
        return wrapper
    return deco
