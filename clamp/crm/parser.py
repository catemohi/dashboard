from enum import Enum
from typing import Sequence,Literal


from exceptions import CantGetData
from client import NaumenUUID

class PageType(Enum):
    
    """Класс данных для хранения типов страниц парсинга.
    
        Attributes:
            REPORT_LIST: Страница со списком сформированных отчётов.
            ISSUES_TABLE: Страница со списком обращений на группе.
            ISSUE_CARD: Страница карточки обращения. 
            SERVICE_LEVEL_REPORT: Страница с отчётом service level.
            MMTR_LEVEL_REPORT: Страница с отчётом mttr level 
            FLR_LEVEL_REPORT: Страница с отчётом flr level.
    
    """
    REPORT_LIST_PAGE = 1
    ISSUES_TABLE_PAGE = 2
    ISSUE_CARD_PAGE = 3
    SERVICE_LEVEL_REPORT_PAGE = 4
    MMTR_LEVEL_REPORT_PAGE = 5
    FLR_LEVEL_REPORT_PAGE = 6
    
    
def parse_naumen_page(page: str, name_report: str,
                      type_page: PageType) -> Sequence:
    """Функция парсинга страниц из crm Naumen, входной интерфейс подмодуля.
    
    Args:
        page: страница которую требуется распарсить.
        type_page: тип страницы
        name_report: уникальное имя сформированное отчёта.
    
    Returns:
        Результат парсинга страницы, коллекция распаршенных элементов
        
    Raises:
        CantGetData: в неправильном сценарии работы функции.
    
    """
    if not isinstance(type_page, PageType):
         raise CantGetData
     
    page_parsers = {
        PageType.REPORT_LIST_PAGE: _parse_reports_lits,
        PageType.ISSUES_TABLE_PAGE: _parse_issues_table,
        PageType.ISSUE_CARD_PAGE: _parse_card_issue,
        PageType.SERVICE_LEVEL_REPORT_PAGE: _parse_service_lavel_report,
        PageType.MMTR_LEVEL_REPORT_PAGE: _parse_mttr_lavel_report,
        PageType.FLR_LEVEL_REPORT_PAGE: _parse_flr_lavel_report,
    }
    
    parser = page_parsers[type_page]
    
    #TODO parsed_collections: Sequence = parser(...)
    #TODO return parsed_collections
    
    
def _parse_reports_lits(text: str, name: str) -> Sequence[NaumenUUID] | \
                                                      Sequence[Literal['']]:
    """Функция парсинга страницы с отчётами и получение UUID отчёта.
    
    Args:
        text: сырой текст страницы.
        name: уникальное название отчета.
        
    Returns:
        Коллекцию с найденными элементами.
        
    Raises:
        CantGetData: Если не удалось найти данные.

    """
    #TODO Логика парсинга.
    pass


def _parse_issues_table(text: str) -> Sequence | Sequence[Literal['']]:
    """Функция парсинга страницы с обращениями на группе.
    
    Args:
        text: сырой текст страницы.
        
    Returns:
        Коллекцию с найденными элементами.
        
    Raises:
        CantGetData: Если не удалось найти данные.
    """
    pass
    #TODO Логика парсинга.


def _parse_card_issue(text: str) -> Sequence | Sequence[Literal['']]:
    """Функция парсинга картточки обращения.
    
    Args:
        text: сырой текст страницы.
        
    Returns:
        Коллекцию с найденными элементами.
        
    Raises:
        CantGetData: Если не удалось найти данные.
    """
    pass
    #TODO Логика парсинга.
    
    
def _parse_service_lavel_report(text: str) -> Sequence | Sequence[Literal['']]:
    """Функция парсинга картточки обращения.
    
    Args:
        text: сырой текст страницы.
        
    Returns:
        Коллекцию с найденными элементами.
        
    Raises:
        CantGetData: Если не удалось найти данные.
    """
    pass
    #TODO Логика парсинга.
    
    
def _parse_mttr_lavel_report(text: str) -> Sequence | Sequence[Literal['']]:
    """Функция парсинга картточки обращения.
    
    Args:
        text: сырой текст страницы.
        
    Returns:
        Коллекцию с найденными элементами.
        
    Raises:
        CantGetData: Если не удалось найти данные.
    """
    pass
    #TODO Логика парсинга.
    

def _parse_flr_lavel_report(text: str) -> Sequence | Sequence[Literal['']]:
    """Функция парсинга картточки обращения.
    
    Args:
        text: сырой текст страницы.
        
    Returns:
        Коллекцию с найденными элементами.
        
    Raises:
        CantGetData: Если не удалось найти данные.
    """
    pass
    #TODO Логика парсинга.