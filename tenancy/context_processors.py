from .models import DEFAULT_PRIMARY, Membership, Role, Tenant

PLATFORM_WORDMARK = '筹策工作台'


def _branding_tenant(request, tenant):
    """已登录用当前企业；登录页可用 ?t=<企业编码> 预览该企业的文字字标。"""
    if tenant is not None:
        return tenant
    code = request.GET.get('t') if hasattr(request, 'GET') else None
    if code:
        return Tenant.objects.filter(code=code, is_active=True).first()
    return None


def tenancy(request):
    tenant = getattr(request, 'tenant', None)
    role = getattr(request, 'role', None)
    user = getattr(request, 'user', None)
    memberships = []
    if user is not None and user.is_authenticated:
        memberships = list(Membership.objects.select_related('tenant').filter(user=user))
    bt = _branding_tenant(request, tenant)
    return {
        'tenant_wordmark': bt.wordmark if bt else PLATFORM_WORDMARK,
        'tenant_primary': bt.primary_color if bt and bt.primary_color else DEFAULT_PRIMARY,
        'tenant_primary_rgb': bt.primary_rgb if bt else '110, 31, 44',
        'tenant_custom_color': bool(bt and bt.primary_color and bt.primary_color.lower() != DEFAULT_PRIMARY),
        'can_edit_branding': bool(tenant is not None and role == Role.BOSS),
        'current_tenant': tenant,
        'current_brand': getattr(request, 'brand', None),
        'current_role': role,
        'current_role_label': Role(role).label if role else '',
        'user_memberships': memberships,
        'tenant_brands': list(tenant.brands.filter(is_active=True)) if tenant else [],
    }
