"""智能补货/库存提示的记录：测算(DecisionRun) → 建议(Suggestion) → 采纳后的草稿(DraftTask)。

本 app 不修改库存、不提交/审批订单；唯一的自动写入是 IOE 原生的库存预警(StockAlert)。
"""
from django.conf import settings
from django.db import models

from tenancy.managers import TenantManager

TENANT = dict(to='tenancy.Tenant', null=True, blank=True, on_delete=models.CASCADE, related_name='+', verbose_name='企业')

WORKFLOW_CHOICES = [
    ('replenish', '补货测算'),
    ('stock_alert', '库存预警'),
]
CYCLE_CHOICES = [('realtime', '实时'), ('day', '日'), ('week', '周'), ('month', '月')]
MODE_CHOICES = [('auto', '自动执行（低风险）'), ('review', '人工复核确认')]


class SupplyTerm(models.Model):
    """供货条款：补货测算的约束主数据（交期、起订量、箱规、采购价）。"""
    tenant = models.ForeignKey(**TENANT)
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='supply_terms', verbose_name='商品')
    supplier = models.ForeignKey('inventory.Supplier', on_delete=models.CASCADE, related_name='supply_terms', verbose_name='供应商')
    lead_time_days = models.PositiveIntegerField(default=10, verbose_name='交期(天)')
    lead_time_sd_days = models.DecimalField(max_digits=5, decimal_places=1, default=2, verbose_name='交期波动(天)')
    moq_units = models.PositiveIntegerField(default=0, verbose_name='起订量(瓶)')
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='采购价')
    is_primary = models.BooleanField(default=True, verbose_name='主供应商')
    objects = TenantManager()

    class Meta:
        verbose_name = verbose_name_plural = '供货条款'
        constraints = [models.UniqueConstraint(fields=['product', 'supplier'], name='ai_supplyterm_prod_sup_uniq')]

    def __str__(self):
        return f'{self.product} ← {self.supplier}'


class DecisionRun(models.Model):
    tenant = models.ForeignKey(**TENANT)
    brand = models.ForeignKey('tenancy.Brand', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    workflow = models.CharField(max_length=30, choices=WORKFLOW_CHOICES, verbose_name='环节')
    params = models.JSONField(default=dict, verbose_name='目标与约束参数')
    objective = models.CharField(max_length=300, blank=True, verbose_name='量化目标')
    update_cycle = models.CharField(max_length=10, choices=CYCLE_CHOICES, verbose_name='更新周期')
    summary = models.JSONField(default=dict, verbose_name='汇总指标')
    engine = models.CharField(max_length=50, default='rules', verbose_name='引擎')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children', verbose_name='基于哪次测算(what-if)')
    as_of = models.DateField(null=True, blank=True, verbose_name='数据截止日')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    objects = TenantManager()

    class Meta:
        verbose_name = verbose_name_plural = 'AI 测算记录'
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f'{self.get_workflow_display()} #{self.pk}'


class Suggestion(models.Model):
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('adopted', '已生成草稿'),
        ('rejected', '已忽略'),
        ('auto_done', '已生成预警'),
        ('superseded', '已被新测算替代'),
    ]
    SEVERITY_CHOICES = [('high', '高'), ('medium', '中'), ('low', '低'), ('info', '提示')]
    tenant = models.ForeignKey(**TENANT)
    run = models.ForeignKey(DecisionRun, on_delete=models.CASCADE, related_name='suggestions')
    workflow = models.CharField(max_length=30, choices=WORKFLOW_CHOICES)
    title = models.CharField(max_length=300, verbose_name='处置动作')
    target_label = models.CharField(max_length=200, blank=True, verbose_name='对象')
    product = models.ForeignKey('inventory.Product', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    quantity = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, verbose_name='数量')
    unit = models.CharField(max_length=20, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, verbose_name='金额')
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    score = models.FloatField(default=0, verbose_name='优先级/异常分')
    rationale = models.TextField(blank=True, verbose_name='依据')
    formula = models.TextField(blank=True, verbose_name='公式')
    inputs = models.JSONField(default=dict, verbose_name='输入数据')
    values = models.JSONField(default=dict, verbose_name='计算取值')
    execution_mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='review')
    required_role = models.CharField(max_length=20, blank=True, verbose_name='确认角色')
    ai_explanation = models.TextField(blank=True, verbose_name='人话解释（展示用）')
    ai_anomalies = models.JSONField(default=list, blank=True, verbose_name='异常标记')
    ai_source = models.CharField(max_length=10, blank=True, verbose_name='解释来源(llm/rule)')
    ai_generated_at = models.DateTimeField(null=True, blank=True, verbose_name='解释生成时间')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    decided_at = models.DateTimeField(null=True, blank=True)
    reject_reason = models.TextField(blank=True, verbose_name='忽略原因')
    draft_kind = models.CharField(max_length=30, blank=True, verbose_name='采纳后生成的草稿类型')
    draft_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = TenantManager()

    class Meta:
        verbose_name = verbose_name_plural = 'AI 建议'
        ordering = ['-score', 'id']

    def __str__(self):
        return self.title


class ChatTurn(models.Model):
    """筹策助手对话记录（按企业+用户持久化，刷新页面不丢）。"""
    tenant = models.ForeignKey(**TENANT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             on_delete=models.CASCADE, related_name='+')
    role = models.CharField(max_length=10, choices=[('user', '用户'), ('assistant', '助手')])
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    objects = TenantManager()

    class Meta:
        verbose_name = verbose_name_plural = '助手对话记录'
        ordering = ['created_at', 'id']
        indexes = [models.Index(fields=['tenant', 'user', 'created_at'])]

    def __str__(self):
        return f'{self.role}: {self.content[:30]}'


class DraftTask(models.Model):
    """人采纳建议后生成的草稿/待办。只有人能把它推进到「已执行」。"""
    KIND_CHOICES = [
        ('purchase_draft', '采购单草稿'),
        ('stock_alert', '库存预警处理'),
    ]
    STATUS_CHOICES = [('open', '待处理'), ('done', '已由人执行'), ('cancelled', '已取消')]
    tenant = models.ForeignKey(**TENANT)
    suggestion = models.ForeignKey(Suggestion, null=True, blank=True, on_delete=models.SET_NULL, related_name='drafts')
    kind = models.CharField(max_length=30, choices=KIND_CHOICES)
    title = models.CharField(max_length=300)
    body = models.TextField(blank=True)
    payload = models.JSONField(default=dict)
    assignee_role = models.CharField(max_length=20, blank=True, verbose_name='处理角色')
    external_ref = models.CharField(max_length=100, blank=True, verbose_name='关联单据', help_text='如 b2b 采购单号')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    closed_at = models.DateTimeField(null=True, blank=True)
    objects = TenantManager()

    class Meta:
        verbose_name = verbose_name_plural = '草稿/待办'
        ordering = ['-created_at', '-id']

    def __str__(self):
        return self.title
