from django.contrib import admin
from .models import CarouselImage

@admin.register(CarouselImage)
class CarouselImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'product', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    raw_id_fields = ('product',)  # 如果商品数量多，用弹窗选择
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'product', 'image', 'link', 'order', 'is_active')
        }),
    )
    help_texts = {
        'link': '如果选择了商品，则自动使用商品详情链接；否则可自定义链接。',
        'image': '如果选择了商品，可以不传图片，将自动使用商品主图。',
    }
