import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from re import findall
from typing import Callable, Iterable, Literal, Mapping, Sequence
from urllib import parse


from bs4 import BeautifulSoup, element

from .exceptions import CantGetData


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

    """
    REPORT_LIST_PAGE = 1
    ISSUES_TABLE_PAGE = 2
    ISSUE_CARD_PAGE = 3
    SERVICE_LEVEL_REPORT_PAGE = 4
    MMTR_LEVEL_REPORT_PAGE = 5
    FLR_LEVEL_REPORT_PAGE = 6


@dataclass
class Issue:

    """Класс данных для хранения данных по обращению.

        Attributes:
            uuid: уникалный идентификатор обьекта в CRM системе.
            number: номер обращения.
            name: название обращения.
            issue_type: тип обращения
            step: шаг на котром находится обращение.
            step_time: время последнего шага .
            responsible: ответственный за последний шаг.
            last_edit_time: время последнего изменения.
            vip_contragent: имеет ли клиент статус vip.
            creation_date: дата создания обращения.
            uuid_service: уникалный идентификатор обьекта в CRM системе.
            name_service: название услуги.
            uuid_contragent: уникалный идентификатор обьекта в CRM системе.
            name_contragent: название контр агента.
            return_to_work_time: время возврата обращения в работу.
            description: описание обращения.
    """
    uuid: str = ''
    number: int = 0
    name: str = ''
    issue_type: str = ''
    step: str = ''
    step_time: timedelta = timedelta(0, 0)
    responsible: str = ''
    last_edit_time: datetime = datetime.now()
    vip_contragent: bool = False
    creation_date: datetime = datetime.now()
    uuid_service: str = ''
    name_service: str = ''
    uuid_contragent: str = ''
    name_contragent: str = ''
    return_to_work_time: datetime = datetime.now()
    description: str = ''


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


@dataclass(slots=True, frozen=True)
class Mttr:

    """Класс данных для хранения данных отчета MTTR.

        Attributes:
            day: день отсчёта.
            total_issues: всего обращений.
            average_mttr: cредний МТТР.
            average_mttr_tech_support: cредний МТТР тех.поддержки.

    """
    day: int
    total_issues: int
    average_mttr: float
    average_mttr_tech_support: float


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


def parse_naumen_page(page: str, name_report: str,
                      type_page: PageType) -> Sequence:
    """Функция парсинга страниц из crm Naumen, входной интерфейс подмодуля.

    Args:
        page: страница которую требуется распарсить.
        type_page: тип страницы
        name_report: уникальное имя сформированное отчёта.

    Returns:
        Sequence: Результат парсинга страницы, коллекция распаршенных элементов

    Raises:
        CantGetData: в неправильном сценарии работы функции.

    """
    log.debug('Запущена функция парсинга страницы.'
              f'Имя необходимого отчета: {name_report}.'
              f'Тип отчёта: {type_page}')
    if not isinstance(type_page, PageType):
        log.error(f'Не зарегистрированный тип страницы: {type_page}')
        raise CantGetData

    page_parsers: Mapping[PageType, Callable] = {
        PageType.REPORT_LIST_PAGE: _parse_reports_lits,
        PageType.ISSUES_TABLE_PAGE: _parse_issues_table,
        PageType.ISSUE_CARD_PAGE: _parse_card_issue,
        PageType.SERVICE_LEVEL_REPORT_PAGE: _parse_service_lavel_report,
        PageType.MMTR_LEVEL_REPORT_PAGE: _parse_mttr_lavel_report,
        PageType.FLR_LEVEL_REPORT_PAGE: _parse_flr_lavel_report,
    }

    parser = page_parsers[type_page]
    log.debug(f'Получен парсер: {parser.__name__} для страницы: {type_page}')
    parsed_collections = parser(page, name_report)
    return parsed_collections


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


def _get_step_duration(raw_duration: str) -> timedelta:
    """Функция для парсинга строки продолжительности в обьект timedelta.

    Args:
        raw_duration: строчная задержка.

    Returns:
        Объект задержки шага.

    Raises:

    """
    duration = dict(zip(('days', 'h', 'min'), findall(r'\d+', raw_duration)))
    duration = timedelta(days=int(duration['days']),
                         hours=int(duration['h']),
                         minutes=int(duration['min']))
    return duration


def _get_issue_num(issue_name: str) -> str:
    """Функция для парсинга номера обращения.

    Args:
        issue_name: имя обращения.

    Returns:
        Номер обращения.

    Raises:

    """
    number = findall(r'\d{7,10}', issue_name)[0]
    return number


def _parse_reports_lits(text: str, name: str) -> Sequence[str] | None:
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


def _parse_issues_table(text: str, *args, **kwargs) \
                        -> Sequence[Issue] | Sequence[Literal['']]:
    """Функция парсинга страницы с обращениями на группе.

    Args:
        text: сырой текст страницы.

    Returns:
        Sequence | Sequence[Literal['']]: Коллекцию с найденными элементами.

    Raises:
        CantGetData: Если не удалось найти данные.
    """
    soup = BeautifulSoup(text, "html.parser")
    category = _get_columns_name(soup)
    rows = soup.select(".supp tr")[7:-1]
    if len(rows) < 1:
        return ('',)
    def parse_table_row(row: element.Tag,
                        category: Iterable[str]) -> Issue:
        """Функция парсинга строки таблицы.

        Args:
            row: сырая строка.
            category: названия столбцов, строки.

        Returns:
            Sequence[Issue] | Sequence[Literal['']: Коллекцию обращений.

        """
        issue = Issue()
        issus_params = [
            col.text.replace('\n', '').strip() for col in row.select('td')]
        issues_dict = dict(zip(category, issus_params))
        _url = (row.find('a', href=True)['href'])
        issue.uuid = _get_url_param_value(_url, 'uuid')
        issue.number = _get_issue_num(issues_dict['Обращение'])
        issue.step_time = _get_step_duration(issues_dict['Время решения'])
        issue.last_edit_time = datetime.now() - issue.step_time
        issue.name = issues_dict['Обращение']
        issue.issue_type = issues_dict['Тип обращения']
        issue.step = issues_dict['Состояние']
        issue.responsible = issues_dict['Ответственный']
        return issue
    issues = [parse_table_row(row, category) for row in rows]
    return issues


def _get_contragent_params(soup: BeautifulSoup) -> Iterable[str]:
    """Функция парсинга данных контрагента.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        Iterable[str]: Коллекцию с параметрами контрагента.

    Raises:

    """
    contragent_tag = soup.find('td', id='contragent')
    if contragent_tag:
        name = contragent_tag.text.replace('\n', '').strip()
        _url = contragent_tag.find('a')['href']
        try:
            uuid = _get_url_param_value(_url, 'uuid')
        except CantGetData:
            uuid = ''
        return (name, uuid)
    return ('', '')


def _get_description(soup: BeautifulSoup) -> str:
    """Функция парсинга данных описания обращения.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        str: Описание обращения.

    Raises:

    """
    description = soup.find('td', id="requestDescription")
    if description:
        description = description\
                                .text\
                                .replace('\r', '')\
                                .replace('\t', '')\
                                .replace('\n', '')\
                                .strip()
        if len(description) > 140:
            description = description[:137] + '...'
        return description
    return ''


def _get_creation_date(soup: BeautifulSoup) -> datetime:
    """Функция парсинга даты создания обращения.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        datetime: дата создания обращения.

    Raises:

    """
    creation_date = soup.find('td', id="creationDate")
    if creation_date:
        str_datetime = creation_date.text.replace('\n', '').strip()
        return datetime.strptime(str_datetime, '%d.%m.%Y %H:%M')
    return datetime.now()


def _get_service_params(soup: BeautifulSoup) -> Iterable[str]:
    """Функция парсинга данных услуги.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        Iterable[str]: коллекцию с параметрами.

    Raises:

    """
    services = soup.find('td', id="services")
    if services:
        name = services.text.replace('\n', '').strip()
        _url = services.find('a')['href']
        try:
            uuid = _get_url_param_value(_url, 'uuid')
        except CantGetData:
            uuid = ''
        return (name, uuid)
    return ('', '')


def _get_return_to_work_time(soup: BeautifulSoup) -> datetime:
    """Функция парсинга данных времени возврата в работу.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        datetime: время возврата в работу

    Raises:

    """
    return_times = (soup.find('td', id="obrd"), soup.find('td', id="obrd1"),
                    soup.find('td', id="obrd2"))
    return_times = [
        time.text.replace('\n', '').strip() for time in return_times if time]
    if return_times:
        times = [datetime.strptime(
            time, '%d.%m.%Y %H:%M') for time in return_times]
        if len(times) > 1:
            times.sort()
        return times[-1]
    return datetime.now() + timedelta(days=365)


def _parse_card_issue(text: str, issue: Issue) -> Issue:
    """Функция парсинга карточки обращения.

    Args:
        text: сырой текст страницы.
        issue: обращение, поля которого нужно дополнить.

    Returns:
        Issue: Модифицированный объект обращения.

    Raises:

    """
    soup = BeautifulSoup(text, "html.parser")
    issue.name_contragent, issue.uuid_contragent = _get_contragent_params(soup)
    issue.description = _get_description(soup)
    issue.creation_date = _get_creation_date(soup)
    issue.name_service, issue.uuid_service = _get_service_params(soup)
    issue.return_to_work_time = _get_return_to_work_time(soup)
    return issue


def _parse_date_report(soup: BeautifulSoup, name_first_date: str,
                       name_second_date: str) -> Iterable[str]:
    """Функция парсинга дат отчёта, со страницы отчёта.

    Args:
        soup: сырой текст страницы.
        name_first_date: название первой даты.
        name_second_date: название второй даты.

    Returns:
        Mapping: Выходной словарь параметров

    Raises:

    """
    log.debug("Парсинг параметров отчёта.")
    options_table = soup.find('table', id="stdViewpart0.legendTableList")
    options_tag = options_table.find_all('td', attrs={'style': 'width:100%;'})
    name_tag = options_table.find_all('td',
                                      attrs={'style': 'white-space:nowrap;'})
    name = [name.text.strip().replace(':', '') for name in name_tag]
    options = [option.text.strip() for option in options_tag]
    report_options = dict(zip(name, options))
    first_day = report_options.get(name_first_date, None)
    last_day = report_options.get(name_second_date, None)
    if not all([first_day, last_day]):
        raise CantGetData
    return first_day, last_day


def _parse_service_lavel_report(text: str, *args, **kwargs) -> \
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
    first_day, last_day = _parse_date_report(
        soup, 'Дата перевода, с', 'Дата перевода, по')
    log.debug(f'Получены даты отчета с {first_day} по {last_day}')
    label = _get_columns_name(soup)
    log.debug(f'Получены названия столбцов {label}')
    data_table = soup.find('table', id='stdViewpart0.part0_TableList')
    data_table = data_table.find_all('tr')[3:-1]
    day_collection = _forming_days_collecion(
        data_table, label, PageType.SERVICE_LEVEL_REPORT_PAGE)
    date_range = _get_date_range(first_day, last_day)
    days = _forming_days_dict(
        date_range, day_collection, PageType.SERVICE_LEVEL_REPORT_PAGE)
    group = set([_['Группа'] for _ in day_collection])
    if len(group) != support_group_count:
        log.error(f'Количество групп ТП не равно {support_group_count}')
        raise CantGetData
    days = _service_lavel_data_completion(days, group, label)
    collection = _formating_service_level_data(days)
    log.debug(f'Парсинг завершился успешно. Колекция отчетов SL '
              f'с {first_day} по {last_day} содержит {len(collection)} элем.')
    return collection


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
    return collection


def _parse_mttr_lavel_report(text: str, *args, **kwargs) -> \
                             Sequence | Sequence[Literal['']]:
    """Функция парсинга картточки обращения.

    Args:
        text: сырой текст страницы.

    Returns:
        Sequence | Sequence[Literal['']]: Коллекцию с найденными элементами.

    Raises:
        CantGetData: Если не удалось найти данные.
    """
    log.debug('Запуск парсинг отчёта MTTR')
    soup = BeautifulSoup(text, "html.parser")
    first_day, last_day = _parse_date_report(
        soup, 'Дата регистр, с', 'Дата регистр, по')
    log.debug(f'Получены даты отчета с {first_day} по {last_day}')
    label = _get_columns_name(soup)
    log.debug(f'Получены названия столбцов {label}')
    data_table = soup.find('table', id='stdViewpart0.part0_TableList')
    data_table = data_table.find_all('tr')[3:]
    day_collection = _forming_days_collecion(
        data_table, label, PageType.MMTR_LEVEL_REPORT_PAGE)
    date_range = _get_date_range(first_day, last_day)
    days = _forming_days_dict(
        date_range, day_collection, PageType.MMTR_LEVEL_REPORT_PAGE)
    days = _mttr_data_completion(days, label)
    collection = _formating_mttr_data(days)
    log.debug(f'Парсинг завершился успешно. Колекция отчетов MTTR '
              f'с {first_day} по {last_day} содержит {len(collection)} элем.')
    return collection


def _formating_mttr_data(days: Mapping[int, Sequence]) \
                                 -> Sequence[Mttr]:
    collection = []
    for day, day_content in days.items():
        day_content = day_content[0]
        day = day_content['День']
        total_issues = day_content['Всего ТТ']
        average_mttr = day_content['Средн МТТР']
        average_mttr_tech_support = day_content['Средн МТТР ТП']
        mttr = Mttr(day, total_issues, average_mttr, average_mttr_tech_support)
        collection.append(mttr)

    return collection


def _mttr_data_completion(days: dict, lable: Sequence) -> \
                          Mapping[int, Sequence]:
    """Функция для дополнения данных отчёта MTTR.
        т.к Naumen отдает не все необходимые данные, необходимо их дополнить.
        Заполнить пропуски за не наступившие дни: MTTR будет 0%

    Args:
        days: словарь дней, где ключ номер дня
        lable: название категорий

    Returns:
        Mapping: дополненый словарь.
    """
    avg_mttr = '0.0'
    mttr = '0.0'
    issues_count = '0'
    for day, content in days.items():
        if len(content) == 0:
            days[day] = [
                dict(zip(lable, (str(day), issues_count, avg_mttr, mttr))),
                ]
    return days


def _parse_flr_lavel_report(text: str, *args, **kwargs) -> \
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
                                 -> Sequence[Mttr]:
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
    first_date = min(date_first, date_second)
    last_date = max(date_first, date_second)
    log.debug(f'Минимальная дата: {first_date}')
    log.debug(f'Максимальная дата: {last_date}')
    date_range = []
    while first_date < last_date:
        date_range.append(first_date)
        first_date += timedelta(days=1)
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
