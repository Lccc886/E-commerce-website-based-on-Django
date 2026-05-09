from django.contrib import admin
from django.utils.html import format_html
from .models import Merchant


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ['shop_name', 'user', 'status', 'contact_phone', 'contact_email', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['shop_name', 'user__username', 'contact_phone', 'contact_email']
    readonly_fields = ['created_at', 'updated_at', 'total_sales', 'total_orders']

    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'shop_name', 'logo', 'description')
        }),
        ('联系方式', {
            'fields': ('contact_phone', 'contact_email', 'address')
        }),
        ('审核状态', {
            'fields': ('status', 'reject_reason')
        }),
        ('统计数据', {
            'fields': ('total_sales', 'total_orders')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['approve_merchants', 'reject_merchants']

    def approve_merchants(self, request, queryset):
        count = queryset.filter(status='pending').update(status='approved')
        self.message_user(request, f'已通过 {count} 个商家申请')
    approve_merchants.short_description = '通过选中的商家申请'

    def reject_merchants(self, request, queryset):
        count = queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f'已拒绝 {count} 个商家申请')
    reject_merchants.short_description = '拒绝选中的商家申请'
