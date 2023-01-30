import logging
from typing import Literal

from requests import Response, Session
from requests.adapters import HTTPAdapter, Retry
from requests.packages import urllib3

from ..config.config import CONFIG
from ..config.structures import ActiveConnect, NaumenRequest
from ..exceptions import CantGetData, ConnectionsFailed


urllib3.disable_warnings()
log = logging.getLogger(__name__)
DOMAIN = Literal['CORP.ERTELECOM.LOC', 'O.WESTCALL.SPB.RU']


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
