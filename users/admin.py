# users/admin.py
from django.contrib import admin
from .models import Address

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'phone', 'city', 'is_default')
    list_filter = ('is_default', 'city')
    search_fields = ('user__username', 'full_name', 'phone', 'address_line')
    list_editable = ('is_default',)