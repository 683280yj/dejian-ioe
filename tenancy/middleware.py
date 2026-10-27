from .context import reset_current, set_current
from .models import Brand, Membership


def resolve_membership(request):
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return None
    qs = Membership.objects.select_related('tenant').filter(user=user, tenant__is_active=True)
    wanted = request.session.get('tenant_id') if hasattr(request, 'session') else None
    m = None
    if wanted:
        m = qs.filter(tenant_id=wanted).first()
    if m is None:
        m = qs.order_by('-is_default', 'id').first()
    return m


class TenantMiddleware:
    """根据登录用户设置 request.tenant / request.membership / request.role / request.brand。"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        m = resolve_membership(request)
        request.membership = m
        request.tenant = m.tenant if m else None
        request.role = m.role if m else None
        brand = None
        if m is not None and hasattr(request, 'session'):
            bid = request.session.get('brand_id')
            if bid:
                brand = Brand.objects.filter(pk=bid, tenant=m.tenant).first()
        request.brand = brand
        tokens = set_current(request.tenant, brand)
        try:
            return self.get_response(request)
        finally:
            reset_current(tokens)
