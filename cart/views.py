from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from goods.models import Product
from django.views.decorators.http import require_POST
from django.http import JsonResponse

def index(request):
    """
    购物车应用的首页视图，重定向到购物车详情页面。
    """
    return redirect('cart:cart_detail')


def get_cart(request):
    """
    获取购物车数据的辅助函数。
    返回购物车字典和商品总数、总价等信息。
    """
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    total_items = 0

    for product_id, quantity in cart.items():
        product = Product.objects.filter(id=product_id, available=True).first()
        if product:
            subtotal = product.price * quantity
            total_price += subtotal
            total_items += quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal,
            })

    return {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
        'total_items': total_items,
    }
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

    # 计算购物车总数量
    total_items = sum(cart.values())

    # 判断是否为 AJAX 请求
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': f'{product.name} 已加入购物车', 'cart_total': total_items})
    else:
        messages.success(request, f'{product.name} 已加入购物车')
        next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
        return redirect(next_url)


def cart_detail(request):
    cart = request.session.get('cart', {})
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
        else:
            # 如果商品已下架或不存在，从购物车中移除
            del cart[product_id]
            request.session.modified = True

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'cart/detail.html', context)


def cart_update(request, product_id):
    """更新购物车中商品的数量（增删改）"""
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 0))
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)

        if quantity > 0:
            cart[product_id_str] = quantity
        else:
            # 如果数量为0或负数，则移除该商品
            cart.pop(product_id_str, None)

        request.session['cart'] = cart
        return  redirect('cart:cart_detail')
    return  redirect('cart:cart_detail')


def cart_remove(request, product_id):
    """从购物车中移除指定商品"""
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        cart.pop(str(product_id), None)
        request.session['cart'] = cart
    return  redirect('cart:cart_detail')