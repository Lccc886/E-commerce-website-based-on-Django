from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from .models import Merchant
from .forms import MerchantRegisterForm, MerchantSettingsForm, ProductForm
from .decorators import merchant_required
from goods.models import Product, Category
from orders.models import Order, OrderItem


def merchant_register(request):
    """商家注册"""
    if request.method == 'POST':
        form = MerchantRegisterForm(request.POST)
        if form.is_valid():
            from django.contrib.auth.models import User
            # 创建用户
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            # 创建商家
            Merchant.objects.create(
                user=user,
                shop_name=form.cleaned_data['shop_name'],
                contact_phone=form.cleaned_data['contact_phone'],
                contact_email=form.cleaned_data['contact_email'],
                address=form.cleaned_data.get('address', ''),
                description=form.cleaned_data.get('description', ''),
                status='pending'
            )
            messages.success(request, '注册成功！请等待管理员审核。')
            return redirect('merchant:login')
    else:
        form = MerchantRegisterForm()
    return render(request, 'merchant/register.html', {'form': form})


def merchant_login(request):
    """商家登录"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # 检查是否是商家（try/except 代替 hasattr：Django 反向关联
            # 在记录不存在时会抛异常，hasattr 无法正确判断）
            try:
                merchant = user.merchant
            except Exception:
                merchant = None
            if merchant is not None:
                if merchant.status == 'approved':
                    login(request, user)
                    return redirect('merchant:dashboard')
                elif merchant.status == 'pending':
                    messages.warning(request, '您的商家账号正在审核中，请耐心等待。')
                else:
                    messages.error(request, f'您的商家账号审核未通过。原因：{merchant.reject_reason or "无"}')
            else:
                messages.error(request, '该账号不是商家账号。')
        else:
            messages.error(request, '用户名或密码错误。')

    return render(request, 'merchant/login.html')


def merchant_logout(request):
    """商家退出"""
    logout(request)
    messages.success(request, '已退出登录')
    return redirect('merchant:login')


@merchant_required
def dashboard(request):
    """商家仪表盘"""
    merchant = request.user.merchant
    merchant.update_statistics()

    # 获取商家商品
    products = Product.objects.filter(merchant=merchant)
    product_ids = products.values_list('id', flat=True)

    # 近30天订单
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_order_items = OrderItem.objects.filter(
        product_id__in=product_ids,
        order__created__gte=thirty_days_ago
    )

    # 统计数据
    context = {
        'merchant': merchant,
        'product_count': products.count(),
        'pending_review_count': products.filter(review_status='pending').count(),
        'approved_count': products.filter(review_status='approved').count(),
        'rejected_count': products.filter(review_status='rejected').count(),
    }
    return render(request, 'merchant/dashboard.html', context)


@merchant_required
def product_list(request):
    """商家商品列表"""
    merchant = request.user.merchant
    products = Product.objects.filter(merchant=merchant).order_by('-created_at')

    # 按审核状态筛选
    status_filter = request.GET.get('status')
    if status_filter:
        products = products.filter(review_status=status_filter)

    context = {
        'products': products,
        'status_filter': status_filter,
    }
    return render(request, 'merchant/products/list.html', context)


@merchant_required
def product_add(request):
    """添加商品"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = Product.objects.create(
                name=form.cleaned_data['name'],
                slug=form.cleaned_data['slug'],
                category_id=form.cleaned_data['category'],
                description=form.cleaned_data['description'],
                price=form.cleaned_data['price'],
                image=form.cleaned_data.get('image'),
                stock=form.cleaned_data['stock'],
                is_new=form.cleaned_data.get('is_new', False),
                merchant=request.user.merchant,
                review_status='pending',  # 新商品默认待审核
                available=False,  # 审核通过后才上架
            )
            messages.success(request, '商品添加成功，等待管理员审核。')
            return redirect('merchant:product_list')
    else:
        form = ProductForm()

    return render(request, 'merchant/products/form.html', {'form': form, 'title': '添加商品'})


@merchant_required
def product_edit(request, product_id):
    """编辑商品"""
    product = get_object_or_404(Product, id=product_id, merchant=request.user.merchant)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product.name = form.cleaned_data['name']
            product.slug = form.cleaned_data['slug']
            product.category_id = form.cleaned_data['category']
            product.description = form.cleaned_data['description']
            product.price = form.cleaned_data['price']
            if form.cleaned_data.get('image'):
                product.image = form.cleaned_data['image']
            product.stock = form.cleaned_data['stock']
            product.is_new = form.cleaned_data.get('is_new', False)
            product.review_status = 'pending'  # 编辑后重新审核
            product.available = False
            product.save()
            messages.success(request, '商品已更新，等待管理员重新审核。')
            return redirect('merchant:product_list')
    else:
        form = ProductForm(initial={
            'name': product.name,
            'slug': product.slug,
            'category': product.category_id,
            'description': product.description,
            'price': product.price,
            'stock': product.stock,
            'is_new': product.is_new,
        })

    return render(request, 'merchant/products/form.html', {
        'form': form,
        'product': product,
        'title': '编辑商品'
    })


@merchant_required
def product_delete(request, product_id):
    """删除商品"""
    product = get_object_or_404(Product, id=product_id, merchant=request.user.merchant)

    if request.method == 'POST':
        product.delete()
        messages.success(request, '商品已删除')
        return redirect('merchant:product_list')

    return render(request, 'merchant/products/delete.html', {'product': product})


@merchant_required
def order_list(request):
    """商家订单列表"""
    merchant = request.user.merchant
    product_ids = Product.objects.filter(merchant=merchant).values_list('id', flat=True)

    # 获取包含商家商品的订单
    orders = Order.objects.filter(
        items__product_id__in=product_ids
    ).distinct().order_by('-created')

    # 按状态筛选
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)

    # 为每个订单添加商家相关的订单项
    for order in orders:
        order.merchant_items = order.items.filter(product_id__in=product_ids)

    context = {
        'orders': orders,
        'status_filter': status_filter,
    }
    return render(request, 'merchant/orders/list.html', context)


@merchant_required
def order_detail(request, order_id):
    """订单详情"""
    merchant = request.user.merchant
    order = get_object_or_404(Order, id=order_id)
    product_ids = Product.objects.filter(merchant=merchant).values_list('id', flat=True)

    # 只显示商家的订单项
    merchant_items = order.items.filter(product_id__in=product_ids)

    context = {
        'order': order,
        'merchant_items': merchant_items,
    }
    return render(request, 'merchant/orders/detail.html', context)


@merchant_required
def order_ship(request, order_id):
    """发货"""
    merchant = request.user.merchant
    order = get_object_or_404(Order, id=order_id)

    product_ids = Product.objects.filter(merchant=merchant).values_list('id', flat=True)
    merchant_items = order.items.filter(product_id__in=product_ids)

    if request.method == 'POST':
        tracking_number = request.POST.get('tracking_number', '')
        # 这里可以记录发货信息，简化处理直接标记订单发货
        # 实际应该按商家分别发货，这里简化为订单整体发货
        order.mark_as_shipped()
        messages.success(request, '订单已发货')
        return redirect('merchant:order_list')

    return render(request, 'merchant/orders/ship.html', {
        'order': order,
        'merchant_items': merchant_items
    })


@merchant_required
def statistics(request):
    """销售统计"""
    merchant = request.user.merchant
    merchant.update_statistics()

    product_ids = Product.objects.filter(merchant=merchant).values_list('id', flat=True)

    # 时间范围
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)

    # 销售额统计
    order_items = OrderItem.objects.filter(
        product_id__in=product_ids,
        order__created__gte=start_date,
        order__status__in=['paid', 'shipped', 'completed']
    )

    total_sales = sum(item.price * item.quantity for item in order_items)
    total_orders = order_items.values('order').distinct().count()

    # 商品销量排行
    product_sales = {}
    for item in order_items:
        if item.product_id not in product_sales:
            product_sales[item.product_id] = {
                'name': item.product.name,
                'quantity': 0,
                'amount': 0
            }
        product_sales[item.product_id]['quantity'] += item.quantity
        product_sales[item.product_id]['amount'] += item.price * item.quantity

    top_products = sorted(product_sales.values(), key=lambda x: x['quantity'], reverse=True)[:10]

    context = {
        'merchant': merchant,
        'days': days,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'top_products': top_products,
    }
    return render(request, 'merchant/statistics.html', context)


@merchant_required
def settings_view(request):
    """店铺设置"""
    merchant = request.user.merchant

    if request.method == 'POST':
        form = MerchantSettingsForm(request.POST, request.FILES, instance=merchant)
        if form.is_valid():
            form.save()
            messages.success(request, '店铺设置已更新')
            return redirect('merchant:settings')
    else:
        form = MerchantSettingsForm(instance=merchant)

    return render(request, 'merchant/settings.html', {'form': form, 'merchant': merchant})


def pending(request):
    """审核等待页面"""
    if not request.user.is_authenticated:
        return redirect('merchant:login')

    # try/except 代替 hasattr：Django 反向 OneToOne 在记录不存在时抛异常
    try:
        merchant = request.user.merchant
    except Exception:
        return redirect('merchant:register')

    if merchant.status == 'approved':
        return redirect('merchant:dashboard')

    return render(request, 'merchant/pending.html', {'merchant': merchant})
