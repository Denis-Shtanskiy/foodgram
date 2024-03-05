from http.client import BAD_REQUEST, CREATED, NO_CONTENT
from io import BytesIO

from django.contrib.auth import get_user_model
from django.db.models import F, Q, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import decorators, permissions, viewsets
from rest_framework.response import Response

from recipes.models import (AmountIngredient, Favorite, Ingredient, Recipe,
                            ShoppingCarts, Tag)
from users.models import Follow

from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitOnPagePagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (FoodgramUserSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeGetSerializer,
                          RecipesForFavoriteCartFollowedSerializer,
                          TagSerializer, UserFollowSerializer)

User = get_user_model()
X_PCM_PDF = 100
Y_PCM_PDF = 800


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = FoodgramUserSerializer
    pagination_class = LimitOnPagePagination

    def get_permissions(self):
        if self.action == 'me':
            return (permissions.IsAuthenticated(),)
        return super().get_permissions()

    @decorators.action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscribe(self, request, pk):
        if request.method == 'POST':
            user = request.user
            author = get_object_or_404(User, id=pk)
            if user == author:
                message = 'Нельзя самоподписаться!'
                return Response(message, status=BAD_REQUEST)
            if Follow.objects.filter(
                user=user,
                author=author,
            ).exists():
                message = 'Такая подписка уже есть!'
                return Response(message, status=BAD_REQUEST)
            Follow.objects.create(
                user=user,
                author=author,
            )
            serializer = UserFollowSerializer(
                author,
                context={'request': request},
            )
            return Response(serializer.data, status=CREATED)

        if request.method == 'DELETE':
            user = request.user
            author = get_object_or_404(User, id=id)
            subscribe = Follow.objects.filter(author=author, user=user)
            if subscribe:
                subscribe.delete()
                message = {'Вы отписаны!'}
                return Response(message, status=NO_CONTENT)
            message = {'Нельзя отписаться, если вы ещё не подписаны!'}
            return Response(message, status=BAD_REQUEST)

    @decorators.action(
        detail=False,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscriptions(self, request, id):
        user = request.user
        queryset = self.filter_queryset(
            User.objects.filter(following__user=user)
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserFollowSerializer(
                page,
                many=True,
                context={'request': request},
            )
            return self.get_paginated_response(serializer.data)
        serializer = UserFollowSerializer(queryset, many=True)
        return Response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = None


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filteset_class = IngredientFilter

    def get_queryset(self):
        name = self.request.query_params.get('name')
        if not name:
            return Ingredient.objects.all()
        return Ingredient.objects.filter(
            Q(name__istartswith=name)
            | (Q(name__icontains=name) & ~Q(name__istartswith=name))
        )


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related('author').all()
    pagination_class = LimitOnPagePagination
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeGetSerializer
        return RecipeCreateSerializer

    def add_recipe(self, model, user, pk, message):
        recipe = get_object_or_404(Recipe, id=pk)
        if not recipe:
            message = 'Такого рецепта не существет!'
            return Response(message, status=BAD_REQUEST)
        relation = model.objects.filter(user=user, recipe=recipe)
        if relation.exists():
            print(relation)
            return Response(
                {f'Нельзя повторно добавить рецепт в {message}'},
                status=BAD_REQUEST,
            )
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipesForFavoriteCartFollowedSerializer(recipe)
        return Response(serializer.data, status=CREATED)

    def delete_recipe(self, model, user, pk, message):
        recipe = get_object_or_404(Recipe, pk=pk)
        relation = model.objects.filter(user=user, recipe=recipe)
        if not relation.exists():
            return Response(
                {f'Нельзя повторно удалить рецепт из {message}'},
                status=BAD_REQUEST,
            )
        relation.delete()
        return Response(status=NO_CONTENT)

    @decorators.action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def favorite(self, request, pk):
        if request.method == 'POST':
            message = 'избранное'
            return self.add_recipe(Favorite, request.user, pk, message)
        if request.method == 'DELETE':
            message = 'избранного'
            return self.delete_recipe(Favorite, request.user, pk, message)

    @decorators.action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            message = 'список покпок'
            return self.add_recipe(ShoppingCarts, request.user, pk, message)
        if request.method == 'DELETE':
            message = 'списка покупок'
            return self.delete_recipe(ShoppingCarts, request.user, pk, message)

    @decorators.action(
        detail=False,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        buffer = BytesIO()
        page = canvas.Canvas(buffer)
        pdfmetrics.registerFont(
            TTFont(
                'DejaVuSerif',
                'DejaVuSerif.ttf',
                'UTF-8',
            )
        )
        pdfmetrics.registerFont(
            TTFont(
                'DejaVuSerif-Bold',
                'DejaVuSerif-Bold.ttf',
                'UTF-8',
            )
        )
        user = request.user
        file = f'{user.username}_shopping_list.pdf'

        ingredients = (
            AmountIngredient.objects.filter(recipe__carts_in_recipe__user=user)
            .values(
                ingredient_item=F('ingredient__name'),
                unit=F('ingredient__measurement_unit'),
            )
            .annotate(amount=Sum('amount'))
        )

        page.setFont('DejaVuSerif-Bold', 13)
        page.drawString(
            X_PCM_PDF,
            Y_PCM_PDF,
            'Список продуктов, который Вам нужно приобрести:',
        )
        y_for_string = 750
        page.setFont('DejaVuSerif', 10)
        for number, ingredient in enumerate(ingredients, start=1):
            ingredient_list = (
                f'{number}. {ingredient["ingredient_item"]}: '
                f'{ingredient["amount"]}, {ingredient["unit"]};'
            )
            page.drawString(
                X_PCM_PDF,
                y_for_string,
                ingredient_list,
            )
            y_for_string -= 20
        page.showPage()
        page.save()
        buffer.seek(0)

        response = FileResponse(buffer, as_attachment=True, filename=file)
        return response
