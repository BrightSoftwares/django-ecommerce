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
    PaymentApiView,
    PaymentTypeView,
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
    LabelView,
    ChooseShipmentView,
    choose_order_shipment,
    cancel_order,
    get_userprofile_current_order,
    choose_order_paymentmethod,
    choose_order_billing_address,
    get_me
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
router.register('payment', PaymentApiView)
router.register('paymenttype', PaymentTypeView)

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
    path('api/orders/<id>/cancel/', cancel_order, name='orders'),
    path('api/userprofile/<id>/current-order/',
         get_userprofile_current_order, name='userprofile-currentorder'),
    path('api/add-to-cart/<slug>/', add_to_cart, name='api-add-to-cart'),
    path('api/choose-shipping-address/', choose_order_shipment,
         name='api-choose-shipping'),
    path('api/choose-billing-address/', choose_order_billing_address,
         name='api-choose-billing'),
    path('api/choose-payment-method/', choose_order_paymentmethod,
         name='api-choose-paymentmethod'),
    path('api/get-me/', get_me,
         name='api-get-me'),
    path('automation/update-from-vinted/',
         update_from_vinted, name='update-from-vinted'),
]
