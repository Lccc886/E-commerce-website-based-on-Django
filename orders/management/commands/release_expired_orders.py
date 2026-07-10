from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from orders.models import Order, Payment


class Command(BaseCommand):
    help = '释放超时未支付订单的库存（30分钟过期）'

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(minutes=30)
        # 用 Payment.created_at 判定过期（而非 Order.created）
        expired_payments = Payment.objects.filter(
            status='pending',
            created_at__lt=cutoff,
        ).select_related('order')

        count = 0
        for payment in expired_payments:
            order = payment.order
            if order.status == 'pending':
                try:
                    with transaction.atomic():
                        payment.mark_as_cancelled()
                        order.cancel()
                    count += 1
                except Exception as e:
                    self.stderr.write(f'释放订单 #{order.id} 失败: {e}')

        self.stdout.write(f'已释放 {count} 个超时订单的库存')
