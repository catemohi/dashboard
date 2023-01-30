import logging
from dataclasses import fields
from time import sleep
from typing import Iterable, Mapping, Tuple, Any

from .crm import ActiveConnect, get_crm_response
from .search import find_report_uuid
from ..config.config import formating_params
from ..config.structures import TypeReport
from ..config.config import get_report_name, get_search_create_report_params
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
    report_name = get_report_name()
    mod_params, mod_data = formating_params(*args, **kwargs)

    if report in [TypeReport.ISSUES_FIRST_LINE, TypeReport.ISSUES_VIP_LINE]:
        mod_data = dict(mod_data)
        parse_history, parse_issues_cards, mod_data = \
            _check_issues_report_keys(**mod_data)
        mod_data = tuple(mod_data.items())

    if report in [TypeReport.ISSUES_SEARCH]:
        get_crm_response(crm, TypeReport.CONTROL_ENABLE_SEARCH,
                         'create_request', *[], **{})
        sleep(1)
        get_crm_response(crm, TypeReport.CONTROL_SELECT_SEARCH,
                         'create_request', *[], **{})
        sleep(2)
        naumen_responce = get_crm_response(crm, report, 'create_request',
                                           *args, mod_params=mod_params,
                                           mod_data=mod_data, **kwargs)
        page_text = naumen_responce.text
        log.debug('Проверка количества страниц')
        page_count = parse_naumen_page(page_text, PageType.PAGINATION_PAGE)
        log.debug(f'Количество страниц: {page_count}')
        page_collection = [page_text]
        for i in range(1, page_count):
            mod_params = dict(mod_params)
            mod_params.update({'pagination': str(i)})
            mod_params = tuple(mod_params.items())
            naumen_responce = get_crm_response(
                crm, report, 'create_request', *args,
                mod_params=mod_params, mod_data=mod_data,
                **kwargs)
            page_collection.append(naumen_responce.text)
        collect = []
        for page in page_collection:
            collect += parse_naumen_page(page, report.page)
        return collect

    report_exists = True if naumen_uuid else False
    is_vip_issues = True if report == TypeReport.ISSUES_VIP_LINE else False

    if report_exists:
        log.debug('Обьект в CRM NAUMEN уже создан. '
                  f'Его UUID: {naumen_uuid}')

    else:
        mod_data = dict(mod_data)
        mod_data.update({'title': report_name})
        mod_data = tuple(mod_data.items())
        naumen_responce = get_crm_response(crm, report, 'create_request',
                                           *args, mod_params=mod_params,
                                           mod_data=mod_data, **kwargs)
        params_for_search_report = get_search_create_report_params(report,
                                                                   report_name)

        naumen_uuid = find_report_uuid(crm, params_for_search_report, report)

    log.debug(f'Найден UUID сформированного отчёта : {naumen_uuid}')

    search_params = tuple({'uuid': naumen_uuid}.items())
    naumen_responce = get_crm_response(crm, report, 'search_created_report',
                                       mod_params=search_params)

    if not naumen_responce:
        raise CantGetData

    page_text = naumen_responce.text
    collect = parse_naumen_page(page_text, report.page)

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
        _delete_report(crm, report, naumen_uuid)

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


def _delete_report(crm: ActiveConnect, report: TypeReport, uuid: str) -> bool:
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

    params = tuple({'uuid': uuid}.items())
    log.debug(f'Параметры для удаления отчёта {params}')
    _responce = get_crm_response(crm, report, 'delete_report',
                                 mod_params=params, method='GET')

    if _responce:
        log.info('Отчет в CRM Наумен удален.')
        return True

    log.error('Отчет в CRM Наумен не удален.')
    return False


# def _create_report(crm: ActiveConnect, report: TypeReport, request_type: str,
#                    *args, mod_params: Tuple[Tuple[str, Any]] = (),
#                    mod_data: Tuple[Tuple[str, Any]] = (),
#                    **kwargs) -> Response:

#     """Метод для создания отчета в NAUMEN POST запросом в NAUMEN.

#     Args:
#         crm: активное соединение с CRM.
#         report: отчёт, который необходимо получить.
#         request_type (str): название необходимого типа запроса
#         mod_params (Tuple[Tuple[str, Any]]): модифицированные параметры запроса
#         mod_params (Tuple[Tuple[str, Any]]): модифицированные данные запроса
#         *args: позиционные аргументы(не используются)
#         **kwargs: именнованные аргументы для создания отчёта.

#     Returns:
#         Itrrable: коллекция обьектов необходимого отчёта.
#     Raises:
#         CantGetData: в случае невозможности вернуть коллекцию.
#     """

#     naumen_reuqest = create_naumen_request(
#         report, request_type, mod_params, mod_data, *args, **kwargs)
#     naumen_response = get_crm_response(crm, naumen_reuqest)
#     if not naumen_response:
#         raise CantGetData

#     return naumen_response
