from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

HEX_COLOR = RegexValidator(r'^#[0-9a-fA-F]{6}$', '请填写 #RRGGBB 格式的颜色')
DEFAULT_PRIMARY = '#6e1f2c'


class Tenant(models.Model):
    """企业客户（租户）。一个企业可以有多个品牌、仓库、渠道。"""
    name = models.CharField(max_length=100, verbose_name='企业名称')
    short_name = models.CharField(max_length=50, blank=True, verbose_name='简称')
    code = models.SlugField(max_length=50, unique=True, verbose_name='企业编码')
    industry = models.CharField(max_length=50, blank=True, verbose_name='行业')
    region = models.CharField(max_length=100, blank=True, verbose_name='所在地')
    description = models.TextField(blank=True, verbose_name='简介')
    is_demo = models.BooleanField(default=False, verbose_name='演示数据')
    is_active = models.BooleanField(default=True, verbose_name='启用')
    # 品牌外观：只用文字字标，不上传图形 logo
    display_name = models.CharField(max_length=20, blank=True, verbose_name='显示名（文字字标）',
                                    help_text='侧栏/顶栏/登录页显示的文字，留空则用简称或企业名称')
    primary_color = models.CharField(max_length=7, default=DEFAULT_PRIMARY, validators=[HEX_COLOR], verbose_name='主色')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = '企业'
        ordering = ['id']

    def __str__(self):
        return self.short_name or self.name

    @property
    def wordmark(self):
        return self.display_name or self.short_name or self.name

    @property
    def primary_rgb(self):
        c = (self.primary_color or DEFAULT_PRIMARY).lstrip('#')
        try:
            return ', '.join(str(int(c[i:i + 2], 16)) for i in (0, 2, 4))
        except ValueError:
            return '110, 31, 44'

    def save(self, *args, **kwargs):
        if not self.code:  # 未指定编码时自动生成，避免唯一约束冲突
            import uuid
            from django.utils.text import slugify
            self.code = (slugify(self.name)[:30] or 't') + '-' + uuid.uuid4().hex[:6]
        super().save(*args, **kwargs)


class Brand(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='brands', verbose_name='企业')
    name = models.CharField(max_length=100, verbose_name='品牌名称')
    code = models.CharField(max_length=30, verbose_name='品牌编码')
    is_own = models.BooleanField(default=True, verbose_name='自有品牌')  # False=代理品牌
    positioning = models.CharField(max_length=200, blank=True, verbose_name='定位')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = verbose_name_plural = '品牌'
        ordering = ['tenant', 'id']
        constraints = [models.UniqueConstraint(fields=['tenant', 'code'], name='tenancy_brand_tenant_code_uniq')]

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='warehouses', verbose_name='企业')
    name = models.CharField(max_length=100, verbose_name='仓库名称')
    code = models.CharField(max_length=30, verbose_name='仓库编码')
    address = models.CharField(max_length=200, blank=True, verbose_name='地址')
    capacity_units = models.PositiveIntegerField(default=0, verbose_name='库容(瓶/件)', help_text='0 表示不限制')
    is_default = models.BooleanField(default=False, verbose_name='默认仓')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = verbose_name_plural = '仓库'
        ordering = ['tenant', '-is_default', 'id']
        constraints = [models.UniqueConstraint(fields=['tenant', 'code'], name='tenancy_wh_tenant_code_uniq')]

    def __str__(self):
        return self.name


class Channel(models.Model):
    KIND_CHOICES = [
        ('DEALER', '经销商'),
        ('GROUP', '团购/企业客户'),
        ('STORE', '直营门店'),
        ('ONLINE', '电商平台'),
        ('OTHER', '其他'),
    ]
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='channels', verbose_name='企业')
    name = models.CharField(max_length=100, verbose_name='渠道名称')
    code = models.CharField(max_length=30, verbose_name='渠道编码')
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='OTHER', verbose_name='类型')
    min_price_ratio = models.DecimalField(max_digits=4, decimal_places=2, default=0.85,
                                          verbose_name='最低成交价/标准价', help_text='价格管控规则，低于此比例视为异常')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = verbose_name_plural = '销售渠道'
        ordering = ['tenant', 'id']
        constraints = [models.UniqueConstraint(fields=['tenant', 'code'], name='tenancy_ch_tenant_code_uniq')]

    def __str__(self):
        return self.name


class Role(models.TextChoices):
    BOSS = 'boss', '老板'
    PURCHASER = 'purchaser', '采购'
    SALES = 'sales', '销售'
    WAREHOUSE = 'warehouse', '仓库'
    FINANCE = 'finance', '财务'
    AUDITOR = 'auditor', '稽核'


class Membership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tenant_memberships')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=Role.choices, verbose_name='角色')
    title = models.CharField(max_length=50, blank=True, verbose_name='职务')
    brands = models.ManyToManyField(Brand, blank=True, verbose_name='负责品牌', help_text='为空表示全部品牌')
    is_default = models.BooleanField(default=True, verbose_name='默认企业')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = '企业成员'
        constraints = [models.UniqueConstraint(fields=['user', 'tenant'], name='tenancy_member_user_tenant_uniq')]

    def __str__(self):
        return f'{self.user} @ {self.tenant} ({self.get_role_display()})'
