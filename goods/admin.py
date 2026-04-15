from django.contrib import admin
from .models import Category, Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'available', 'created_at')
    list_filter = ('available', 'category', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('price', 'stock', 'available')
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 20
    fieldsets = (
        ('基本信息', {'fields': ('category', 'name', 'slug', 'description')}),
        ('价格与库存', {'fields': ('price', 'stock')}),
        ('状态', {'fields': ('available',)}),
        ('图片', {'fields': ('image',)}),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('created_at',)