from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from .models import Follow

User = get_user_model()


class FoodgramUserSerializer(UserSerializer):
    """Сериализатор для кастомной модели пользователя.
    Получает список пользователей подмешивая новое поле is_subscribe.
    """

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )
        read_only_fields = ('is_subscribed',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user
        return (
            False
            if user.is_anonymous
            else Follow.objects.filter(author=obj, user=user).exists()
        )


class FoodgramCreateUserSerializer(UserCreateSerializer):
    """Сериализатор для создания кастомной модели пользователя."""

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        extra_kwargs = {
            'password': {'write_only': True},
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }
