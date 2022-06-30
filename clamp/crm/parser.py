from enum import Enum
from typing import Sequence

from exceptions import CantGetData

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
        PageType.REPORT_LIST_PAGE: '',
        PageType.ISSUES_TABLE_PAGE: '',
        PageType.ISSUE_CARD_PAGE: '',
        PageType.SERVICE_LEVEL_REPORT_PAGE: '',
        PageType.MMTR_LEVEL_REPORT_PAGE: '',
        PageType.FLR_LEVEL_REPORT_PAGE: ''
    }
    
    parser = page_parsers[type_page]
    
    #TODO parsed_collections: Sequence = parser(...)
    #TODO return parsed_collections