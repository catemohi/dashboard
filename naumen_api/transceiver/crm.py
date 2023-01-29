import logging
from dataclasses import dataclass
from typing import Literal, Mapping, NamedTuple

from requests import Session, Response
from requests.adapters import HTTPAdapter, Retry
from requests.packages import urllib3

from ..config.config import CONFIG
from ..exceptions import ConnectionsFailed, CantGetData


urllib3.disable_warnings()
log = logging.getLogger(__name__)
DOMAIN = Literal['CORP.ERTELECOM.LOC', 'O.WESTCALL.SPB.RU']


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


def get_session(username: str, password: str, domain: DOMAIN) -> ActiveConnect:
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

    url = CONFIG.config['url']['login']
    if not all([username, password, domain, url]):
        raise ConnectionsFailed
    session = Session()
    retries = Retry(total=5, backoff_factor=0.5)
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.mount('http://', HTTPAdapter(max_retries=retries))

    data = {'login': username,
            'password': password,
            'domain': domain,
            }
    response = session.post(url=url, data=data, verify=False)
    if response.status_code != 200:
        raise ConnectionsFailed

    return ActiveConnect(session)


def get_crm_response(crm: ActiveConnect,
                     rq: NaumenRequest,
                     method: Literal['GET', 'POST'] = 'POST') -> Response:
    """Функция для получения ответа из CRM системы.

    Args:
        crm: сессия с CRM Naumen.
        request: запрос в CRM Naumen.
        method: HTTP метод.

    Returns:
        Ответ сервера CRM системы Naumen

    Raises:
        CantGetData: если не удалось получить ответ.

    """
    if method == 'POST':
        _response = crm.session.post(url=rq.url, headers=rq.headers,
                                     params=rq.params,
                                     data=rq.data, verify=rq.verify)
    else:
        _response = crm.session.get(url=rq.url,
                                    headers=rq.headers,
                                    params=rq.params,
                                    verify=rq.verify)
    if _response.status_code != 200:
        raise CantGetData

    return _response
