from django import forms
from shop.models import Product
from django.utils.translation import gettext_lazy as _

class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = ['name', 'price', 'description', 'is_published']
        labels = {'name': _('商品名称'), 'price': _('销售价格'), 'description': _('详细介绍'), 'is_published': _('立即上架')}
        help_texts = {'name': _('请输入不超过 100 个字符的名称'), 'price': _('单位为人民币元')}
        error_messages = {'name': {'required': _('商品名称不能为空'), 'max_length': _('商品名称过长')}}

    def clean_price(self):
        price = self.cleaned_data['price']
        if price is not None and price < 0:
            raise forms.ValidationError(_('价格不能为负数'))
        return price
