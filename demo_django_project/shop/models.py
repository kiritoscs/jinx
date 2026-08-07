from django.db import models
from django.utils.translation import gettext_lazy as _

class Product(models.Model):
    """商品模型"""
    name = models.CharField(_('商品名称'), max_length=100)
    price = models.DecimalField(_('价格'), max_digits=10, decimal_places=2)
    is_published = models.BooleanField(_('是否上架'), default=False)
    description = models.TextField(_('商品描述'), blank=True)

    class Meta:
        verbose_name = _('商品')
        verbose_name_plural = _('商品列表')

    def __str__(self) -> str:
        return self.name

    def status_label(self) -> str:
        if self.is_published:
            return _('已上架')
        return _('已下架')
