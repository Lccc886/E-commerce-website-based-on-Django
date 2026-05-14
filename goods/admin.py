from django.contrib import admin
from django.utils import timezone
from .models import Category, Product, ProductSpec, ProductSpecValue, ProductSKU


class ProductSpecInline(admin.TabularInline):
    """规格内联管理"""
    model = ProductSpec
    extra = 1
    show_change_link = True


class ProductSKUInline(admin.TabularInline):
    """SKU内联管理"""
    model = ProductSKU
    extra = 1
    fields = ('sku_code', 'specs', 'price', 'original_price', 'stock', 'is_default')
    readonly_fields = ('created_at', 'updated_at')


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
    inlines = [ProductSpecInline, ProductSKUInline]

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


@admin.register(ProductSpec)
class ProductSpecAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'sort_order')
    list_filter = ('product',)
    search_fields = ('product__name', 'name')
    ordering = ('product', 'sort_order')


@admin.register(ProductSpecValue)
class ProductSpecValueAdmin(admin.ModelAdmin):
    list_display = ('spec', 'value', 'sort_order')
    list_filter = ('spec',)
    search_fields = ('spec__name', 'value')
    ordering = ('spec', 'sort_order')


@admin.register(ProductSKU)
class ProductSKUAdmin(admin.ModelAdmin):
    list_display = ('sku_code', 'product', 'price', 'stock', 'is_default')
    list_filter = ('product', 'is_default')
    search_fields = ('sku_code', 'product__name')
    list_editable = ('price', 'stock', 'is_default')
    ordering = ('product', 'id')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('created_at',)
