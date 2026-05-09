from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def merchant_required(view_func):
    """
    装饰器：验证用户是否为已审核通过的商家
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, '请先登录')
            return redirect('merchant:login')

        if not hasattr(request.user, 'merchant'):
            messages.error(request, '您不是商家')
            return redirect('merchant:login')

        if not request.user.merchant.is_approved:
            messages.error(request, '您的商家账号尚未审核通过，请耐心等待')
            return redirect('merchant:pending')

        return view_func(request, *args, **kwargs)
    return wrapper
