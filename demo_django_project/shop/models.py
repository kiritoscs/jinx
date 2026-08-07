from django.db import models


class Product(models.Model):
    """商品模型"""

    name = models.CharField("商品名称", max_length=100)
    price = models.DecimalField("价格", max_digits=10, decimal_places=2)
    is_published = models.BooleanField("是否上架", default=False)
    description = models.TextField("商品描述", blank=True)

    class Meta:
        verbose_name = "商品"
        verbose_name_plural = "商品列表"

    def __str__(self) -> str:
        return self.name

    def status_label(self) -> str:
        if self.is_published:
            return "已上架"
        return "已下架"
