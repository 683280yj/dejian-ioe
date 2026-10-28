from django.contrib import admin

from inventory.models import BookingLead


@admin.register(BookingLead)
class BookingLeadAdmin(admin.ModelAdmin):
    list_display = ('phone', 'category', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('phone', 'category')
    readonly_fields = ('phone', 'category', 'created_at')
    fields = ('phone', 'category', 'status', 'created_at')

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False
