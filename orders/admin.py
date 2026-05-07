from django.contrib import admin
from .models import Order, OrderItem, Coupon, CouponUsage

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ('product',)
    readonly_fields = ('price', 'quantity', 'get_cost')
    fields = ('product', 'price', 'quantity', 'get_cost')
    extra = 0
    can_delete = False

    def get_cost(self, obj):
        return obj.get_cost()
    get_cost.short_description = '小计'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'paid', 'created', 'total_cost')
    list_filter = ('status', 'paid', 'created')
    search_fields = ('user__username', 'user__email', 'address')
    list_editable = ('status',)
    inlines = [OrderItemInline]
    readonly_fields = ('created', 'updated', 'total_cost')
    fieldsets = (
        ('订单信息', {'fields': ('user', 'status', 'paid')}),
        ('收货信息', {'fields': ('first_name', 'last_name', 'email', 'address', 'postal_code', 'city')}),
        ('时间信息', {'fields': ('created', 'updated')}),
    )
    actions = ['mark_as_paid', 'mark_as_shipped', 'mark_as_cancelled']

    def total_cost(self, obj):
        return obj.get_total_cost()
    total_cost.short_description = '总计'

    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='paid', paid=True)
        self.message_user(request, f'{updated} 个订单已标记为已支付')
    mark_as_paid.short_description = '标记为已支付'

    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f'{updated} 个订单已标记为已发货')
    mark_as_shipped.short_description = '标记为已发货'

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} 个订单已标记为已取消')
    mark_as_cancelled.short_description = '标记为已取消'


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'min_order_amount',
                    'valid_from', 'valid_to', 'usage_limit', 'used_count', 'active')
    list_filter = ('active', 'discount_type', 'valid_from', 'valid_to')
    search_fields = ('code',)
    list_editable = ('active',)
    ordering = ('-valid_from',)


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ('user', 'coupon', 'order', 'used_at')
    list_filter = ('used_at',)
    search_fields = ('user__username', 'coupon__code')
    readonly_fields = ('user', 'coupon', 'order', 'used_at')