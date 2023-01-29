import logging
from dataclasses import fields
from enum import Enum
from random import randint
from time import sleep
from typing import Any, Iterable, Mapping, Tuple

from requests import Response

from .crm import ActiveConnect, NaumenRequest, get_crm_response
from .search import SearchOptions, find_report_uuid
from ..config.config import get_params_control, get_params_search
from ..config.config import get_params_create_report, get_raw_params
from ..config.config import get_params_find_create_report
from ..config.config import get_params_for_delete, params_erector
from ..exceptions import CantGetData
from ..parser.parser import parse_naumen_page
from ..parser.parser_base import PageType


log = logging.getLogger(__name__)


class TypeReport(Enum):

    """Enum перечисление видов отчета.

        Attributes:
            ISSUE_CARD: карточка одного обращения.
            ISSUES_FIRST_LINE: таблица обращений первой линии.
            ISSUES_VIP_LINE: таблица обращений vip линии.
            ISSUES_SEARCH: запрос для поиска обращения
            SERVICE_LEVEL: отчет по уровню SL
            MTTR_LEVEL: отчет по уровню MTTR
            FLR_LAVEL: отчет по уровню FLR

    """
    ISSUE_CARD = 'issue card'
    ISSUES_FIRST_LINE = "issues"
    ISSUES_VIP_LINE = "vip issues"
    ISSUES_SEARCH = "search issues"
    SERVICE_LEVEL = "service level report"
    MTTR_LEVEL = "mttr report"
    FLR_LEVEL = "flr report"
    CONTROL_ENABLE_SEARCH = "enable search"
    CONTROL_SELECT_SEARCH = "select search"

    def __init__(self, value):
        self.page = self._get_page()

    def _get_page(self):
        page_dict = {
            'ISSUE_CARD': PageType.ISSUE_CARD_PAGE,
            'ISSUES_FIRST_LINE': PageType.ISSUES_TABLE_PAGE,
            'ISSUES_VIP_LINE': PageType.ISSUES_TABLE_PAGE,
            'ISSUES_SEARCH':  PageType.SEARCH_RESULT_ISSUES_PAGE,
            'SERVICE_LEVEL': PageType.SERVICE_LEVEL_REPORT_PAGE,
            'MTTR_LEVEL': PageType.MMTR_LEVEL_REPORT_PAGE,
            'FLR_LEVEL': PageType.FLR_LEVEL_REPORT_PAGE,
            'CONTROL_ENABLE_SEARCH': None,
            'CONTROL_SELECT_SEARCH': None,
        }
        try:
            return page_dict[self.name]
        except (KeyError, TypeError):
            raise CantGetData


def get_report(crm: ActiveConnect, report: TypeReport, *args,
               naumen_uuid: str = '', **kwargs) -> Iterable:
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

    if report in [TypeReport.ISSUES_SEARCH]:
        name_report = ''
        _get_search_issue_responce(crm, TypeReport.CONTROL_ENABLE_SEARCH,
                                   *[], **{})
        sleep(1)
        _get_search_issue_responce(crm, TypeReport.CONTROL_SELECT_SEARCH,
                                   *[], **{})
        sleep(2)
        naumen_responce = _get_search_issue_responce(
            crm, report, *args, **kwargs)
        page_text = naumen_responce.text
        log.debug('Проверка количества страниц')
        page_count = parse_naumen_page(page_text, '', PageType.PAGINATION_PAGE)
        log.debug(f'Количество страниц: {page_count}')
        page_collection = [page_text]
        for i in range(1, page_count):
            naumen_responce = _get_search_issue_responce(
                crm, report, *args, **{'mod_params': {'pagination': str(i)},
                                       **kwargs})
            page_collection.append(naumen_responce.text)
        collect = []
        for page in page_collection:
            collect += parse_naumen_page(page, name_report, report.page)
        return collect

    report_exists = True if naumen_uuid else False
    is_vip_issues = True if report == TypeReport.ISSUES_VIP_LINE else False

    if report_exists:
        log.debug('Обьект в CRM NAUMEN уже создан. '
                  f'Его UUID: {naumen_uuid}')
        name_report = ''
    else:
        naumen_uuid, params_for_search_report = \
            _create_report_and_find_uuid(crm, report, *args, **kwargs)
        name_report = params_for_search_report.name

    url, headers, params, data, verify = get_params_find_create_report()
    params.update({'uuid': naumen_uuid})
    search_request = NaumenRequest(url, headers, params, data, verify)
    naumen_responce = get_crm_response(crm, search_request)

    if not naumen_responce:
        raise CantGetData

    page_text = naumen_responce.text
    collect = parse_naumen_page(page_text, name_report, report.page)

    if is_vip_issues:
        for vip_issue in collect:
            if vip_issue:
                vip_issue.vip_contragent = True

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
        raise NotImplementedError

    if not report_exists:
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


def _create_naumen_request(crm: ActiveConnect, report: TypeReport,
                           mod_params: Tuple[Tuple[str, Any]] = (),
                           mod_data: Tuple[Tuple[str, Any]] = (),
                           *args, **kwargs) -> Tuple[Response, SearchOptions]:

    """Метод для создания и отправки первичного запроса в NAUMEN .

    Args:
        crm: активное соединение с CRM.
        report: отчёт, который необходимо получить.
        *args: позиционные аргументы(не используются)
        **kwargs: именнованные аргументы для создания отчёта.

    Returns:
        Tuple[Response, SearchOptions]: коллекция обьектов необходимого отчёта.
    Raises:
        CantGetData: в случае невозможности вернуть коллекцию.
    """

    log.debug(f'Запуск создания отчета: {report}')
    log.debug(f'Переданы модифицированные params: {mod_params}')
    log.debug(f'Переданы модифицированные data: {mod_data}')
    log.debug(f'Переданы параметры args: {args}')
    log.debug(f'Переданы параметры kwargs: {kwargs}')

    if not isinstance(report, TypeReport):
        raise CantGetData
    data, params = get_raw_params(report.value, 'create_request',
                                  mod_params, mod_data, *args, **kwargs)
    naumen_reuqest, params_for_search_report = _configure_params(report, data,
                                                                 params)
    log.debug(f'Запрос к CRM: {naumen_reuqest}')
    naumen_response = get_crm_response(crm, naumen_reuqest)
    if not naumen_response:
        raise CantGetData

    return naumen_response, params_for_search_report


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

    if kwargs.get('mod_params', False):
        mod_params = kwargs('mod_params')
    else:
        mod_params = ()
    mod_data = tuple(kwargs.items())
    naumen_responce, params_for_search_report = _create_naumen_request(
        crm, report, mod_params, mod_data, *args, **kwargs)

    naumen_uuid = find_report_uuid(crm, params_for_search_report)
    log.debug(f'Найден UUID сформированного отчёта : {naumen_uuid}')
    return naumen_uuid, params_for_search_report


def _get_search_issue_responce(crm: ActiveConnect, report: TypeReport, *args,
                               **kwargs) -> Response:

    """Метод отправка поисковой POST запроса обращения в NAUMEN

    Args:
        crm: активное соединение с CRM.
        report: тип отчёт,для формирования запроса.
        *args: позиционные аргументы(не используются)
        **kwargs: именнованные аргументы для создания отчёта.

    Returns:
        Itrrable: коллекция обьектов необходимого отчёта.
    Raises:
        CantGetData: в случае невозможности вернуть коллекцию.
    """
    if kwargs.get('mod_params', False):
        mod_params = kwargs('mod_params')
    else:
        mod_params = ()
    mod_data = tuple(kwargs.items())
    naumen_responce, params_for_search_report = _create_naumen_request(
        crm, report, mod_params, mod_data, *args, **kwargs)
    return naumen_responce


def _configure_params(report: TypeReport, mod_data: Iterable = (),
                      mod_params: Iterable = ()) -> \
                          Tuple[NaumenRequest, SearchOptions]:
    """Функция для создания, даты или параметров запроса.

    Args:
        report: тип запрашиваемого отчета.
        mod_data: параметры даты которые необходимо модифицировать

    Returns:
        NaumenRequest: сформированный запрос для CRM Naumen
        SearchOptions: параметры для поиска созданного отчета
    """
    if report in [TypeReport.ISSUES_SEARCH]:
        url, uuid, headers, params, data, verify, delay_attems, num_attems = \
            get_params_search(report.value)
    elif report in [TypeReport.CONTROL_SELECT_SEARCH,
                    TypeReport.CONTROL_ENABLE_SEARCH]:
        url, uuid, headers, params, data, verify, delay_attems, num_attems = \
            get_params_control(report.value)
    else:
        url, uuid, headers, params, data, verify, delay_attems, num_attems = \
            get_params_create_report(report.value)

    if mod_data:
        data.update(mod_data)

    if mod_params:
        params.update(mod_params)

    name = _get_report_name()

    if data.get('title', False):
        data['title']['value'] = name

    data = params_erector(data)
    params = params_erector(params)

    if not url:
        raise CantGetData

    search_options = SearchOptions(name, delay_attems, num_attems, uuid)
    request = NaumenRequest(url, headers, params, data, verify)
    return (request, search_options)


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
    params = params_erector(params)
    params.update({'uuid': uuid})
    log.debug(f'Параметры для удаления отчёта {params}')
    delete_request = NaumenRequest(url, headers, params, data, verify)
    _responce = get_crm_response(crm, delete_request, 'GET')

    if _responce:
        log.info('Отчет в CRM Наумен удален.')
        return True

    log.error('Отчет в CRM Наумен не удален.')
    return False
