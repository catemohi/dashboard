import logging
from dataclasses import dataclass
from typing import Literal, Mapping, Sequence

from bs4 import BeautifulSoup

from .parser_base import PageType, _get_columns_name, _get_date_range
from .parser_base import _forming_days_collecion, _forming_days_dict
from .parser_base import _parse_date_report
from .parser_base import _get_url_param_value
from .parser_base import _validate_text_for_parsing


log = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchIssueResult:

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
    uuid_responsible: str = ''
    name_responsible: str = ''
    description: str = ''
    contact: str = ''


def parse(text: str, *args, **kwargs) \
          -> Sequence[SearchIssueResult] or Sequence[Literal['']]:

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
    collection = _parse_result_table(soup, category)
    return collection


def _parse_result_table(soup: BeautifulSoup,
                        category: Sequence[str]
                        ) -> Sequence[SearchIssueResult]:
    """Функция парсинга таблицы с результатами поиска.

    Args:
        soup (BeautifulSoup): обьект для парсинка.
        category (Sequence[str]): наименования столбцов результотов поиска

    Returns:
        Sequence or Sequence[SearchIssueResult]: Коллекцию с найденными элемен.

    Raises:

    """
    collection = []
    result_table = soup.find(name='table', attrs={
        'id': 'advSearchTab.searchResults'})

    if not result_table:
        return tuple(collection)

    tr_tag_collection = result_table.find_all(name='tr')[1:]

    for tr in tr_tag_collection:
        tr_dict = dict(zip(category, tr.find_all(name='td')))
        _url = tr_dict['Номер обращения'].find('a', href=True)
        if _url is not None:
            _url = _url.get('href')
            uuid = _get_url_param_value(_url, 'uuid')
        else:
            uuid = ''
        number = tr_dict['Номер обращения'].find('a').text
        _url = tr_dict['Источник обращения'].find('a', href=True)
        if _url is not None:
            _url = _url.get('href')
            uuid_contragent = _get_url_param_value(_url, 'uuid')
        else:
            uuid_contragent = ''
        name_contragent = tr_dict['Источник обращения'].find('a').text
        issue_type = ' '.join(list(tr_dict['Тип обращения'].stripped_strings))
        step = ' '.join(list(tr_dict['Статус'].stripped_strings))
        _url = tr_dict['Ответственный'].find('a', href=True)
        if _url is not None:
            _url = _url.get('href')
            uuid_responsible = _get_url_param_value(_url, 'uuid')
        else:
            uuid_responsible = ''
        name_responsible = tr_dict['Ответственный'].find('a')
        if name_responsible is not None:
            name_responsible = ' '.join(list(
                name_responsible.stripped_strings))
        else:
            name_responsible = ''
        description = ' '.join(list(tr_dict['Описание'].stripped_strings))
        contact = tr_dict['Контактное лицо'].text.replace('\n', '').strip()
        search_issue_result = SearchIssueResult(number, uuid, uuid_contragent,
                                                name_contragent, issue_type,
                                                step, uuid_responsible,
                                                name_responsible, description,
                                                contact)
        collection.append(search_issue_result)

    return collection
