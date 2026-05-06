from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from goods.models import Product
from users.models import Address
from .models import Order, OrderItem, Coupon, CouponUsage


def _build_cart_items(cart):
    """从 session cart 构建购物车商品列表和总价，批量查询避免 N+1。"""
    if not cart:
        return [], Decimal('0')

    product_ids = [int(pid) for pid in cart.keys()]
    products = {
        p.id: p
        for p in Product.objects.filter(id__in=product_ids, available=True)
    }

    cart_items = []
    total_price = Decimal('0')
    for product_id_str, quantity in cart.items():
        product = products.get(int(product_id_str))
        if not product:
            continue
        quantity = int(quantity)
        subtotal = product.price * quantity
        total_price += subtotal
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
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
        return redirect('cart:detail')

    cart_items, total_price = _build_cart_items(cart)
    if not cart_items:
        messages.error(request, '购物车中没有有效商品。')
        return redirect('cart:detail')

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
            province = request.POST.get('province', '')
            city = request.POST.get('city', '')
            phone = request.POST.get('phone', '')
            district = request.POST.get('district', '')
            address_line = request.POST.get('address', '')
            postal_code = request.POST.get('postal_code', '')

            full_address = f"{province}{city}{district} {address_line}" if province and city and district else address_line
            if request.user.is_authenticated and province and city and address_line:
                Address.objects.create(
                    user=request.user,
                    full_name=f"{first_name} {last_name}".strip(),
                    phone=phone,
                    province=province,
                    city=city,
                    district=district,
                    address_line=address_line,
                    postal_code=postal_code,
                    is_default=False,
                )
            address_line = full_address

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
                        price=item['product'].price,
                        quantity=item['quantity'],
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
