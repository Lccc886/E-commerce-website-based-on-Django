# main/context_processors.py
def cart_total(request):
    cart = request.session.get('cart', {})
    total_items = sum(cart.values())
    return {'cart_total_items': total_items}