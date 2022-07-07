from datetime import datetime, timedelta
from calendar import monthrange
from enum import Enum
from typing import Sequence,Literal, Iterable
from dataclasses import dataclass, replace
from bs4 import BeautifulSoup, element
from urllib import parse
from re import findall

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
            vip_contragent: имеет ли клиент статус vip.
            creation_date: дата создания обращения.
            uuid_service: уникалный идентификатор обьекта в CRM системе.
            name_service: название услуги.
            uuid_contragent: уникалный идентификатор обьекта в CRM системе.
            name_contragent: название контр агента.
            return_to_work_time: время возврата обращения в работу.
            description: описание обращения.
    """
    uuid: str
    number: int
    name: str
    issue_type: str
    step: str
    step_time: timedelta
    responsible: str
    last_edit_time: datetime
    vip_contragent: bool
    creation_date: datetime
    uuid_service: str
    name_service: str
    uuid_contragent: str
    name_contragent: str
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
        Sequence: Результат парсинга страницы, коллекция распаршенных элементов
        
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
    
    
def _get_url_param_value(url: str, needed_param: str) -> str:
    """Функция парсинга URL и получение значения необходимого GET параметра.
    
    Args:
        url: строчная ссылка.
        needed_param: ключ необходимого GET параметра. 
        
    Returns:
        str: Значение необходимого GET параметра
        
    Raises:
        CantGetData: проблема с парсингом данных
    """    
    if not url:
        raise CantGetData
    param_value = parse.parse_qs(parse.urlparse(url).query)[needed_param][0]  
    return param_value

def _get_columns_name(soup: BeautifulSoup) -> Iterable[str]:
    """Функция парсинга названий столбцов отчётов.
    
    Args:
        soup: подготовленная для парсинга HTML страница.
        
    Returns:
        Коллекцию с названиями столбцов.
        
    Raises:

    """
    column_name = [tag.text.strip() for tag in soup.select(".supp tr th b")]
    return tuple(column_name)

def  _get_step_duration(raw_duration: str) -> timedelta:
    """Функция для парсинга строки продолжительности в обьект timedelta.
    
    Args:
        raw_duration: строчная задержка.
        
    Returns:
        Объект задержки шага.
        
    Raises:

    """
    duration = dict(zip(('days', 'h', 'min'), findall(r'\d+', raw_duration)))
    duration = timedelta(days=duration['days'],
                         hours=duration['h'], minutes=duration['min'])
    return duration
         

def  _get_issue_num(issue_name: str) -> str:
    """Функция для парсинга номера обращения.
    
    Args:
        issue_name: имя обращения.
        
    Returns:
        Номер обращения.
        
    Raises:

    """
    number = findall(r'\d{7,10}', issue_name)[0]
    return number

def _parse_reports_lits(text: str, name: str) -> Sequence[str] | \
                                                      Sequence[Literal['']]:
    """Функция парсинга страницы с отчётами и получение UUID отчёта.
    
    Args:
        text: сырой текст страницы.
        name: уникальное название отчета.
        
    Returns:
        Sequence | Sequence[Literal['']]: Коллекцию с найденными элементами.
        
    Raises:

    """
    soup = BeautifulSoup(text, "html.parser")
    report_tag = soup.select(f'[title="{name}"]')
    if report_tag:
        url = report_tag[0]['href']
        return (str(_get_url_param_value(url, 'uuid')), ) 
    return ('',)
        
        
def _parse_issues_table(text: str) -> Sequence[Issue] | Sequence[Literal['']]:
    """Функция парсинга страницы с обращениями на группе.
    
    Args:
        text: сырой текст страницы.
        
    Returns:
        Sequence | Sequence[Literal['']]: Коллекцию с найденными элементами.
        
    Raises:
        CantGetData: Если не удалось найти данные.
    """
    soup = BeautifulSoup(text, "html.parser")
    category = _get_columns_name(soup)
    rows = soup.select(".supp tr")[7:-1]
    if len(rows) < 1:
        return ('',)
    def parse_table_row(row: element.Tag, 
                        category: Iterable[str]) -> Issue:
        """Функция парсинга строки таблицы.

        Args:
            row: сырая строка.
            category: названия столбцов, строки.

        Returns:
            Sequence[Issue] | Sequence[Literal['']: Коллекцию обращений.
            
        """
        issue = Issue()
        issus_params = [
            col.text.replace('\n', '').strip() for col in row.select('td')]
        issues_dict = dict(zip(category, issus_params))
        _url = (row.find('a', href=True)['href'])
        issue.uuid = _get_url_param_value(_url, 'uuid')
        issue.number = _get_issue_num(issues_dict['Обращение'])
        issue.step_time = _get_step_duration(issues_dict['Время решения'])
        issue.last_edit_time = datetime.now() - issue.step_time
        issue.name = issues_dict['Обращение']
        issue.issue_type = issues_dict['Тип обращения']
        issue.step = issues_dict['Состояние']
        issue.responsible = issues_dict['Ответственный']
        return issue   
    
    issues = [parse_table_row(row, category) for row in rows]
    return issues


def _get_contragent_params(soup: BeautifulSoup) -> Iterable[str]:
    """Функция парсинга данных контрагента.
    
    Args:
        soup: подготовленная для парсинга HTML страница.
        
    Returns:
        Iterable[str]: Коллекцию с параметрами контрагента.
        
    Raises:

    """
    contragent_tag = soup.find('td',id='contragent')
    if contragent_tag:
        name = contragent_tag.text.replace('\n', '').strip()
        _url = contragent_tag.find('a')['href']
        try: uuid = _get_url_param_value(_url, 'uuid')
        except CantGetData: uuid = ''
        return (name, uuid)
    return ('', '')

def _get_description(soup: BeautifulSoup) -> str:
    """Функция парсинга данных описания обращения.
    
    Args:
        soup: подготовленная для парсинга HTML страница.
        
    Returns:
        str: Описание обращения.
        
    Raises:
    
    """
    description = soup.find('td', id="requestDescription")
    if description:
        description = description\
                                .text\
                                .replace('\r', '')\
                                .replace('\t', '')\
                                .replace('\n', '')\
                                .strip()
        if len(description) > 140:
            description = description[:137] + '...'
        return description
    return ''


def _get_creation_date(soup: BeautifulSoup) -> datetime:
    """Функция парсинга даты создания обращения.
    
    Args:
        soup: подготовленная для парсинга HTML страница.
        
    Returns:
        datetime: дата создания обращения.
        
    Raises:
    
    """
    creation_date = soup.find('td', id="creationDate")
    if creation_date:
        str_datetime = creation_date.text.replace('\n', '').strip()
        return datetime.strptime(str_datetime, '%d.%m.%Y %H:%M')
    return datetime.now()
        
def _get_service_params(soup: BeautifulSoup) -> Iterable[str]:
    """Функция парсинга данных услуги.
    
    Args:
        soup: подготовленная для парсинга HTML страница.
        
    Returns:
        Iterable[str]: коллекцию с параметрами.
        
    Raises:

    """
    services = soup.find('td', id="services")
    if services:
        name = services.text.replace('\n', '').strip()
        _url = services.find('a')['href']
        try: uuid = _get_url_param_value(_url, 'uuid')
        except CantGetData: uuid = ''
        return (name, uuid)
    return ('','')    


def _get_return_to_work_time(soup: BeautifulSoup) -> datetime:
    """Функция парсинга данных времени возврата в работу.
    
    Args:
        soup: подготовленная для парсинга HTML страница.
        
    Returns:
        datetime: время возврата в работу
        
    Raises:

    """
    return_times = (soup.find('td', id="obrd"),soup.find('td', id="obrd1"),
                    soup.find('td', id="obrd2"))
    return_times = [
        time.text.replace('\n', '').strip() for time in return_times if time]
    if return_times:
        times = [datetime.strptime(
            time, '%d.%m.%Y %H:%M') for time in return_times]
        if len(times) > 1:
            times.sort()
        return times[-1]
    return datetime.now() + timedelta(days=365)
        

def _parse_card_issue(text: str, issue: Issue) -> Issue:
    """Функция парсинга картточки обращения.
    
    Args:
        text: сырой текст страницы.
        issue: обращение, поля которого нужно дополнить.
        
    Returns:
        Issue: Модифицированный объект обращения.
        
    Raises:

    """
    soup = BeautifulSoup(text, "html.parser")
    issue.name_contragent, issue.uuid_contragent = _get_contragent_params(soup)
    issue.description = _get_description(soup)
    issue.creation_date = _get_creation_date(soup)
    issue.name_service, issue.uuid_service = _get_service_params(soup)
    issue.return_to_work_time = _get_return_to_work_time(soup)
    return issue  
    
    
def _parse_service_lavel_report(text: str) -> Sequence | Sequence[Literal['']]:
    """Функция парсинга картточки обращения.
    
    Args:
        text: сырой текст страницы.
        
    Returns:
        Sequence | Sequence[Literal['']]: Коллекцию с найденными элементами.
        
    Raises:
        CantGetData: Если не удалось найти данные.
    """
    soup = BeautifulSoup(text, "html.parser")
    #TODO Логика парсинга.
    
    
def _parse_mttr_lavel_report(text: str) -> Sequence | Sequence[Literal['']]:
    """Функция парсинга картточки обращения.
    
    Args:
        text: сырой текст страницы.
        
    Returns:
        Sequence | Sequence[Literal['']]: Коллекцию с найденными элементами.
        
    Raises:
        CantGetData: Если не удалось найти данные.
    """
    soup = BeautifulSoup(text, "html.parser")
    #TODO Логика парсинга.
    

def _parse_flr_lavel_report(text: str) -> Sequence | Sequence[Literal['']]:
    """Функция парсинга картточки обращения.
    
    Args:
        text: сырой текст страницы.
        
    Returns:
        Sequence | Sequence[Literal['']]: Коллекцию с найденными элементами.
        
    Raises:
        CantGetData: Если не удалось найти данные.
    """
    soup = BeautifulSoup(text, "html.parser")
    category = _get_columns_name(soup)
    rows = soup.select(".supp tr")[9:-1]
    rows = [row.select('td') for row in rows]
    rows = [[col.text.replace('\n', '').strip() for col in row] for row in rows]
    rows[0].pop(0)
    day_list = [dict(zip(category[1:], row)) for row in rows]
    # days_in_mouth = monthrange(year,month)[1]
    # mouth_group_flr_dict = {}
    # for day in range(1,days_in_mouth + 1):
    #     current_date = date(year,month,day)
    #     [mouth_group_flr_dict.update({current_date: need_day}) for need_day in day_list if need_day['День'] == str(day)]
    #     if current_date not in mouth_group_flr_dict:
    #         mouth_group_flr_dict[current_date] = {'День': 'n/a', 'FLR по дн (в %)': '0.0', 'Закрыто ТП без др отд': '0', 'Количество первичных': '0'}
    #     mouth_group_flr_dict[current_date]['День'] = current_date
    # return mouth_group_flr_dict
