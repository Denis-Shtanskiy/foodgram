from django.contrib.auth import get_user_model
from django.db.models import F
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import AmountIngredient, Ingredient, Recipe, Tag
from users.models import Follow

User = get_user_model()
MIN_TIME_COOKING_LIMIT = 1
MAX_TIME_COOKING_LIMIT = 300


class RecipesForFavoriteCartFollowedSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


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


class UserFollowerSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Follow
        field = (
            'author',
            'user',
        )

        def validate(self, data):
            user = data.get('user')
            author = data.get('author')
            if user == author:
                raise serializers.ValidationError('Нельзя самоподписаться!')
            if Follow.objects.filter(author=author, user=user).exists():
                raise serializers.ValidationError(
                    'Вы уже подписаны на этого пользователя!'
                )
            return data


class UserFollowSerializer(UserFollowerSerializer, FoodgramUserSerializer):
    recipes = RecipesForFavoriteCartFollowedSerializer(
        many=True, read_only=True
    )  # serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        read_only_fields = (
            'email',
            'username',
            'first_name',
            'last_name',
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    # def get_recipes(self, obj):
    #     request = self.context.get('request')
    #     recipes_limit = int(request.query_param.get('recipes_limit'))
    #     recipes = obj.recipes.all()
    #     if recipes_limit:
    #         recipes = recipes[:recipes_limit]
    #     serializer = RecipesForFavoriteCartFollowedSerializer(
    #         recipes,
    #         many=True,
    #         read_only=True,
    #     )
    #     return serializer.data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug',
        )


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class RecipeGetSerializer(serializers.ModelSerializer):
    tags = TagSerializer(
        read_only=True,
        many=True,
    )
    author = FoodgramUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_ingredients(self, obj):
        ingredients = obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('amount_ingredient__amount'),
        )
        return ingredients

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        user = request.user
        return (
            False
            if user.is_anonymous
            else user.favorite.filter(recipe_id=obj.id).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        user = request.user
        return (
            False
            if user.is_anonymous
            else user.carts.filter(recipe_id=obj.id).exists()
        )


class AmountIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        required=True,
    )

    class Meta:
        model = AmountIngredient
        fields = (
            'id',
            'amount',
        )

        def validate_amount(self, value):
            if value < 1:
                raise serializers.ValidationError(
                    'Количество не должно быть меньше 1'
                )
            return value


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = AmountIngredientSerializer(
        many=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                {'ingredients': 'Рецепт без ингредиентов - несуществует!'}
            )
        ingredients_for_recipe = []
        for ingredient in value:
            ingredient_id = ingredient.get('id')
            if ingredient_id in ingredients_for_recipe:
                raise serializers.ValidationError(
                    {
                        'recipe': 'Один и тот же ингредиент, '
                        'добейтесь уникальности!'
                    }
                )
            ingredients_for_recipe.append(ingredient_id)
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                {'tags': 'Теги обязательны, выберите один!'}
            )
        tags_for_recipe = []
        for tag in value:
            if tag in tags_for_recipe:
                raise serializers.ValidationError(
                    {'recipe': 'Такой тег уже есть!'}
                )
            tags_for_recipe.append(tag)
        return value

    def validate_cooking_time(self, value):
        if MAX_TIME_COOKING_LIMIT < value < MIN_TIME_COOKING_LIMIT:
            raise serializers.ValidationError(
                'Выберите подходящее время от 1 до 300 минут!'
            )
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('Фото или картинка обязательны!')
        return value

    def create_tags_and_ingredients(self, ingredients, tags, recipe):
        for tag in tags:
            recipe.tags.add(tag)
        list_ingredients = [
            AmountIngredient(
                recipe=recipe,
                ingredient=ingredient.get('id'),
                amount=ingredient.get('amount'),
            )
            for ingredient in ingredients
        ]
        AmountIngredient.objects.bulk_create(list_ingredients)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.create_tags_and_ingredients(ingredients, tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.clear()
        instance = super().update(instance, validated_data)
        AmountIngredient.objects.filter(recipe=instance).delete()
        self.create_tags_and_ingredients(ingredients, tags, instance)
        return instance

    def to_representation(self, instance):
        return RecipeGetSerializer(instance, context=self.context).data
