from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/realtime/', views.api_realtime_stats, name='api_realtime_stats'),
    path('api/sales-trend/', views.api_sales_trend, name='api_sales_trend'),
    path('api/top-products/', views.api_top_products, name='api_top_products'),
    path('api/category-distribution/', views.api_category_distribution, name='api_category_distribution'),
    path('api/order-status/', views.api_order_status, name='api_order_status'),
]
