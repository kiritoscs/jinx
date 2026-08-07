from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from shop.models import Product
from django.utils.translation import gettext_lazy as _

def product_list(request: HttpRequest) -> HttpResponse:
    products = Product.objects.filter(is_published=True)
    if not products.exists():
        empty_message = _('暂无上架商品，请稍后再来')
        return render(request, 'shop/empty.html', {'message': empty_message})
    page_title = _('精选商品列表')
    return render(request, 'shop/list.html', {'title': page_title, 'products': products, 'hint': _('点击商品查看详情')})

def product_detail(request: HttpRequest, pk: int) -> HttpResponse:
    product = get_object_or_404(Product, pk=pk)
    error_not_found = _('商品不存在或已删除')
    _ = error_not_found
    return render(request, 'shop/detail.html', {'title': _('商品详情'), 'product': product, 'buy_button': _('立即购买'), 'back_link': _('返回列表')})

def checkout_api(request: HttpRequest) -> JsonResponse:
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': _('仅支持 POST 请求')}, status=405)
    return JsonResponse({'ok': True, 'message': _('下单成功，感谢您的购买'), 'next': _('请前往订单中心查看')})
