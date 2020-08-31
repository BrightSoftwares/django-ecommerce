from django.urls import path, include
from rest_framework import routers
from rest_framework.authtoken import views

from .views import (
    ItemDetailView,
    CheckoutView,
    HomeView,
    OrderSummaryView,
    add_to_cart,
    remove_from_cart,
    remove_single_item_from_cart,
    PaymentView,
    AddCouponView,
    RequestRefundView,
    handle_bot_queries,
    ItemView,
    OrderView,
    AddressView,
    CouponView,
    OrderItemView,
    UserProfileView,
    update_from_vinted,
    CategoryView,
    LabelView
)

app_name = 'core'

router = routers.DefaultRouter()
router.register('orders', OrderView)
router.register('items', ItemView)
router.register('address', AddressView)
router.register('coupon', CouponView)
router.register('orderitem', OrderItemView)
router.register('userprofile', UserProfileView)
router.register('category', CategoryView)
router.register('label', LabelView)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('add-coupon/', AddCouponView.as_view(), name='add-coupon'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('remove-item-from-cart/<slug>/', remove_single_item_from_cart,
         name='remove-single-item-from-cart'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),
    path('request-refund/', RequestRefundView.as_view(), name='request-refund'),
    path('bot/', handle_bot_queries, name='bot'),
    path('api/', include(router.urls), name='apiindex'),
    path('api-token-auth/', views.obtain_auth_token, name='api-token-auth'),
    path('api/orders/', OrderView, name='orders'),
    path('api/items/', ItemView, name='items'),
    path('api/address/', AddressView, name='address'),
    path('api/coupon/', CouponView, name='coupon'),
    path('api/category/', CategoryView, name='category'),
    path('api/label/', LabelView, name='label'),
    path('api/orderitem/', OrderItemView, name='orderitem'),
    path('api/userprofile/', UserProfileView, name='userprofile'),
    path('automation/update-from-vinted/',
         update_from_vinted, name='update-from-vinted'),
]
