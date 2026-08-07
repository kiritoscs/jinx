from django.urls import path

from shop import views

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("products/<int:pk>/", views.product_detail, name="product_detail"),
    path("api/checkout/", views.checkout_api, name="checkout_api"),
]
