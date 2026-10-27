from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.apps import apps
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import BrandingForm
from .models import Brand, Membership, Role
from .permissions import role_required


@login_required
def overview(request):
    """企业概览：品牌、仓库、渠道、成员与角色。"""
    tenant = request.tenant
    ctx = {'tenant': tenant, 'roles': Role.choices}
    if tenant is not None:
        from inventory.models import Inventory, Product
        brands = []
        for b in tenant.brands.all():
            brands.append({'brand': b, 'sku_count': Product.objects.filter(brand=b).count()})
        warehouses = []
        for w in tenant.warehouses.all():
            used = sum(Inventory.objects.filter(warehouse=w).values_list('quantity', flat=True))
            warehouses.append({'warehouse': w, 'used': used,
                               'utilization': round(used / w.capacity_units * 100, 1) if w.capacity_units else None})
        ctx.update({
            'brands': brands,
            'warehouses': warehouses,
            'channels': list(tenant.channels.all()),
            'members': list(Membership.objects.filter(tenant=tenant).select_related('user').prefetch_related('brands')),
        })
    return render(request, 'tenancy/overview.html', ctx)


@login_required
@require_POST
def switch(request):
    tid = request.POST.get('tenant_id')
    if tid:
        if Membership.objects.filter(user=request.user, tenant_id=tid).exists():
            request.session['tenant_id'] = int(tid)
            request.session.pop('brand_id', None)
        else:
            messages.error(request, '你不是该企业成员')
    if 'brand_id' in request.POST:
        bid = request.POST.get('brand_id')
        tenant_id = request.session.get('tenant_id') or (request.tenant.pk if request.tenant else None)
        if not bid:
            request.session.pop('brand_id', None)
        elif Brand.objects.filter(pk=bid, tenant_id=tenant_id).exists():
            request.session['brand_id'] = int(bid)
    nxt = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/'
    if not url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        nxt = '/'
    return redirect(nxt)


@role_required(Role.BOSS)
def branding(request):
    """企业外观：企业名称、文字字标、主色。只改当前企业。"""
    tenant = request.tenant
    if tenant is None:
        messages.error(request, '当前账号未加入企业')
        return redirect('/')
    form = BrandingForm(request.POST or None, instance=tenant)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '企业外观已保存')
        return redirect('tenancy:branding')
    return render(request, 'tenancy/branding.html', {'form': form, 'tenant': tenant})


IMPORT_ROLES = {
    'products': (Role.PURCHASER, Role.WAREHOUSE),
    'stock': (Role.WAREHOUSE,),
    'customers': (Role.SALES,),
    'wholesale_orders': (Role.SALES,),
    'purchase_orders': (Role.PURCHASER,),
}
IMPORT_SESSION_KEY = 'tenant_import'


def _import_kinds(request):
    from .importer import KINDS
    from .permissions import has_role
    return [(k, v['label']) for k, v in KINDS.items()
            if (k in ('products', 'stock') or apps.is_installed('b2b')) and has_role(request, *IMPORT_ROLES[k])]


@login_required
def import_template(request, kind, fmt):
    from . import importer
    if kind not in dict(_import_kinds(request)) or fmt not in ('csv', 'xlsx'):
        raise Http404
    name = f'import_{kind}_template.{fmt}'
    if fmt == 'csv':
        resp = HttpResponse(importer.template_csv(kind), content_type='text/csv; charset=utf-8')
    else:
        resp = HttpResponse(importer.template_xlsx(kind),
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = f'attachment; filename="{name}"'
    return resp


@login_required
def import_sample(request, kind, fmt):
    """示例模板（已填写）下载：与 seed_dejian 同源。"""
    from . import importer
    if kind not in dict(_import_kinds(request)) or fmt not in ('csv', 'xlsx'):
        raise Http404
    name = f'import_{kind}_filled.{fmt}'
    if fmt == 'csv':
        resp = HttpResponse(importer.sample_csv(kind), content_type='text/csv; charset=utf-8')
    else:
        resp = HttpResponse(importer.sample_xlsx(kind),
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = f'attachment; filename="{name}"'
    return resp


@login_required
def data_import(request):
    """上传 → 预览（不写库）→ 确认写入当前企业。"""
    from . import importer
    tenant = request.tenant
    kinds = _import_kinds(request)
    if tenant is None or not kinds:
        messages.error(request, '当前账号未加入企业或无导入权限')
        return redirect('/')
    allowed = dict(kinds)
    ctx = {'kinds': kinds, 'kind': request.POST.get('kind') or request.GET.get('kind') or kinds[0][0]}
    if ctx['kind'] not in allowed:
        ctx['kind'] = kinds[0][0]
    ctx['columns'] = importer.KINDS[ctx['kind']]['columns']
    step = request.POST.get('step')
    if request.method == 'POST' and step == 'preview':
        upload = request.FILES.get('file')
        if not upload:
            messages.error(request, '请选择文件')
        else:
            try:
                rows = importer.parse_upload(ctx['kind'], upload)
            except importer.ImportFileError as e:
                messages.error(request, str(e))
            else:
                checked = importer.validate(ctx['kind'], tenant, rows)
                for r in checked:
                    r['cells'] = [r['data'].get(f, '') for f, _, _ in ctx['columns']]
                ok = bool(rows) and not any(r['errors'] for r in checked)
                if ok:
                    request.session[IMPORT_SESSION_KEY] = {'kind': ctx['kind'], 'tenant_id': tenant.pk, 'rows': rows}
                else:
                    request.session.pop(IMPORT_SESSION_KEY, None)
                ctx.update(preview=checked, can_confirm=ok, error_count=sum(1 for r in checked if r['errors']))
    elif request.method == 'POST' and step == 'confirm':
        pending = request.session.pop(IMPORT_SESSION_KEY, None)
        if not pending or pending['tenant_id'] != tenant.pk or pending['kind'] not in allowed:
            messages.error(request, '预览已失效，请重新上传')
        else:
            try:
                n = importer.apply(pending['kind'], tenant, request.user, pending['rows'])
            except importer.ImportFileError as e:
                messages.error(request, str(e))
            else:
                messages.success(request, f'已导入 {n} 行{importer.KINDS[pending["kind"]]["label"]}')
                return redirect(f"{request.path}?kind={pending['kind']}")
    return render(request, 'tenancy/import.html', ctx)
