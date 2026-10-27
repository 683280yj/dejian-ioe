from django.contrib import admin

from . import models


class POLineInline(admin.TabularInline):
    model = models.PurchaseOrderLine
    extra = 0


class SOLineInline(admin.TabularInline):
    model = models.WholesaleOrderLine
    extra = 0


@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'kind', 'region', 'credit_limit', 'is_active')
    search_fields = ('code', 'name')


@admin.register(models.PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    # status 不可编辑：流转只能走 b2b 页面上的人工操作按钮
    list_display = ('number', 'supplier', 'status', 'created_at')
    readonly_fields = ('number', 'status')
    inlines = [POLineInline]


@admin.register(models.WholesaleOrder)
class WholesaleOrderAdmin(admin.ModelAdmin):
    list_display = ('number', 'customer', 'status', 'created_at')
    readonly_fields = ('number', 'status')
    inlines = [SOLineInline]


for m in (models.Payable, models.Receivable, models.SettlementEntry, models.SupplierStatement):
    admin.site.register(m)
