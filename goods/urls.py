from django.urls import path
from . import views

app_name = 'goods'

urlpatterns = [
    path('wishlist/', views.wishlist_detail, name='wishlist'),
    path('', views.product_list, name='product_list'),
    path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('review/<int:product_id>/', views.add_review, name='add_review'),
    path('<slug:slug>/', views.product_detail, name='product_detail'),

    path('wishlist/add/<int:product_id>/', views.wishlist_add, name='wishlist_add'),
    path('wishlist/remove/<int:product_id>/', views.wishlist_remove, name='wishlist_remove'),
]