from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from orders.models import Order

class Command(BaseCommand):
    help = '释放超时未支付订单的库存'

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(minutes=30)
        expired_orders = Order.objects.filter(status='pending', created__lt=cutoff)
        count = 0
        for order in expired_orders:
            order.cancel()  # cancel 方法会恢复库存并设置状态为 cancelled
            count += 1
        self.stdout.write(f'已释放 {count} 个超时订单的库存')