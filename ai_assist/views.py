"""补货建议的两个 POST 动作（生成采购草稿 / 忽略），以及重新测算。无独立页面。"""
from django.apps import apps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import NoReverseMatch, reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from . import assistant as _assistant
from . import services
from .hints import restock_suggestions
from .models import Suggestion
from .workflows import WORKFLOWS


def _tenant(request):
    t = getattr(request, 'tenant', None)
    if t is None:
        raise Http404('未选择企业')
    return t


def _back(request):
    nxt = request.POST.get('next') or request.META.get('HTTP_REFERER') or ''
    if url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(nxt)
    return redirect('inventory_list')


def _suggestion(request, pk):
    return get_object_or_404(Suggestion, pk=pk, tenant=_tenant(request), workflow='replenish')


@login_required
@require_POST
def restock_adopt(request, pk):
    sug = _suggestion(request, pk)
    try:
        task = services.adopt(sug, request.user, getattr(request, 'membership', None))
    except (PermissionDenied, ValidationError) as e:
        messages.error(request, '; '.join(getattr(e, 'messages', [str(e)])))
        return _back(request)
    if task.external_ref and apps.is_installed('b2b'):
        PO = apps.get_model('b2b', 'PurchaseOrder')
        po = PO.objects.filter(tenant=sug.tenant, number=task.external_ref).first()
        if po is not None:
            messages.success(request, f'已生成采购单草稿 {po.number}')
            try:
                return redirect(reverse('b2b:po_detail', args=[po.pk]))
            except NoReverseMatch:
                pass
    messages.success(request, '已生成采购草稿')
    return _back(request)


@login_required
@require_POST
def restock_dismiss(request, pk):
    sug = _suggestion(request, pk)
    try:
        services.reject(sug, request.user, request.POST.get('reason') or '暂不补货', getattr(request, 'membership', None))
    except (PermissionDenied, ValidationError) as e:
        messages.error(request, '; '.join(getattr(e, 'messages', [str(e)])))
    return _back(request)


@login_required
@require_POST
def refresh(request):
    tenant = _tenant(request)
    for key in WORKFLOWS:
        services.run_workflow(tenant, key, {}, user=request.user)
    messages.success(request, '补货建议和库存提示已更新')
    return _back(request)


@login_required
def assistant_chat(request):
    """筹策助手对话入口（GET，兼容体验库只读访客）。

    问答不写数据；生成草稿时只返回 adopt 动作，由前端走既有采纳入口
    （POST + CSRF + 权限/只读中间件）真正执行，助手本身不写库。
    """
    tenant = getattr(request, 'tenant', None)
    if tenant is None:
        return JsonResponse({'reply': '还没选企业，先选好企业我再帮你看。'}, status=400)
    _run, items = restock_suggestions(tenant, limit=10)
    from . import explain as _explain
    for s in items:
        if not s.ai_explanation:
            _explain.ensure_explanation(s, allow_llm=False, persist=False)
    if request.GET.get('init'):
        return JsonResponse({'reply': _assistant.briefing(items)})
    text, state, action = _assistant.reply(items, request.GET.get('message', ''),
                                           request.session.get('assistant_state'))
    request.session['assistant_state'] = state
    return JsonResponse({'reply': text, 'action': action})
