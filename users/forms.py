from .models import Profile, Address
from django import forms
from django.contrib.auth.models import User
from django.core.cache import cache
import re
from django import forms
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full border-gray-300 rounded-md py-2 px-3 focus:ring-black focus:border-black'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full border-gray-300 rounded-md py-2 px-3 focus:ring-black focus:border-black'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border-gray-300 rounded-md py-2 px-3 focus:ring-black focus:border-black'}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'phone', 'birth_date']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'w-full border-gray-300 rounded-md py-2 px-3 focus:ring-black focus:border-black'}),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border-gray-300 rounded-md py-2 px-3 focus:ring-black focus:border-black'}),
        }



class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['full_name', 'phone', 'province', 'city', 'district', 'address_line', 'is_default']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black'}),
            'phone': forms.TextInput(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black'}),
            'province': forms.TextInput(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black'}),
            'city': forms.TextInput(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black'}),
            'district': forms.TextInput(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black'}),
            'address_line': forms.Textarea(attrs={'rows': 3, 'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-black focus:ring-black border-gray-300 rounded'}),
        }

# users/forms.py


class RegisterForm(forms.ModelForm):
    email = forms.EmailField(label='邮箱')
    password = forms.CharField(widget=forms.PasswordInput, label='密码')
    password2 = forms.CharField(widget=forms.PasswordInput, label='确认密码')
    verification_code = forms.CharField(max_length=6, label='验证码')

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    # ========== 用户名验证 ==========
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError('用户名不能为空')
        # 长度限制
        if len(username) < 3:
            raise ValidationError('用户名长度不能少于3个字符')
        if len(username) > 20:
            raise ValidationError('用户名长度不能超过20个字符')
        # 字符限制：字母、数字、下划线、中文（可根据需要调整）
        if not re.match(r'^[\w\u4e00-\u9fa5]+$', username):
            raise ValidationError('用户名只能包含字母、数字、下划线或中文')
        # 唯一性检查（Django 模型已有，但可自定义提示）
        if User.objects.filter(username=username).exists():
            raise ValidationError('用户名已存在')
        return username

    # ========== 邮箱验证 ==========
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError('邮箱不能为空')
        # Django 的 EmailField 已经做了格式校验，但可自定义更严格的格式
        # 唯一性检查
        if User.objects.filter(email=email).exists():
            raise ValidationError('该邮箱已被注册')
        return email

    # ========== 密码验证 ==========
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password:
            raise ValidationError('密码不能为空')
        # 长度限制
        if len(password) < 8:
            raise ValidationError('密码长度不能少于8个字符')
        if len(password) > 20:
            raise ValidationError('密码长度不能超过20个字符')
        # 复杂度：必须包含大写字母、小写字母、数字（可根据需要调整）
        if not re.search(r'[A-Z]', password):
            raise ValidationError('密码必须包含至少一个大写字母')
        if not re.search(r'[a-z]', password):
            raise ValidationError('密码必须包含至少一个小写字母')
        if not re.search(r'\d', password):
            raise ValidationError('密码必须包含至少一个数字')
        # 可选：包含特殊字符
        # if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        #     raise ValidationError('密码必须包含至少一个特殊字符')
        return password

    # ========== 确认密码验证 ==========
    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password and password2 and password != password2:
            raise ValidationError('两次输入的密码不一致')
        return password2

    # ========== 验证码验证 ==========
    def clean_verification_code(self):
        code = self.cleaned_data.get('verification_code')
        email = self.cleaned_data.get('email')
        if not email:
            return code
        cached_code = cache.get(f'verification_code_{email}')
        if not cached_code or cached_code != code:
            raise ValidationError('验证码错误或已过期')
        return code