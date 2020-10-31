from django.contrib import admin

from .models import Item, OrderItem, Order, Payment, Coupon, Refund, Address, UserProfile, Category, Label, ShippingMethod, PaymentType


def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_requested=False, refund_granted=True)


make_refund_accepted.short_description = 'Update orders to refund granted'


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user',
                    'ordered',
                    'being_delivered',
                    'received',
                    'refund_requested',
                    'refund_granted',
                    'shipping_address',
                    'billing_address',
                    'payments',
                    'coupon'
                    ]
    list_display_links = [
        'user',
        'shipping_address',
        'billing_address',
        'payments',
        'coupon'
    ]
    list_filter = ['ordered',
                   'being_delivered',
                   'received',
                   'refund_requested',
                   'refund_granted']
    search_fields = [
        'user__username',
        'ref_code'
    ]
    actions = [make_refund_accepted]


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'street_address',
        'apartment_address',
        'country',
        'zip',
        'address_type',
        'default'
    ]
    list_filter = ['default', 'address_type', 'country']
    search_fields = ['user', 'street_address', 'apartment_address', 'zip']


class ItemAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'price',
        'discount_price',
        'stock_quantity',
        'category',
        'label',
        'slug'
    ]
    list_filter = ['price', 'category', 'label']
    search_fields = ['title', 'category__name', 'label__name', 'price']


admin.site.register(Item, ItemAdmin)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)
admin.site.register(Refund)
admin.site.register(Address, AddressAdmin)
admin.site.register(UserProfile)
admin.site.register(Category)
admin.site.register(Label)
admin.site.register(ShippingMethod)
admin.site.register(PaymentType)
