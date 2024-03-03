from rest_framework import pagination


class LimitOnPagePagination(pagination.PageNumberPagination):
    """Кастомизированный стандартный пагинатор.
    Выводит запрощенное количество обьектов на страницу, максимум=50.
    """

    page_size_query_param = 'limit'
    max_page_size = 50
