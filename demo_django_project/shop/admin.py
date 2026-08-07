from django.contrib import admin
from shop.models import Product
from django.utils.translation import gettext_lazy as _

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_published')
    list_filter = ('is_published',)
    search_fields = ('name',)
    actions = ['mark_published']

    @admin.action(description=_('批量上架所选商品'))
    def mark_published(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f'已成功上架 {updated} 个商品')
