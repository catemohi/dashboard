import logging
from dataclasses import fields
from time import sleep
from typing import Any, Mapping, Sequence, Tuple, Union

from ..config.config import get_report_name, get_search_create_report_params
from ..config.structures import NaumenRequestType, SearchOptions, TypeReport
from ..exceptions import CantGetData
from ..parser.parser import parse_naumen_page
from ..parser.parser_base import PageType
from .crm import ActiveConnect, get_crm_response

log = logging.getLogger(__name__)


def get_report(
    crm: ActiveConnect,
    report: TypeReport,
    *args: Sequence,
    naumen_uuid: str = "",
    mod_params: Union[Tuple[Tuple[str, Any]], Tuple] = (),
    mod_data: Union[Tuple[Tuple[str, Any]], Tuple] = (),
    **kwargs: Mapping,
) -> Sequence:
    """Функция для получения отчёта из CRM.

    Args:
        crm (ActiveConnect): активное соединение с CRM.
        report (TypeReport): отчёт, который необходимо получить.
        *args (Sequence): позиционные аргументы(не используются)

    Kwargs:
        naumen_uuid (str): uuid уже созданного отчёта.
        mod_params (Union[Tuple[Tuple[str, Any]], Tuple]): обновленные
        параметры
        mod_data (Union[Tuple[Tuple[str, Any]], Tuple]): обновленные
        данные запроса
        **kwargs: именнованные аргументы для создания отчёта.

    Returns:
        Sequence: коллекция обьектов необходимого отчёта.
    Raises:
        CantGetData: в случае невозможности вернуть коллекцию.
    """

    report_exists = True if naumen_uuid else False
    need_delete_report = False
    is_vip_issues = True if report == TypeReport.ISSUES_VIP_LINE else False
    parse_issue_history, parse_issue_card = False, False
    report_name = get_report_name()

    if report in [TypeReport.ISSUES_FIRST_LINE, TypeReport.ISSUES_VIP_LINE]:
        _: Mapping[str, Any] = dict(mod_data)
        parse_issue_history, parse_issue_card, _ = _check_issues_report_keys(**_)
        mod_data = tuple(_.items())

    if report_exists:
        log.debug(f"Обьект в CRM NAUMEN уже создан. Его UUID: {naumen_uuid}")

    else:
        need_delete_report = True
        _ = dict(mod_data)
        _.update({"title": report_name})
        mod_data = tuple(_.items())

        _create_report(
            crm,
            report,
            NaumenRequestType.CREATE_REPORT,
            *args,
            mod_params=mod_params,
            mod_data=mod_data,
            **kwargs,
        )
        params_for_search_report = get_search_create_report_params(report, report_name)
        naumen_uuid = _find_report_uuid(crm, params_for_search_report, report)

    log.debug(f"Найден UUID сформированного отчёта : {naumen_uuid}")

    mod_params = tuple({"uuid": naumen_uuid}.items())
    report_page = _get_report(
        crm,
        report,
        NaumenRequestType.SEARCH_REPORT,
        mod_params=mod_params,
    )

    collect = parse_naumen_page(report_page, report.page)

    if is_vip_issues:
        for vip_issue in collect:
            if vip_issue:
                vip_issue.vip_contragent = True

    if parse_issue_card:
        collect = list(collect)
        log.debug("Парсинг карточек обращений.")

        for num, issue in enumerate(collect):
            issue_card = get_report(crm, TypeReport.ISSUE_CARD, naumen_uuid=issue.uuid)[
                0
            ]

            for field in fields(issue_card):
                issue_card_field_value = getattr(issue_card, field.name)

                if issue_card_field_value:
                    setattr(issue, field.name, issue_card_field_value)

            collect[num] = issue

    if parse_issue_history:
        log.debug("Парсинг истории обращений.")
        raise NotImplementedError

    if need_delete_report:
        _delete_report(crm, report, naumen_uuid)

    return collect


def _check_issues_report_keys(
    *args: Sequence,
    **kwargs: Mapping,
) -> Tuple[bool, bool, Mapping]:

    """Функция для проверки определенных атрибутов ключей.

    Args:
        *args: все позиционные аргументы(не проверяются).

    Kwargs:
        **kwargs: все именнованные аргументы

    Retuns:
        Mapping: преобразованный список именнованных аргументов
    """

    log.debug(
        "Проверка необходимости парсинга " "карточек обращений и историй обращений.",
    )
    parse_issue_history: bool = kwargs.pop("parse_issue_history", False)  # type: ignore
    parse_issue_card: bool = kwargs.pop("parse_issue_card", False)  # type: ignore
    log.debug(f"Парсить карточки обращений: {parse_issue_card}")
    log.debug(f"Парсить историю: {parse_issue_history}")
    return (parse_issue_history, parse_issue_card, kwargs)


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

    log.debug("Удаление созданного отчета в CRM Наумен")
    log.debug(f"Передан uuid отчёта: {uuid}")

    params = tuple({"uuid": uuid}.items())
    log.debug(f"Параметры для удаления отчёта {params}")
    _responce = get_crm_response(
        crm,
        report,
        NaumenRequestType.DELETE_REPORT,
        mod_params=params,
        method="GET",
    )

    if _responce:
        log.info("Отчет в CRM Наумен удален.")
        return True

    log.error("Отчет в CRM Наумен не удален.")
    return False


def _find_report_uuid(
    crm: ActiveConnect,
    options: SearchOptions,
    report: TypeReport,
) -> str:
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

    def _searching(
        report: TypeReport,
        num_attems: int,
        mod_params: Tuple,
    ) -> Sequence[str]:
        """Рекурсивная функция поиска отчета в CRM системе.

        Args:
            num_attems: количество попыток поиска.
            search_request: запрос для поиска отчета.

        Returns:
            Sequence[str]: коллекцию внутри которой идентификатор в CRM Naumen.

        Raises:

        """

        log.debug(
            f"Поиск свормированного отчета: {options.name}."
            f"Осталось попыток: {num_attems}",
        )
        sleep(options.delay_attems)
        response = get_crm_response(
            crm,
            report,
            NaumenRequestType.SEARCH_REPORT,
            mod_params=mod_params,
            method="GET",
        )
        page_text = response.text
        parsed_collection = parse_naumen_page(
            page_text,
            PageType.REPORT_LIST_PAGE,
            options.name,
        )
        if parsed_collection is None:
            if num_attems >= 1:
                return _searching(report, num_attems - 1, mod_params)
            log.error(f"Не удалось найти отчёт: {options.name}")
            raise CantGetData
        return parsed_collection

    mod_params = tuple({"uuid": options.uuid}.items())
    parsed_collection = _searching(report, options.num_attems, mod_params)

    if len(parsed_collection) != 1:
        raise CantGetData

    return str(parsed_collection[0])


def _create_report(
    crm: ActiveConnect,
    report: TypeReport,
    request_type: NaumenRequestType,
    *args: Sequence,
    mod_params: Union[Tuple[Tuple[str, Any]], Tuple] = (),
    mod_data: Union[Tuple[Tuple[str, Any]], Tuple] = (),
    **kwargs: Mapping,
) -> None:

    """Метод для создания отчета в NAUMEN отправкой POST запроса в NAUMEN.

    Args:
        crm: активное соединение с CRM.
        report: отчёт, который необходимо получить.
        request_type (NaumenRequestType): название необходимого типа запроса
        mod_params (Union[Tuple[Tuple[str, Any]], Tuple]: модифицированные
        параметры запроса
        mod_params (Union[Tuple[Tuple[str, Any]], Tuple]: модифицированные
        данные запроса
        *args: позиционные аргументы(не используются)
        **kwargs: именнованные аргументы для создания отчёта.

    Returns:
        None
    Raises:
        CantGetData: в случае невозможности вернуть коллекцию.
    """
    get_crm_response(
        crm,
        report,
        request_type,
        *args,
        mod_params=mod_params,
        mod_data=mod_data,
        method="POST",
        **kwargs,
    )


def _get_report(
    crm: ActiveConnect,
    report: TypeReport,
    request_type: NaumenRequestType,
    *args: Sequence,
    mod_params: Union[Tuple[Tuple[str, Any]], Tuple] = (),
    mod_data: Union[Tuple[Tuple[str, Any]], Tuple] = (),
    **kwargs: Mapping,
) -> str:

    """Метод для получения данных отчета из NAUMEN.

    Args:
        crm: активное соединение с CRM.
        report: отчёт, который необходимо получить.
        request_type (NaumenRequestType): название необходимого типа запроса
        mod_params (Union[Tuple[Tuple[str, Any]], Tuple]): модифицированные
        параметры запроса
        mod_params (Union[Tuple[Tuple[str, Any]], Tuple]): модифицированные
        данные запроса
        *args: позиционные аргументы(не используются)
        **kwargs: именнованные аргументы для создания отчёта.

    Returns:
        str: Данные отчета
    Raises:
        CantGetData: в случае невозможности вернуть коллекцию.
    """
    naumen_responce = get_crm_response(
        crm,
        report,
        request_type,
        *args,
        mod_params=mod_params,
        mod_data=mod_data,
        method="GET",
        **kwargs,
    )
    return naumen_responce.text
