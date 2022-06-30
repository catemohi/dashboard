from requests import Session
from typing import Iterable, Literal, Mapping, TypeAlias, Sequence
from dataclasses import dataclass
from enum import Enum
from time import sleep


from config import *
from exceptions import ConnectionsFailed, CantGetData
from parser import PageType, parse_naumen_page


NaumenUUID: TypeAlias = str 


@dataclass(slots=True, frozen=True)
class ActiveConnect:
    
    """Класс данных для хранения сессии активного соединения c CRM Naumen.
    
        Attributes:
            session: активное соединение с crm системой.
    """
    session: Session


class TypeReport(Enum):
    
    """Enum перечисление видов отчета.
    
        Attributes:
            ISSUES_FIRST_LINE: таблица обращений первой линии.
            ISSUES_VIP_LINE: таблица обращений vip линии.
            SERVICE_LEVEL: отчет по уровню SL
            MTTR_LEVEL: отчет по уровню MTTR
            FLR_LAVEL: отчет по уровню FLR
    
    """
    ISSUES_FIRST_LINE = 1
    ISSUES_VIP_LINE = 2
    SERVICE_LEVEL = 3
    MTTR_LEVEL = 4
    FLR_LEVEL = 5 
    

@dataclass(slots=True, frozen=True)
class NaumenRequest:
    
    """Класс данных для хранения сформированного запроса к CRM Naumen.
    
        Attributes:
            url: ссылка для запроса
            header: header для запроса
            parsms: параметры для запроса
            data: данные запроса
            verify: верификация
    """
    url: str
    header: Mapping
    params: Mapping
    data: Mapping
    verify: bool


@dataclass(slots=True, frozen=True)
class ReportSearchParams(NaumenRequest):
    
    """Класс данных для хранения параметров поиска сформированного отчета.
    
        Attributes:
            name: уникальное имя отчета
            delay_attems: задержка в секундах, между попытками
            num_attems: количество попыток.
    """
    name: str
    delay_attems: int
    num_attems: int


def get_session(username: str, password: str,
                domain: Literal['CORP.ERTELECOM.LOC', 'O.WESTCALL.SPB.RU']) -> ActiveConnect:
    """Функция для создания сессии с CRM системой.
    
    Args:
        username: имя пользователя в Naumen
        password: пароль пользователя
        domain: домен учетной записи
        
    Returns:
        Session: обьект сессии с CRM системой.
        
    Raises:
        ConnectionsFailed: если не удалось подключиться к CRM системе.
        
    """
    session = Session()
    url = f'{NAUMEN_MAIN_URL}{NAUMEN_LOGIN_URL}'
    data = {'login': username,
            'password': password,
            'domain': domain
            }
    response = session.post(url=url, data=data, verify=False)
    
    if response.status_code != 200: 
        raise ConnectionsFailed
    
    return ActiveConnect(session)


def get_issues(crm: ActiveConnect, line: Literal['first', 'vip']) -> None:
    """Получить все обращения на линию тех.поддержки.
    
    Args:
        crm: сессия с CRM Naumen.
        line: название линии обращения которой необходимо получить.
        
    Returns:
        Ответ сервера CRM системы Naumen 
        
    Raises:
        ConnectionsFailed: если не удалось подключиться к CRM системе.
    
    """
    pass

def _get_crm_response(crm: ActiveConnect, request: NaumenRequest) -> str:
    """Функция для получения ответа из CRM системы.
    
    Args:
        crm: сессия с CRM Naumen.
        request: запрос в CRM Naumen.
        
    Returns:
        Ответ сервера CRM системы Naumen 
        
    Raises:
        ConnectionsFailed: если не удалось подключиться к CRM системе.
    
    """
    
    response = crm.session.post(url=request.url,
                                headers=request.header,
                                params=request.params, 
                                data=request.data, verify=request.verify)
    if response.status_code != 200 or not response.text: 
        raise ConnectionsFailed
    
    return response.text


def _create_report_in_crm(crm: ActiveConnect, report: TypeReport) -> None:
    """Создание отчета в CRM системе Naumen.
    
    Args:
    
    Returns:
    
    Raises:
    
    """
    if not isinstance(report, TypeReport):
        raise CantGetData
    
    url = f'{NAUMEN_MAIN_URL}{NAUMEN_CREATE_REPORTS_URL}'
    verify = False
    header = {}
    
    request_creators = {
        TypeReport.ISSUES_FIRST_LINE: _create_request_issues_first_line,
        TypeReport.ISSUES_VIP_LINE: _create_request_issues_vip_line,
        TypeReport.SERVICE_LEVEL: _create_request_service_lavel,
        TypeReport.MTTR_LEVEL: _create_request_mttr_lavel,
        TypeReport.FLR_LEVEL: _create_request_flr_lavel
        }

    try:
        request_creator = request_creators.get[report]
        request, search_params = request_creator(url,header,verify)
    except KeyError:
        raise CantGetData
    
    _get_crm_response(crm, request)
    report_uuid = _find_report_uuid(crm, search_params)
    #TODO

def _create_request_issues_first_line(url: str, header: Mapping,
                                     verify: bool) -> tuple[
                                         NaumenRequest, ReportSearchParams]:
    """Функция формирования запроса обращений первой линии.
    
    Args:
        url: ссылка для запроса
        header: header запроса
        verify: verify запроса
    
    Returns:
        NaumenRequest: сформированный запрос для CRM Naumen
        ReportSearchParams: параметры для поиска отчета в CRM Naumen
    Raises:
    
    """
    #TODO строчка получения данных для запроса
    params = {}
    data = {}
    name = ''
    delay_attems = 1 
    num_attems = 1
    request = NaumenRequest(url, header, params, data, verify)
    search_params = ReportSearchParams(*request,
                                       name, delay_attems, num_attems)
    return (request, search_params)


def _create_request_issues_vip_line(url: str, header: Mapping,
                                     verify: bool) -> tuple[
                                         NaumenRequest, ReportSearchParams]:
    """Функция формирования запроса обращений вип линии.
    
    Args:
        url: ссылка для запроса
        header: header запроса
        verify: verify запроса
    
    Returns:
        NaumenRequest: сформированный запрос для CRM Naumen
        ReportSearchParams: параметры для поиска отчета в CRM Naumen
    Raises:
    
    """
    #TODO строчка получения данных для запроса
    params = {}
    data = {}
    name = ''
    delay_attems = 1 
    num_attems = 1
    request = NaumenRequest(url, header, params, data, verify)
    search_params = ReportSearchParams(*request,
                                       name, delay_attems, num_attems)
    return (request, search_params)


def _create_request_service_lavel(url: str, header: Mapping,
                                     verify: bool) -> tuple[
                                         NaumenRequest, ReportSearchParams]:
    """Функция формирования запроса уровня SL.
    
    Args:
        url: ссылка для запроса
        header: header запроса
        verify: verify запроса
    
    Returns:
        NaumenRequest: сформированный запрос для CRM Naumen
        ReportSearchParams: параметры для поиска отчета в CRM Naumen
    Raises:
    
    """
    #TODO строчка получения данных для запроса
    params = {}
    data = {}
    name = ''
    delay_attems = 1 
    num_attems = 1
    request = NaumenRequest(url, header, params, data, verify)
    search_params = ReportSearchParams(*request,
                                       name, delay_attems, num_attems)
    return (request, search_params)


def _create_request_mttr_lavel(url: str, header: Mapping,
                                     verify: bool) -> tuple[
                                         NaumenRequest, ReportSearchParams]:
    """Функция формирования запроса уровня MTTR.
    
    Args:
        url: ссылка для запроса
        header: header запроса
        verify: verify запроса
    
    Returns:
        NaumenRequest: сформированный запрос для CRM Naumen
        ReportSearchParams: параметры для поиска отчета в CRM Naumen
    Raises:
    
    """
    #TODO строчка получения данных для запроса
    params = {}
    data = {}
    name = ''
    delay_attems = 1 
    num_attems = 1
    request = NaumenRequest(url, header, params, data, verify)
    search_params = ReportSearchParams(*request,
                                       name, delay_attems, num_attems)
    return (request, search_params)


def _create_request_flr_lavel(url: str, header: Mapping,
                                     verify: bool) -> tuple[
                                         NaumenRequest, ReportSearchParams]:
    """Функция формирования запроса уровня FLR.
    
    Args:
        url: ссылка для запроса
        header: header запроса
        verify: verify запроса
    
    Returns:
        NaumenRequest: сформированный запрос для CRM Naumen
        ReportSearchParams: параметры для поиска отчета в CRM Naumen
    Raises:
    
    """
    #TODO строчка получения данных для запроса
    params = {}
    data = {}
    name = ''
    delay_attems = 1 
    num_attems = 1
    request = NaumenRequest(url, header, params, data, verify)
    search_params = ReportSearchParams(*request,
                                       name, delay_attems, num_attems)
    return (request, search_params)
    
 
def _find_report_uuid(crm: ActiveConnect,
                        params: ReportSearchParams) -> NaumenUUID:
    """Функция поиска сформированного отчета в CRM Naumen.
    
    Args:
        crm:  активное соединение с CRM Naumen.
        params: параметры для поиска отчета в CRM Naumen.
        
    Returns:
        NaumenUUID: строчный идентификатор обьекта в CRM Naumen.
        
    Raises:
        ConnectionsFailed: если не удалось подключиться к CRM системе.
    
    """
    *search_request, report_name, delay_attems, num_attems = params
    
    def _searching(num_attems: int, 
                  search_request: NaumenRequest) -> Sequence[str]:
        """Рекурсивная функция поиска отчета в CRM системе.
        
        Args:
            num_attems: количество попыток поиска.
            search_request: запрос для поиска отчета.
            
        Returns:
            Sequence[NaumenUUID]: коллекцию внутри которой идентификатор обьекта в CRM Naumen.
            
        Raises:
        
        """
        sleep(delay_attems)
        page_text = _get_crm_response(crm,search_request)
        parsed_collection = parse_naumen_page(page_text,report_name,
                                              PageType.REPORT_LIST_PAGE)
        if not parsed_collection: 
            if num_attems >= 1:
                return _searching(num_attems - 1, search_request)
            raise CantGetData

        return parsed_collection
    
    parsed_collection = _searching(num_attems, search_request)
    if len(parsed_collection) != 1:
        raise CantGetData
    
    return NaumenUUID(parsed_collection[0])