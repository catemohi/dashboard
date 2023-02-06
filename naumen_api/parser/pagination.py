import logging
from dataclasses import dataclass
from typing import Mapping, Sequence

from bs4 import BeautifulSoup

from .parser_base import _validate_text_for_parsing

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class PaginationPage:

    """Класс данных для хранения данных одного результата поиска по обращениям.

    Attributes:
        number: номер обращения
        url: ссылка на следующую страницу пагинации


    """

    number: int = 0
    url: str = ""


def parse(text: str, *args: Sequence, **kwargs: Mapping) -> int:

    """Функция парсинга пагинации страницы

    Args:
        text: сырой текст страницы.

    Returns:
        int: Количество страниц пагинации

    Raises:
        CantGetData: Если не удалось найти данные.
    """

    _validate_text_for_parsing(text)
    soup = BeautifulSoup(text, "html.parser")
    i = 1
    raw_page_collection = []
    while i > 0:
        page = soup.find(attrs={"id": f"advSearchTab.searchResults_page{i}"})
        if page:
            raw_page_collection.append(page)
            i += 1
        else:
            i = -1
    return len(raw_page_collection)
