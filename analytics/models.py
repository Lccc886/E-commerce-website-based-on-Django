from django.db import models


class DailyStatistics(models.Model):
    """每日统计汇总"""
    date = models.DateField(unique=True, verbose_name="日期")

    # 订单统计
    order_count = models.PositiveIntegerField(default=0, verbose_name="订单数")
    order_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="订单金额")

    # 用户统计
    new_users = models.PositiveIntegerField(default=0, verbose_name="新增用户")
    active_users = models.PositiveIntegerField(default=0, verbose_name="活跃用户")

    # 商品统计
    product_views = models.PositiveIntegerField(default=0, verbose_name="商品浏览量")

    # 支付统计
    paid_orders = models.PositiveIntegerField(default=0, verbose_name="支付订单数")
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="支付金额")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "每日统计"
        verbose_name_plural = "每日统计"
        ordering = ['-date']

    def __str__(self):
        return str(self.date)
