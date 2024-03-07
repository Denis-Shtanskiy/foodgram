# Generated by Django 3.2.3 on 2024-03-07 08:48

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='cooking_time',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(limit_value=1, message='Даже чайнику нужно время закипеть! Укажите время'), django.core.validators.MaxValueValidator(limit_value=300, message='Вы готовите "хамон"?\nСлишком долго, проверьте время приготовления')], verbose_name='Время приготовления блюда'),
        ),
    ]
