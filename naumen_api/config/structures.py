from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, NamedTuple, Union

from requests import Session

from ..exceptions import CantGetData


@dataclass(frozen=True)
class ActiveConnect:

    """Класс данных для хранения сессии активного соединения c CRM Naumen.

    Attributes:
        session: активное соединение с crm системой.
    """

    session: Session


class NaumenRequest(NamedTuple):

    """Класс данных для хранения сформированного запроса к CRM Naumen.

    Attributes:
        url: ссылка для запроса
        header: header для запроса
        parsms: параметры для запроса
        data: данные запроса
        verify: верификация
    """

    url: str
    headers: Mapping
    params: Mapping
    data: Mapping
    verify: bool


class StatusType(Enum):

    """Enum перечисление видов статуса API .

    Attributes:
        _SUCCESS: успешный ответ
        _BAD_REQUEST: ответ при ошибке запроса
        _UNAUTHORIZED: ответ при проблемах с авторизацией
        _GATEWAY_TIMEOUT: при проблемах с Naumen

    """

    _SUCCESS = {
        "code": 200,
        "message": "OK",
        "description": "",
    }
    _BAD_REQUEST = {
        "code": 400,
        "message": "Bad Request",
        "description": "Wrong, incorrect request.",
    }
    _UNAUTHORIZED = {
        "code": 401,
        "message": "Unauthorized",
        "description": "Failed to create a connection. "
        "Please check the data and route to the system "
        "or config.json settings.",
    }
    _GATEWAY_TIMEOUT = {
        "code": 504,
        "message": "Naumen Does Not Answer",
        "description": "Remote end closed " "connection without response",
    }

    def __init__(self, status_content: Mapping):
        self.code = status_content["code"]
        self.message = status_content["message"]
        self.description = status_content["description"]


class PageType(Enum):

    """Класс данных для хранения типов страниц парсинга.

    Attributes:
        REPORT_LIST: Страница со списком сформированных отчётов.
        ISSUES_TABLE: Страница со списком обращений на группе.
        ISSUE_CARD: Страница карточки обращения.
        SERVICE_LEVEL_REPORT: Страница с отчётом service level.
        MMTR_LEVEL_REPORT: Страница с отчётом mttr level
        FLR_LEVEL_REPORT: Страница с отчётом flr level.
        SEARCH_RESULT_ISSUES_PAGE: Страница с результатом поиска обращений
        PAGINATION_PAGE: Парсинг пагинации
        AHT_LEVEL_REPORT: Страница с отчётом aht level.

    """

    REPORT_LIST_PAGE = 1
    ISSUES_TABLE_PAGE = 2
    ISSUE_CARD_PAGE = 3
    SERVICE_LEVEL_REPORT_PAGE = 4
    MMTR_LEVEL_REPORT_PAGE = 5
    FLR_LEVEL_REPORT_PAGE = 6
    SEARCH_RESULT_ISSUES_PAGE = 7
    PAGINATION_PAGE = 8
    AHT_LEVEL_REPORT_PAGE = 9


class NaumenRequestType(Enum):

    """Класс данных для хранения типов запросов к CRM NAUMEN.

    Attributes:
        CREATE_REPORT: Запрос на создание отчета.
        SEARCH_REPORT: Запрос для поиска созданного отчета.
        DELETE_REPORT: Запрос для удаления.

    """

    CREATE_REPORT = "create_report"
    SEARCH_REPORT = "search_report"
    DELETE_REPORT = "delete_report"
    CONTROL = "create_control_request"


class TypeReport(Enum):

    """Enum перечисление видов отчета.

    Attributes:
        ISSUE_CARD: карточка одного обращения.
        ISSUES_FIRST_LINE: таблица обращений первой линии.
        ISSUES_VIP_LINE: таблица обращений vip линии.
        ISSUES_SEARCH: запрос для поиска обращения
        SERVICE_LEVEL: отчет по уровню SL
        MTTR_LEVEL: отчет по уровню MTTR
        FLR_LAVEL: отчет по уровню FLR
        AHT_LEVEL: отчет по уровню AHT

    """

    ISSUE_CARD = "issue card"
    ISSUES_FIRST_LINE = "issues"
    ISSUES_VIP_LINE = "vip issues"
    ISSUES_SEARCH = "search issues"
    SERVICE_LEVEL = "service level report"
    MTTR_LEVEL = "mttr report"
    FLR_LEVEL = "flr report"
    CONTROL_ENABLE_SEARCH = "enable search"
    CONTROL_SELECT_SEARCH = "select search"
    AHT_LEVEL = "aht report"

    def __init__(self, value: Any):
        self.page = self._get_page()

    def _get_page(self) -> Union[PageType, None]:
        page_dict = {
            "ISSUE_CARD": PageType.ISSUE_CARD_PAGE,
            "ISSUES_FIRST_LINE": PageType.ISSUES_TABLE_PAGE,
            "ISSUES_VIP_LINE": PageType.ISSUES_TABLE_PAGE,
            "ISSUES_SEARCH": PageType.SEARCH_RESULT_ISSUES_PAGE,
            "SERVICE_LEVEL": PageType.SERVICE_LEVEL_REPORT_PAGE,
            "MTTR_LEVEL": PageType.MMTR_LEVEL_REPORT_PAGE,
            "FLR_LEVEL": PageType.FLR_LEVEL_REPORT_PAGE,
            "CONTROL_ENABLE_SEARCH": None,
            "CONTROL_SELECT_SEARCH": None,
            "AHT_LEVEL": PageType.AHT_LEVEL_REPORT_PAGE,
        }
        try:
            return page_dict[self.name]
        except (KeyError, TypeError) as exc:
            raise CantGetData from exc


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

    def __init__(self, value: Any):
        self.page = self._get_page()

    def _get_page(self) -> PageType:
        page_dict = {
            "ISSUES_SEARCH": PageType.SEARCH_RESULT_ISSUES_PAGE,
        }
        try:
            return page_dict[self.name]
        except (KeyError, TypeError) as exc:
            raise CantGetData from exc
