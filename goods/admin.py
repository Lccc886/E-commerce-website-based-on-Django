from django.contrib import admin
from django.utils import timezone
from .models import Category, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'available', 'review_status', 'merchant', 'created_at')
    list_filter = ('available', 'review_status', 'category', 'created_at')
    search_fields = ('name', 'description', 'merchant__shop_name')
    list_editable = ('price', 'stock', 'available')
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 20
    fieldsets = (
        ('基本信息', {'fields': ('category', 'name', 'slug', 'description')}),
        ('价格与库存', {'fields': ('price', 'stock')}),
        ('状态', {'fields': ('available', 'is_new')}),
        ('图片', {'fields': ('image',)}),
        ('商家信息', {'fields': ('merchant',)}),
        ('审核信息', {'fields': ('review_status', 'reject_reason', 'reviewed_at')}),
    )
    readonly_fields = ('created_at', 'updated_at', 'reviewed_at')
    actions = ['approve_products', 'reject_products']

    def approve_products(self, request, queryset):
        count = queryset.filter(review_status='pending').update(
            review_status='approved',
            available=True,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'已通过 {count} 个商品审核')
    approve_products.short_description = '通过选中的商品审核'

    def reject_products(self, request, queryset):
        count = queryset.filter(review_status='pending').update(
            review_status='rejected',
            available=False,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'已拒绝 {count} 个商品')
    reject_products.short_description = '拒绝选中的商品'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('created_at',)
