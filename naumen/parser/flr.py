import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Mapping, Sequence

from bs4 import BeautifulSoup

from .parser_base import PageType,  _get_columns_name, _get_date_range
from .parser_base import _forming_days_collecion, _forming_days_dict
from .parser_base import _parse_date_report


log = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class Flr:

    """Класс данных для хранения данных отчета FLR.

        Attributes:
            date: дата отсчёта.
            flr_level: уровень flr level в процентах.
            num_issues_closed_independently: Обращения закрытые самостоятельно.
            total_primary_issues: всего первичных обращений.

    """
    date: str
    flr_level: float
    num_issues_closed_independently: int
    total_primary_issues: int


def parse(text: str, *args, **kwargs) -> \
                            Sequence | Sequence[Literal['']]:
    """Функция парсинга карточки обращения.

    Args:
        text: сырой текст страницы.

    Returns:
        Sequence | Sequence[Literal['']]: Коллекцию с найденными элементами.

    Raises:
        CantGetData: Если не удалось найти данные.
    """
    log.debug('Запуск парсинг отчёта FLR')
    soup = BeautifulSoup(text, "html.parser")
    first_day, last_day = _parse_date_report(
        soup, 'Дата перевода, с', 'Дата перевода, по')
    log.debug(f'Получены даты отчета с {first_day} по {last_day}')
    label = _get_columns_name(soup)
    log.debug(f'Получены названия столбцов {label}')
    data_table = soup.find('table', id='stdViewpart0.part0_TableList')
    data_table = data_table.find_all('tr')[3:-1]
    day_collection = _forming_days_collecion(
        data_table, label, PageType.FLR_LEVEL_REPORT_PAGE)
    date_range = _get_date_range(first_day, last_day)
    days = _forming_days_dict(
        date_range, day_collection, PageType.FLR_LEVEL_REPORT_PAGE)
    days = _flr_data_completion(days, label)
    collection = _formating_flr_data(days)
    log.debug(f'Парсинг завершился успешно. Колекция отчетов FLR '
              f'с {first_day} по {last_day} содержит {len(collection)} элем.')
    return collection


def _flr_data_completion(days: dict, lable: Sequence) -> \
                          Mapping[int, Sequence]:
    """Функция для дополнения данных отчёта FLR.
        т.к Naumen отдает не все необходимые данные, необходимо их дополнить.
        Заполнить пропуски за не наступившие дни:FLR будет 0%

    Args:
        days: словарь дней, где ключ номер дня
        lable: название категорий

    Returns:
        Mapping: дополненый словарь.
    """
    flr_level = '0'
    num_issues_closed_independently = '0'
    total_primary_issues = '0'
    for day, content in days.items():
        if len(content) == 0:
            obj_day = datetime.strptime(day, '%d.%m.%Y')
            days[day] = [
                dict(zip(
                    lable,
                    (str(obj_day.month),
                     str(obj_day.day),
                     flr_level,
                     num_issues_closed_independently,
                     total_primary_issues),
                    )),
                ]
    return days


def _formating_flr_data(days: Mapping[int, Sequence]) \
                                 -> Sequence[Flr]:
    collection = []
    for day, day_content in days.items():
        day_content = day_content[0]
        date = day
        flr_level = day_content['FLR по дн (в %)']
        num_issues_closed_independently = day_content['Закрыто ТП без др отд']
        total_primary_issues = day_content['Количество первичных']
        flr = Flr(
            date, flr_level,
            num_issues_closed_independently,
            total_primary_issues,
            )
        collection.append(flr)

    return collection
