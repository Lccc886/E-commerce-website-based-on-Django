from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import DailyStatistics
from orders.models import Order, OrderItem
from goods.models import Product, Category
from django.contrib.auth import get_user_model

User = get_user_model()


def dashboard(request):
    """数据可视化大屏"""
    return render(request, 'analytics/dashboard.html')


def api_realtime_stats(request):
    """实时统计数据API"""
    today = timezone.now().date()

    # 今日订单
    today_orders = Order.objects.filter(created__date=today)
    today_order_count = today_orders.count()
    today_order_amount = today_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

    # 今日支付
    today_paid = Order.objects.filter(paid_at__date=today, paid=True)
    today_paid_count = today_paid.count()
    today_paid_amount = today_paid.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

    # 今日新用户
    today_new_users = User.objects.filter(date_joined__date=today).count()

    # 总计数据
    total_orders = Order.objects.count()
    total_amount = Order.objects.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    total_users = User.objects.count()
    total_products = Product.objects.filter(available=True).count()

    return JsonResponse({
        'today': {
            'order_count': today_order_count,
            'order_amount': float(today_order_amount),
            'paid_count': today_paid_count,
            'paid_amount': float(today_paid_amount),
            'new_users': today_new_users,
        },
        'total': {
            'order_count': total_orders,
            'order_amount': float(total_amount),
            'users': total_users,
            'products': total_products,
        }
    })


def api_sales_trend(request):
    """销售趋势API（最近7天）"""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=6)

    # 获取每日统计数据
    daily_stats = DailyStatistics.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')

    # 如果没有统计数据，从订单实时计算
    if not daily_stats.exists():
        dates = []
        order_counts = []
        order_amounts = []
        paid_counts = []
        paid_amounts = []

        current_date = start_date
        while current_date <= end_date:
            day_orders = Order.objects.filter(created__date=current_date)
            day_paid = Order.objects.filter(paid_at__date=current_date, paid=True)

            dates.append(current_date.strftime('%m-%d'))
            order_counts.append(day_orders.count())
            order_amounts.append(float(day_orders.aggregate(total=Sum('total_amount'))['total'] or 0))
            paid_counts.append(day_paid.count())
            paid_amounts.append(float(day_paid.aggregate(total=Sum('total_amount'))['total'] or 0))

            current_date += timedelta(days=1)

        return JsonResponse({
            'dates': dates,
            'order_counts': order_counts,
            'order_amounts': order_amounts,
            'paid_counts': paid_counts,
            'paid_amounts': paid_amounts,
        })

    # 使用统计数据
    stats_data = {stat.date: stat for stat in daily_stats}
    dates = []
    order_counts = []
    order_amounts = []
    paid_counts = []
    paid_amounts = []

    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime('%m-%d'))
        if current_date in stats_data:
            stat = stats_data[current_date]
            order_counts.append(stat.order_count)
            order_amounts.append(float(stat.order_amount))
            paid_counts.append(stat.paid_orders)
            paid_amounts.append(float(stat.paid_amount))
        else:
            order_counts.append(0)
            order_amounts.append(0)
            paid_counts.append(0)
            paid_amounts.append(0)
        current_date += timedelta(days=1)

    return JsonResponse({
        'dates': dates,
        'order_counts': order_counts,
        'order_amounts': order_amounts,
        'paid_counts': paid_counts,
        'paid_amounts': paid_amounts,
    })


def api_top_products(request):
    """热销商品TOP 10"""
    top_products = OrderItem.objects.values(
        'product__id',
        'product__name',
        'product__image'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_sales=Sum('price') * Sum('quantity')
    ).order_by('-total_quantity')[:10]

    products_data = []
    for item in top_products:
        products_data.append({
            'id': item['product__id'],
            'name': item['product__name'][:20] + '...' if len(item['product__name'] or '') > 20 else item['product__name'],
            'image': item['product__image'],
            'quantity': item['total_quantity'],
            'sales': float(item['total_sales'] or 0),
        })

    return JsonResponse({'products': products_data})


def api_category_distribution(request):
    """分类销售分布"""
    category_sales = OrderItem.objects.values(
        'product__category__id',
        'product__category__name'
    ).annotate(
        total_sales=Sum('price') * Sum('quantity')
    ).order_by('-total_sales')

    categories = []
    sales = []
    for item in category_sales:
        if item['product__category__name']:
            categories.append(item['product__category__name'])
            sales.append(float(item['total_sales'] or 0))

    return JsonResponse({
        'categories': categories[:10],
        'sales': sales[:10],
    })


def api_order_status(request):
    """订单状态分布"""
    status_counts = Order.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')

    status_map = {
        'pending': '待支付',
        'paid': '已支付',
        'shipped': '已发货',
        'completed': '已完成',
        'cancelled': '已取消',
    }

    data = []
    for item in status_counts:
        data.append({
            'status': status_map.get(item['status'], item['status']),
            'count': item['count'],
        })

    return JsonResponse({'data': data})
