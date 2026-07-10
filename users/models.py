from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver



class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="头像")
    phone = models.CharField(max_length=20, blank=True, verbose_name="手机号")
    birth_date = models.DateField(blank=True, null=True, verbose_name="生日")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} 的资料"

    class Meta:
        verbose_name = "用户资料"
        verbose_name_plural = "用户资料"


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=100, verbose_name="收货人姓名")
    phone = models.CharField(max_length=20, verbose_name="联系电话")
    province = models.CharField(max_length=50, verbose_name="省份")
    city = models.CharField(max_length=50, verbose_name="城市")
    district = models.CharField(max_length=50, verbose_name="区/县")
    address_line = models.CharField(max_length=200, verbose_name="详细地址")
    is_default = models.BooleanField(default=False, verbose_name="设为默认")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "收货地址"
        verbose_name_plural = "收货地址"
        ordering = ['-is_default', '-created']

    def __str__(self):
        return f"{self.full_name} - {self.address_line}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)