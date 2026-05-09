from django import forms
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError
import re

from .models import Merchant


class MerchantRegisterForm(forms.Form):
    """商家注册表单"""
    # 用户账号信息
    username = forms.CharField(
        max_length=30,
        label='用户名',
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black',
            'placeholder': '请输入用户名'
        })
    )
    email = forms.EmailField(
        label='邮箱',
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black',
            'placeholder': '请输入邮箱'
        })
    )
    password = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black',
            'placeholder': '请输入密码（至少8位）'
        })
    )
    password2 = forms.CharField(
        label='确认密码',
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black',
            'placeholder': '请再次输入密码'
        })
    )

    # 店铺信息
    shop_name = forms.CharField(
        max_length=100,
        label='店铺名称',
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black',
            'placeholder': '请输入店铺名称'
        })
    )
    contact_phone = forms.CharField(
        max_length=20,
        label='联系电话',
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black',
            'placeholder': '请输入联系电话'
        })
    )
    contact_email = forms.EmailField(
        label='联系邮箱',
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black',
            'placeholder': '请输入联系邮箱'
        })
    )
    address = forms.CharField(
        max_length=200,
        required=False,
        label='店铺地址',
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black',
            'placeholder': '请输入店铺地址（选填）'
        })
    )
    description = forms.CharField(
        required=False,
        label='店铺简介',
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black',
            'placeholder': '请输入店铺简介（选填）'
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError('用户名不能为空')
        if len(username) < 3:
            raise ValidationError('用户名长度不能少于3个字符')
        if len(username) > 20:
            raise ValidationError('用户名长度不能超过20个字符')
        if not re.match(r'^[\w一-龥]+$', username):
            raise ValidationError('用户名只能包含字母、数字、下划线或中文')
        if User.objects.filter(username=username).exists():
            raise ValidationError('用户名已存在')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError('邮箱不能为空')
        if User.objects.filter(email=email).exists():
            raise ValidationError('该邮箱已被注册')
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password:
            raise ValidationError('密码不能为空')
        if len(password) < 8:
            raise ValidationError('密码长度不能少于8个字符')
        if not re.search(r'[A-Z]', password):
            raise ValidationError('密码必须包含至少一个大写字母')
        if not re.search(r'[a-z]', password):
            raise ValidationError('密码必须包含至少一个小写字母')
        if not re.search(r'\d', password):
            raise ValidationError('密码必须包含至少一个数字')
        return password

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password and password2 and password != password2:
            raise ValidationError('两次输入的密码不一致')
        return password2


class MerchantSettingsForm(forms.ModelForm):
    """商家设置表单"""
    class Meta:
        model = Merchant
        fields = ['shop_name', 'logo', 'description', 'contact_phone', 'contact_email', 'address']
        widgets = {
            'shop_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black'
            }),
            'address': forms.TextInput(attrs={
                'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black'
            }),
        }


class ProductForm(forms.Form):
    """商家商品表单"""
    name = forms.CharField(
        max_length=200,
        label='商品名称',
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black'
        })
    )
    slug = forms.SlugField(
        label='URL别名',
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black'
        })
    )
    category = forms.ChoiceField(
        label='分类',
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black'
        })
    )
    description = forms.CharField(
        label='商品描述',
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black'
        })
    )
    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label='价格',
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black',
            'step': '0.01'
        })
    )
    image = forms.ImageField(
        label='商品图片',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black'
        })
    )
    stock = forms.IntegerField(
        min_value=0,
        label='库存',
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-black focus:border-black'
        })
    )
    is_new = forms.BooleanField(
        required=False,
        label='是否新品',
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-black focus:ring-black border-gray-300 rounded'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from goods.models import Category
        self.fields['category'].choices = [('', '-- 请选择分类 --')] + [
            (c.id, c.name) for c in Category.objects.all()
        ]
