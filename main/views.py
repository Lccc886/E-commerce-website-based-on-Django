from django.shortcuts import render
from goods.models import Product
from main.models import CarouselImage


def index(request):
    products = Product.objects.filter(available=True).select_related('category')[:4]
    carousel_list = CarouselImage.objects.filter(is_active=True).select_related('product').order_by('order')
    return render(request, 'main/index.html', {'products': products, 'carousel_list': carousel_list})