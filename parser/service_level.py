import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Mapping, Sequence

from bs4 import BeautifulSoup

from .parser_base import PageType, _get_columns_name, _get_date_range
from .parser_base import _forming_days_collecion, _forming_days_dict
from .parser_base import _parse_date_report
from ..exceptions import CantGetData


log = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class ServiceLevel:

    """Класс данных для хранения данных отчета Service Level.

        Attributes:
            day: день отсчёта.
            group: группа отчёта.
            total_issues: всего обращений.
            total_primary_issues: всего первичных обращений.
            num_issues_before_deadline: кол-во вовремя принятых обращений.
            num_issues_after_deadline: кол-во принятых после срока обращений.
            service_level: уровень servece level в процентах.
    """

    day: int
    group: str
    total_issues: int
    total_primary_issues: int
    num_issues_before_deadline: int
    num_issues_after_deadline: int
    service_level: float


def parse(text: str, *args, **kwargs) -> \
                                Sequence | Sequence[Literal['']]:

    """Функция парсинга картточки обращения.

    Args:
        text: сырой текст страницы.

    Returns:
        Sequence | Sequence[Literal['']]: Коллекцию с найденными элементами.

    Raises:
        CantGetData: Если не удалось найти данные.
    """

    support_group_count = 2
    log.debug('Запуск парсинг отчёта SL')
    soup = BeautifulSoup(text, "html.parser")
    start_date, end_date = _parse_date_report(
        soup, 'Дата перевода, с', 'Дата перевода, по')
    log.debug(f'Получены даты отчета с {start_date} по {end_date}')
    label = _get_columns_name(soup)
    log.debug(f'Получены названия столбцов {label}')
    data_table = soup.find('table', id='stdViewpart0.part0_TableList')
    data_table = data_table.find_all('tr')[3:-1]
    day_collection = _forming_days_collecion(
        data_table, label, PageType.SERVICE_LEVEL_REPORT_PAGE)
    date_range = _get_date_range(start_date, end_date)
    days = _forming_days_dict(
        date_range, day_collection, PageType.SERVICE_LEVEL_REPORT_PAGE)
    group = set([_['Группа'] for _ in day_collection])
    if len(group) != support_group_count:
        log.error(f'Количество групп ТП не равно {support_group_count}')
        raise CantGetData
    days = _service_lavel_data_completion(days, group, label)
    collection = _formating_service_level_data(days)
    log.debug(f'Парсинг завершился успешно. Колекция отчетов SL '
              f'с {start_date} по {end_date} содержит {len(collection)} элем.')
    return tuple(collection)


def _service_lavel_data_completion(days: dict, groups: Sequence,
                                   lable: Sequence) -> Mapping[int, Sequence]:

    """Функция для дополнения данных отчёта  Service Level.
        т.к Naumen отдает не все необходимые данные, необходимо их дополнить.
        Заполнить пропуски групп за прошедшие дни: SL будет 100%
        Заполнить пропуски за не наступившие дни: SL будет 0%

    Args:
        days: словарь дней, где ключ номер дня
        groups: название групп в crm Naumen
        lable: название категорий

    Returns:
        Mapping: дополненый словарь.
    """

    today = datetime.now().day
    for day, content in days.items():
        sl = '0.0'
        if today > day:
            sl = '100.0'
        if len(content) == 0:
            days[day] = [dict(
                zip(lable,
                    (str(day), group, '0', '0', '0', '0', sl)),
                ) for group in groups]
        elif len(content) != 2:
            day_groups = [_['Группа'] for _ in days[day]]
            for group in groups:
                if group not in day_groups:
                    days[day].append(
                        dict(
                            zip(lable,
                                (str(day), group, '0', '0', '0', '0', sl)),
                            ),
                        )
    return days


def _formating_service_level_data(days: Mapping[int, Sequence]) \
                                 -> Sequence[ServiceLevel]:

    """Формирование итоговой коллекции обьектов отчёта Service Level.

    Args:
        days: словарь дней, где ключ номер дня.

    Returns:
        Sequence[ServiceLevel]: коллекция с отчётами Service Level.
    """

    collection = []
    for day, group_data in days.items():
        day_collection = []
        gen_total_issues = 0
        gen_total_primary_issues = 0
        gen_num_issues_before_deadline = 0
        gen_num_issues_after_deadline = 0
        gen_service_level = 0.0
        for data in group_data:
            day = data['День']
            group = data['Группа']
            total_issues = int(data['Поступило в ТП'])
            total_primary_issues = int(data['Количество первичных'])
            num_issues_before_deadline = int(data['Принято за 15 минут'])
            num_issues_after_deadline = int(data['В очереди более 15 мин'])
            service_level = float(data['Service Level (%)'])
            gen_total_issues += total_issues
            gen_total_primary_issues += total_primary_issues
            gen_num_issues_before_deadline += num_issues_before_deadline
            gen_num_issues_after_deadline += num_issues_after_deadline
            gen_service_level += service_level
            sl = ServiceLevel(day, group, total_issues, total_primary_issues,
                              num_issues_before_deadline,
                              num_issues_after_deadline, service_level)
            day_collection.append(sl)
        group = 'Итог'
        sl = ServiceLevel(day, group, gen_total_issues,
                          gen_total_primary_issues,
                          gen_num_issues_before_deadline,
                          gen_num_issues_after_deadline, gen_service_level/2)
        day_collection.append(sl)
        collection.append(day_collection)
    return tuple(collection)
