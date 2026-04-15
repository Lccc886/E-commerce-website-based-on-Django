from django.conf import settings
from django.db import models, transaction
from django.urls import reverse



class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="分类名称")
    slug = models.SlugField(unique=True, verbose_name="URL别名")
    description = models.TextField(blank=True, verbose_name="描述")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "商品分类"
        verbose_name_plural = "商品分类"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', args=[self.slug])

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="分类")
    name = models.CharField(max_length=200, verbose_name="商品名称")
    slug = models.SlugField(unique=True, verbose_name="URL别名")
    description = models.TextField(verbose_name="描述")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="价格")
    image = models.ImageField(upload_to='products/', verbose_name="商品图片")
    stock = models.PositiveIntegerField(default=0, verbose_name="库存")
    available = models.BooleanField(default=True, verbose_name="是否上架")
    is_new = models.BooleanField(default=False, verbose_name="是否新品")
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0, verbose_name="评分")
    review_count = models.PositiveIntegerField(default=0, verbose_name="评论数")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "商品"
        verbose_name_plural = "商品"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('goods:product_detail', args=[self.slug])

    @property
    def average_rating(self):
        """计算平均评分"""
        reviews = self.reviews.all()
        if reviews:
            return sum(r.rating for r in reviews) / reviews.count()
        return 0

    @property
    def review_count(self):
        return self.reviews.count()

    @transaction.atomic
    def decrease_stock(self, quantity):
        """扣减库存，使用 select_for_update 防止超卖"""
        if self.stock >= quantity:
            self.stock -= quantity
            self.save()
            return True
        return False

class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # 一个用户只能收藏同一商品一次
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"





class Review(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name="评分")
    comment = models.TextField(verbose_name="评论")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created']

    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.rating}"