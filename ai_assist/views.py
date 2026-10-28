"""补货建议的两个 POST 动作（生成采购草稿 / 忽略），以及重新测算。无独立页面。"""
import logging

from django.apps import apps

logger = logging.getLogger(__name__)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import NoReverseMatch, reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods

from . import assistant as _assistant
from . import chat_api
from . import services
from .hints import restock_suggestions
from .models import ChatTurn, Suggestion
from .workflows import WORKFLOWS

HISTORY_LIMIT = 30


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


def _chat_history(request):
    """当前用户在本企业的最近对话（正序，返回可序列化的 dict 列表）。"""
    turns = (ChatTurn.objects.filter(tenant=request.tenant, user=request.user)
             .order_by('-created_at', '-id')[:HISTORY_LIMIT])
    return [{'role': t.role, 'content': t.content, 'created_at': t.created_at.isoformat()}
            for t in reversed(list(turns))]


@login_required
@require_http_methods(['GET', 'POST', 'DELETE'])
def assistant_chat(request):
    """筹策助手对话入口（POST 聊天，GET 初始化，DELETE 清空历史）。

    问答记录按企业+用户持久化到 ChatTurn，刷新/换设备不丢；
    写操作凭老板权限由工具直接落库。
    """
    tenant = getattr(request, 'tenant', None)
    if tenant is None:
        return JsonResponse({'reply': '还没选企业，先选好企业我再帮你看。'}, status=400)
    _run, items = restock_suggestions(tenant, limit=10)
    from . import explain as _explain
    for s in items:
        if not s.ai_explanation:
            _explain.ensure_explanation(s, allow_llm=False, persist=False)
    if request.method == 'DELETE':
        ChatTurn.objects.filter(tenant=tenant, user=request.user).delete()
        return JsonResponse({'reply': '对话记录已清空。', 'history': []})
    if request.method == 'GET':
        history = _chat_history(request)
        return JsonResponse({'reply': _assistant.briefing(items), 'history': history})
    message = (request.POST.get('message') or '').strip()[:1000]
    if not message:
        return JsonResponse({'reply': '先说说你想了解哪条补货建议。'}, status=400)
    previous_state = request.session.get('assistant_state') or {}
    actor = (request.user, getattr(request, 'membership', None))
    model_text = None
    state, action = previous_state, None

    # 规则层待确认草稿期间走规则层（确认/取消/追问），不被模型打断
    if previous_state.get('pending_adopt'):
        text, state, action = _assistant.reply(items, message, previous_state)
    elif chat_api.configured():
        # 直接操作模式：模型带工具优先，写操作凭老板权限直接落库
        model_text, model_action = chat_api.answer(tenant, items, message,
                                                   _chat_history(request),
                                                   actor=actor)
        if model_text:
            text, state, action = model_text, {}, None
            if model_action and model_action.get('adopt_pks'):
                # 兜底：模型未直接执行时，写入待确认状态，下一句「好」走规则层确认执行
                state = {'pending_adopt': model_action['adopt_pks']}
                action = None
        else:
            text, state, action = _assistant.reply(items, message, previous_state)
    else:
        # 模型未配置：纯规则层（草稿仍走确认流程）
        text, state, action = _assistant.reply(items, message, previous_state)
    request.session['assistant_state'] = state
    try:
        ChatTurn.objects.bulk_create([
            ChatTurn(tenant=tenant, user=request.user, role='user', content=message),
            ChatTurn(tenant=tenant, user=request.user, role='assistant', content=text),
        ])
        # 只保留每个用户最近 N 条，防无限增长
        turns = (ChatTurn.objects.filter(tenant=tenant, user=request.user)
                 .order_by('-created_at', '-id'))
        if turns.count() > HISTORY_LIMIT * 2:
            old_ids = list(turns.values_list('id', flat=True)[HISTORY_LIMIT * 2:])
            ChatTurn.objects.filter(id__in=old_ids).delete()
    except Exception:
        logger.warning('助手对话记录落库失败，不影响本次回复', exc_info=True)
    try:
        history = _chat_history(request)
    except Exception:
        history = []
    return JsonResponse({'reply': text, 'action': action,
                         'mode': 'model' if model_text else 'rule', 'history': history})
