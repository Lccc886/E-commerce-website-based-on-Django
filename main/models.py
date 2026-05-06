from django.db import models

from goods.models import Product

class CarouselImage(models.Model):
    title = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=200, blank=True)
    # 方式一：继续保留手动上传图片
    image = models.ImageField(upload_to='carousel/', blank=True, null=True)
    # 方式二：关联商品（如果选择商品，则优先使用商品的图片和链接）
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True, related_name='carousel_images')
    link = models.CharField(max_length=200, blank=True, help_text="自定义链接，如果关联商品则可留空")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def get_image_url(self):
        if self.product and self.product.image:
            return self.product.image.url
        if self.image:
            return self.image.url
        return ''

    def get_link_url(self):
        if self.product:
            return self.product.get_absolute_url()
        return self.link or '#'

    class Meta:
        ordering = ['order']