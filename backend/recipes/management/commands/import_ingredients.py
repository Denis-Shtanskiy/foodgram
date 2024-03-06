from recipes.management.commands.base_command import ImportCsvCommand
from recipes.models import Ingredient


class Command(ImportCsvCommand):
    help = 'Импорт ингредиентов из файла CSV.'

    def process_row(self, row):
        Ingredient.objects.get_or_create(
            name=row['абрикосовое варенье'], measurement_unit=row['г']
        )
