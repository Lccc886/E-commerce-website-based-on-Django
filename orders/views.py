from decimal import Decimal
import json
import uuid
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from goods.models import Product, ProductSKU
from users.models import Address
from .models import Order, OrderItem, Coupon, CouponUsage, Payment
from points.views import award_purchase_points


def _parse_cart_key(cart_key):
    """解析购物车key，返回(product_id, sku_id)"""
    parts = cart_key.split('_')
    product_id = int(parts[0])
    sku_id = int(parts[1]) if len(parts) > 1 else None
    return product_id, sku_id


def _build_cart_items(cart):
    """从 session cart 构建购物车商品列表和总价，批量查询避免 N+1。"""
    if not cart:
        return [], Decimal('0')

    # 收集所有商品ID和SKU ID
    product_ids = set()
    sku_ids = set()
    for cart_key in cart.keys():
        product_id, sku_id = _parse_cart_key(cart_key)
        product_ids.add(product_id)
        if sku_id:
            sku_ids.add(sku_id)

    # 批量查询商品和SKU
    products = {
        p.id: p
        for p in Product.objects.filter(id__in=product_ids, available=True)
    }
    skus = {
        s.id: s
        for s in ProductSKU.objects.filter(id__in=sku_ids)
    }

    cart_items = []
    total_price = Decimal('0')
    for cart_key, quantity in cart.items():
        product_id, sku_id = _parse_cart_key(cart_key)
        product = products.get(product_id)
        if not product:
            continue
        sku = skus.get(sku_id) if sku_id else None
        quantity = int(quantity)

        # 确定价格
        if sku:
            price = sku.price
        else:
            price = product.price

        subtotal = price * quantity
        total_price += subtotal
        cart_items.append({
            'product': product,
            'sku': sku,
            'quantity': quantity,
            'price': price,
            'subtotal': subtotal,
            'cart_key': cart_key,
        })
    return cart_items, total_price


def _apply_coupon(coupon_code, total_price, user):
    """验证并计算优惠券折扣，返回 (coupon, discount, error_message)。"""
    if not coupon_code:
        return None, Decimal('0'), None

    try:
        now = timezone.now()
        coupon = Coupon.objects.get(
            code=coupon_code,
            valid_from__lte=now,
            valid_to__gte=now,
            active=True,
        )
    except Coupon.DoesNotExist:
        return None, Decimal('0'), '优惠券无效或已过期'

    used_count = CouponUsage.objects.filter(coupon=coupon).count()
    if used_count >= coupon.usage_limit:
        return None, Decimal('0'), '优惠券已达到使用次数上限'

    if total_price < coupon.min_order_amount:
        return None, Decimal('0'), f'订单金额未达到优惠券使用门槛（最低¥{coupon.min_order_amount}）'

    if coupon.discount_type == 'fixed':
        discount = coupon.discount_value
    elif coupon.discount_type == 'percent':
        discount = total_price * (coupon.discount_value / Decimal('100'))
    else:
        discount = Decimal('0')

    discount = min(discount, total_price)
    return coupon, discount, None


@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, '您的购物车是空的，无法结算。')
        return redirect('cart:cart_detail')

    cart_items, total_price = _build_cart_items(cart)
    if not cart_items:
        messages.error(request, '购物车中没有有效商品。')
        return redirect('cart:cart_detail')

    # 优惠券处理
    coupon_code = request.POST.get('coupon_code') or request.GET.get('coupon_code')
    coupon, discount, coupon_error = _apply_coupon(coupon_code, total_price, request.user)
    if coupon_error:
        messages.error(request, coupon_error)
    final_total = total_price - discount

    addresses = request.user.addresses.all()

    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        if address_id:
            address = get_object_or_404(Address, id=address_id, user=request.user)
            first_name = address.full_name.split()[0] if ' ' in address.full_name else address.full_name
            last_name = address.full_name.split()[-1] if ' ' in address.full_name else ''
            email = request.user.email
            address_line = f"{address.province}{address.city}{address.district} {address.address_line}"
            postal_code = getattr(address, 'postal_code', '')
            city = address.city
        else:
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            email = request.POST.get('email', '')
            province_code = request.POST.get('province', '')
            city_code = request.POST.get('city', '')
            phone = request.POST.get('phone', '')
            district_code = request.POST.get('district', '')
            address_line = request.POST.get('address_line', '')
            postal_code = request.POST.get('postal_code', '')

            # 将省市区代码转换为名称（前端使用的是代码）
            province_name = request.POST.get('province_name', province_code)
            city_name = request.POST.get('city_name', city_code)
            district_name = request.POST.get('district_name', district_code)

            full_address = f"{province_name}{city_name}{district_name} {address_line}" if province_name and city_name and district_name else address_line
            if request.user.is_authenticated and province_name and city_name and address_line:
                Address.objects.create(
                    user=request.user,
                    full_name=f"{first_name} {last_name}".strip(),
                    phone=phone,
                    province=province_name,
                    city=city_name,
                    district=district_name,
                    address_line=address_line,
                    postal_code=postal_code,
                    is_default=False,
                )
            address_line = full_address
            city = city_name

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    address=address_line,
                    postal_code=postal_code,
                    city=city,
                    total_amount=final_total,
                    coupon=coupon,
                    discount=discount,
                    status='pending',
                )
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item['product'],
                        sku=item.get('sku'),
                        price=item['price'],
                        quantity=item['quantity'],
                        specs_snapshot=item['sku'].specs if item.get('sku') else {},
                    )
                if coupon:
                    CouponUsage.objects.create(
                        user=request.user,
                        coupon=coupon,
                        order=order,
                    )

                request.session['cart'] = {}
                messages.success(request, '订单已创建，请尽快支付。')
                return redirect('users:profile')

        except Exception as e:
            messages.error(request, f'订单创建失败：{str(e)}')

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'discount': discount,
        'coupon': coupon,
        'final_total': final_total,
        'addresses': addresses,
    }
    return render(request, 'orders/checkout.html', context)


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


@require_POST
@login_required
def apply_coupon(request):
    """AJAX 请求：验证优惠券并返回折扣信息"""
    try:
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '无效的请求数据'})

    cart = request.session.get('cart', {})
    cart_items, total_price = _build_cart_items(cart)

    if not cart_items:
        return JsonResponse({'success': False, 'error': '购物车为空'})

    coupon, discount, error = _apply_coupon(coupon_code, total_price, request.user)

    if error:
        return JsonResponse({'success': False, 'error': error})

    return JsonResponse({
        'success': True,
        'coupon_code': coupon.code,
        'discount': str(discount),
        'discount_display': f'-${discount}',
        'final_total': str(total_price - discount),
        'final_total_display': f'${total_price - discount}',
    })


# ==================== 支付相关视图 ====================

@login_required
def payment_create(request, order_id):
    """创建支付订单"""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # 检查订单状态
    if order.status != 'pending':
        messages.error(request, '该订单无法支付')
        return redirect('users:profile')

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'alipay')

        # 检查是否已有支付记录
        if hasattr(order, 'payment'):
            payment = order.payment
            if payment.status == 'pending':
                return redirect('orders:payment_sandbox', payment_id=payment.id)
            elif payment.status == 'success':
                messages.info(request, '该订单已支付')
                return redirect('users:profile')

        # 创建支付记录
        trade_no = f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
        payment = Payment.objects.create(
            order=order,
            payment_method=payment_method,
            trade_no=trade_no,
            total_amount=order.total_amount,
            status='pending',
        )

        return redirect('orders:payment_sandbox', payment_id=payment.id)

    return render(request, 'orders/payment/method_select.html', {'order': order})


@login_required
def payment_sandbox(request, payment_id):
    """沙箱支付页面"""
    payment = get_object_or_404(Payment, id=payment_id, order__user=request.user)

    if payment.status != 'pending':
        return redirect('orders:payment_result', payment_id=payment.id)

    # 计算支付超时时间（30分钟）
    expire_time = payment.created_at.timestamp() + 30 * 60

    context = {
        'payment': payment,
        'order': payment.order,
        'expire_time': int(expire_time),
        'payment_method_display': dict(Payment.PAYMENT_METHOD_CHOICES).get(payment.payment_method),
    }
    return render(request, 'orders/payment/sandbox.html', context)


@login_required
def payment_callback(request, payment_id):
    """模拟支付回调"""
    payment = get_object_or_404(Payment, id=payment_id, order__user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'pay':
            # 模拟支付成功
            payment.mark_as_success()

            # 发放购物积分
            try:
                points = award_purchase_points(request.user, payment.order)
                if points > 0:
                    messages.success(request, f'支付成功！获得{points}积分')
                else:
                    messages.success(request, '支付成功！')
            except Exception:
                messages.success(request, '支付成功！')

            return redirect('orders:payment_result', payment_id=payment.id)

        elif action == 'cancel':
            # 取消支付
            payment.mark_as_cancelled()
            messages.info(request, '支付已取消')
            return redirect('users:profile')

    return redirect('orders:payment_sandbox', payment_id=payment.id)


@login_required
def payment_result(request, payment_id):
    """支付结果页"""
    payment = get_object_or_404(Payment, id=payment_id, order__user=request.user)

    context = {
        'payment': payment,
        'order': payment.order,
        'payment_method_display': dict(Payment.PAYMENT_METHOD_CHOICES).get(payment.payment_method),
        'status_display': dict(Payment.STATUS_CHOICES).get(payment.status),
    }
    return render(request, 'orders/payment/result.html', context)


@login_required
def payment_status(request, payment_id):
    """查询支付状态API"""
    payment = get_object_or_404(Payment, id=payment_id, order__user=request.user)
    return JsonResponse({
        'status': payment.status,
        'paid_at': payment.paid_at.isoformat() if payment.paid_at else None,
    })
