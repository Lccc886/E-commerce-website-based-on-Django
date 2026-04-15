# orders/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Order, OrderItem, Coupon, CouponUsage  # 假设优惠券模型已定义
from goods.models import Product
from cart.context_processors import cart_total
from users.models import Address

@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, '您的购物车是空的，无法结算。')
        return redirect('cart:detail')

    # 获取购物车商品详情并计算总价
    cart_items = []
    total_price = 0
    for product_id, quantity in cart.items():
        product = Product.objects.filter(id=product_id, available=True).first()
        if product:
            subtotal = product.price * quantity
            total_price += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal,
            })

    # --- 优惠券处理 ---
    coupon = None
    discount = 0
    coupon_code = request.POST.get('coupon_code') or request.GET.get('coupon_code')  # 从表单或URL参数获取

    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, valid_from__lte=timezone.now(), valid_to__gte=timezone.now(), active=True)
            # 检查使用次数限制
            used_count = CouponUsage.objects.filter(coupon=coupon).count()
            if used_count >= coupon.usage_limit:
                messages.error(request, '优惠券已达到使用次数上限')
                coupon = None
            else:
                # 检查最低金额
                if total_price < coupon.minimum_amount:
                    messages.error(request, f'订单金额未达到优惠券使用门槛（最低¥{coupon.minimum_amount}）')
                    coupon = None
                else:
                    # 计算折扣
                    if coupon.discount_type == 'fixed':
                        discount = coupon.discount_value
                    elif coupon.discount_type == 'percent':
                        discount = total_price * (coupon.discount_value / 100)
                    # 确保折扣不超过订单金额
                    discount = min(discount, total_price)
        except Coupon.DoesNotExist:
            messages.error(request, '优惠券无效或已过期')

    final_total = total_price - discount
    # --- 优惠券处理结束 ---

    addresses = request.user.addresses.all()
    total_price = 0
    cart_items = []
    for product_id, quantity in cart.items():
        product = Product.objects.filter(id=product_id, available=True).first()
        if product:
            subtotal = product.price * quantity
            total_price += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal,
            })
    default_address = addresses.filter(is_default=True).first()  # 获取默认地址

    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        if address_id:
            address = get_object_or_404(Address, id=address_id, user=request.user)
            # 从 address 中提取字段
            first_name = address.full_name.split()[0] if ' ' in address.full_name else address.full_name
            last_name = address.full_name.split()[-1] if ' ' in address.full_name else ''
            email = request.user.email
            address_line = f"{address.province}{address.city}{address.district} {address.address_line}"
            postal_code = address.postal_code
            city = address.city
        else:
            # 新建地址
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            province = request.POST.get('province')
            city = request.POST.get('city')
            phone = request.POST.get('phone')
            district = request.POST.get('district')
            address_line = request.POST.get('address')
            postal_code = request.POST.get('postal_code')

            # 组合完整地址用于订单存储
            full_address = f"{province}{city}{district} {address_line}" if province and city and district else address_line
            # 可选：保存新地址到用户地址列表
            if request.user.is_authenticated and province and city and address_line:
                Address.objects.create(
                    user=request.user,
                    full_name=f"{first_name} {last_name}".strip(),
                    phone=request.POST.get('phone', ''),
                    province=province,
                    city=city,
                    district=district,
                    address_line=address_line,
                    postal_code=postal_code,
                    is_default=False
                )
            # 将 full_address 赋值给 address_line 用于订单
            address_line = full_address

        # 可选：重新获取优惠券（因为可能从表单提交）
        # 优惠券已在上面处理，直接使用 coupon 对象

        try:
            with transaction.atomic():
                # 扣减库存（略，需实现库存管理逻辑）
                # 应用优惠券（略）
                # 创建订单
                order = Order.objects.create(
                    user=request.user,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,  # 确保 Order 模型有 phone 字段，否则需添加
                    address=address_line,
                    postal_code=postal_code,
                    city=city,
                    status='pending'  # 待支付
                )
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item['product'],
                        price=item['product'].price,
                        quantity=item['quantity']
                    )

                # 清空购物车
                request.session['cart'] = {}
                messages.success(request, '订单已创建，请尽快支付。')
                return redirect('users:profile')



        except Exception as e:
            messages.error(request, f'订单创建失败：{str(e)}')
            # 事务回滚，库存自动恢复
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'addresses': addresses,
    }
    return render(request, 'orders/checkout.html', context)

    # GET 请求：显示表单，并传递购物车信息、总价、优惠券信息等
    cart_items = []
    total_price = 0
    for product_id, quantity in cart.items():
        product = Product.objects.filter(id=product_id, available=True).first()
        if product:
            subtotal = product.price * quantity
            total_price += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal,
            })

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'addresses': addresses,
        'default_address': default_address,  # 传递默认地址
    }
    return render(request, 'orders/checkout.html', context)