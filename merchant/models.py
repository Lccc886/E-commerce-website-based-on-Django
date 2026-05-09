from django.db import models
from django.conf import settings


class Merchant(models.Model):
    """商家信息"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='merchant',
        verbose_name="关联用户"
    )
    shop_name = models.CharField(max_length=100, verbose_name="店铺名称")
    logo = models.ImageField(
        upload_to='merchants/logos/',
        blank=True,
        null=True,
        verbose_name="店铺Logo"
    )
    description = models.TextField(blank=True, verbose_name="店铺简介")
    contact_phone = models.CharField(max_length=20, verbose_name="联系电话")
    contact_email = models.EmailField(verbose_name="联系邮箱")
    address = models.CharField(max_length=200, blank=True, verbose_name="店铺地址")

    # 审核状态
    STATUS_CHOICES = (
        ('pending', '待审核'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="审核状态"
    )
    reject_reason = models.TextField(blank=True, verbose_name="拒绝原因")

    # 统计数据
    total_sales = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="总销售额"
    )
    total_orders = models.PositiveIntegerField(default=0, verbose_name="总订单数")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "商家"
        verbose_name_plural = "商家"
        ordering = ['-created_at']

    def __str__(self):
        return self.shop_name

    @property
    def is_approved(self):
        return self.status == 'approved'

    def update_statistics(self):
        """更新统计数据"""
        from orders.models import Order, OrderItem
        from goods.models import Product

        # 获取商家所有商品
        product_ids = Product.objects.filter(merchant=self).values_list('id', flat=True)

        # 获取包含商家商品的订单项
        order_items = OrderItem.objects.filter(product_id__in=product_ids)

        # 计算总销售额
        self.total_sales = sum(item.price * item.quantity for item in order_items)

        # 计算总订单数（去重）
        self.total_orders = order_items.values('order').distinct().count()

        self.save(update_fields=['total_sales', 'total_orders'])
