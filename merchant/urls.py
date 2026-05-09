from django.urls import path
from . import views

app_name = 'merchant'

urlpatterns = [
    # 认证相关
    path('register/', views.merchant_register, name='register'),
    path('login/', views.merchant_login, name='login'),
    path('logout/', views.merchant_logout, name='logout'),
    path('pending/', views.pending, name='pending'),

    # 仪表盘
    path('', views.dashboard, name='dashboard'),

    # 商品管理
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/<int:product_id>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:product_id>/delete/', views.product_delete, name='product_delete'),

    # 订单管理
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/ship/', views.order_ship, name='order_ship'),

    # 统计
    path('statistics/', views.statistics, name='statistics'),

    # 设置
    path('settings/', views.settings_view, name='settings'),
]
