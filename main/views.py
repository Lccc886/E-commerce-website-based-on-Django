from django.shortcuts import render
from goods.models import Product

def index(request):
    # 获取所有上架的商品，按创建时间倒序排列
    products = Product.objects.filter(available=True).order_by('-created_at')[:4]
    return render(request, 'main/index.html', {'products': products})
