from datetime import timezone

from django.db import models
from django.conf import settings
from goods.models import Product


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ('fixed', '固定金额'),
        ('percent', '百分比折扣'),
    )
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)  # 固定金额或百分比数值
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    usage_limit = models.PositiveIntegerField(default=1)  # 每个用户可用次数
    used_count = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

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
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid = models.BooleanField(default=False, verbose_name="已支付")
    STATUS_CHOICES = (
        ('pending', '待支付'),
        ('paid', '已支付'),
        ('shipped', '已发货'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    )
    class Meta:
        ordering = ['-created']
        verbose_name = "订单"
        verbose_name_plural = "订单"

    def __str__(self):
        return f'Order {self.id}'

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

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
        # 取消订单时恢复库存
        if self.status == 'pending':
            for item in self.items.all():
                product = item.product
                product.stock += item.quantity
                product.save()
            self.status = 'cancelled'
            self.save()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paid_at = models.DateTimeField(null=True, blank=True)

    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def get_total_cost(self):
        total = sum(item.get_cost() for item in self.items.all())
        if self.discount:
            total -= self.discount
        return total

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity





class CouponUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'coupon')