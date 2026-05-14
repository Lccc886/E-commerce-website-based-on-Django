import json
import random
import string

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm, AuthenticationForm
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.http import JsonResponse

from orders.models import Order
from .models import Profile, Address
from .forms import UserProfileForm, ProfileForm, AddressForm, RegisterForm


def generate_code():
    return ''.join(random.choices(string.digits, k=6))


def user_login(request):
    """用户登录"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('main:index')
        else:
            messages.error(request, '用户名或密码错误')

    form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def user_logout(request):
    """用户退出登录"""
    logout(request)
    messages.success(request, '已成功退出登录')
    return redirect('main:index')


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('main:index')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def send_verification_code(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            if not email:
                return JsonResponse(
                    {'status': 'error', 'message': '邮箱不能为空'}, status=400
                )
            code = generate_code()
            cache.set(f'verification_code_{email}', code, timeout=300)

            email_msg = EmailMessage(
                'LUMINA 注册验证码',
                f'您的验证码是：{code}，5分钟内有效。',
                to=[email],
            )
            email_msg.encoding = 'utf-8'
            email_msg.send(fail_silently=False)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse(
                {'status': 'error', 'message': str(e)}, status=500
            )
    return JsonResponse({'status': 'error', 'message': '无效请求'}, status=400)


@login_required
def profile(request):
    profile, _created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user_form = UserProfileForm(request.POST, instance=request.user)
            profile_form = ProfileForm(
                request.POST, request.FILES, instance=profile
            )
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, '个人资料已更新')
                return redirect('users:profile')
            messages.error(request, '请检查表单错误')

        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, '密码已修改')
                return redirect('users:profile')
            messages.error(request, '密码修改失败，请检查')

        elif 'add_address' in request.POST:
            address_form = AddressForm(request.POST)
            if address_form.is_valid():
                address = address_form.save(commit=False)
                address.user = request.user
                if address.is_default:
                    Address.objects.filter(
                        user=request.user, is_default=True
                    ).update(is_default=False)
                address.save()
                messages.success(request, '地址添加成功')
                return redirect('users:profile')
            messages.error(request, '地址添加失败')

        elif 'delete_address' in request.POST:
            address_id = request.POST.get('address_id')
            if address_id:
                address = get_object_or_404(
                    Address, id=address_id, user=request.user
                )
                address.delete()
                messages.success(request, '地址已删除')
                return redirect('users:profile')
    else:
        user_form = UserProfileForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)
        password_form = PasswordChangeForm(request.user)
        address_form = AddressForm()

    return render(request, 'users/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': password_form,
        'address_form': address_form,
        'addresses': Address.objects.filter(user=request.user),
        'profile': profile,
        'orders': Order.objects.filter(user=request.user).order_by('-created'),
    })


@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            address = form.save(commit=False)
            if address.is_default:
                Address.objects.filter(
                    user=request.user, is_default=True
                ).exclude(id=address.id).update(is_default=False)
            address.save()
            messages.success(request, '地址已更新')
            return redirect('users:profile')
        messages.error(request, '地址更新失败')
    else:
        form = AddressForm(instance=address)
    return render(request, 'users/edit_address.html', {
        'form': form, 'address': address,
    })


@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, '地址已删除')
        return redirect('users:profile')
    return render(request, 'users/delete_address.html', {'address': address})


@login_required
def address_list(request):
    return render(request, 'users/address_list.html', {
        'addresses': Address.objects.filter(user=request.user),
    })


@login_required
def address_add(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if address.is_default:
                Address.objects.filter(
                    user=request.user, is_default=True
                ).update(is_default=False)
            address.save()
            messages.success(request, '地址添加成功')
            return redirect('users:address_list')
        messages.error(request, '地址添加失败')
    else:
        form = AddressForm()
    return render(request, 'users/address_form.html', {
        'form': form, 'title': '添加地址',
    })


@login_required
def address_edit(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            address = form.save(commit=False)
            if address.is_default:
                Address.objects.filter(
                    user=request.user, is_default=True
                ).exclude(pk=address.pk).update(is_default=False)
            address.save()
            messages.success(request, '地址已更新')
            return redirect('users:address_list')
        messages.error(request, '地址更新失败')
    else:
        form = AddressForm(instance=address)
    return render(request, 'users/address_form.html', {
        'form': form, 'title': '编辑地址',
    })


@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, '地址已删除')
        return redirect('users:address_list')
    return render(request, 'users/address_confirm_delete.html', {
        'address': address,
    })
