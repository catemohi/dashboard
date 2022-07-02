from datetime import datetime, timedelta
from enum import Enum
from typing import Sequence,Literal
from dataclasses import dataclass
from bs4 import BeautifulSoup as bs
from urllib import parse

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
    
    
@dataclass
class Issue:
    
    """Класс данных для хранения данных по обращению.
    
        Attributes:
            uuid: уникалный идентификатор обьекта в CRM системе.
            number: номер обращения.
            name: название обращения.
            issue_type: тип обращения
            step: шаг на котром находится обращение.
            step_time: время последнего шага .
            responsible: ответственный за последний шаг.
            last_edit_time: время последнего изменения.
            vip_contractor: имеет ли клиент статус vip.
            create_date: дата создания обращения.
            uuid_service: уникалный идентификатор обьекта в CRM системе.
            name_service: название услуги.
            uuid_contractor: уникалный идентификатор обьекта в CRM системе.
            name_contractor: название контр агента.
            return_to_work_time: время возврата обращения в работу.
            description: описание обращения.
    """
    uuid: NaumenUUID
    number: int
    name: str
    issue_type: str
    step: str
    step_time: timedelta
    responsible: str
    last_edit_time: datetime
    vip_contractor: bool
    create_date: datetime
    uuid_service: NaumenUUID
    name_service: str
    uuid_contractor: NaumenUUID
    name_contractor: str
    return_to_work_time: datetime
    description: str
   
    
@dataclass(slots=True, frozen=True)
class ServiceLevel:
    
    """Класс данных для хранения данных отчета Service Level.
    
        Attributes:
            date: дата отсчёта.
            group: группа отчёта.
            total_issues: всего обращений.
            total_primary_issues: всего первичных обращений.
            num_issues_before_deadline: кол-во вовремя принятых обращений.
            num_issues_after_deadline: кол-во принятых после срока обращений.
            service_level: уровень servece level в процентах.
    """
    date: datetime
    group: str
    total_issues: int
    total_primary_issues: int
    num_issues_before_deadline: int
    num_issues_after_deadline: int
    service_level: float


@dataclass(slots=True, frozen=True)
class Mttr:
    
    """Класс данных для хранения данных отчета MTTR.
    
        Attributes:
            date: дата отсчёта.
            total_issues: всего обращений.
            average_mttr: cредний МТТР.
            average_mttr_tech_support: cредний МТТР тех.поддержки.

    """
    date: datetime
    total_issues: int
    average_mttr: timedelta
    average_mttr_tech_support: timedelta


@dataclass(slots=True, frozen=True)
class Flr:
    
    """Класс данных для хранения данных отчета FLR.
    
        Attributes:
            date: дата отсчёта.
            flr_level: уровень flr level в процентах.
            num_issues_closed_independently: Обращения закрытые самостоятельно.
            total_primary_issues: всего первичных обращений.

    """
    date: datetime
    flr_level: float
    num_issues_closed_independently: int
    total_primary_issues: int


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
    
    
def _get_url_param_value(url: str, needed_param: str):
    """Функция парсинга URL и получение значения необходимого GET параметра.
    
    Args:
        url: строчная ссылка.
        needed_param: ключ необходимого GET параметра. 
        
    Returns:
        Значение необходимого GET параметра
        
    Raises:

    """    
    param_value = parse.parse_qs(parse.urlparse(url).query)[needed_param][0]  
    return param_value


def _parse_reports_lits(text: str, name: str) -> Sequence[NaumenUUID] | \
                                                      Sequence[Literal['']]:
    """Функция парсинга страницы с отчётами и получение UUID отчёта.
    
    Args:
        text: сырой текст страницы.
        name: уникальное название отчета.
        
    Returns:
        Коллекцию с найденными элементами.
        
    Raises:

    """
    soup = bs(text, "html.parser")
    report_tag = soup.select(f'[title="{name}"]')
    if report_tag:
        url = report_tag[0]['href']
        return (NaumenUUID(_get_url_param_value(url, 'uuid')), ) 
    return ('',)
        
        


def _parse_issues_table(text: str) -> Sequence | Sequence[Literal['']]:
    """Функция парсинга страницы с обращениями на группе.
    
    Args:
        text: сырой текст страницы.
        
    Returns:
        Коллекцию с найденными элементами.
        
    Raises:
        CantGetData: Если не удалось найти данные.
    """
    soup = bs(text, "html.parser")
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
    soup = bs(text, "html.parser")
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
    soup = bs(text, "html.parser")
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
    soup = bs(text, "html.parser")
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
    soup = bs(text, "html.parser")
    #TODO Логика парсинга.