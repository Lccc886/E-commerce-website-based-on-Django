from decimal import Decimal

from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from goods.models import Product


def _build_cart_data(cart):
    """从 session cart 批量构建购物车数据和清理无效商品ID列表。"""
    cart_items = []
    total_price = Decimal('0')
    total_items = 0
    invalid_ids = []

    if not cart:
        return cart_items, total_price, total_items, invalid_ids

    product_ids = [int(pid) for pid in cart.keys()]
    products = {
        p.id: p
        for p in Product.objects.filter(id__in=product_ids, available=True)
    }

    for product_id_str, quantity in cart.items():
        product = products.get(int(product_id_str))
        if not product:
            invalid_ids.append(product_id_str)
            continue
        quantity = int(quantity)
        subtotal = product.price * quantity
        total_price += subtotal
        total_items += quantity
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })

    return cart_items, total_price, total_items, invalid_ids


def index(request):
    return redirect('cart:cart_detail')


@require_POST
def cart_add(request, product_id):
    quantity = int(request.POST.get('quantity', 1))
    product = get_object_or_404(Product, id=product_id, available=True)

    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    if product_id_str in cart:
        cart[product_id_str] += quantity
    else:
        cart[product_id_str] = quantity
    request.session['cart'] = cart

    total_items = sum(cart.values())

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{product.name} 已加入购物车',
            'cart_total': total_items,
        })
    else:
        messages.success(request, f'{product.name} 已加入购物车')
        next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
        return redirect(next_url)


def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items, total_price, _total_items, invalid_ids = _build_cart_data(cart)

    # 清理无效商品（不在迭代过程中修改字典）
    if invalid_ids:
        for pid in invalid_ids:
            cart.pop(pid, None)
        request.session['cart'] = cart

    return render(request, 'cart/detail.html', {
        'cart_items': cart_items,
        'total_price': total_price,
    })


@require_POST
def cart_update(request, product_id):
    quantity = int(request.POST.get('quantity', 0))
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)

    if quantity > 0:
        cart[product_id_str] = quantity
    else:
        cart.pop(product_id_str, None)

    request.session['cart'] = cart
    return redirect('cart:cart_detail')


@require_POST
def cart_remove(request, product_id):
    cart = request.session.get('cart', {})
    cart.pop(str(product_id), None)
    request.session['cart'] = cart
    return redirect('cart:cart_detail')
