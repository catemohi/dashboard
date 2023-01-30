import logging
from time import sleep
from typing import Sequence, Iterable

from .crm import ActiveConnect, NaumenRequest, get_crm_response
from ..config.structures import SearchOptions
from ..config.config import get_params_find_create_report
from ..config.structures import PageType, SearchType
from ..exceptions import CantGetData
from ..parser.parser import parse_naumen_page


log = logging.getLogger(__name__)


def find_report_uuid(crm: ActiveConnect, options: SearchOptions) -> str:
    """Функция поиска сформированного отчета в CRM Naumen.

    Args:
        crm:  активное соединение с CRM Naumen.
        params: параметры для поиска отчета в CRM Naumen.

    Returns:
        str: строчный идентификатор обьекта в CRM Naumen.

    Raises:
        ConnectionsFailed: если не удалось подключиться к CRM системе.

    """

    def _searching(num_attems: int, search_request: NaumenRequest,
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
        log.debug(f'Сформированный запрос: {search_request}')
        sleep(options.delay_attems)
        response = get_crm_response(crm, search_request, 'GET')
        page_text = response.text
        parsed_collection = parse_naumen_page(page_text,
                                              PageType.REPORT_LIST_PAGE,
                                              options.name,
                                              )
        if parsed_collection is None:
            if num_attems >= 1:
                return _searching(num_attems - 1, search_request)
            log.error(f'Не удалось найти отчёт: {options.name}')
            raise CantGetData
        return parsed_collection

    url, headers, params, data, verify = get_params_find_create_report()
    params.update({'uuid': options.uuid})
    search_request = NaumenRequest(url, headers, params, data, verify)
    parsed_collection = _searching(options.num_attems, search_request)

    if len(parsed_collection) != 1:
        raise CantGetData

    return str(parsed_collection[0])


def search(crm: ActiveConnect, report: SearchType, *args,
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

    if report in [SearchType.ISSUES_SEARCH]:
        naumen_responce = _create_report(crm, report, *args, **kwargs)
        page_text = naumen_responce.text
        log.debug('Проверка количества страниц')
        page_count = parse_naumen_page(page_text, PageType.PAGINATION_PAGE)
        log.debug(f'Количество страниц: {page_count}')
        page_collection = [page_text]
        for i in range(1, page_count):
            naumen_responce = _create_report(
                crm, report, *args, **{'mod_params': {'pagination': str(i)},
                                       **kwargs})
            page_collection.append(naumen_responce.text)
        collect = []
        for page in page_collection:
            collect += parse_naumen_page(page, report.page)
        return collect