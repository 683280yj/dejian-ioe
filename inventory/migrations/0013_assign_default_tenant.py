"""数据迁移：已有 IOE 数据（升级前单店数据）统一归入「默认企业」。

全新库没有业务数据时什么都不做。可逆：反向迁移把 tenant 置空，不删除企业。
"""
from django.db import migrations

MODELS = ['Category', 'Product', 'Store', 'ProductBatch', 'Supplier', 'Inventory',
          'InventoryTransaction', 'StockAlert', 'InventoryCheck', 'MemberLevel', 'Member',
          'Sale', 'OperationLog']


def forwards(apps, schema_editor):
    has_data = any(apps.get_model('inventory', m).objects.filter(tenant__isnull=True).exists() for m in MODELS)
    if not has_data:
        return
    Tenant = apps.get_model('tenancy', 'Tenant')
    tenant, _ = Tenant.objects.get_or_create(code='default', defaults={'name': '默认企业', 'short_name': '默认企业'})
    for m in MODELS:
        apps.get_model('inventory', m).objects.filter(tenant__isnull=True).update(tenant=tenant)


def backwards(apps, schema_editor):
    Tenant = apps.get_model('tenancy', 'Tenant')
    t = Tenant.objects.filter(code='default').first()
    if t:
        for m in MODELS:
            apps.get_model('inventory', m).objects.filter(tenant=t).update(tenant=None)


class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0012_tenant_scoping'),
        ('tenancy', '0001_initial'),
    ]
    operations = [migrations.RunPython(forwards, backwards)]
