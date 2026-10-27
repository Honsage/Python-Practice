"""Помощник постраничной пагинации для списков."""

from django.core.paginator import Paginator

PER_PAGE = 12


def paginate(request, queryset, per_page=PER_PAGE):
    """Возвращает объект страницы для текущего GET-параметра ?page=."""
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page"))
