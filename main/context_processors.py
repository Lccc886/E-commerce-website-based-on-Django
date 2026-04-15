from goods.models import Category

def categories(request):
    """将分类列表注入到所有模板中"""
    return {'categories': Category.objects.all()}