import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Iterable, Mapping, Sequence
from urllib import parse

from bs4 import BeautifulSoup

from ..exceptions import CantGetData


log = logging.getLogger(__name__)


class PageType(Enum):

    """Класс данных для хранения типов страниц парсинга.

        Attributes:
            REPORT_LIST: Страница со списком сформированных отчётов.
            ISSUES_TABLE: Страница со списком обращений на группе.
            ISSUE_CARD: Страница карточки обращения.
            SERVICE_LEVEL_REPORT: Страница с отчётом service level.
            MMTR_LEVEL_REPORT: Страница с отчётом mttr level
            FLR_LEVEL_REPORT: Страница с отчётом flr level.
            SEARCH_RESULT_ISSUES_PAGE: Страница с результатом поиска обращений

    """
    REPORT_LIST_PAGE = 1
    ISSUES_TABLE_PAGE = 2
    ISSUE_CARD_PAGE = 3
    SERVICE_LEVEL_REPORT_PAGE = 4
    MMTR_LEVEL_REPORT_PAGE = 5
    FLR_LEVEL_REPORT_PAGE = 6
    SEARCH_RESULT_ISSUES_PAGE = 7


def _get_date_range(date_first: str, date_second: str) -> Sequence[datetime]:

    """Функция для создания коллекции чисел.

    Args:
        date_first: первая дата.
        date_second: вторая дата

    Returns:
        Sequence[datetime]: Коллекцию дат.

    Raises:

    """

    log.debug(f'Формирование списка дат между {date_first} и {date_second}')
    date_first = datetime.strptime(date_first, '%d.%m.%Y')
    date_second = datetime.strptime(date_second, '%d.%m.%Y')
    start_date = min(date_first, date_second)
    end_date = max(date_first, date_second)
    log.debug(f'Минимальная дата: {start_date}')
    log.debug(f'Максимальная дата: {end_date}')
    date_range = []
    while start_date < end_date:
        date_range.append(start_date)
        start_date += timedelta(days=1)
    return date_range


def _forming_days_dict(date_range: Sequence[datetime],
                       day_collection: Sequence,
                       report_type: PageType) -> Mapping:

    """Функция для преобразование сырых спаршенных данных к словарю с
    ключем по дню.

    Args:
        date_range (Sequence[datetime]): последовательность дней.
        day_collection (Sequence): сырые данные из CRM.

    Returns:
        Mapping: словарю с ключем по дню.
    """

    days = {}
    if report_type == PageType.FLR_LEVEL_REPORT_PAGE:

        for day in date_range:
            days[day.strftime("%d.%m.%Y")] = [
                _ for _ in day_collection
                if _['День'] == str(day.day)
                and _['Месяц'] == str(day.month)
            ]
        return days

    for day in date_range:
        days[day.day] = [
            _ for _ in day_collection if _['День'] == str(day.day)]
    return days


def _forming_days_collecion(data_table: Sequence, label: Sequence,
                            report_type: PageType) -> Sequence:

    """Функция для преобразование сырых данных bs4 в коллекцию словарей.

    Args:
        data_table: данных таблицы bs4.
        label: название столбцов таблицы.
        report_type: тип отчета
    Returns:
        Mapping: коллекцию словарей дней.
    """

    day_collection = list()
    for num, elem in enumerate(data_table):
        elem = [_.text.strip() for _ in elem.find_all('td')]

        if all(
            [
                report_type == PageType.SERVICE_LEVEL_REPORT_PAGE,
                not elem[0].isdigit(),
                ]):
            elem.insert(0, day_collection[num-1][0])

        elif all(
            [
                report_type == PageType.FLR_LEVEL_REPORT_PAGE,
                len(elem) < 5,
                ]):
            elem.insert(0, day_collection[num-1][0])

        day_collection.append(elem)
    day_collection = [dict(zip(label, day)) for day in day_collection]
    return day_collection


def _get_columns_name(soup: BeautifulSoup) -> Iterable[str]:

    """Функция парсинга названий столбцов отчётов.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        Коллекцию с названиями столбцов.

    Raises:

    """

    css_selector = ".supp tr th b"
    log.debug(f'Поиск столбцов таблицы по селектору: {css_selector}')
    column_name = [tag.text.strip() for tag in soup.select(css_selector)]
    if column_name:
        return tuple(column_name)
    log.error(f'Не удалось найти данные по селектору: {css_selector} в soup.')
    raise CantGetData


def _parse_date_report(soup: BeautifulSoup, name_start_date: str,
                       name_end_date: str) -> Iterable[str]:

    """Функция парсинга дат отчёта, со страницы отчёта.

    Args:
        soup: сырой текст страницы.
        name_start_date: название первой даты.
        name_end_date: название второй даты.

    Returns:
        Mapping: Выходной словарь параметров

    Raises:

    """

    log.debug("Парсинг параметров отчёта.")
    options_table = soup.find('table', id="stdViewpart0.legendTableList")

    if not options_table:
        log.error('BeautifulSoup нечего не нашел.')
        raise CantGetData

    options_tag = options_table.find_all('td', attrs={'style': 'width:100%;'})
    name_tag = options_table.find_all('td',
                                      attrs={'style': 'white-space:nowrap;'})
    name = [name.text.strip().replace(':', '') for name in name_tag]
    options = [option.text.strip() for option in options_tag]
    report_options = dict(zip(name, options))
    start_date = report_options.get(name_start_date, None)
    end_date = report_options.get(name_end_date, None)

    if not all([start_date, end_date]):
        raise CantGetData

    return start_date, end_date


def _get_url_param_value(url: str, needed_param: str) -> str:

    """Функция парсинга URL и получение значения необходимого GET параметра.

    Args:
        url: строчная ссылка.
        needed_param: ключ необходимого GET параметра.

    Returns:
        str: Значение необходимого GET параметра

    Raises:
        CantGetData: проблема с парсингом данных
    """

    log.debug(f'Получение параметра: {needed_param} из URL: {url}')
    if not url:
        log.error(f'Передан несуществующий URL: {url}')
        raise CantGetData
    param_value = parse.parse_qs(parse.urlparse(url).query)[needed_param][0]
    return param_value


def _validate_text_for_parsing(text: str) -> None:

    """Функция для валидации входного текста для парсинга:

    Args:
        text: исходный текст

    Raises:
        CantGetData: если текст не прошел проверки.

    Returns:

    """
    if not isinstance(text, str):
        log.error(f'BeautifulSoup не сможет распарсить {type(text)}')
        raise CantGetData

    if not text:
        log.error('Строка для парсинга пустая')
        raise CantGetData
