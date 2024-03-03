from django.core.exceptions import ValidationError


def validate_username(username):
    if username.lower() == 'me':
        raise ValidationError('Выберите другое имя пользователя')
    return username
