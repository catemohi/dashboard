import logging
from dataclasses import dataclass, fields
from datetime import datetime
from enum import Enum
from random import randint
from time import sleep
from typing import Iterable, Literal, Mapping, NamedTuple
from typing import Sequence, Tuple

from requests import Response, Session
from requests.adapters import HTTPAdapter, Retry
from requests.packages import urllib3

from .config.config import CONFIG, get_params_create_report
from .config.config import get_params_find, get_params_for_delete
from .exceptions import CantGetData, ConnectionsFailed, InvalidDate
from .parser.parser import parse_naumen_page
from .parser.parser_base import PageType
urllib3.disable_warnings()


log = logging.getLogger(__name__)
DOMAIN = Literal['CORP.ERTELECOM.LOC', 'O.WESTCALL.SPB.RU']


@dataclass(slots=True, frozen=True)
class ActiveConnect:

    """Класс данных для хранения сессии активного соединения c CRM Naumen.

        Attributes:
            session: активное соединение с crm системой.
    """
    session: Session


class TypeReport(Enum):

    """Enum перечисление видов отчета.

        Attributes:
            ISSUE_CARD: карточка одного обращения.
            ISSUES_FIRST_LINE: таблица обращений первой линии.
            ISSUES_VIP_LINE: таблица обращений vip линии.
            SERVICE_LEVEL: отчет по уровню SL
            MTTR_LEVEL: отчет по уровню MTTR
            FLR_LAVEL: отчет по уровню FLR

    """
    ISSUE_CARD = 'issue card'
    ISSUES_FIRST_LINE = "issues"
    ISSUES_VIP_LINE = "vip issues"
    SERVICE_LEVEL = "service level report"
    MTTR_LEVEL = "mttr report"
    FLR_LEVEL = "flr report"

    def __init__(self, value):
        self.page = self._get_page()

    def _get_page(self):
        page_dict = {
            'ISSUE_CARD': PageType.ISSUE_CARD_PAGE,
            'ISSUES_FIRST_LINE': PageType.ISSUES_TABLE_PAGE,
            'ISSUES_VIP_LINE': PageType.ISSUES_TABLE_PAGE,
            'SERVICE_LEVEL': PageType.SERVICE_LEVEL_REPORT_PAGE,
            'MTTR_LEVEL': PageType.MMTR_LEVEL_REPORT_PAGE,
            'FLR_LEVEL': PageType.FLR_LEVEL_REPORT_PAGE,
        }
        try:
            return page_dict[self.name]
        except (KeyError, TypeError):
            raise CantGetData


class SearchOptions(NamedTuple):

    """Класс данных для хранения сформированного запроса к CRM Naumen.

        Attributes:
            name: имя искомого отчета
            delay_attems: задержка между попытками
            num_attems: количество попыток поиска отчета
            uuid: идентификатор обьекта в CRM Naumen
    """
    name: str
    delay_attems: int
    num_attems: int
    uuid: str


class NaumenRequest(NamedTuple):

    """Класс данных для хранения сформированного запроса к CRM Naumen.

        Attributes:
            url: ссылка для запроса
            header: header для запроса
            parsms: параметры для запроса
            data: данные запроса
            verify: верификация
    """
    url: str
    headers: Mapping
    params: Mapping
    data: Mapping
    verify: bool


def get_session(username: str, password: str,
                domain: DOMAIN) \
                -> ActiveConnect:
    """Функция для создания сессии с CRM системой.

    Args:
        username: имя пользователя в Naumen
        password: пароль пользователя
        domain: домен учетной записи

    Returns:
        Session: обьект сессии с CRM системой.

    Raises:
        ConnectionsFailed: если не удалось подключиться к CRM системе.

    """
    url = CONFIG['url']['login']
    if not all([username, password, domain, url]):
        raise ConnectionsFailed
    session = Session()
    retries = Retry(total=5, backoff_factor=0.5)
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.mount('http://', HTTPAdapter(max_retries=retries))

    data = {'login': username,
            'password': password,
            'domain': domain,
            }
    response = session.post(url=url, data=data, verify=False)
    if response.status_code != 200:
        raise ConnectionsFailed

    return ActiveConnect(session)


def get_report(crm: ActiveConnect, report: TypeReport,
               *args, naumen_uuid: str = '', **kwargs) -> Iterable:
    """Функция для получения отчёта из CRM.

    Args:
        crm: активное соединение с CRM.
        report: отчёт, который необходимо получить.
        *args: позиционные аргументы(не используются)

    Kwargs:
        naumen_uuid: uuid уже созданного отчёта.
        **kwargs: именнованные аргументы для создания отчёта.

    Returns:
        Itrrable: коллекция обьектов необходимого отчёта.
    Raises:
        CantGetData: в случае невозможности вернуть коллекцию.
    """

    parse_history, parse_issues_cards = False, False
    if report in [TypeReport.ISSUES_FIRST_LINE, TypeReport.ISSUES_VIP_LINE]:
        parse_history, parse_issues_cards, kwargs = \
            _check_issues_report_keys(**kwargs)

    report_exists = True if naumen_uuid else False

    if report_exists:
        log.debug('Обьект в CRM NAUMEN уже создан. '
                  f'Его UUID: {naumen_uuid}')
        name_report = ''
    else:
        naumen_uuid, params_for_search_report = \
            _create_report_and_find_uuid(crm, report, *args, **kwargs)
        name_report = params_for_search_report.name

    url, headers, params, data, verify = get_params_find()
    params.update({'uuid': naumen_uuid})
    search_request = NaumenRequest(url, headers, params, data, verify)
    naumen_responce = _get_crm_response(crm, search_request)
    if not naumen_responce:
        raise CantGetData
    page_text = naumen_responce.text
    collect = parse_naumen_page(page_text, name_report, report.page)

    if parse_issues_cards:
        collect = list(collect)
        log.debug('Парсинг карточек обращений.')
        for num, issue in enumerate(collect):
            issue_card = get_report(
                crm, TypeReport.ISSUE_CARD, naumen_uuid=issue.uuid)[0]
            for field in fields(issue_card):
                issue_card_field_value = getattr(issue_card, field.name)
                if issue_card_field_value:
                    setattr(issue, field.name, issue_card_field_value)
            collect[num] = issue

    if parse_history:
        log.debug('Парсинг истории обращений.')

    _delete_report(crm, naumen_uuid)

    return collect


def _check_issues_report_keys(*args, **kwargs) -> Tuple[bool, bool, Mapping]:

    """Функция для проверки определенных атрибутов ключей.

    Args:
        *args: все позиционные аргументы(не проверяются).

    Kwargs:
        **kwargs: все именнованные аргументы

    Retuns:
        Mapping: преобразованный список именнованных аргументов
    """

    log.debug('Проверка необходимости парсинга '
              'карточек обращений и историй обращений.')
    parse_history = kwargs.pop('parse_history', False)
    parse_issues_cards = kwargs.pop('parse_issues_cards', False)
    log.debug(f'Парсить карточки обращений: {parse_issues_cards}')
    log.debug(f'Парсить историю: {parse_history}')
    return (parse_history, parse_issues_cards, kwargs)


def _create_report_and_find_uuid(crm: ActiveConnect, report: TypeReport, *args,
                                 **kwargs) -> Tuple[str, SearchOptions]:

    """Метод для создания отчета и получение его uuid, для парсинга.

    Args:
        crm: активное соединение с CRM.
        report: отчёт, который необходимо получить.
        *args: позиционные аргументы(не используются)
        **kwargs: именнованные аргументы для создания отчёта.

    Returns:
        Itrrable: коллекция обьектов необходимого отчёта.
    Raises:
        CantGetData: в случае невозможности вернуть коллекцию.
    """

    log.debug(f'Запуск создания отчета: {report}')
    log.debug(f'Переданы параметры args: {args}')
    log.debug(f'Переданы параметры kwargs: {kwargs}')
    naumen_reuqest, params_for_search_report = _create_request(report, *args,
                                                               **kwargs)
    log.debug(f'Запрос к CRM: {naumen_reuqest}')
    naumen_reuqest = _get_crm_response(crm, naumen_reuqest)
    if not naumen_reuqest:
        raise CantGetData
    log.debug('Запрос на создание отчёта обработан CRM')
    naumen_uuid = _find_report_uuid(crm, params_for_search_report)
    log.debug(f'Найден UUID сформированного отчёта : {naumen_uuid}')
    return naumen_uuid, params_for_search_report


def _create_request(report: TypeReport, *args, **kwargs) -> \
                                        Tuple[NaumenRequest, SearchOptions]:
    """Функция создания запроса для создания отчета и сбора параметров для
        поиска созданного отчета.

    Args:
        report: тип отчета для которого надо создать запрос.
        *args: параметры необходимые для создания отчета.

    Kwargs:
        **kwargs: именнованные параметры необходимы для создания отчета.

    Returns:
        NaumenRequest: готовый запрос да создания отчёта.
        SearchOptions: параментры для поиска созданного отчёта.

    Raises:
        CantGetData: в случае неверной работы функции.

    """

    log.debug(f'Запуск создания запроса для отчета: {report}')
    log.debug(f'Переданы параметры args: {args}')
    log.debug(f'Переданы параметры kwargs: {kwargs}')
    if not isinstance(report, TypeReport):
        raise CantGetData
    data = CONFIG[report.value]['create_request']['data'].copy()

    if not kwargs:
        return _configure_params(report)

    date_name_keys = ('start_date', 'end_date')
    log.debug(f'Получены именнованные аргументы: {kwargs}')
    for name, value in kwargs.items():
        if name in date_name_keys:
            value = _validate_date(value)
        data[name]['value'] = value

    return _configure_params(report, tuple(data.items()))


def _get_crm_response(crm: ActiveConnect,
                      rq: NaumenRequest,
                      method: Literal['GET', 'POST'] = 'POST') -> Response:
    """Функция для получения ответа из CRM системы.

    Args:
        crm: сессия с CRM Naumen.
        request: запрос в CRM Naumen.
        method: HTTP метод.

    Returns:
        Ответ сервера CRM системы Naumen

    Raises:
        CantGetData: если не удалось получить ответ.

    """
    if method == 'POST':
        _response = crm.session.post(url=rq.url, headers=rq.headers,
                                     params=rq.params,
                                     data=rq.data, verify=rq.verify)
    else:
        _response = crm.session.get(url=rq.url,
                                    headers=rq.headers,
                                    params=rq.params,
                                    verify=rq.verify)
    if _response.status_code != 200:
        raise CantGetData

    return _response


def _configure_params(report: TypeReport, mod_data: Iterable = ()) -> \
                                        Tuple[NaumenRequest, SearchOptions]:
    """Функция для создания, даты или параметров запроса.

    Args:
        report: тип запрашиваемого отчета.
        mod_data: параметры даты которые необходимо модифицировать

    Returns:
        NaumenRequest: сформированный запрос для CRM Naumen
        SearchOptions: параметры для поиска созданного отчета
    """

    url, uuid, headers, params, data, verify, delay_attems, num_attems = \
        get_params_create_report(report.value)
    if mod_data:
        data.update(mod_data)
    name = _get_report_name()
    data['title']['value'] = name
    data = _params_erector(data)
    params = _params_erector(params)
    if not url:
        raise CantGetData

    search_options = SearchOptions(name, delay_attems, num_attems, uuid)
    request = NaumenRequest(url, headers, params, data, verify)
    return (request, search_options)


def _find_report_uuid(crm: ActiveConnect, options: SearchOptions) -> str:
    """Функция поиска сформированного отчета в CRM Naumen.

    Args:
        crm:  активное соединение с CRM Naumen.
        params: параметры для поиска отчета в CRM Naumen.

    Returns:
        str: строчный идентификатор обьекта в CRM Naumen.

    Raises:
        ConnectionsFailed: если не удалось подключиться к CRM системе.

    """

    def _searching(num_attems: int,
                   search_request: NaumenRequest) -> Sequence[str]:
        """Рекурсивная функция поиска отчета в CRM системе.

        Args:
            num_attems: количество попыток поиска.
            search_request: запрос для поиска отчета.

        Returns:
            Sequence[str]: коллекцию внутри которой идентификатор в CRM Naumen.

        Raises:

        """

        log.debug(f'Поиск свормированного отчета: {options.name}.'
                  f'Осталось попыток: {num_attems}')
        log.debug(f'Сформированный запрос: {search_request}')
        sleep(options.delay_attems)
        response = _get_crm_response(crm, search_request, 'GET')
        page_text = response.text
        parsed_collection = parse_naumen_page(page_text, options.name,
                                              PageType.REPORT_LIST_PAGE)
        if parsed_collection is None:
            if num_attems >= 1:
                return _searching(num_attems - 1, search_request)
            log.error(f'Не удалось найти отчёт: {options.name}')
            raise CantGetData
        return parsed_collection

    url, headers, params, data, verify = get_params_find()
    params.update({'uuid': options.uuid})
    search_request = NaumenRequest(url, headers, params, data, verify)
    parsed_collection = _searching(options.num_attems, search_request)

    if len(parsed_collection) != 1:
        raise CantGetData

    return str(parsed_collection[0])


def _validate_date(check_date: str) -> str:
    """Функция проверки формата даты.

    Args:
        first_date: первая дата, format '%d.%m.%Y'

    Returns:
        date: строка даты необходимого формата.

    Raises:
        InvalidDate: при неудачной проверке или конвертиртации даты.

    """

    try:
        return datetime.strptime(check_date, '%d.%m.%Y').strftime("%d.%m.%Y")
    except ValueError:
        raise InvalidDate


def _params_erector(params: Mapping[str,
                                    Mapping[Literal['name', 'value'],
                                            str]]) -> Mapping[str, str]:
    """Функция для уплотнения, даты или параметров запроса.

    Args:
        params: данные которые необходимо собрать

    Returns:
        Mapping: Готовый словарь для запроса.
    """

    return dict([[val for _, val in root_val.items()
                  ] for _, root_val in params.items()])


def _get_report_name() -> str:
    """Функция получения уникального названия для отчета.

    Args:

    Returns:
        Строку названия.
    """

    return f"ID{randint(1000000,9999999)}"


def _delete_report(crm: ActiveConnect, uuid: str) -> bool:
    """_summary_

    Args:
        crm (ActiveConnect): _description_
        uuid (str): _description_

    Raises:
        CantGetData: если не удалось получить ответ.

    Returns:
        bool: статус True или False, в случае успеха или неудачи.
    """

    log.debug('Удаление созданного отчета в CRM Наумен')
    log.debug(f'Передан uuid отчёта: {uuid}')

    url, headers, params, data, verify = get_params_for_delete()
    params.update({'uuid': uuid})
    delete_request = NaumenRequest(url, headers, params, data, verify)
    _responce = _get_crm_response(crm, delete_request, 'GET')

    if _responce == 200:
        log.info('Отчет в CRM Наумен удален.')
        return True

    log.error('Отчет в CRM Наумен не удален.')
    return False
