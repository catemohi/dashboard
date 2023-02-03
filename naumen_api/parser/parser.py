import logging
from typing import Callable, Mapping, Sequence, Union

from . import flr, issue_card, issues, mttr, report_page, service_level
from . import pagination, search_result_issues
from .parser_base import PageType
from ..exceptions import CantGetData


log = logging.getLogger(__name__)


def parse_naumen_page(page: str, type_page: Union[PageType, None],
                      name_report: str = '') -> Sequence:

    """Функция парсинга страниц из crm Naumen, входной интерфейс подмодуля.

    Args:
        page (str): страница которую требуется распарсить.
        type_page (Union[PageType, None]): тип страницы
        name_report (str): уникальное имя сформированное отчёта.
        По умолчанию ''

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
        PageType.REPORT_LIST_PAGE: report_page.parse,
        PageType.ISSUES_TABLE_PAGE: issues.parse,
        PageType.ISSUE_CARD_PAGE: issue_card.parse,
        PageType.SERVICE_LEVEL_REPORT_PAGE: service_level.parse,
        PageType.MMTR_LEVEL_REPORT_PAGE: mttr.parse,
        PageType.FLR_LEVEL_REPORT_PAGE: flr.parse,
        PageType.SEARCH_RESULT_ISSUES_PAGE: search_result_issues.parse,
        PageType.PAGINATION_PAGE: pagination.parse,
    }

    parser = page_parsers[type_page]
    log.debug(f'Получен парсер: {parser.__name__} для страницы: {type_page}')
    parsed_collections = parser(page, name_report)
    return parsed_collections
