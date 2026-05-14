from decimal import Decimal

from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from goods.models import Product, ProductSKU


def _get_cart_key(product_id, sku_id=None):
    """生成购物车key"""
    if sku_id:
        return f"{product_id}_{sku_id}"
    return str(product_id)


def _parse_cart_key(cart_key):
    """解析购物车key，返回(product_id, sku_id)"""
    parts = cart_key.split('_')
    product_id = int(parts[0])
    sku_id = int(parts[1]) if len(parts) > 1 else None
    return product_id, sku_id


def _build_cart_data(cart):
    """从 session cart 批量构建购物车数据和清理无效商品ID列表。"""
    cart_items = []
    total_price = Decimal('0')
    total_items = 0
    invalid_keys = []

    if not cart:
        return cart_items, total_price, total_items, invalid_keys

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

    for cart_key, quantity in cart.items():
        product_id, sku_id = _parse_cart_key(cart_key)
        product = products.get(product_id)
        if not product:
            invalid_keys.append(cart_key)
            continue

        sku = skus.get(sku_id) if sku_id else None
        quantity = int(quantity)

        # 确定价格：有SKU用SKU价格，否则用商品价格
        if sku:
            price = sku.price
            stock = sku.stock
            specs = sku.specs
        else:
            price = product.price
            stock = product.stock
            specs = {}

        subtotal = price * quantity
        total_price += subtotal
        total_items += quantity
        cart_items.append({
            'cart_key': cart_key,
            'product': product,
            'sku': sku,
            'quantity': quantity,
            'price': price,
            'subtotal': subtotal,
            'specs': specs,
            'stock': stock,
        })

    return cart_items, total_price, total_items, invalid_keys


def index(request):
    return redirect('cart:cart_detail')


@require_POST
def cart_add(request, product_id):
    quantity = int(request.POST.get('quantity', 1))
    sku_id = request.POST.get('sku_id')  # 获取SKU ID

    product = get_object_or_404(Product, id=product_id, available=True)

    # 验证SKU
    sku = None
    if sku_id:
        sku = get_object_or_404(ProductSKU, id=sku_id, product=product)

    # 检查库存
    if sku:
        if sku.stock < quantity:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': '库存不足'}, status=400)
            messages.error(request, '库存不足')
            return redirect('cart:cart_detail')
    else:
        if product.stock < quantity:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': '库存不足'}, status=400)
            messages.error(request, '库存不足')
            return redirect('cart:cart_detail')

    cart = request.session.get('cart', {})
    cart_key = _get_cart_key(product_id, sku_id)

    if cart_key in cart:
        cart[cart_key] += quantity
    else:
        cart[cart_key] = quantity
    request.session['cart'] = cart

    total_items = sum(cart.values())

    # 构建商品名称显示
    item_name = product.name
    if sku:
        specs_str = ', '.join([f"{k}:{v}" for k, v in sku.specs.items()])
        item_name = f"{product.name} ({specs_str})"

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{item_name} 已加入购物车',
            'cart_total': total_items,
        })
    else:
        messages.success(request, f'{item_name} 已加入购物车')
        next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
        return redirect(next_url)


def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items, total_price, _total_items, invalid_keys = _build_cart_data(cart)

    # 清理无效商品
    if invalid_keys:
        for key in invalid_keys:
            cart.pop(key, None)
        request.session['cart'] = cart

    return render(request, 'cart/detail.html', {
        'cart_items': cart_items,
        'total_price': total_price,
    })


@require_POST
def cart_update(request, product_id):
    quantity = int(request.POST.get('quantity', 0))
    sku_id = request.POST.get('sku_id')

    cart = request.session.get('cart', {})
    cart_key = _get_cart_key(product_id, sku_id)

    if quantity > 0:
        cart[cart_key] = quantity
    else:
        cart.pop(cart_key, None)

    request.session['cart'] = cart
    return redirect('cart:cart_detail')


@require_POST
def cart_remove(request, product_id):
    sku_id = request.POST.get('sku_id')
    cart = request.session.get('cart', {})
    cart_key = _get_cart_key(product_id, sku_id)
    cart.pop(cart_key, None)
    request.session['cart'] = cart
    return redirect('cart:cart_detail')
