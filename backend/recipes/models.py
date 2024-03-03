from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

MAX_LENGTH_CHARFIELD = 200
MAX_LENGTH_FOR_HEX = 7
User = get_user_model()


class Tag(models.Model):
    """Модель тегов для рецептов."""

    name = models.CharField(
        verbose_name='Название тега',
        max_length=MAX_LENGTH_CHARFIELD,
        unique=True,
    )
    color = ColorField(
        verbose_name='Цвет тега в hex-формате',
        max_length=MAX_LENGTH_FOR_HEX,
        default='#000000',
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        max_length=MAX_LENGTH_CHARFIELD,
        unique=True,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингридиентов для рецептов."""

    name = models.CharField(
        verbose_name='Ингридиент',
        max_length=MAX_LENGTH_CHARFIELD,
    )
    measurement_unit = models.CharField(
        verbose_name='Единицы измерения',
        max_length=MAX_LENGTH_CHARFIELD,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        constraints = [
            UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_unit_for_ingredient',
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецептов."""

    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH_CHARFIELD,
    )
    author = models.ForeignKey(
        verbose_name='Автор рецепта',
        to=User,
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    image = models.ImageField(
        verbose_name='Фото блюда',
        upload_to='recipes/',
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
    )
    ingredients = models.ManyToManyField(
        verbose_name='Ингридиенты',
        to=Ingredient,
        through='AmountIngredient',
        related_name='recipes',
    )
    tags = models.ManyToManyField(
        verbose_name='Тег',
        to=Tag,
        related_name='recipes',
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления блюда',
        default=5,
        validators=[
            MinValueValidator(
                limit_value=1,
                message='Даже чайнику нужно время закипеть! Укажите время',
            ),
            MaxValueValidator(
                limit_value=300,
                message='Вы готовите "хамон"?\n'
                'Слишком долго, проверьте время приготовления',
            ),
        ],
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата создания рецепта',
        auto_now_add=True,
        editable=False,
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.pub_date} {self.author} добавил рецепт {self.name}'


class AmountIngredient(models.Model):
    """Модель количества ингридиентов в рецепте."""

    recipe = models.ForeignKey(
        verbose_name='Количество ингридиента в рецепте',
        to=Recipe,
        on_delete=models.CASCADE,
        related_name='amount_recipe',
    )
    ingredient = models.ForeignKey(
        verbose_name='Продукты, которые понадобятся',
        to=Ingredient,
        on_delete=models.CASCADE,
        related_name='amount_ingredient',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество продукта',
        default=1,
        validators=[
            MinValueValidator(
                limit_value=1,
                message='Из ничего приготовить невозможно! Добавьте значение',
            ),
        ],
    )

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Количество ингридиента'
        verbose_name_plural = 'Количество ингридиентов'

    def __str__(self):
        return f' {self.amount} {self.ingredient} в {self.recipe}'


class Favorite(models.Model):
    """Модель добавления понравившегося рецепта в избранное."""

    user = models.ForeignKey(
        verbose_name='Пользователь',
        to=User,
        on_delete=models.CASCADE,
        related_name='favorite',
    )
    recipe = models.ForeignKey(
        verbose_name='Понравившиеся рецепты',
        to=Recipe,
        on_delete=models.CASCADE,
        related_name='favorite',
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_recipe_for_favorites',
            )
        ]

    def __str__(self):
        return f'{self.user} понравился {self.recipe}'


class ShoppingCarts(models.Model):
    """Модель списка покупок из понравившихся рецептов."""

    user = models.ForeignKey(
        verbose_name='Пользователь',
        to=User,
        on_delete=models.CASCADE,
        related_name='carts',
    )
    recipe = models.ForeignKey(
        verbose_name='Понравившиеся рецепты',
        to=Recipe,
        on_delete=models.CASCADE,
        related_name='carts',
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_recipe_for_carts',
            )
        ]

    def __str__(self):
        return f'{self.user} добавил в список покупок {self.recipe}'
