from django.db import models
from django.conf import settings
from django.utils import timezone
from goods.models import Product


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ('fixed', '固定金额'),
        ('percent', '百分比折扣'),
    )
    code = models.CharField(max_length=50, unique=True, verbose_name="优惠券代码")
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, verbose_name="折扣类型")
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="折扣值")
    valid_from = models.DateTimeField(verbose_name="有效期开始")
    valid_to = models.DateTimeField(verbose_name="有效期结束")
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="最低订单金额")
    usage_limit = models.PositiveIntegerField(default=1, verbose_name="使用次数限制")
    used_count = models.PositiveIntegerField(default=0, verbose_name="已使用次数")
    active = models.BooleanField(default=True, verbose_name="是否激活")

    class Meta:
        verbose_name = "优惠券"
        verbose_name_plural = "优惠券"

    def __str__(self):
        return self.code

    def is_valid(self, user):
        now = timezone.now()
        if not self.active:
            return False
        if now < self.valid_from or now > self.valid_to:
            return False
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        # 检查用户使用次数（需要额外记录）
        return True


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    first_name = models.CharField(max_length=50, verbose_name="名字")
    last_name = models.CharField(max_length=50, verbose_name="姓氏")
    email = models.EmailField(verbose_name="邮箱")
    address = models.CharField(max_length=250, verbose_name="地址")
    postal_code = models.CharField(max_length=20, verbose_name="邮政编码")
    city = models.CharField(max_length=100, verbose_name="城市")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid = models.BooleanField(default=False, verbose_name="已支付")
    STATUS_CHOICES = (
        ('pending', '待支付'),
        ('paid', '已支付'),
        ('shipped', '已发货'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="支付时间")
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="优惠券")
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="折扣金额")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-created']
        verbose_name = "订单"
        verbose_name_plural = "订单"

    def __str__(self):
        return f'Order {self.id}'

    def get_total_cost(self):
        total = sum(item.get_cost() for item in self.items.all())
        if self.discount:
            total -= self.discount
        return total

    def mark_as_paid(self):
        self.status = 'paid'
        self.paid = True
        self.paid_at = timezone.now()
        self.save()

    def mark_as_shipped(self):
        self.status = 'shipped'
        self.save()

    def mark_as_completed(self):
        self.status = 'completed'
        self.save()

    def cancel(self):
        if self.status == 'pending':
            for item in self.items.all():
                product = item.product
                product.stock += item.quantity
                product.save()
            self.status = 'cancelled'
            self.save()

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="订单")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items', verbose_name="商品")
    sku = models.ForeignKey('goods.ProductSKU', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="SKU")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="单价")
    quantity = models.PositiveIntegerField(default=1, verbose_name="数量")
    specs_snapshot = models.JSONField(default=dict, blank=True, verbose_name="规格快照")  # 下单时的规格信息

    class Meta:
        verbose_name = "订单项"
        verbose_name_plural = "订单项"

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity

    @property
    def specs_display(self):
        """显示规格信息"""
        if self.specs_snapshot:
            return ', '.join([f"{k}: {v}" for k, v in self.specs_snapshot.items()])
        return "-"





class CouponUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="用户")
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, verbose_name="优惠券")
    order = models.ForeignKey('Order', on_delete=models.CASCADE, verbose_name="订单")
    used_at = models.DateTimeField(auto_now_add=True, verbose_name="使用时间")

    class Meta:
        verbose_name = "优惠券使用记录"
        verbose_name_plural = "优惠券使用记录"
        unique_together = ('user', 'coupon')


class Payment(models.Model):
    """支付记录（模拟沙箱）"""
    PAYMENT_METHOD_CHOICES = (
        ('alipay', '支付宝'),
        ('wechat', '微信支付'),
    )
    STATUS_CHOICES = (
        ('pending', '待支付'),
        ('success', '支付成功'),
        ('failed', '支付失败'),
        ('cancelled', '已取消'),
    )

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment', verbose_name="订单")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name="支付方式")
    trade_no = models.CharField(max_length=64, unique=True, verbose_name="交易号")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="支付金额")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="支付状态")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="支付时间")

    class Meta:
        verbose_name = "支付记录"
        verbose_name_plural = "支付记录"
        ordering = ['-created_at']

    def __str__(self):
        return f"支付记录 {self.trade_no}"

    def mark_as_success(self):
        """标记支付成功"""
        self.status = 'success'
        self.paid_at = timezone.now()
        self.save()
        # 同时更新订单状态
        self.order.mark_as_paid()

    def mark_as_failed(self):
        """标记支付失败"""
        self.status = 'failed'
        self.save()

    def mark_as_cancelled(self):
        """标记支付取消"""
        self.status = 'cancelled'
        self.save()