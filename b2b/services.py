"""b2b 状态流转服务。

规则（产品铁律）：
- 每个推进状态的函数都必须传入 `actor`（已登录、启用的真人 User），并由视图在 POST 时调用。
- 没有任何信号、定时任务或 save() 钩子会自动推进状态、动库存或登记收付款。
- AI/规则模块只能调用本模块里的只读函数或 `create_*_draft`（生成 DRAFT），不能调用流转函数。
"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from inventory.models import OperationLog
from inventory.models.inventory import update_inventory

from .models import (
    PurchaseOrder, PurchaseOrderLine, WholesaleOrder, Payable, Receivable, SettlementEntry, SupplierStatement,
)


class InvalidTransition(ValidationError):
    pass


@transaction.atomic
def create_purchase_draft(tenant, supplier, lines, user=None, source='AI_DRAFT', warehouse=None, notes=''):
    """生成采购单草稿（供 ai_assist「采纳」调用）。只创建 DRAFT，不提交、不审批、不入库。

    lines: 可迭代的 (product, quantity, unit_price) 或 dict(product=, quantity=, unit_price=)。
    user: 点「采纳」的人（可为 None）；仅记为制单人，不赋予任何流转。
    """
    if source not in ('MANUAL', 'AI_DRAFT'):
        raise ValueError('source 必须是 MANUAL 或 AI_DRAFT')
    norm = []
    for line in lines:
        if isinstance(line, dict):
            product, qty, price = line['product'], line['quantity'], line['unit_price']
        else:
            product, qty, price = line
        qty, price = int(qty), Decimal(str(price))
        if qty <= 0 or price < 0:
            raise ValidationError('数量必须为正、单价不能为负')
        norm.append((product, qty, price))
    if not norm:
        raise ValidationError('至少一行明细')
    order = PurchaseOrder(tenant=tenant, supplier=supplier, warehouse=warehouse, notes=notes,
                          created_by=user if getattr(user, 'is_authenticated', False) else None)
    order.source = source
    order.save()
    PurchaseOrderLine.objects.bulk_create(
        [PurchaseOrderLine(order=order, product=p, quantity=q, unit_price=u) for p, q, u in norm])
    return order


PO_TRANSITIONS = {
    'submit': ({'DRAFT'}, 'SUBMITTED', None),
    'approve': ({'SUBMITTED'}, 'APPROVED', 'b2b.approve_purchaseorder'),
    'receive': ({'APPROVED'}, 'RECEIVED', 'b2b.receive_purchaseorder'),
    'cancel': ({'DRAFT', 'SUBMITTED', 'APPROVED'}, 'CANCELLED', None),
}

SO_TRANSITIONS = {
    'submit': ({'DRAFT'}, 'SUBMITTED', None),
    'approve': ({'SUBMITTED'}, 'APPROVED', 'b2b.approve_wholesaleorder'),
    'ship': ({'APPROVED'}, 'SHIPPED', 'b2b.ship_wholesaleorder'),
    'complete': ({'SHIPPED'}, 'COMPLETED', 'b2b.ship_wholesaleorder'),
    'cancel': ({'DRAFT', 'SUBMITTED', 'APPROVED'}, 'CANCELLED', None),
}


def _require_human(actor, perm=None):
    if actor is None or not getattr(actor, 'is_authenticated', False) or not getattr(actor, 'is_active', False):
        raise PermissionDenied('状态流转必须由已登录的人员显式操作')
    if perm and not actor.has_perm(perm):
        raise PermissionDenied(f'缺少权限 {perm}')


def _log(actor, obj, details):
    OperationLog.objects.create(
        operator=actor, operation_type='OTHER', details=f'[b2b] {details}',
        related_object_id=obj.pk, related_content_type=ContentType.objects.get_for_model(obj),
    )


def _lock(model, pk):
    return model.objects.select_for_update().get(pk=pk)


@transaction.atomic
def transition_purchase_order(order, action, actor):
    if action not in PO_TRANSITIONS:
        raise InvalidTransition(f'未知操作 {action}')
    sources, target, perm = PO_TRANSITIONS[action]
    _require_human(actor, perm)
    order = _lock(PurchaseOrder, order.pk)
    if order.status not in sources:
        raise InvalidTransition(f'采购单 {order.number} 当前为「{order.get_status_display()}」，不能执行 {action}')
    now = timezone.now()
    if action in ('submit', 'approve', 'receive') and not order.lines.exists():
        raise InvalidTransition('采购单没有明细')
    if action == 'submit':
        order.submitted_by, order.submitted_at = actor, now
    elif action == 'approve':
        order.approved_by, order.approved_at = actor, now
    elif action == 'receive':
        for line in order.lines.select_related('product'):
            ok, _, err = update_inventory(line.product, line.quantity, 'IN', actor,
                                          notes=f'采购入库 {order.number}')
            if not ok:
                raise InvalidTransition(f'入库失败：{err}')
            line.received_quantity = line.quantity
            line.save(update_fields=['received_quantity'])
        order.received_by, order.received_at = actor, now
        Payable.objects.create(
            tenant=order.tenant, supplier=order.supplier, purchase_order=order,
            amount=order.total_received_amount, due_date=timezone.localdate() + timedelta(days=30),
        )
    elif action == 'cancel':
        order.cancelled_by, order.cancelled_at = actor, now
    order.status = target
    order.save()
    _log(actor, order, f'采购单 {order.number} {action} → {target}')
    return order


@transaction.atomic
def transition_wholesale_order(order, action, actor):
    if action not in SO_TRANSITIONS:
        raise InvalidTransition(f'未知操作 {action}')
    sources, target, perm = SO_TRANSITIONS[action]
    _require_human(actor, perm)
    order = _lock(WholesaleOrder, order.pk)
    if order.status not in sources:
        raise InvalidTransition(f'批发订单 {order.number} 当前为「{order.get_status_display()}」，不能执行 {action}')
    now = timezone.now()
    if action in ('submit', 'approve', 'ship') and not order.lines.exists():
        raise InvalidTransition('批发订单没有明细')
    if action == 'submit':
        order.submitted_by, order.submitted_at = actor, now
    elif action == 'approve':
        order.approved_by, order.approved_at = actor, now
    elif action == 'ship':
        for line in order.lines.select_related('product'):
            ok, _, err = update_inventory(line.product, -line.quantity, 'OUT', actor,
                                          notes=f'批发发货 {order.number}')
            if not ok:
                # 抛异常 → 整个 atomic 回滚，已扣减的其他行一起撤销
                raise InvalidTransition(f'发货失败：{err}')
        order.shipped_by, order.shipped_at = actor, now
        Receivable.objects.create(
            tenant=order.tenant, customer=order.customer, wholesale_order=order,
            amount=order.total_amount,
            due_date=timezone.localdate() + timedelta(days=order.customer.payment_terms_days),
        )
    elif action == 'complete':
        order.completed_by, order.completed_at = actor, now
    elif action == 'cancel':
        order.cancelled_by, order.cancelled_at = actor, now
    order.status = target
    order.save()
    _log(actor, order, f'批发订单 {order.number} {action} → {target}')
    return order


def _settle(obj, field, amount, actor, perm, kind, reference):
    _require_human(actor, perm)
    amount = Decimal(str(amount))
    if amount <= 0:
        raise InvalidTransition('金额必须大于 0')
    if obj.status == 'SETTLED':
        raise InvalidTransition('已结清，不能再登记')
    paid = getattr(obj, field) + amount
    if paid > obj.amount:
        raise InvalidTransition(f'登记金额超过余额 {obj.amount - getattr(obj, field)}')
    setattr(obj, field, paid)
    obj.status = 'SETTLED' if paid == obj.amount else 'PARTIAL'
    obj.save()
    entry = SettlementEntry.objects.create(
        tenant=obj.tenant, kind=kind, amount=amount, reference=reference, operator=actor,
        **({'payable': obj} if kind == 'PAY' else {'receivable': obj}),
    )
    _log(actor, obj, f'{entry.get_kind_display()} {amount} ({reference})')
    return obj


@transaction.atomic
def record_payment(payable, amount, actor, reference=''):
    """人登记一笔已在线下完成的付款（系统不发起支付）。"""
    return _settle(_lock(Payable, payable.pk), 'paid_amount', amount, actor, 'b2b.record_payment', 'PAY', reference)


@transaction.atomic
def record_receipt(receivable, amount, actor, reference=''):
    return _settle(_lock(Receivable, receivable.pk), 'received_amount', amount, actor, 'b2b.record_receipt', 'COLLECT', reference)


def refresh_statement_amount(statement):
    """重新汇总系统入库金额：只改金额快照，不改状态（AI/规则可调用）。"""
    if statement.status != 'DRAFT':
        raise InvalidTransition('已决定的对账单不能重算')
    statement.system_amount = statement.compute_system_amount()
    statement.save(update_fields=['system_amount'])
    return statement


@transaction.atomic
def decide_statement(statement, decision, actor):
    targets = {'confirm': 'CONFIRMED', 'dispute': 'DISPUTED'}
    if decision not in targets:
        raise InvalidTransition(f'未知操作 {decision}')
    _require_human(actor, 'b2b.confirm_supplierstatement')
    statement = _lock(SupplierStatement, statement.pk)
    if statement.status != 'DRAFT':
        raise InvalidTransition('对账单已确认或已标记争议')
    if decision == 'confirm':
        if statement.supplier_amount is None:
            raise InvalidTransition('请先录入供应商对账金额')
        if statement.difference != 0:
            raise InvalidTransition(f'存在差异 {statement.difference}，不能确认；请核对或标记争议')
    statement.status = targets[decision]
    statement.decided_by, statement.decided_at = actor, timezone.now()
    statement.save()
    _log(actor, statement, f'对账单 {statement.pk} {decision}')
    return statement
