from rest_framework import serializers

from .models import Item, Order, UserProfile, Coupon, Address, OrderItem, Category, Label


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('id', 'name')


class LabelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Label
        fields = ('id', 'name')


class ItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    label = LabelSerializer()

    class Meta:
        model = Item
        fields = ('id', 'title', 'price', 'discount_price', 'category',
                  'label', 'slug', 'description', 'image')

    def create(self, validated_data):
        category_data = validated_data.pop('category')
        label_data = validated_data.pop('label')
        print("Category data", category_data)
        print("Label data", label_data)
        category, _ = Category.objects.get_or_create(**category_data)
        label, _ = Label.objects.get_or_create(**label_data)

        album = Item.objects.create(
            **validated_data, category=category, label=label)

        return album


class UserProfileSerializer(serializers.ModelSerializer):
    # plates = PlateSerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = ('id', 'user', 'one_click_purchasing')


class OrderItemSerializer(serializers.ModelSerializer):
    # plates = PlateSerializer(many=True, read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'user', 'ordered', 'item', 'quantity', 'order')


class OrderSerializer(serializers.ModelSerializer):
    # plates = PlateSerializer(many=True, read_only=True)
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ('id', 'user', 'ref_code', 'items', 'start_date', 'ordered_date', 'ordered', 'shipping_address',
                  'billing_address', 'payment', 'coupon', 'being_delivered', 'received', 'refund_requested', 'refund_granted')


class AddressSerializer(serializers.ModelSerializer):
    # plates = PlateSerializer(many=True, read_only=True)

    class Meta:
        model = Address
        fields = ('id', 'user', 'street_address', 'country',
                  'apartment_address', 'zip', 'address_type', 'default')


class CouponSerializer(serializers.ModelSerializer):
    # plates = PlateSerializer(many=True, read_only=True)

    class Meta:
        model = Coupon
        fields = ('id', 'code')
