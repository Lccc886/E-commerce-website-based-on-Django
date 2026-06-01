from django.db import models
from django.conf import settings
from django.utils import timezone


class PointsAccount(models.Model):
    """积分账户"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='points_account',
        verbose_name="用户"
    )
    balance = models.PositiveIntegerField(default=0, verbose_name="积分余额")
    total_earned = models.PositiveIntegerField(default=0, verbose_name="累计获得")
    total_used = models.PositiveIntegerField(default=0, verbose_name="累计使用")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "积分账户"
        verbose_name_plural = "积分账户"

    def __str__(self):
        return f"{self.user.username} - {self.balance}积分"

    def add_points(self, points, record_type, description, related_order=None):
        """增加积分"""
        self.balance += points
        self.total_earned += points
        self.save()

        PointsRecord.objects.create(
            account=self,
            points=points,
            balance_after=self.balance,
            record_type=record_type,
            description=description,
            related_order=related_order,
        )
        return True

    def use_points(self, points, record_type, description, related_order=None):
        """使用积分"""
        if self.balance < points:
            return False

        self.balance -= points
        self.total_used += points
        self.save()

        PointsRecord.objects.create(
            account=self,
            points=-points,  # 使用为负数
            balance_after=self.balance,
            record_type=record_type,
            description=description,
            related_order=related_order,
        )
        return True


class PointsRecord(models.Model):
    """积分记录"""
    TYPE_CHOICES = (
        ('purchase', '购物获得'),
        ('checkin', '签到获得'),
        ('bonus', '奖励获得'),
        ('exchange', '积分兑换'),
        ('expire', '积分过期'),
        ('admin', '管理员调整'),
    )

    account = models.ForeignKey(
        PointsAccount,
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name="账户"
    )
    points = models.IntegerField(verbose_name="积分变动（正数获得，负数使用）")
    balance_after = models.PositiveIntegerField(verbose_name="变动后余额")
    record_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="类型")
    description = models.CharField(max_length=200, verbose_name="描述")
    related_order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="关联订单"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "积分记录"
        verbose_name_plural = "积分记录"
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.points > 0 else ''
        return f"{self.account.user.username} {sign}{self.points}"


class CheckInRecord(models.Model):
    """签到记录"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='checkins',
        verbose_name="用户"
    )
    checkin_date = models.DateField(verbose_name="签到日期")
    continuous_days = models.PositiveIntegerField(default=1, verbose_name="连续签到天数")
    points_earned = models.PositiveIntegerField(verbose_name="获得积分")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "签到记录"
        verbose_name_plural = "签到记录"
        unique_together = ('user', 'checkin_date')
        ordering = ['-checkin_date']

    def __str__(self):
        return f"{self.user.username} - {self.checkin_date}"


class PointsExchange(models.Model):
    """积分兑换商品"""
    name = models.CharField(max_length=100, verbose_name="兑换商品名称")
    image = models.ImageField(
        upload_to='points_exchange/',
        blank=True,
        null=True,
        verbose_name="图片"
    )
    points_required = models.PositiveIntegerField(verbose_name="所需积分")
    stock = models.PositiveIntegerField(default=0, verbose_name="库存")
    description = models.TextField(blank=True, verbose_name="描述")
    is_active = models.BooleanField(default=True, verbose_name="是否上架")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "积分兑换商品"
        verbose_name_plural = "积分兑换商品"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.points_required}积分)"


class PointsExchangeOrder(models.Model):
    """积分兑换订单"""
    STATUS_CHOICES = (
        ('pending', '待处理'),
        ('shipped', '已发货'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exchange_orders',
        verbose_name="用户"
    )
    exchange_item = models.ForeignKey(
        PointsExchange,
        on_delete=models.CASCADE,
        verbose_name="兑换商品"
    )
    points_used = models.PositiveIntegerField(verbose_name="使用积分")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="状态"
    )
    address = models.CharField(max_length=250, blank=True, verbose_name="收货地址")
    phone = models.CharField(max_length=20, blank=True, verbose_name="联系电话")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "积分兑换订单"
        verbose_name_plural = "积分兑换订单"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.exchange_item.name}"
