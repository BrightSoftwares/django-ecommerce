from enum import Enum
from django.db.models.signals import post_save
from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.shortcuts import reverse
from django_countries.fields import CountryField
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name='userprofile', on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    one_click_purchasing = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def get_current_order(self, create=False):
        current_order = Order.objects.filter(
            user=self.user).filter(ordered=False).filter(cancelled=False).first()

        if current_order is None and create is True:
            current_order = Order(user=self.user, ordered_date=timezone.now())
            current_order.save()
        return current_order


class Category(models.Model):
    name = models.CharField(max_length=256)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'


class Label(models.Model):
    name = models.CharField(max_length=256)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ShippingMethod(models.Model):
    name = models.CharField(max_length=256)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Item(models.Model):
    title = models.CharField(max_length=100)
    price = models.FloatField()
    discount_price = models.FloatField(blank=True, null=True)
    # category = models.CharField(choices=CATEGORY_CHOICES, max_length=2)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, blank=False, null=False)
    # label = models.CharField(choices=LABEL_CHOICES, max_length=1)
    label = models.ForeignKey(
        Label, on_delete=models.CASCADE, blank=False, null=False)
    slug = models.SlugField(max_length=256)
    description = models.TextField()
    image = models.ImageField(default='default.jpg')
    stock_quantity = models.IntegerField(default=1)
    external_image = models.URLField(default="")
    external_product_id = models.CharField(max_length=256)

    def __str__(self):
        return "{} {}€ {}".format(self.title, self.price, self.label)

    def get_absolute_url(self):
        return reverse("core:product", kwargs={
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse("core:add-to-cart", kwargs={
            'slug': self.slug
        })

    def get_remove_from_cart_url(self):
        return reverse("core:remove-from-cart", kwargs={
            'slug': self.slug
        })

    class Meta:
        ordering = ['-id']


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="orders",
                             on_delete=models.CASCADE)
    ref_code = models.CharField(max_length=20, blank=True, null=True)
    # items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    shipping_address = models.ForeignKey(
        'Address', related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    billing_address = models.ForeignKey(
        'Address', related_name='billing_address', on_delete=models.SET_NULL, blank=True, null=True)
    # payment = models.ForeignKey(
    #     'Payment', on_delete=models.SET_NULL, blank=True, null=True)
    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, blank=True, null=True)
    shipping_method = models.ForeignKey(
        'ShippingMethod', on_delete=models.PROTECT, null=True)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)

    '''
    1. Item added to cart
    2. Adding a billing address
    (Failed checkout)
    3. Payment
    (Preprocessing, processing, packaging etc.)
    4. Being delivered
    5. Received
    6. Refunds
    '''

    def __str__(self):
        nbitems = self.items.length if self.items is None else 0
        return f"Order for {self.user.username} with {nbitems} items, Ordered: {self.ordered}"

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        if self.coupon:
            total -= self.coupon.amount
        return total

    def cancel(self):
        print("Cancelling order with id {}".format(self.id))

        if self.ordered is True:
            raise Exception(
                "Cannot cancel an ordered (paid) order. Use the refund system instead")
        else:
            self.cancelled = True
            self.save()

    def get_waitingforpayment_payment(self, create=True):
        print('Get the current payment waiting to be paid')

        payment_qs = Payment.objects.filter(
            order=self).filter(status=PaymentStatus.N.name)

        if not payment_qs.exists() and create is True:
            payment = Payment(user=self.user, amount=self.amount, order=self)
            payment.save()
        else:
            payment = payment_qs.first()

        return payment


class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", related_query_name="orderitem", null=True)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"Product: {self.item.title}, Qty: {self.quantity} for {self.user.username}"

    def get_total_item_price(self):
        return self.quantity * self.item.price

    def get_total_discount_item_price(self):
        return self.quantity * self.item.discount_price

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()

    def get_final_price(self):
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        return self.get_total_item_price()


# ADDRESS_CHOICES = (
#     ('B', 'Billing'),
#     ('S', 'Shipping'),
# )

class AddressType(Enum):
    B = "Billing"
    S = "Shipping"


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="addresses",
                             on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)
    address_type = models.CharField(max_length=1, choices=[(
        tag.name, tag.value) for tag in AddressType], default=AddressType.S.name)
    default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.address_type} address (default? {self.default}): {self.user.username}, {self.street_address}, {self.apartment_address}, {self.country}"

    class Meta:
        verbose_name_plural = 'Addresses'


# PAYMENT_STATUS = (
#     ('N', 'New, waiting for payment'),
#     ('P', 'Paid'),
#     ('F', 'Payment failed'),
# )

class PaymentStatus(Enum):
    N = "New, waiting for payment"
    P = "Paid"
    F = "Payment failed"


class PaymentType(models.Model):
    name = models.CharField(max_length=256, blank=True, null=True)
    payment_link = models.CharField(max_length=256, default="")
    payment_instructions = models.TextField(default="")

    def __str__(self):
        return "{} [{}...] {}...".format(self.name, self.payment_link[:30], self.payment_instructions[:60])


class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="payments", related_query_name="orderpayment", null=True)
    payment_type = models.ForeignKey(
        PaymentType, on_delete=models.CASCADE, blank=True, null=True)
    status = models.CharField(
        max_length=1, choices=[(tag.name, tag.value) for tag in PaymentStatus], default=PaymentStatus.N.name)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount}€"


class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField()

    def __str__(self):
        return f"{self.code} - {self.amount}"


class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f"Refund accepted: {self.accepted} : {self.pk}, Reason: {self.reason}"


def userprofile_receiver(sender, instance, created, *args, **kwargs):
    if created:
        userprofile = UserProfile.objects.create(user=instance)


post_save.connect(userprofile_receiver, sender=settings.AUTH_USER_MODEL)
