import logging
from time import sleep
from typing import Sequence

from .crm import ActiveConnect, NaumenRequest, get_crm_response
from ..config.structures import SearchOptions
from ..config.config import get_params_find_create_report
from ..config.structures import PageType
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
        parsed_collection = parse_naumen_page(page_text, options.name,
                                              PageType.REPORT_LIST_PAGE)
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
