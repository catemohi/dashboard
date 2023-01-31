import logging
from dataclasses import fields
from time import sleep
from typing import Any, Iterable, Mapping, Tuple, Sequence

from .crm import ActiveConnect, get_crm_response
from ..config.config import formating_params
from ..config.structures import TypeReport, NaumenRequestType, SearchOptions
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

    report_exists = True if naumen_uuid else False
    is_vip_issues = True if report == TypeReport.ISSUES_VIP_LINE else False
    parse_history, parse_issues_cards = False, False
    report_name = get_report_name()
    mod_params, mod_data = formating_params(*args, **kwargs)

    if report in [TypeReport.ISSUES_FIRST_LINE, TypeReport.ISSUES_VIP_LINE]:
        mod_data = dict(mod_data)
        parse_history, parse_issues_cards, mod_data = \
            _check_issues_report_keys(**mod_data)
        mod_data = tuple(mod_data.items())

    if report_exists:
        log.debug(f'Обьект в CRM NAUMEN уже создан. Его UUID: {naumen_uuid}')

    else:
        mod_data = dict(mod_data)
        mod_data.update({'title': report_name})
        mod_data = tuple(mod_data.items())
        _create_report(crm, report, NaumenRequestType.CREATE_REPORT, *args,
                       mod_params=mod_params, mod_data=mod_data, **kwargs)
        params_for_search_report = get_search_create_report_params(
            report, report_name)
        naumen_uuid = _find_report_uuid(crm, params_for_search_report, report)

    log.debug(f'Найден UUID сформированного отчёта : {naumen_uuid}')
    mod_params = tuple({'uuid': naumen_uuid}.items())
    report_page = _get_report(crm, report, NaumenRequestType.SEARCH_REPORT,
                              mod_params=mod_params)
    collect = parse_naumen_page(report_page, report.page)

    if is_vip_issues:
        for vip_issue in collect:
            if vip_issue:
                vip_issue.vip_contragent = True

    if parse_issues_cards:
        collect = list(collect)
        log.debug('Парсинг карточек обращений.')

        for num, issue in enumerate(collect):
            issue_card = get_report(crm, TypeReport.ISSUE_CARD,
                                    naumen_uuid=issue.uuid)[0]

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
    _responce = get_crm_response(crm, report, NaumenRequestType.DELETE_REPORT,
                                 mod_params=params, method='GET')

    if _responce:
        log.info('Отчет в CRM Наумен удален.')
        return True

    log.error('Отчет в CRM Наумен не удален.')
    return False


def _find_report_uuid(crm: ActiveConnect, options: SearchOptions,
                      report: TypeReport) -> str:
    """Функция поиска сформированного отчета в CRM Naumen.

    Args:
        crm:  активное соединение с CRM Naumen.
        options: параметры для поиска отчета в CRM Naumen.
        report: тип отчета который необходимо найти

    Returns:
        str: строчный идентификатор обьекта в CRM Naumen.

    Raises:
        ConnectionsFailed: если не удалось подключиться к CRM системе.

    """

    def _searching(report: TypeReport, num_attems: int, mod_params: Tuple,
                   ) -> Sequence[str]:
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
        sleep(options.delay_attems)
        response = get_crm_response(crm, report,
                                    NaumenRequestType.SEARCH_REPORT,
                                    mod_params=mod_params, method='GET')
        page_text = response.text
        parsed_collection = parse_naumen_page(page_text,
                                              PageType.REPORT_LIST_PAGE,
                                              options.name,
                                              )
        if parsed_collection is None:
            if num_attems >= 1:
                return _searching(report, num_attems - 1, mod_params)
            log.error(f'Не удалось найти отчёт: {options.name}')
            raise CantGetData
        return parsed_collection

    mod_params = tuple({'uuid': options.uuid}.items())
    parsed_collection = _searching(report, options.num_attems, mod_params)

    if len(parsed_collection) != 1:
        raise CantGetData

    return str(parsed_collection[0])


def _create_report(crm: ActiveConnect, report: TypeReport,
                   request_type: NaumenRequestType,
                   *args, mod_params: Tuple[Tuple[str, Any]] = (),
                   mod_data: Tuple[Tuple[str, Any]] = (),
                   **kwargs) -> None:

    """Метод для создания отчета в NAUMEN отправкой POST запроса в NAUMEN.

    Args:
        crm: активное соединение с CRM.
        report: отчёт, который необходимо получить.
        request_type (NaumenRequestType): название необходимого типа запроса
        mod_params (Tuple[Tuple[str, Any]]): модифицированные параметры запроса
        mod_params (Tuple[Tuple[str, Any]]): модифицированные данные запроса
        *args: позиционные аргументы(не используются)
        **kwargs: именнованные аргументы для создания отчёта.

    Returns:
        None
    Raises:
        CantGetData: в случае невозможности вернуть коллекцию.
    """
    naumen_responce = get_crm_response(crm, report, request_type,
                                       *args, mod_params=mod_params,
                                       mod_data=mod_data, **kwargs)
    return naumen_responce


def _get_report(crm: ActiveConnect, report: TypeReport,
                request_type: NaumenRequestType,
                *args, mod_params: Tuple[Tuple[str, Any]] = (),
                mod_data: Tuple[Tuple[str, Any]] = (),
                **kwargs) -> str:

    """Метод для получения данных отчета из NAUMEN.

    Args:
        crm: активное соединение с CRM.
        report: отчёт, который необходимо получить.
        request_type (NaumenRequestType): название необходимого типа запроса
        mod_params (Tuple[Tuple[str, Any]]): модифицированные параметры запроса
        mod_params (Tuple[Tuple[str, Any]]): модифицированные данные запроса
        *args: позиционные аргументы(не используются)
        **kwargs: именнованные аргументы для создания отчёта.

    Returns:
        str: Данные отчета
    Raises:
        CantGetData: в случае невозможности вернуть коллекцию.
    """
    naumen_responce = get_crm_response(crm, report, request_type,
                                       *args, mod_params=mod_params,
                                       mod_data=mod_data, method='GET',
                                       **kwargs)
    return naumen_responce.text