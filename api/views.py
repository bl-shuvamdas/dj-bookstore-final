from django.contrib.auth import authenticate
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import exceptions, permissions, serializers

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


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    data = serializers.SerializerMethodField(read_only=True)

    def get_data(self, obj):
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
def verify_user_view(request, token: str):
    payload = JWT.decode(token=token, aud=AudienceENUM.VERIFY_USER)
    user = get_object_or_404(User, pk=payload["user_id"])
    user.is_verified = True
    user.save()
    return HttpResponse("%s is verified" % user.username.capitalize())


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "price", "author")


class BookAPIView(BaseAPIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = []
    serializer = BookSerializer
    model = Book
