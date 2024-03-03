from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()
LIMIT_POSTS_PER_PAGE = 15


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'first_name',
        'last_name',
        'username',
        'email',
    )
    list_editable = (
        'first_name',
        'last_name',
    )
    search_fields = (
        'username',
        'email',
    )
    list_filter = (
        'email',
        'username',
        'first_name',
    )
    list_display_links = (
        'username',
        'email',
    )
    list_per_page = LIMIT_POSTS_PER_PAGE
