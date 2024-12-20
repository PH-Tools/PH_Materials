from typing import Iterable

from django import template
from django.core.paginator import Paginator

register = template.Library()


@register.filter
def pages_to_display(paginator: Paginator, current_page_num: int) -> Iterable[int]:
    if paginator.num_pages <= 5:
        return paginator.page_range
    else:
        if current_page_num < 3:
            return [*paginator.page_range[:4], paginator.num_pages]
        elif current_page_num > paginator.num_pages - 2:
            return [1, *paginator.page_range[-4:]]
        else:
            return [
                1,
                current_page_num - 1,
                current_page_num,
                current_page_num + 1,
                paginator.num_pages,
            ]
