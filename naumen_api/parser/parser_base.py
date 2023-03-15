import logging
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Sequence, Union
from urllib import parse

from bs4 import BeautifulSoup

from ..config.structures import PageType
from ..exceptions import CantGetData

log = logging.getLogger(__name__)


def _get_date_range(
    date_first: Union[str, datetime],
    date_second: Union[str, datetime],
) -> Sequence[datetime]:

    """Функция для создания коллекции чисел.

    Args:
        date_first (Union[str, datetime]): первая дата.
        date_second (Union[str, datetime]): вторая дата

    Returns:
        Sequence[datetime]: Коллекцию дат.

    Raises:

    """

    log.debug(f"Формирование списка дат между {date_first} и {date_second}")
    if isinstance(date_first, str):
        date_first = datetime.strptime(date_first, "%d.%m.%Y")
    if isinstance(date_second, str):
        date_second = datetime.strptime(date_second, "%d.%m.%Y")
    start_date = min(date_first, date_second)
    end_date = max(date_first, date_second)
    log.debug(f"Минимальная дата: {start_date}")
    log.debug(f"Максимальная дата: {end_date}")
    date_range = []
    while start_date < end_date:
        date_range.append(start_date)
        start_date += timedelta(days=1)
    return date_range


def _forming_days_dict(
    date_range: Sequence[datetime],
    day_collection: Sequence,
    report_type: PageType,
) -> Dict:

    """Функция для преобразование сырых спаршенных данных к словарю с
    ключем по дню.

    Args:
        date_range (Sequence[datetime]): последовательность дней.
        day_collection (Sequence): сырые данные из CRM.

    Returns:
        Mapping: словарю с ключем по дню.
    """

    days: Dict = {}
    if (
        report_type == PageType.FLR_LEVEL_REPORT_PAGE
        or report_type == PageType.AHT_LEVEL_REPORT_PAGE
    ):

        for day in date_range:
            days[day.strftime("%d.%m.%Y")] = [
                _
                for _ in day_collection
                if _["День"] == str(day.day) and _["Месяц"] == str(day.month)
            ]
        return days

    for day in date_range:
        days[str(day.day)] = [_ for _ in day_collection if _["День"] == str(day.day)]
    return days


def _forming_days_collecion(
    data_table: Sequence,
    label: Sequence,
    report_type: PageType,
) -> Sequence:

    """Функция для преобразование сырых данных bs4 в коллекцию словарей.

    Args:
        data_table: данных таблицы bs4.
        label: название столбцов таблицы.
        report_type: тип отчета
    Returns:
        Mapping: коллекцию словарей дней.
    """

    day_collection: List = list()
    for num, elem in enumerate(data_table):
        elem = [_.text.strip() for _ in elem.find_all("td")]

        if all(
            [
                report_type == PageType.SERVICE_LEVEL_REPORT_PAGE,
                not elem[0].isdigit(),
            ],
        ):
            elem.insert(0, day_collection[num - 1][0])

        elif all(
            [
                report_type == PageType.FLR_LEVEL_REPORT_PAGE,
                len(elem) < 5,
            ],
        ):
            elem.insert(0, day_collection[num - 1][0])
        day_collection.append(elem)
    day_collection = [dict(zip(label, day)) for day in day_collection]
    return day_collection


def _get_columns_name(soup: BeautifulSoup) -> Sequence[str]:

    """Функция парсинга названий столбцов отчётов.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        Коллекцию с названиями столбцов.

    Raises:

    """

    css_selector = ".supp tr th b"
    log.debug(f"Поиск столбцов таблицы по селектору: {css_selector}")
    column_name = [tag.text.strip() for tag in soup.select(css_selector)]
    if column_name:
        return tuple(column_name)
    log.error(f"Не удалось найти данные по селектору: {css_selector} в soup.")
    raise CantGetData


def _parse_date_report(
    soup: BeautifulSoup,
    name_start_date: str,
    name_end_date: str,
) -> Iterable[str]:

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
    options_table = soup.find("table", id="stdViewpart0.legendTableList")
    report_options = {}
    if not options_table:
        log.error("BeautifulSoup нечего не нашел.")
        raise CantGetData
    options_row = options_table.find_all("tr")
    log.debug("Options row: %s", options_row)
    for row in options_row:
        td_tags = row.find_all("td")
        td_content = [td.text.strip().replace(":", "") for td in td_tags]
        log.debug("Options td: %s", td_content)
        if len(td_content) == 2:
            report_options[td_content[0]] = td_content[1]
    log.debug("Report options: %s", report_options)
    start_date = report_options.get(name_start_date, None)
    log.debug("Start date: %s", start_date)
    end_date = report_options.get(name_end_date, None)
    log.debug("End date: %s", end_date)
    if all([start_date, end_date]):
        return start_date, end_date

    # options_tag = options_table.find_all("td", attrs={"style": "width:100%;"})
    # name_tag = options_table.find_all("td", attrs={"style": "white-space:nowrap;"})
    # name = [name.text.strip().replace(":", "") for name in name_tag]
    # log.debug("Names: %s", name)
    # options = [option.text.strip() for option in options_tag]
    # log.debug("Options: %s", options)
    # report_options = dict(zip(name, options))
    # log.debug("Report options: %s", report_options)
    # start_date = report_options.get(name_start_date, None)
    # log.debug("Start date: %s", start_date)
    # end_date = report_options.get(name_end_date, None)
    # log.debug("End date: %s", end_date)

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

    log.debug(f"Получение параметра: {needed_param} из URL: {url}")
    if not url:
        log.error(f"Передан несуществующий URL: {url}")
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
        log.error(f"BeautifulSoup не сможет распарсить {type(text)}")
        raise CantGetData

    if not text:
        log.error("Строка для парсинга пустая")
        raise CantGetData
