import logging
from typing import Sequence

from bs4 import BeautifulSoup

from .parser_base import _get_url_param_value


log = logging.getLogger(__name__)


def parse(text: str, name: str) -> Sequence[str] | None:
    """Функция парсинга страницы с отчётами и получение UUID отчёта.

    Args:
        text: сырой текст страницы.
        name: уникальное название отчета.

    Returns:
        Sequence | Sequence[Literal['']]: Коллекцию с найденными элементами.

    Raises:

    """
    log.debug(f'Поиск отчета с именем: {name}')
    soup = BeautifulSoup(text, "html.parser")
    report_tag = soup.select(f'[title="{name}"]')
    if report_tag:
        log.debug(f'Отчет с именем {name} найден.')
        url = report_tag[0]['href']
        return (str(_get_url_param_value(url, 'uuid')), )
    log.debug(f'Отчет с именем {name} не найден.')
    return None
