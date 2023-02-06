import logging
from typing import Sequence, Union

from bs4 import BeautifulSoup

from .parser_base import _get_url_param_value, _validate_text_for_parsing

log = logging.getLogger(__name__)


def parse(text: str, name: str) -> Union[Sequence[str], None]:

    """Функция парсинга страницы с отчётами и получение UUID отчёта.

    Args:
        text: сырой текст страницы.
        name: уникальное название отчета.

    Returns:
        Union[Sequence[str], None]: Коллекцию с найденными элементами.

    Raises:

    """

    log.debug(f"Поиск отчета с именем: {name}")
    _validate_text_for_parsing(text)
    soup = BeautifulSoup(text, "html.parser")
    report_tag = soup.select(f'[title="{name}"]')
    if report_tag:
        log.debug(f"Отчет с именем {name} найден.")
        url = report_tag[0]["href"]
        return (str(_get_url_param_value(url, "uuid")),)
    log.debug(f"Отчет с именем {name} не найден.")
    return None
