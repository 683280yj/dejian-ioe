from django.contrib import admin

from .models import Brand, Channel, Membership, Tenant, Warehouse

for m in (Tenant, Brand, Warehouse, Channel, Membership):
    admin.site.register(m)
