from rest_framework import serializers

from .models import Item, Order


class ItemSerializer(serializers.ModelSerializer):
    # owner_name = serializers.CharField(read_only=True, source="owner.name")
    # owner_surname = serializers.CharField(read_only=True, source="owner.surname")

    class Meta:
        model = Item
        fields = ('title', 'price', 'discount_price', 'label', 'slug', 'description', 'image')


class OrderSerializer(serializers.ModelSerializer):
    # plates = PlateSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ('user', 'ref_code', 'items', 'start_date', 'ordered_date', 'ordered', 'shipping_address', 'billing_address', 'payment', 'coupon', 'being_delivered', 'received', 'refund_requested', 'refund_granted')
