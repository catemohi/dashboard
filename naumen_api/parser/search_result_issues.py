import logging
from dataclasses import dataclass
from typing import Literal, Mapping, Sequence

from bs4 import BeautifulSoup

from .parser_base import PageType, _get_columns_name, _get_date_range
from .parser_base import _forming_days_collecion, _forming_days_dict
from .parser_base import _parse_date_report
from .parser_base import _validate_text_for_parsing


log = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchIssuesResult:

    """Класс данных для хранения данных одного результата поиска по обращениям.

        Attributes:
            number: номер обращения
            uuid: уникальный идентификатор обьекта в CRM системе.
            name_contragent: источник обращения(контрагент)
            uuid_contragent: уникальный идентификатор контрагента в CRM системе 
            issue_type: тип обращения
            step: щаг обращения
            responsible: ответственный за последний шаг
            description: описание
            contact: контактное лицо

    """
    number: int = 0
    uuid: str = ''
    uuid_contragent: str = ''
    name_contragent: str = ''
    issue_type: str = ''
    step: str = ''
    responsible: str = ''
    description: str = ''
    contact: str = ''


def parse(text: str, *args, **kwargs) \
                        -> Sequence[SearchIssuesResult] or Sequence[Literal['']]:

    """Функция парсинга страницы с обращениями на группе.

    Args:
        text: сырой текст страницы.

    Returns:
        Sequence or Sequence[Literal['']]: Коллекцию с найденными элементами.

    Raises:
        CantGetData: Если не удалось найти данные.
    """
    _validate_text_for_parsing(text)
    soup = BeautifulSoup(text, "html.parser")
    category = _get_columns_name(soup)
    rows = soup.select(".supp tr")[4:]
    BeautifulSoup(text, "html.parser")
    print(category)
    print(rows)
    return tuple()