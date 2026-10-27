from django.contrib import admin

from .models import DecisionRun, DraftTask, Suggestion, SupplyTerm


@admin.register(SupplyTerm)
class SupplyTermAdmin(admin.ModelAdmin):
    list_display = ('product', 'supplier', 'lead_time_days', 'lead_time_sd_days', 'moq_units', 'unit_cost', 'is_primary', 'tenant')
    list_filter = ('tenant', 'is_primary')
    search_fields = ('product__name', 'supplier__name')


class SuggestionInline(admin.TabularInline):
    model = Suggestion
    extra = 0
    fields = ('title', 'severity', 'score', 'execution_mode', 'required_role', 'status')
    readonly_fields = fields
    can_delete = False


@admin.register(DecisionRun)
class DecisionRunAdmin(admin.ModelAdmin):
    list_display = ('pk', 'workflow', 'tenant', 'as_of', 'engine', 'parent', 'created_by', 'created_at')
    list_filter = ('tenant', 'workflow', 'engine')
    inlines = [SuggestionInline]
    readonly_fields = ('params', 'summary')


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'workflow', 'title', 'severity', 'execution_mode', 'status', 'decided_by', 'tenant')
    list_filter = ('tenant', 'workflow', 'status', 'execution_mode', 'severity')
    search_fields = ('title', 'target_label')
    readonly_fields = ('run', 'inputs', 'values', 'draft_payload')


@admin.register(DraftTask)
class DraftTaskAdmin(admin.ModelAdmin):
    list_display = ('pk', 'kind', 'title', 'assignee_role', 'external_ref', 'status', 'created_at', 'tenant')
    list_filter = ('tenant', 'kind', 'status')
