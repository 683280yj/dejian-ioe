"""To B 交易模型：企业客户/经销商、采购单、批发订单、供应商对账、应收应付。

复用 IOE 现有模型：inventory.Product（商品）、inventory.Supplier（供应商）、
tenancy.Warehouse（lane-a 多仓）。

铁律：所有状态推进只能经 b2b.services 里的函数、由已登录的人显式触发；
模型本身的 save() 不会推进状态、不会动库存、不会付款。
"""
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.utils import timezone


def TenantFK():
    # lane-a 约定：tenancy app 由 渚 建；字段写法统一
    return models.ForeignKey('tenancy.Tenant', null=True, blank=True, on_delete=models.PROTECT)


def _next_number(model, prefix):
    today = timezone.localdate().strftime('%Y%m%d')
    stem = f'{prefix}-{today}-'
    last = model.objects.filter(number__startswith=stem).order_by('-number').values_list('number', flat=True).first()
    seq = int(last.rsplit('-', 1)[1]) + 1 if last else 1
    return f'{stem}{seq:04d}'


MONEY = dict(max_digits=14, decimal_places=2)


class Customer(models.Model):
    """企业客户 / 经销商（To B 下游）。"""
    KIND_CHOICES = [
        ('DISTRIBUTOR', '经销商'),
        ('ENTERPRISE', '企业客户'),
        ('RETAILER', '终端门店'),
    ]
    tenant = TenantFK()
    code = models.CharField(max_length=50, verbose_name='客户编码')
    name = models.CharField(max_length=200, verbose_name='客户名称')
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='DISTRIBUTOR', verbose_name='类型')
    contact_person = models.CharField(max_length=50, blank=True, verbose_name='联系人')
    phone = models.CharField(max_length=30, blank=True, verbose_name='电话')
    region = models.CharField(max_length=100, blank=True, verbose_name='授权区域')
    address = models.TextField(blank=True, verbose_name='地址')
    credit_limit = models.DecimalField(default=Decimal('0'), verbose_name='信用额度', **MONEY)
    payment_terms_days = models.PositiveIntegerField(default=30, verbose_name='账期(天)')
    is_active = models.BooleanField(default=True, verbose_name='启用')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = '企业客户/经销商'
        ordering = ['code']
        constraints = [models.UniqueConstraint(fields=['tenant', 'code'], name='b2b_customer_tenant_code_uniq')]

    def __str__(self):
        return f'{self.code} {self.name}'

    @property
    def outstanding(self):
        agg = self.receivables.exclude(status='SETTLED').aggregate(a=Sum('amount'), r=Sum('received_amount'))
        return (agg['a'] or Decimal('0')) - (agg['r'] or Decimal('0'))


class _OrderBase(models.Model):
    tenant = TenantFK()
    number = models.CharField(max_length=40, unique=True, editable=False, verbose_name='单号')
    warehouse = models.ForeignKey('tenancy.Warehouse', null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='仓库')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name='+', verbose_name='制单人')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='审批人')
    approved_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    cancelled_at = models.DateTimeField(null=True, blank=True)

    NUMBER_PREFIX = 'X'

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = _next_number(type(self), self.NUMBER_PREFIX)
        super().save(*args, **kwargs)

    @property
    def total_amount(self):
        expr = ExpressionWrapper(F('quantity') * F('unit_price'), output_field=DecimalField(**MONEY))
        # SQLite 对乘积聚合会丢精度格式（如 61582.2000000000），统一量化到分
        return (self.lines.aggregate(t=Sum(expr))['t'] or Decimal('0')).quantize(Decimal('0.01'))

    def __str__(self):
        return self.number


class PurchaseOrder(_OrderBase):
    """采购单。DRAFT → SUBMITTED → APPROVED → RECEIVED；DRAFT/SUBMITTED/APPROVED 可 CANCELLED。"""
    STATUS_CHOICES = [
        ('DRAFT', '草稿'),
        ('SUBMITTED', '待审批'),
        ('APPROVED', '已审批'),
        ('RECEIVED', '已入库'),
        ('CANCELLED', '已取消'),
    ]
    NUMBER_PREFIX = 'PO'
    supplier = models.ForeignKey('inventory.Supplier', on_delete=models.PROTECT, related_name='b2b_purchase_orders', verbose_name='供应商')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', editable=False, verbose_name='状态')
    expected_date = models.DateField(null=True, blank=True, verbose_name='预计到货')
    source = models.CharField(max_length=20, default='MANUAL', editable=False,
                              choices=[('MANUAL', '人工创建'), ('AI_DRAFT', 'AI 建议生成的草稿')], verbose_name='来源')
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='入库确认人')
    received_at = models.DateTimeField(null=True, blank=True)

    class Meta(_OrderBase.Meta):
        verbose_name = verbose_name_plural = '采购单'
        permissions = [
            ('approve_purchaseorder', '可以审批采购单'),
            ('receive_purchaseorder', '可以确认采购入库'),
        ]

    @property
    def total_received_amount(self):
        return sum((l.received_quantity * l.unit_price for l in self.lines.all()), Decimal('0'))


class PurchaseOrderLine(models.Model):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey('inventory.Product', on_delete=models.PROTECT, related_name='b2b_purchase_lines', verbose_name='商品')
    quantity = models.PositiveIntegerField(verbose_name='数量')
    unit_price = models.DecimalField(verbose_name='单价', **MONEY)
    received_quantity = models.PositiveIntegerField(default=0, editable=False, verbose_name='实收数量')

    class Meta:
        verbose_name = verbose_name_plural = '采购明细'

    @property
    def amount(self):
        return self.quantity * self.unit_price


class WholesaleOrder(_OrderBase):
    """批发订单。DRAFT → SUBMITTED → APPROVED → SHIPPED → COMPLETED；发货前可 CANCELLED。"""
    STATUS_CHOICES = [
        ('DRAFT', '草稿'),
        ('SUBMITTED', '待审批'),
        ('APPROVED', '已审批'),
        ('SHIPPED', '已发货'),
        ('COMPLETED', '已签收'),
        ('CANCELLED', '已取消'),
    ]
    NUMBER_PREFIX = 'SO'
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders', verbose_name='客户/经销商')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', editable=False, verbose_name='状态')
    shipped_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='发货人')
    shipped_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta(_OrderBase.Meta):
        verbose_name = verbose_name_plural = '批发订单'
        permissions = [
            ('approve_wholesaleorder', '可以审批批发订单'),
            ('ship_wholesaleorder', '可以确认批发发货'),
        ]


class WholesaleOrderLine(models.Model):
    order = models.ForeignKey(WholesaleOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey('inventory.Product', on_delete=models.PROTECT, related_name='b2b_wholesale_lines', verbose_name='商品')
    quantity = models.PositiveIntegerField(verbose_name='数量')
    unit_price = models.DecimalField(verbose_name='单价', **MONEY)

    class Meta:
        verbose_name = verbose_name_plural = '批发明细'

    @property
    def amount(self):
        return self.quantity * self.unit_price


class Payable(models.Model):
    """应付款：采购单人工确认入库时生成（金额=实收×单价）。付款只能由人登记。"""
    STATUS_CHOICES = [('OPEN', '未付'), ('PARTIAL', '部分已付'), ('SETTLED', '已结清')]
    tenant = TenantFK()
    supplier = models.ForeignKey('inventory.Supplier', on_delete=models.PROTECT, related_name='b2b_payables', verbose_name='供应商')
    purchase_order = models.OneToOneField(PurchaseOrder, null=True, blank=True, on_delete=models.PROTECT, related_name='payable')
    amount = models.DecimalField(verbose_name='应付金额', **MONEY)
    paid_amount = models.DecimalField(default=Decimal('0'), editable=False, verbose_name='已付金额', **MONEY)
    due_date = models.DateField(null=True, blank=True, verbose_name='到期日')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN', editable=False, verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = '应付款'
        ordering = ['due_date', 'id']
        permissions = [('record_payment', '可以登记付款')]

    @property
    def balance(self):
        return self.amount - self.paid_amount

    def __str__(self):
        return f'应付 {self.supplier} {self.amount}'


class Receivable(models.Model):
    """应收款：批发订单人工确认发货时生成。收款只能由人登记。"""
    STATUS_CHOICES = Payable.STATUS_CHOICES
    tenant = TenantFK()
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='receivables', verbose_name='客户/经销商')
    wholesale_order = models.OneToOneField(WholesaleOrder, null=True, blank=True, on_delete=models.PROTECT, related_name='receivable')
    amount = models.DecimalField(verbose_name='应收金额', **MONEY)
    received_amount = models.DecimalField(default=Decimal('0'), editable=False, verbose_name='已收金额', **MONEY)
    due_date = models.DateField(null=True, blank=True, verbose_name='到期日')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN', editable=False, verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = '应收款'
        ordering = ['due_date', 'id']
        permissions = [('record_receipt', '可以登记收款')]

    @property
    def balance(self):
        return self.amount - self.received_amount

    def __str__(self):
        return f'应收 {self.customer} {self.amount}'


class SettlementEntry(models.Model):
    """付款/收款登记流水（线下转账等由人录入；系统不发起任何支付）。"""
    KIND_CHOICES = [('PAY', '付款'), ('COLLECT', '收款')]
    tenant = TenantFK()
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    payable = models.ForeignKey(Payable, null=True, blank=True, on_delete=models.PROTECT, related_name='entries')
    receivable = models.ForeignKey(Receivable, null=True, blank=True, on_delete=models.PROTECT, related_name='entries')
    amount = models.DecimalField(**MONEY)
    reference = models.CharField(max_length=100, blank=True, verbose_name='凭证号/流水号')
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = '收付款登记'
        ordering = ['-created_at']


class SupplierStatement(models.Model):
    """供应商对账单：系统按期间汇总已入库采购额，人录入供应商对账金额，差异由人确认或标记争议。"""
    STATUS_CHOICES = [('DRAFT', '待对账'), ('CONFIRMED', '已确认'), ('DISPUTED', '有争议')]
    tenant = TenantFK()
    supplier = models.ForeignKey('inventory.Supplier', on_delete=models.PROTECT, related_name='b2b_statements', verbose_name='供应商')
    period_start = models.DateField(verbose_name='期间开始')
    period_end = models.DateField(verbose_name='期间结束')
    system_amount = models.DecimalField(default=Decimal('0'), editable=False, verbose_name='系统入库金额', **MONEY)
    supplier_amount = models.DecimalField(null=True, blank=True, verbose_name='供应商对账金额', **MONEY)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', editable=False, verbose_name='状态')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='确认人')
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = '供应商对账单'
        ordering = ['-period_end', '-id']
        permissions = [('confirm_supplierstatement', '可以确认供应商对账')]

    @property
    def difference(self):
        if self.supplier_amount is None:
            return None
        return self.supplier_amount - self.system_amount

    def purchase_orders(self):
        qs = PurchaseOrder.objects.filter(
            supplier=self.supplier, status='RECEIVED',
            received_at__date__gte=self.period_start, received_at__date__lte=self.period_end,
        )
        return qs.filter(tenant=self.tenant) if self.tenant_id else qs

    def compute_system_amount(self):
        """只读计算（可由 AI/规则调用），不改变状态。"""
        return sum((po.total_received_amount for po in self.purchase_orders()), Decimal('0'))

    def __str__(self):
        return f'{self.supplier} {self.period_start}~{self.period_end}'

