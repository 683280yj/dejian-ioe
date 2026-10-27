"""b2b 页面。所有状态流转都是 POST + 登录 + 权限，由人点击按钮触发。"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import services
from .forms import (
    CustomerForm, PurchaseOrderForm, PurchaseOrderLineForm, WholesaleOrderForm,
    WholesaleOrderLineForm, SupplierStatementForm, SupplierAmountForm, SettlementForm,
)
from .models import (
    Customer, PurchaseOrder, WholesaleOrder, Payable, Receivable, SupplierStatement,
)


def current_tenant(request):
    """lane-a 的中间件会把当前租户挂到 request.tenant；未接入时为 None（不过滤）。"""
    return getattr(request, 'tenant', None)


def scoped(request, qs):
    tenant = current_tenant(request)
    return qs.filter(tenant=tenant) if tenant is not None else qs


def get_scoped(request, model, pk):
    # 越权访问 → 404
    return get_object_or_404(scoped(request, model.objects.all()), pk=pk)


def _errmsg(exc):
    return '; '.join(exc.messages) if isinstance(exc, ValidationError) else str(exc)


@login_required
def dashboard(request):
    ctx = {
        'po_pending': scoped(request, PurchaseOrder.objects.filter(status__in=['SUBMITTED', 'APPROVED'])).count(),
        'so_pending': scoped(request, WholesaleOrder.objects.filter(status__in=['SUBMITTED', 'APPROVED'])).count(),
        'payable_open': scoped(request, Payable.objects.exclude(status='SETTLED')).aggregate(a=Sum('amount'), p=Sum('paid_amount')),
        'receivable_open': scoped(request, Receivable.objects.exclude(status='SETTLED')).aggregate(a=Sum('amount'), p=Sum('received_amount')),
        'statements_draft': scoped(request, SupplierStatement.objects.filter(status='DRAFT')).count(),
    }
    return render(request, 'b2b/dashboard.html', ctx)


# ---------- 企业客户 / 经销商 ----------
@login_required
def customer_list(request):
    return render(request, 'b2b/customer_list.html',
                  {'customers': scoped(request, Customer.objects.all())})


@login_required
def customer_form(request, pk=None):
    instance = get_scoped(request, Customer, pk) if pk else None
    form = CustomerForm(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        if obj.tenant_id is None:
            obj.tenant = current_tenant(request)
        obj.save()
        messages.success(request, '已保存')
        return redirect('b2b:customer_list')
    return render(request, 'b2b/form.html', {'form': form, 'title': '企业客户/经销商'})


# ---------- 通用订单 ----------
def _order_list(request, model, template, status_choices):
    qs = scoped(request, model.objects.all())
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    return render(request, template, {'orders': qs, 'status': status, 'status_choices': status_choices})


def _order_create(request, form_cls, title, detail_name):
    form = form_cls(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.tenant = current_tenant(request)
        obj.created_by = request.user
        obj.save()  # 永远以 DRAFT 创建
        return redirect(detail_name, pk=obj.pk)
    return render(request, 'b2b/form.html', {'form': form, 'title': title})


def _order_detail(request, model, pk, template, line_form_cls, actions):
    order = get_scoped(request, model, pk)
    line_form = line_form_cls()
    if request.method == 'POST':
        if order.status != 'DRAFT':
            raise PermissionDenied('只有草稿可以加明细')
        line_form = line_form_cls(request.POST)
        if line_form.is_valid():
            line = line_form.save(commit=False)
            line.order = order
            line.save()
            return redirect(request.path)
    available = [a for a, (src, _, _) in actions.items() if order.status in src]
    return render(request, template, {'order': order, 'line_form': line_form, 'actions': available})


def _order_transition(request, model, pk, action, fn, detail_name):
    order = get_scoped(request, model, pk)
    try:
        fn(order, action, request.user)
        label = {'submit': '提交审批', 'approve': '审批通过', 'receive': '确认入库', 'ship': '确认发货',
                 'complete': '确认签收', 'cancel': '取消'}.get(action, action)
        messages.success(request, f'已执行：{label}')
    except PermissionDenied:
        raise
    except ValidationError as exc:
        messages.error(request, _errmsg(exc))
    return redirect(detail_name, pk=pk)


@login_required
def po_list(request):
    return _order_list(request, PurchaseOrder, 'b2b/po_list.html', PurchaseOrder.STATUS_CHOICES)


@login_required
def po_create(request):
    return _order_create(request, PurchaseOrderForm, '新建采购单', 'b2b:po_detail')


@login_required
def po_detail(request, pk):
    return _order_detail(request, PurchaseOrder, pk, 'b2b/po_detail.html', PurchaseOrderLineForm, services.PO_TRANSITIONS)


@login_required
@require_POST
def po_transition(request, pk, action):
    if action not in services.PO_TRANSITIONS:
        raise Http404
    return _order_transition(request, PurchaseOrder, pk, action, services.transition_purchase_order, 'b2b:po_detail')


@login_required
def so_list(request):
    return _order_list(request, WholesaleOrder, 'b2b/so_list.html', WholesaleOrder.STATUS_CHOICES)


@login_required
def so_create(request):
    form_cls = WholesaleOrderForm
    tenant = current_tenant(request)
    if tenant is not None:
        class form_cls(WholesaleOrderForm):  # noqa: N801 只显示本租户客户
            def __init__(self, *a, **kw):
                super().__init__(*a, **kw)
                self.fields['customer'].queryset = Customer.objects.filter(tenant=tenant)
    return _order_create(request, form_cls, '新建批发订单', 'b2b:so_detail')


@login_required
def so_detail(request, pk):
    return _order_detail(request, WholesaleOrder, pk, 'b2b/so_detail.html', WholesaleOrderLineForm, services.SO_TRANSITIONS)


@login_required
@require_POST
def so_transition(request, pk, action):
    if action not in services.SO_TRANSITIONS:
        raise Http404
    return _order_transition(request, WholesaleOrder, pk, action, services.transition_wholesale_order, 'b2b:so_detail')


# ---------- 应收应付 ----------
@login_required
def payable_list(request):
    return render(request, 'b2b/ledger_list.html', {
        'title': '应付款', 'rows': scoped(request, Payable.objects.select_related('supplier', 'purchase_order').order_by('status', 'due_date', 'id')),
        'kind': 'payable', 'form': SettlementForm()})


@login_required
def receivable_list(request):
    return render(request, 'b2b/ledger_list.html', {
        'title': '应收款', 'rows': scoped(request, Receivable.objects.select_related('customer', 'wholesale_order').order_by('status', 'due_date', 'id')),
        'kind': 'receivable', 'form': SettlementForm()})


def _settle_view(request, model, pk, fn, back):
    obj = get_scoped(request, model, pk)
    form = SettlementForm(request.POST)
    if not form.is_valid():
        messages.error(request, '金额无效')
        return redirect(back)
    try:
        fn(obj, form.cleaned_data['amount'], request.user, form.cleaned_data['reference'])
        messages.success(request, '已登记')
    except PermissionDenied:
        raise
    except ValidationError as exc:
        messages.error(request, _errmsg(exc))
    return redirect(back)


@login_required
@require_POST
def payable_pay(request, pk):
    return _settle_view(request, Payable, pk, services.record_payment, 'b2b:payable_list')


@login_required
@require_POST
def receivable_collect(request, pk):
    return _settle_view(request, Receivable, pk, services.record_receipt, 'b2b:receivable_list')


# ---------- 供应商对账 ----------
@login_required
def statement_list(request):
    return render(request, 'b2b/statement_list.html',
                  {'statements': scoped(request, SupplierStatement.objects.select_related('supplier'))})


@login_required
def statement_create(request):
    form = SupplierStatementForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        st = form.save(commit=False)
        st.tenant = current_tenant(request)
        st.created_by = request.user
        st.save()
        services.refresh_statement_amount(st)
        return redirect('b2b:statement_detail', pk=st.pk)
    return render(request, 'b2b/form.html', {'form': form, 'title': '新建供应商对账单'})


@login_required
def statement_detail(request, pk):
    st = get_scoped(request, SupplierStatement, pk)
    form = SupplierAmountForm(instance=st)
    if request.method == 'POST':
        if st.status != 'DRAFT':
            raise PermissionDenied('已决定的对账单不能修改')
        form = SupplierAmountForm(request.POST, instance=st)
        if form.is_valid():
            form.save()
            services.refresh_statement_amount(st)
            return redirect(request.path)
    return render(request, 'b2b/statement_detail.html',
                  {'st': st, 'form': form, 'orders': st.purchase_orders()})


@login_required
@require_POST
def statement_decide(request, pk, decision):
    if decision not in ('confirm', 'dispute'):
        raise Http404
    st = get_scoped(request, SupplierStatement, pk)
    try:
        services.decide_statement(st, decision, request.user)
        messages.success(request, '已处理')
    except PermissionDenied:
        raise
    except ValidationError as exc:
        messages.error(request, _errmsg(exc))
    return redirect('b2b:statement_detail', pk=pk)
