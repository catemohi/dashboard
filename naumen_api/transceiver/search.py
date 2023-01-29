import logging
from enum import Enum
from time import sleep
from typing import NamedTuple, Sequence

from .crm import ActiveConnect, NaumenRequest, get_crm_response
from ..config.config import get_params_find_create_report
from ..exceptions import CantGetData
from ..parser.parser import parse_naumen_page
from ..parser.parser_base import PageType


log = logging.getLogger(__name__)


class SearchOptions(NamedTuple):

    """Класс данных для хранения опций поиска созданных отчетов в CRM.

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


class SearchType(Enum):

    """Enum перечисление видов поиска в CRM NAUMEN.

        Attributes:
            ISSUES_SEARCH: запрос для поиска обращения

    """
    ISSUES_SEARCH = "search issues"

    def __init__(self, value):
        self.page = self._get_page()

    def _get_page(self):
        page_dict = {
            'ISSUES_SEARCH':  PageType.SEARCH_RESULT_ISSUES_PAGE,
        }
        try:
            return page_dict[self.name]
        except (KeyError, TypeError):
            raise CantGetData


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

    def _searching(num_attems: int, search_request: NaumenRequest
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
