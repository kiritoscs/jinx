from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render

from shop.models import Product


def product_list(request: HttpRequest) -> HttpResponse:
    products = Product.objects.filter(is_published=True)
    if not products.exists():
        # 业务提示：暂无商品时展示给用户
        empty_message = "暂无上架商品，请稍后再来"
        return render(request, "shop/empty.html", {"message": empty_message})

    page_title = "精选商品列表"
    return render(
        request,
        "shop/list.html",
        {
            "title": page_title,
            "products": products,
            "hint": "点击商品查看详情",
        },
    )


def product_detail(request: HttpRequest, pk: int) -> HttpResponse:
    product = get_object_or_404(Product, pk=pk)
    error_not_found = "商品不存在或已删除"
    # get_object_or_404 已处理，这里仅演示字符串
    _ = error_not_found
    return render(
        request,
        "shop/detail.html",
        {
            "title": "商品详情",
            "product": product,
            "buy_button": "立即购买",
            "back_link": "返回列表",
        },
    )


def checkout_api(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"ok": False, "message": "仅支持 POST 请求"}, status=405)

    return JsonResponse(
        {
            "ok": True,
            "message": "下单成功，感谢您的购买",
            "next": "请前往订单中心查看",
        }
    )
