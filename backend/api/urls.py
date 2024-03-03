from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CustomUserViewSet, IngredientsViewSet, RecipeViewSet,
                    TagViewSet)

app_name = 'api'

routerv_1 = DefaultRouter()
routerv_1.register('tags', TagViewSet, basename='tags')
routerv_1.register('ingredients', IngredientsViewSet, basename='ingredients')
routerv_1.register('recipes', RecipeViewSet, basename='recipes')
routerv_1.register('users', CustomUserViewSet, basename='users')


urlpatterns = [
    path('', include(routerv_1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
