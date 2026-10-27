"""测算持久化与采纳/忽略。

采纳补货建议 = 生成 DraftTask + b2b 的 DRAFT 采购单（b2b.services.create_purchase_draft），
不提交、不审批、不改库存；库存提示自动写入 IOE 原生 StockAlert。
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

from django.apps import apps
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from tenancy.models import Role

from . import data
from .models import DecisionRun, DraftTask, Suggestion
from .workflows import WORKFLOWS
from .workflows.base import RunContext

ROLE_LABELS = dict(Role.choices)
SUG_FIELDS = ('title', 'target_label', 'quantity', 'unit', 'amount', 'severity', 'score', 'rationale', 'formula',
              'inputs', 'values', 'execution_mode', 'required_role', 'draft_kind', 'draft_payload')


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, Decimal):
        return float(o)
    if isinstance(o, (dt.date, dt.datetime)):
        return o.isoformat()
    return o


def user_can(user, membership, role):
    """老板拥有全部权限；无企业成员身份的超级管理员放行（运维）。"""
    if user is None or not user.is_authenticated:
        return False
    if membership is None:
        return user.is_superuser
    return membership.role == Role.BOSS or membership.role == role


@transaction.atomic
def run_workflow(tenant, key, raw_params=None, user=None, brand=None, as_of=None, parent=None):
    wf = WORKFLOWS[key]
    params = wf.clean_params(raw_params)
    as_of = as_of or data.today()
    result = wf.run(RunContext(tenant=tenant, params=params, as_of=as_of, brand=brand, user=user))
    run = DecisionRun.objects.create(
        tenant=tenant, brand=brand, workflow=key, params=_jsonable(params), objective=wf.objective,
        update_cycle=wf.cycle, summary=_jsonable(result.summary), engine='rules',
        parent=parent, as_of=as_of, created_by=user if getattr(user, 'is_authenticated', False) else None)
    # 新一轮测算替代同环节尚未决定的旧建议（what-if 子测算不替代，便于对比）
    if parent is None:
        Suggestion.objects.filter(tenant=tenant, workflow=key, status__in=['pending', 'auto_done']).exclude(run=run).update(status='superseded')
    objs = []
    for s in result.suggestions:
        kw = {f: s[f] for f in SUG_FIELDS if f in s and s[f] is not None}
        kw['inputs'] = _jsonable(kw.get('inputs', {}))
        kw['values'] = _jsonable(kw.get('values', {}))
        kw['draft_payload'] = _jsonable(kw.get('draft_payload', {}))
        objs.append(Suggestion(tenant=tenant, run=run, workflow=key, product_id=s.get('product_id'), **kw))
    for o in objs:
        o.save()
    if key == 'replenish' and parent is None:
        from . import explain as _explain
        # 解释生成可能调外部 LLM（慢），必须等事务提交后再跑，避免长开事务锁库
        transaction.on_commit(lambda objs=objs: _explain.fill_run_explanations(objs))
    if parent is None:
        for sug, extra in zip(objs, result.suggestions):
            if sug.execution_mode == 'auto':
                _auto_execute(sug, extra)
    return run


def _auto_execute(sug, s_extra):
    """自动动作：只写 IOE 库存预警，不改库存、不下单。"""
    tenant = sug.tenant
    if sug.workflow == 'stock_alert' and s_extra.get('alert_type') and sug.product_id:
        StockAlert = apps.get_model('inventory', 'StockAlert')
        if not StockAlert.objects.filter(tenant=tenant, product_id=sug.product_id, alert_type=s_extra['alert_type'], is_active=True).exists():
            StockAlert.objects.create(tenant=tenant, product_id=sug.product_id, alert_type=s_extra['alert_type'])
    sug.status = 'auto_done'
    sug.decided_at = timezone.now()
    sug.save(update_fields=['status', 'decided_at'])


def what_if(run, raw_params, user=None):
    """改参数重算：生成子测算，并给出汇总指标差异。"""
    child = run_workflow(run.tenant, run.workflow, raw_params, user=user, brand=run.brand, as_of=run.as_of, parent=run)
    return child, summary_diff(run.summary, child.summary)


def summary_diff(a, b):
    out = []
    for k in b:
        va, vb = a.get(k), b.get(k)
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)) and not isinstance(va, bool):
            out.append({'指标': k, '原方案': va, '新方案': vb, '变化': round(vb - va, 4)})
        elif va != vb and not isinstance(vb, (dict, list)):
            out.append({'指标': k, '原方案': va, '新方案': vb, '变化': None})
    return out


@transaction.atomic
def adopt(sug, user, membership=None, note=''):
    sug = Suggestion.objects.select_for_update().get(pk=sug.pk)
    if sug.status != 'pending':
        raise ValidationError('该建议已处理')
    if not user_can(user, membership, sug.required_role):
        raise PermissionDenied(f"需要「{ROLE_LABELS.get(sug.required_role, sug.required_role)}」或老板确认")
    payload = dict(sug.draft_payload or {})
    task = DraftTask(tenant=sug.tenant, suggestion=sug, kind=sug.draft_kind or 'purchase_draft', title=sug.title,
                     body=(note + '\n\n' if note else '') + f"依据：{sug.rationale}\n公式：{sug.formula}",
                     payload=payload, assignee_role=sug.required_role, created_by=user)
    if sug.draft_kind == 'purchase_draft' and apps.is_installed('b2b') and payload.get('lines'):
        task.external_ref = _create_b2b_po(sug, payload, user) or ''
    task.save()
    sug.status, sug.decided_by, sug.decided_at = 'adopted', user, timezone.now()
    sug.save(update_fields=['status', 'decided_by', 'decided_at'])
    return task


def _create_b2b_po(sug, payload, user):
    """调用 lane-c 提供的唯一 AI 写入口：只生成 DRAFT 采购单。"""
    from b2b.services import create_purchase_draft  # noqa: WPS433
    Supplier = apps.get_model('inventory', 'Supplier')
    Product = apps.get_model('inventory', 'Product')
    supplier = Supplier.objects.filter(pk=payload.get('supplier_id'), tenant=sug.tenant).first()
    if supplier is None:
        return None
    prods = {p.pk: p for p in Product.objects.filter(tenant=sug.tenant, pk__in=[l['product_id'] for l in payload['lines']])}
    lines = [{'product': prods[l['product_id']], 'quantity': int(l['quantity']), 'unit_price': l['unit_price']}
             for l in payload['lines'] if l['product_id'] in prods and int(l['quantity']) > 0]
    if not lines:
        return None
    po = create_purchase_draft(sug.tenant, supplier, lines, user=user, source='AI_DRAFT',
                               notes=f'由补货建议 #{sug.pk} 生成')
    return po.number


@transaction.atomic
def reject(sug, user, reason, membership=None):
    reason = (reason or '').strip()
    if not reason:
        raise ValidationError('请填写忽略原因')
    sug = Suggestion.objects.select_for_update().get(pk=sug.pk)
    if sug.status != 'pending':
        raise ValidationError('该建议已处理')
    if not user_can(user, membership, sug.required_role):
        raise PermissionDenied(f"需要「{ROLE_LABELS.get(sug.required_role, sug.required_role)}」或老板确认")
    sug.status, sug.decided_by, sug.decided_at, sug.reject_reason = 'rejected', user, timezone.now(), reason
    sug.save(update_fields=['status', 'decided_by', 'decided_at', 'reject_reason'])
    return sug


def close_task(task, user, done=True):
    task.status = 'done' if done else 'cancelled'
    task.closed_by, task.closed_at = user, timezone.now()
    task.save(update_fields=['status', 'closed_by', 'closed_at'])
    return task

