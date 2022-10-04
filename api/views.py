from django.contrib.auth import authenticate
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from rest_framework import exceptions, permissions, serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from utils.authentication import JWT, AudienceENUM
from utils.views import BaseAPIView

from .models import Book, Cart, CartItem, User


# Create your views here.
class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "username", "password", "email")
        read_only_fields = ("id", "first_name", "last_name")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        return self.Meta.model.objects.create_user(**validated_data)


class RegistrationAPIView(BaseAPIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = []
    serializer = RegistrationSerializer
    model = User
    http_method_not_allowed = ("GET", "PUT", "DELETE")


class LoginSerializer(serializers.Serializer):  # noqa
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    data = serializers.SerializerMethodField(read_only=True)

    def get_data(self, obj):  # noqa
        return obj.token

    def create(self, validated_data):
        user = authenticate(**validated_data)
        if not user:
            raise exceptions.NotAuthenticated()
        return user


class LoginAPIView(BaseAPIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = []
    serializer = LoginSerializer
    http_method_not_allowed = ("GET", "PUT", "DELETE")


@require_http_methods(["GET"])
def verify_user_view(request, token: str):  # noqa
    payload = JWT.decode(token=token, aud=AudienceENUM.VERIFY_USER)
    user = get_object_or_404(User, pk=payload["user_id"])
    user.is_verified = True
    user.save()
    return HttpResponse("%s is verified" % user.username.capitalize())


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "price", "author", "quantity")


class BookAPIView(BaseAPIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = []
    serializer = BookSerializer
    model = Book


class CartItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ("id", "book", "total_price", "quantity", "cart")
        read_only_fields = fields


class CartBookSerializer(serializers.Serializer):  # noqa
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
    quantity = serializers.IntegerField(min_value=1)


class CartSerializer(serializers.ModelSerializer):
    cart_items = CartItemsSerializer(many=True, read_only=True)
    books = CartBookSerializer(many=True, write_only=True)

    class Meta:
        model = Cart
        fields = ("id", "is_ordered", "user", "total_price", "cart_items", "books")
        read_only_fields = ("id", "user", "is_ordered", "total_price")

    @staticmethod
    def create_cart_item_list(books, cart, user):  # noqa
        item_list = []
        for book in books:
            cart_item, created = CartItem.objects.get_or_create(  # noqa
                cart=cart, user=user, book=book["book"]
            )
            if not created:
                if book["quantity"] > book["book"].quantity:
                    raise exceptions.APIException(
                        detail=f"{book['book'].quantity} {book['book'].title} left in the "
                        f"inventory",
                        code="insufficient-product",
                    )
                cart_item.quantity += book["quantity"]
                cart_item.save()
            item_list.append(cart_item)
        return item_list

    def create(self, validated_data: dict):
        user = self.context["user"]
        cart, _ = Cart.objects.get_or_create(user=user, is_ordered=False)
        item_list = self.create_cart_item_list(
            books=validated_data["books"], cart=cart, user=user
        )
        cart.cart_items.add(*item_list)
        return cart


class CartAPIView(BaseAPIView):
    serializer = CartSerializer
    http_method_not_allowed = ("PUT",)

    def get_queryset(self, lookup_value=None):
        if lookup_value:
            qs = Cart.objects.get(
                user=self.request.user,
                is_ordered=False,
                **{self.lookup_field: lookup_value},
            )
        else:
            qs = Cart.objects.filter(user=self.request.user, is_ordered=False)
        return qs

    def delete(self, request, pk=None):
        cart = self.get_queryset(lookup_value=pk)
        if cart.cart_items.all().count() == 0:
            cart.delete()
        else:
            for data in request.data:
                cart_item_id, quantity = data.values()
                cart_item = cart.cart_items.get(id=cart_item_id)

                if cart_item.quantity < quantity:
                    raise exceptions.APIException(
                        f"Your cart contains {cart_item.quantity} no. of {cart_item.book}"
                    )

                cart_item.quantity -= quantity
                cart_item.save() if cart_item.quantity != 0 else cart.cart_items.remove(
                    cart_item
                )

        return Response(status=204)


@api_view(["POST"])
def checkout_view(request, pk):
    cart = get_object_or_404(Cart, pk=pk, user=request.user, is_ordered=False)
    # # =========================================
    # #
    # # payment process
    # #
    # # =========================================
    cart.is_ordered = True
    cart.save()
    return Response(
        {"message": "Congrats, item id %d successfully purchased" % cart.id}, status=201
    )
