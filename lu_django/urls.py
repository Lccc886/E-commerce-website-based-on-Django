"""
URL configuration for lu_django project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('goods/', include('goods.urls',namespace='goods')),
    path('cart/', include('cart.urls',namespace='cart')),
    path('accounts/', include('django.contrib.auth.urls')),  # 内置认证视图
    path('users/', include('users.urls',namespace='users')),  # 自定义用户相关视图（如注册、个人中心）
    path('orders/', include('orders.urls',namespace='orders')),
    path('merchant/', include('merchant.urls', namespace='merchant')),  # 商家后台
    path('points/', include('points.urls', namespace='points')),  # 积分系统
    path('analytics/', include('analytics.urls', namespace='analytics')),  # 数据可视化
]

# 开发环境下提供媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
