from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from decimal import Decimal

from .models import (
    PointsAccount, PointsRecord, CheckInRecord,
    PointsExchange, PointsExchangeOrder
)
from orders.models import Order


def get_or_create_account(user):
    """获取或创建用户积分账户"""
    account, created = PointsAccount.objects.get_or_create(user=user)
    return account


@login_required
def points_overview(request):
    """积分概览"""
    account = get_or_create_account(request.user)

    # 检查今日是否已签到
    today = timezone.now().date()
    today_checkin = CheckInRecord.objects.filter(
        user=request.user,
        checkin_date=today
    ).first()

    # 获取最近签到记录
    last_checkin = CheckInRecord.objects.filter(
        user=request.user
    ).order_by('-checkin_date').first()

    # 计算连续签到天数
    continuous_days = 0
    if last_checkin:
        continuous_days = last_checkin.continuous_days
        if today_checkin:
            continuous_days = today_checkin.continuous_days

    # 可兑换商品
    exchange_items = PointsExchange.objects.filter(
        is_active=True,
        stock__gt=0
    ).order_by('-points_required')[:6]

    context = {
        'account': account,
        'today_checkin': today_checkin,
        'continuous_days': continuous_days,
        'exchange_items': exchange_items,
    }
    return render(request, 'points/overview.html', context)


@login_required
def points_history(request):
    """积分历史"""
    account = get_or_create_account(request.user)
    records = account.records.all()[:50]

    context = {
        'account': account,
        'records': records,
    }
    return render(request, 'points/history.html', context)


@login_required
@require_POST
def checkin(request):
    """签到"""
    today = timezone.now().date()

    # 检查今日是否已签到
    if CheckInRecord.objects.filter(user=request.user, checkin_date=today).exists():
        return JsonResponse({
            'success': False,
            'message': '今日已签到'
        })

    # 获取上次签到记录
    last_checkin = CheckInRecord.objects.filter(
        user=request.user
    ).order_by('-checkin_date').first()

    # 计算连续签到天数
    continuous_days = 1
    if last_checkin:
        yesterday = today - timezone.timedelta(days=1)
        if last_checkin.checkin_date == yesterday:
            continuous_days = last_checkin.continuous_days + 1

    # 计算签到积分（基础10分 + 连续签到奖励）
    base_points = 10
    bonus_points = 0

    # 连续签到奖励
    if continuous_days >= 30:
        bonus_points = 50
    elif continuous_days >= 14:
        bonus_points = 30
    elif continuous_days >= 7:
        bonus_points = 20

    total_points = base_points + bonus_points

    # 创建签到记录
    CheckInRecord.objects.create(
        user=request.user,
        checkin_date=today,
        continuous_days=continuous_days,
        points_earned=total_points,
    )

    # 增加积分
    account = get_or_create_account(request.user)
    description = f"签到获得{total_points}积分"
    if bonus_points > 0:
        description += f"（连续签到{continuous_days}天奖励{bonus_points}积分）"
    account.add_points(total_points, 'checkin', description)

    return JsonResponse({
        'success': True,
        'message': f'签到成功！获得{total_points}积分',
        'points': total_points,
        'continuous_days': continuous_days,
        'balance': account.balance,
    })


@login_required
def exchange_list(request):
    """积分兑换商城"""
    items = PointsExchange.objects.filter(
        is_active=True,
        stock__gt=0
    ).order_by('-points_required')

    account = get_or_create_account(request.user)

    context = {
        'items': items,
        'account': account,
    }
    return render(request, 'points/exchange.html', context)


@login_required
def exchange_item(request, item_id):
    """兑换商品"""
    item = get_object_or_404(PointsExchange, id=item_id, is_active=True)
    account = get_or_create_account(request.user)

    if request.method == 'POST':
        # 检查库存
        if item.stock <= 0:
            messages.error(request, '商品库存不足')
            return redirect('points:exchange_list')

        # 检查积分
        if account.balance < item.points_required:
            messages.error(request, '积分不足')
            return redirect('points:exchange_list')

        # 获取收货地址
        address = request.POST.get('address', '')
        phone = request.POST.get('phone', '')

        # 使用积分
        if account.use_points(item.points_required, 'exchange', f'兑换{item.name}'):
            # 创建兑换订单
            PointsExchangeOrder.objects.create(
                user=request.user,
                exchange_item=item,
                points_used=item.points_required,
                address=address,
                phone=phone,
            )

            # 扣减库存
            item.stock -= 1
            item.save()

            messages.success(request, f'兑换成功！消耗{item.points_required}积分')
            return redirect('points:points_overview')
        else:
            messages.error(request, '积分不足')
            return redirect('points:exchange_list')

    context = {
        'item': item,
        'account': account,
    }
    return render(request, 'points/exchange_item.html', context)


def award_purchase_points(user, order):
    """购物发放积分（供订单模块调用）"""
    from django.conf import settings

    # 获取积分配置
    points_config = getattr(settings, 'POINTS_CONFIG', {})
    rate = points_config.get('PURCHASE_RATE', 1)  # 默认每元1积分

    # 计算积分（按订单实际支付金额）
    amount = order.total_amount
    points = int(amount * Decimal(str(rate)))

    if points > 0:
        account = get_or_create_account(user)
        account.add_points(
            points,
            'purchase',
            f'订单#{order.id}购物获得{points}积分',
            related_order=order
        )

    return points
