"""当前请求的租户上下文（线程/协程局部）。

中间件在请求开始时写入，结束时清除。管理命令、测试里默认没有当前租户，
此时 TenantManager 不做过滤（向后兼容 IOE 原有逻辑）。
"""
import contextlib
from contextvars import ContextVar

_tenant = ContextVar('current_tenant', default=None)
_brand = ContextVar('current_brand', default=None)


def get_current_tenant():
    return _tenant.get()


def get_current_brand():
    return _brand.get()


def set_current(tenant, brand=None):
    return _tenant.set(tenant), _brand.set(brand)


def reset_current(tokens):
    t, b = tokens
    _tenant.reset(t)
    _brand.reset(b)


@contextlib.contextmanager
def use_tenant(tenant, brand=None):
    tokens = set_current(tenant, brand)
    try:
        yield tenant
    finally:
        reset_current(tokens)
