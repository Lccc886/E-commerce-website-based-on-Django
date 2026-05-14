from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from .models import Category, Product, Wishlist, Review, ProductSKU
from orders.models import OrderItem


def product_list(request, category_slug=None):
    category = None
    products = Product.objects.filter(
        available=True,
        review_status='approved'
    ).select_related('category')

    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'goods/product_list.html', {
        'category': category,
        'page_obj': page_obj,
        'query': query,
        # categories 由 main.context_processors.categories 注入，无需重复查询
    })


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category'),
        slug=slug,
        available=True,
        review_status='approved'
    )
    user_has_purchased = False
    if request.user.is_authenticated:
        user_has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            order__paid=True,
            product=product,
        ).exists()

    # 获取SKU数据
    skus = product.skus.all().order_by('id')
    default_sku = product.get_default_sku()

    # 构建规格数据结构
    specs_data = {}
    for spec in product.specs.all().order_by('sort_order'):
        values = [value.value for value in spec.values.all().order_by('sort_order')]
        specs_data[spec.name] = values

    # 构建SKU映射
    sku_map = {}
    for sku in skus:
        sku_map[sku.id] = {
            'id': sku.id,
            'price': str(sku.price),
            'original_price': str(sku.original_price) if sku.original_price else None,
            'stock': sku.stock,
            'specs': sku.specs,
            'is_default': sku.is_default,
            'image': sku.image.url if sku.image else None,
        }

    return render(request, 'goods/product_detail.html', {
        'product': product,
        'user_has_purchased': user_has_purchased,
        'skus': skus,
        'default_sku': default_sku,
        'specs_data': specs_data,
        'sku_map': sku_map,
    })


def get_sku_info(request, product_id, sku_id):
    """获取SKU信息的API"""
    sku = get_object_or_404(ProductSKU, id=sku_id, product_id=product_id)
    return JsonResponse({
        'id': sku.id,
        'price': str(sku.price),
        'original_price': str(sku.original_price) if sku.original_price else None,
        'stock': sku.stock,
        'specs': sku.specs,
        'image': sku.image.url if sku.image else None,
    })


@login_required
def wishlist_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    _wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user, product=product
    )
    if created:
        messages.success(request, f'{product.name} 已添加到心愿单')
    else:
        messages.info(request, f'{product.name} 已在心愿单中')
    return redirect(request.META.get('HTTP_REFERER', 'main:index'))


@login_required
def wishlist_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    messages.success(request, f'{product.name} 已从心愿单移除')
    return redirect(request.META.get('HTTP_REFERER', 'main:index'))


@login_required
def wishlist_detail(request):
    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related('product__category')
    return render(request, 'goods/wishlist.html', {
        'wishlist_items': wishlist_items,
    })


@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        order__paid=True,
        product=product,
    ).exists()
    if not has_purchased:
        messages.error(request, "只有购买过该商品的用户才能评价。")
        return redirect('goods:product_detail', slug=product.slug)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        if rating and comment:
            review, created = Review.objects.get_or_create(
                user=request.user,
                product=product,
                defaults={'rating': rating, 'comment': comment},
            )
            if not created:
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
