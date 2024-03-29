from http.client import BAD_REQUEST, CREATED, NO_CONTENT
from io import BytesIO

from django.contrib.auth import get_user_model
from django.db.models import Q, Sum
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
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, pk=id)
        if request.method == 'POST':
            if user == author:
                return Response('Нельзя самоподписаться!', status=BAD_REQUEST)
            if Follow.objects.filter(
                user=user,
                author=author,
            ).exists():
                return Response('Такая подписка уже есть!', status=BAD_REQUEST)
            Follow.objects.create(
                user=user,
                author=author,
            )
            serializer = UserFollowSerializer(
                author,
                context={'request': request},
            )
            return Response(serializer.data, status=CREATED)

        subscribe = Follow.objects.filter(author=author, user=user)
        if subscribe.exists():
            subscribe.delete()
            return Response('Вы отписаны!', status=NO_CONTENT)
        return Response(
            'Нельзя отписаться, если вы ещё не подписаны!', status=BAD_REQUEST
        )

    @decorators.action(
        detail=False,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscriptions(self, request, pk=None):
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
        relation = model.objects.filter(user=user, recipe=recipe)
        if relation.exists():
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
            return self.add_recipe(Favorite, request.user, pk, 'избранное')
        return self.delete_recipe(Favorite, request.user, pk, 'избранного')

    @decorators.action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return self.add_recipe(
                ShoppingCarts, request.user, pk, 'список покупок'
            )
        return self.delete_recipe(
            ShoppingCarts, request.user, pk, 'списка покупок'
        )

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
        file = '_shopping_list'

        ingredients = (
            AmountIngredient.objects.annotate(
                sum_amount=Sum('ingredient__amount_ingredient__amount')
            )
            .values(
                'ingredient__name',
                'ingredient__measurement_unit',
                'sum_amount',
            )
            .filter(recipe__carts_in__user=request.user)
        )
        page.setFont('DejaVuSerif-Bold', 13)
        page.drawString(
            X_PCM_PDF,
            Y_PCM_PDF,
            'Список продуктов, который Вам потребуется:',
        )
        y_for_string = 750
        for number, ingredient in enumerate(ingredients, start=1):
            page.setFont('DejaVuSerif', 10)
            ingredients_list = (
                f'{number}. {ingredient["ingredient__name"]}: '
                f'{ingredient["sum_amount"]} '
                f'{ingredient["ingredient__measurement_unit"]};'
            )
            page.drawString(
                X_PCM_PDF,
                y_for_string,
                ingredients_list,
            )
            y_for_string -= 20
            if y_for_string <= 50:
                page.showPage()
                y_for_string = 800
        page.save()
        buffer.seek(0)

        response = FileResponse(
            buffer,
            as_attachment=True,
            filename=f'{request.user.username}_{file}.pdf',
        )
        return response
