from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Category, Product
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Product, Wishlist,Review
from orders.models import OrderItem


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    # 搜索处理
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # 分页（可选）
    paginator = Paginator(products, 12)  # 每页12个商品
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'categories': categories,
        'page_obj': page_obj,
        'query': query,  # 保留搜索关键词以便模板中回填
    }
    return render(request, 'goods/product_list.html', context)

def product_detail(request, slug):
    """商品详情页"""
    product = get_object_or_404(Product, slug=slug, available=True)
    user_has_purchased = False
    if request.user.is_authenticated:
        user_has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            order__paid=True,
            product=product
        ).exists()
    context = {
        'product': product,
        'user_has_purchased': user_has_purchased,
    }
    return render(request, 'goods/product_detail.html', context)


@login_required
def wishlist_add(request, product_id):
    """添加商品到心愿单"""
    product = get_object_or_404(Product, id=product_id, available=True)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if created:
        messages.success(request, f'{product.name} 已添加到心愿单')
    else:
        messages.info(request, f'{product.name} 已在心愿单中')
    # 返回上一页
    return redirect(request.META.get('HTTP_REFERER', 'main:index'))

@login_required
def wishlist_remove(request, product_id):
    """从心愿单移除商品"""
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    messages.success(request, f'{product.name} 已从心愿单移除')
    return redirect(request.META.get('HTTP_REFERER', 'main:index'))

@login_required
def wishlist_detail(request):
    """心愿单详情页"""
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'goods/wishlist.html', {'wishlist_items': wishlist_items})


@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    # 检查用户是否购买过该商品（订单中已支付且包含该商品）
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        order__paid=True,
        product=product
    ).exists()
    if not has_purchased:
        messages.error(request, "只有购买过该商品的用户才能评价。")
        return redirect('goods:product_detail', slug=product.slug)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        if rating and comment:
            # 检查是否已评价过
            review, created = Review.objects.get_or_create(
                user=request.user,
                product=product,
                defaults={'rating': rating, 'comment': comment}
            )
            if not created:
                # 更新已有评价
                review.rating = rating
                review.comment = comment
                review.save()
                messages.success(request, "评价已更新。")
            else:
                messages.success(request, "评价已提交。")
        else:
            messages.error(request, "请填写评分和评论。")
        return redirect('goods:product_detail', slug=product.slug)
    return redirect('goods:product_detail', slug=product.slug)