import csv
import os

from django.core.management.base import BaseCommand, CommandError
from foodgram import settings


class ImportCsvCommand(BaseCommand):
    help = 'Базовые команды для загрузки данных из CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Путь до файла')

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Старт команды.'))
        try:
            with open(options['csv_file'], encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    self.process_row(row)
            self.stdout.write(self.style.SUCCESS('Данные загружены.'))
        except FileNotFoundError:
            raise CommandError(f'Файл не найден: {options["csv_file"]}')

    def process_row(self, row):
        raise NotImplementedError(
            'Подкласс должен реализовывать метод process_row'
        )
