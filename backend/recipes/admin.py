from django.contrib import admin

from .models import AmountIngredient, Ingredient, Recipe, Tag

admin.site.empty_value_display = 'Не задано'
admin.site.site_header = 'Администрирование проекта "Foodgram"'
admin.site.site_title = 'Портал администраторов "Foodgram"'
admin.site.index_title = 'Добро пожаловать, на самый вкусный сайт'

LIMIT_POSTS_PER_PAGE = 15


class AmountInline(admin.TabularInline):
    model = AmountIngredient
    extra = 3


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (AmountInline,)
    list_display = (
        'name',
        'get_full_name',
        'pub_date',
        'get_favorite_count',
    )
    fields = (
        (
            'name',
            'cooking_time',
        ),
        ('text',),
        (
            'author',
            'tags',
        ),
        ('image',),
    )
    search_fields = (
        'name',
        'author',
        'tags__name',
    )
    list_filter = (
        'name',
        'author',
        'tags',
    )
    filter_horizontal = (
        'ingredients',
        'tags',
    )
    list_per_page = LIMIT_POSTS_PER_PAGE

    def get_favorite_count(self, obj):
        return obj.favorite.count()

    get_favorite_count.short_description = 'Добавлен в избранное'

    def get_full_name(self, obj):
        return obj.author.first_name + ' ' + obj.author.last_name

    get_full_name.short_description = 'Имя пользователя'
    get_full_name.admin_order_field = 'author__first_name'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    inlines = (AmountInline,)
    list_display = (
        'name',
        'measurement_unit',
    )
    list_filter = ('name',)
    search_fields = ('name',)
    list_editable = ('measurement_unit',)
    list_per_page = LIMIT_POSTS_PER_PAGE


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'color',
        'slug',
    )
    list_filter = ('name',)
    search_fields = (
        'name',
        'slug',
    )
    list_editable = (
        'color',
        'slug',
    )
