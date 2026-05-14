from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),

    # 支付相关
    path('payment/create/<int:order_id>/', views.payment_create, name='payment_create'),
    path('payment/sandbox/<int:payment_id>/', views.payment_sandbox, name='payment_sandbox'),
    path('payment/callback/<int:payment_id>/', views.payment_callback, name='payment_callback'),
    path('payment/result/<int:payment_id>/', views.payment_result, name='payment_result'),
    path('payment/status/<int:payment_id>/', views.payment_status, name='payment_status'),
]