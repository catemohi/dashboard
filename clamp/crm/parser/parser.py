import logging
from typing import Callable, Mapping, Sequence

from . import flr, issue, mttr, report_page, service_level
from .parser_base import PageType
from ..exceptions import CantGetData


log = logging.getLogger(__name__)


def parse_naumen_page(page: str, name_report: str,
                      type_page: PageType) -> Sequence:
    """Функция парсинга страниц из crm Naumen, входной интерфейс подмодуля.

    Args:
        page: страница которую требуется распарсить.
        type_page: тип страницы
        name_report: уникальное имя сформированное отчёта.

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
        PageType.ISSUES_TABLE_PAGE: issue.parse,
        PageType.ISSUE_CARD_PAGE: issue.card_parse,
        PageType.SERVICE_LEVEL_REPORT_PAGE: service_level.parse,
        PageType.MMTR_LEVEL_REPORT_PAGE: mttr.parse,
        PageType.FLR_LEVEL_REPORT_PAGE: flr.parse,
    }

    parser = page_parsers[type_page]
    log.debug(f'Получен парсер: {parser.__name__} для страницы: {type_page}')
    parsed_collections = parser(page, name_report)
    return parsed_collections
