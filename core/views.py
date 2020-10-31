from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.text import slugify
from .forms import CheckoutForm, CouponForm, RefundForm, PaymentForm
from .models import Item, OrderItem, Order, Address, Payment, PaymentType, Coupon, Refund, UserProfile, Category, Label
from twilio.twiml.messaging_response import MessagingResponse, Media, Message, Body
from core import controller

from django_twilio.decorators import twilio_view

from rest_framework import viewsets, filters, status
from rest_framework.decorators import api_view, permission_classes, schema
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.schemas import AutoSchema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions

from .serializers import (OrderSerializer, ItemSerializer, AddressSerializer, CouponSerializer,
                          OrderItemSerializer, UserProfileSerializer, CategorySerializer, LabelSerializer,
                          UserSerializer, PaymentSerializer, PaymentTypeSerializer)

from core.tasks import pull_vinted_products

import random
import string
import json
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


"""
Customer journey :

+> Search a product OK
    +> Sub searches
    +> Update search terms

-> Add product to the cart
    -> Update quantity : give user's ID, item ID and quantity
    -> Update color : give user id, item id that has the new color
    -> Update size : give user id, item id that has the new size
    -> Delete product from cart : user id and product id

-> Address management OK
    -> Add address (billing and/or shipping)
    -> Remove address : user's ID, address details and the type of address billing or shipping
    -> Update address : user's ID, address details and the type of address ID
    -> Choose address : order's ID, address ID

-> Shipment (to create) OK
    -> Choose shipment : order ID, shipment ID
    -> Update shipment : order ID, new shipment ID

-> Checkout / Pay (to create) TODO
    -> Choose payment method OK
    -> Get the link where to pay OK
    -> Pay TODO

-> View order / -> View cart OK
    -> Return only the non paid order (see view order status) OK
    -> Return only the order that belong to the user with the ID specified OK
    -> OrderItems :
        - Show the order items of the current order alone OK
        - Show the order item of the user with the speficied ID OK (see Return only the order that belong to the user with the ID specified)

-> Cancel order OK
    - Means set the ordered to false + delete all the order items attached to that order (empty the cart)

-> View order status OK
    - Get the details of the order that is not paid yet
"""


def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


def products(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, "products.html", context)


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='S',
                default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='B',
                default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address': billing_address_qs[0]})

            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():

                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')
                if use_default_shipping:
                    print("Using the defualt shipping address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default shipping address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new shipping address")
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                            address_type='S'
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required shipping address fields")

                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print("Using the defualt billing address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default billing address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new billing address")
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            address_type='B'
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required billing address fields")

                payment_option = form.cleaned_data.get('payment_option')

                if payment_option == 'S':
                    return redirect('core:payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('core:payment', payment_option='paypal')
                else:
                    messages.warning(
                        self.request, "Invalid payment option selected")
                    return redirect('core:checkout')
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:order-summary")


class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False
            }
            userprofile = self.request.user.userprofile
            if userprofile.one_click_purchasing:
                # fetch the users card list
                cards = stripe.Customer.list_sources(
                    userprofile.stripe_customer_id,
                    limit=3,
                    object='card'
                )
                card_list = cards['data']
                if len(card_list) > 0:
                    # update the context with the default card
                    context.update({
                        'card': card_list[0]
                    })
            return render(self.request, "payment.html", context)
        else:
            messages.warning(
                self.request, "You have not added a billing address")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        form = PaymentForm(self.request.POST)
        userprofile = UserProfile.objects.get(user=self.request.user)
        if form.is_valid():
            token = form.cleaned_data.get('stripeToken')
            save = form.cleaned_data.get('save')
            use_default = form.cleaned_data.get('use_default')

            if save:
                if userprofile.stripe_customer_id != '' and userprofile.stripe_customer_id is not None:
                    customer = stripe.Customer.retrieve(
                        userprofile.stripe_customer_id)
                    customer.sources.create(source=token)

                else:
                    customer = stripe.Customer.create(
                        email=self.request.user.email,
                    )
                    customer.sources.create(source=token)
                    userprofile.stripe_customer_id = customer['id']
                    userprofile.one_click_purchasing = True
                    userprofile.save()

            amount = int(order.get_total() * 100)

            try:

                if use_default or save:
                    # charge the customer because we cannot charge the token more than once
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="usd",
                        customer=userprofile.stripe_customer_id
                    )
                else:
                    # charge once off on the token
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="usd",
                        source=token
                    )

                # create the payment
                payment = Payment()
                payment.stripe_charge_id = charge['id']
                payment.user = self.request.user
                payment.amount = order.get_total()
                payment.save()

                # assign the payment to the order

                order_items = order.items.all()
                order_items.update(ordered=True)
                for item in order_items:
                    item.save()

                order.ordered = True
                order.payment = payment
                order.ref_code = create_ref_code()
                order.save()

                messages.success(self.request, "Your order was successful!")
                return redirect("/")

            except stripe.error.CardError as e:
                body = e.json_body
                err = body.get('error', {})
                messages.warning(self.request, f"{err.get('message')}")
                return redirect("/")

            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.warning(self.request, "Rate limit error")
                return redirect("/")

            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                print(e)
                messages.warning(self.request, "Invalid parameters")
                return redirect("/")

            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                messages.warning(self.request, "Not authenticated")
                return redirect("/")

            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                messages.warning(self.request, "Network error")
                return redirect("/")

            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                messages.warning(
                    self.request, "Something went wrong. You were not charged. Please try again.")
                return redirect("/")

            except Exception as e:
                # send an email to ourselves
                messages.warning(
                    self.request, "A serious error occurred. We have been notifed.")
                return redirect("/")

        messages.warning(self.request, "Invalid data received")
        return redirect("/payment/stripe/")


class HomeView(ListView):
    model = Item
    paginate_by = 10
    template_name = "home.html"


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/")


class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"


def handle_add_to_cart(request, item):
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            return False  # Only the quantity was updated.
        else:
            order.items.add(order_item)
            return True  # The item was added
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        return True  # The item was added


@login_required
@permission_classes((IsAuthenticated,))
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    added = handle_add_to_cart(request.user, item)

    if added is True:  # For more clarity
        messages.info(request, "This item was added to your cart.")
        return redirect("core:order-summary")
    else:
        messages.info(request, "This item quantity was updated.")
        return redirect("core:order-summary")


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "This item was removed from your cart.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("core:checkout")


@api_view(['POST'])
@schema(AutoSchema)
def update_from_vinted(request):
    # Create a celery task to update the products
    # pull_vinted_products.delay()
    # return HttpResponse("<h1>Task added {}</h1>".format(timezone.now()))

    # Get the request body
    print("Post request data: {}".format(request.data))
    vinted_data = request.data['vinted_data']
    print("vinted_data : {}".format(vinted_data))
    html_response = "<h2>Product updates</h2>"

    # Read the json data
    # vinted_data_json = json.load(vinted_data)
    vinted_data_json = vinted_data

    for product in vinted_data_json['items']:
        product_id = product['id']
        html_response += "<p>Processing product id {}</p>".format(product_id)

        print("Processing product id {}".format(product_id))
        # Get or create the category
        category, createdcategory = Category.objects.get_or_create(
            name=product['brand'])

        # Get or create the label
        label, createdlabel = Label.objects.get_or_create(name="vinted")

        # Update the products
        item, created = Item.objects.get_or_create(
            title=product['title'],
            price=product['original_price_numeric'],
            discount_price=product['price_numeric'],
            category=category,
            label=label,
            slug=slugify("{}{}".format(product['title'][:200], product['id'])),
            description=product['description']
        )

        item.description = product['description'],
        # external_image=product['photos'][0]['thumbnails'][0]['url'],
        item.external_image = product['photos'][0]['url'],
        item.external_product_id = product['id'],
        item.stock_quantity = 1

        item.save()
        print("Done for product id {}".format(product_id))

    html_response += "<h2>Task finished at {}</h2>".format(timezone.now())
    return HttpResponse(html_response)


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("core:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("core:checkout")


class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }
        return render(self.request, "request_refund.html", context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            # edit the order
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                # store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, "Your request was received.")
                return redirect("core:request-refund")

            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist.")
                return redirect("core:request-refund")


@twilio_view
def handle_bot_queries(request):
    resp = MessagingResponse()
    message = Message()
    brain_response = controller.handle_whatsapp_user_input(request)
    message.body(brain_response)
    resp.append(message)
    return resp


class OrderView(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


@permission_classes((AllowAny, ))
class ItemView(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', '=price', 'category__name',
                     'description', 'slug', 'label__name']
    ordering_fields = ['price', 'category__name']
    ordering = ['price']


class AddressView(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer


class PaymentApiView(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer


class PaymentTypeView(viewsets.ModelViewSet):
    queryset = PaymentType.objects.all()
    serializer_class = PaymentTypeSerializer


class CouponView(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer


class OrderItemView(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer


class UserProfileView(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer


class CategoryView(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class LabelView(viewsets.ModelViewSet):
    queryset = Label.objects.all()
    serializer_class = LabelSerializer


class ChooseShipmentView(APIView):
    authentication_classes = [authentication.TokenAuthentication]

    def get(self, request, format=None):
        """
        Return a list of all users.
        """
        print("query set", self.queryset)
        usernames = [user.user.username for user in UserProfile.objects.all()]
        return Response(usernames)


class LogoutView(APIView):
    def get(self, request, format=None):
        # simply delete the token to force a login
        request.user.auth_token.delete()
        return JsonResponse({"message": "Logout successful."}, status=status.HTTP_200_OK)


@api_view(['POST'])
@schema(AutoSchema)
def choose_order_shipment(request):

    # Get the request data and extract the values
    print("Post request data: {}".format(request.data))
    username = request.data['username']
    address_id = request.data['address_id']
    print("Username : {}, address id {}".format(username, address_id))

    user = UserProfile.objects.filter(user__username=username).first()
    shipment = Address.objects.filter(id=address_id).first()

    if user is not None and shipment is not None:
        current_order = user.get_current_order(create=True)
        print("Got current order : {}".format(current_order))
        print("Shipment address: {}".format(shipment))

        current_order.shipping_address = shipment
        current_order.save()
        return Response({"message": "Shipment address updated"})

        # if request.method == 'POST':
        #     return Response({"message": "Got some data!", "data": request.data})
        # return Response({"message": "Hello, world!"})
    elif user is None:
        return Response({"message": "Cannot find user with username {}".format(username)})
    elif shipment is None:
        return Response({"message": "Cannot find shipment with id {}".format(address_id)})
    else:
        return Response({"message": "Unknwon error"})


@api_view(['POST'])
@schema(AutoSchema)
def choose_order_billing_address(request):

    # Get the request data and extract the values
    print("Post request data: {}".format(request.data))
    username = request.data['username']
    address_id = request.data['address_id']
    print("Username : {}, address id {}".format(username, address_id))

    user = UserProfile.objects.filter(user__username=username).first()
    billing = Address.objects.filter(id=address_id).first()

    if user is not None and billing is not None:
        current_order = user.get_current_order(create=True)
        print("Got current order : {}".format(current_order))
        print("Billing address: {}".format(billing))

        current_order.billing_address = billing
        current_order.save()
        return Response({"message": "Billing address updated"})

        # if request.method == 'POST':
        #     return Response({"message": "Got some data!", "data": request.data})
        # return Response({"message": "Hello, world!"})
    elif user is None:
        return Response({"message": "Cannot find user with username {}".format(username)})
    elif billing is None:
        return Response({"message": "Cannot find billing with id {}".format(address_id)})
    else:
        return Response({"message": "Unknwon error"})


@api_view(['POST'])
def cancel_order(request, id):
    print('Getting the order with the ID {}'.format(id))

    order = get_object_or_404(Order, id=id)
    order.cancel()

    return Response({"message": "Order with ID {} cancelled".format(order.id)})


@api_view(['GET'])
def get_userprofile_current_order(request, id):
    print("Get the user profile")
    user = get_object_or_404(UserProfile, id=id)
    current_order = user.get_current_order()
    print("Got current order {}".format(current_order))

    serializer = OrderSerializer(current_order, many=False)

    return JsonResponse(serializer.data, status=200)


@api_view(['POST'])
@schema(AutoSchema)
def choose_order_paymentmethod(request):

    # Get the request data and extract the values
    print("Post request data: {}".format(request.data))
    username = request.data['username']
    payment_method_id = request.data['payment_method']
    print("Username : {}, payment method {}".format(username, payment_method_id))

    user = UserProfile.objects.filter(user__username=username).first()
    payment_type = PaymentType.objects.filter(id=payment_method_id).first()

    if user is not None and payment_type is not None:
        current_order = user.get_current_order(create=True)
        print("Got current order : {}".format(current_order))
        print("Payment method: {}".format(payment_method_id))

        current_payment = current_order.get_waitingforpayment_payment(
            create=False)
        if current_payment is None:
            current_payment = Payment(user=current_order.user, amount=current_order.get_total(
            ), order=current_order, payment_type=payment_type)
        else:
            current_payment.payment_type = payment_type

        current_payment.save()
        return Response({"message": "Payment method updated to {}".format(payment_type)})
    elif user is None:
        return Response({"message": "Cannot find user with username {}".format(username)})
    elif payment_type is None:
        return Response({"message": "Cannot find payment method with id {}".format(payment_method_id)})
    else:
        return Response({"message": "Unknwon error"})


@api_view(['POST'])
@schema(AutoSchema)
def get_me(request):
    print("Getting currently connected user {}".format(request.user))
    user = get_object_or_404(UserProfile, user=request.user)

    serializer = UserProfileSerializer(user, many=False)

    return JsonResponse(serializer.data, status=200)


@api_view(['POST'])
@schema(AutoSchema)
@permission_classes((IsAuthenticated,))
def add_to_cart_byid(request, id):
    item = get_object_or_404(Item, id=id)
    added = handle_add_to_cart(request.user, item)

    if added is True:
        return Response({"message": "Product added"})
    else:
        return Response({"message": "Product quantity updated"})
