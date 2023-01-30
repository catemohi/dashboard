import logging
from dataclasses import fields
from time import sleep
from typing import Iterable, Mapping, Tuple

from requests import Response

from .crm import ActiveConnect, NaumenRequest, get_crm_response
from .search import SearchOptions, find_report_uuid
from ..config.config import create_naumen_request, formating_params
from ..config.config import get_params_find_create_report
from ..config.config import get_params_for_delete, params_erector
from ..config.structures import TypeReport
from ..exceptions import CantGetData
from ..parser.parser import parse_naumen_page
from ..parser.parser_base import PageType


log = logging.getLogger(__name__)


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
        _create_report(crm, TypeReport.CONTROL_ENABLE_SEARCH, *[], **{})
        sleep(1)
        _create_report(crm, TypeReport.CONTROL_SELECT_SEARCH, *[], **{})
        sleep(2)
        naumen_responce = _create_report(
            crm, report, *args, **kwargs)
        page_text = naumen_responce.text
        log.debug('Проверка количества страниц')
        page_count = parse_naumen_page(page_text, '', PageType.PAGINATION_PAGE)
        log.debug(f'Количество страниц: {page_count}')
        page_collection = [page_text]
        for i in range(1, page_count):
            naumen_responce = _create_report(
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
        naumen_responce, params_for_search_report = _create_report(
            crm, report, *args, **kwargs)
        naumen_uuid = find_report_uuid(crm, params_for_search_report)
        name_report = params_for_search_report.name

    log.debug(f'Найден UUID сформированного отчёта : {naumen_uuid}')

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


def _create_report(crm: ActiveConnect, report: TypeReport, *args,
                   **kwargs) -> Tuple[Response, SearchOptions]:

    """Метод для создания отчета в NAUMEN POST запросом в NAUMEN.

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

    mod_params, mod_data = formating_params(*args, **kwargs)
    naumen_reuqest, params_for_search_report = create_naumen_request(
        report, 'create_request', mod_params, mod_data, *args, **kwargs)
    naumen_response = get_crm_response(crm, naumen_reuqest)
    if not naumen_response:
        raise CantGetData

    return naumen_response, params_for_search_report


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
