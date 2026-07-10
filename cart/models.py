"""
购物车数据模型
从 Session 迁移到数据库，支持持久化存储
"""
from django.conf import settings
from django.db import models


class Cart(models.Model):
    """用户购物车"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name="用户"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "购物车"
        verbose_name_plural = "购物车"

    def __str__(self):
        return f"{self.user.username} 的购物车"

    @property
    def total_items(self):
        return self.items.filter(
            product__available=True, product__review_status='approved'
        ).aggregate(total=models.Sum('quantity'))['total'] or 0

    @property
    def total_price(self):
        result = self.items.filter(
            product__available=True, product__review_status='approved'
        ).aggregate(
            total=models.Sum(models.F('price_at_add') * models.F('quantity'))
        )['total']
        return result or 0


class CartItem(models.Model):
    """购物车商品项"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name="购物车")
    product = models.ForeignKey(
        'goods.Product', on_delete=models.CASCADE, verbose_name="商品"
    )
    sku = models.ForeignKey(
        'goods.ProductSKU',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="SKU"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="数量")
    price_at_add = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="加入时单价"
    )
    specs_snapshot = models.JSONField(
        default=dict, blank=True, verbose_name="规格快照"
    )
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")

    class Meta:
        verbose_name = "购物车项"
        verbose_name_plural = "购物车项"
        # 同商品+同SKU在购物车中只能出现一次
        unique_together = ('cart', 'product', 'sku')
        ordering = ['-added_at']

    def save(self, *args, **kwargs):
        # 数量上限保护：不超过 99
        self.quantity = min(self.quantity, 99)
        super().save(*args, **kwargs)

    def __str__(self):
        sku_info = f" ({self.sku.sku_code})" if self.sku else ""
        return f"{self.product.name}{sku_info} × {self.quantity}"

    @property
    def subtotal(self):
        return self.price_at_add * self.quantity

    @property
    def specs_display(self):
        """规格文本：'红色 / XL'"""
        if self.sku and self.sku.specs:
            return ' / '.join(self.sku.specs.values())
        if self.specs_snapshot:
            return ' / '.join(self.specs_snapshot.values())
        return ''
