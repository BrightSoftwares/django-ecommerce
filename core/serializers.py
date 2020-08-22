from rest_framework import serializers

from .models import Item, Order, UserProfile, Coupon, Address, OrderItem


class ItemSerializer(serializers.ModelSerializer):
    # owner_name = serializers.CharField(read_only=True, source="owner.name")
    # owner_surname = serializers.CharField(read_only=True, source="owner.surname")

    class Meta:
        model = Item
        fields = ('title', 'price', 'discount_price',
                  'label', 'slug', 'description', 'image')


class OrderSerializer(serializers.ModelSerializer):
    # plates = PlateSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ('user', 'ref_code', 'items', 'start_date', 'ordered_date', 'ordered', 'shipping_address',
                  'billing_address', 'payment', 'coupon', 'being_delivered', 'received', 'refund_requested', 'refund_granted')


class UserProfileSerializer(serializers.ModelSerializer):
    # plates = PlateSerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = ('user', 'one_click_purchasing')


class OrderItemSerializer(serializers.ModelSerializer):
    # plates = PlateSerializer(many=True, read_only=True)

    class Meta:
        model = OrderItem
        fields = ('user', 'ordered', 'item', 'quantity')


class AddressSerializer(serializers.ModelSerializer):
    # plates = PlateSerializer(many=True, read_only=True)

    class Meta:
        model = Address
        fields = ('user', 'street_address', 'country',
                  'apartment_address', 'zip', 'address_type', 'default')


class CouponSerializer(serializers.ModelSerializer):
    # plates = PlateSerializer(many=True, read_only=True)

    class Meta:
        model = Coupon
        fields = ('id', 'code')
