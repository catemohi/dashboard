import logging
from typing import Any, Literal, Tuple, Union

from requests import Response, Session
from requests.adapters import HTTPAdapter, Retry
from requests.packages import urllib3

from ..config.config import CONFIG, create_naumen_request
from ..config.structures import ActiveConnect, NaumenRequestType
from ..config.structures import SearchType, TypeReport
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
                     obj: Union[TypeReport, SearchType],
                     request_type: NaumenRequestType,
                     *args,
                     mod_params: Tuple[Tuple[str, Any]] = (),
                     mod_data: Tuple[Tuple[str, Any]] = (),
                     method: Literal['GET', 'POST'] = 'POST',
                     **kwargs) -> Response:
    """Функция для получения ответа из CRM системы.

    Args:
        crm: сессия с CRM Naumen.
        obj (Union[TypeReport, SearchType]): обьект которого строится запрос.
        mod_params (Tuple[Tuple[str, Any]]): модифицированные параметры запроса
        mod_params (Tuple[Tuple[str, Any]]): модифицированные данные запроса
        method: HTTP метод.

    Returns:
        Ответ сервера CRM системы Naumen

    Raises:
        CantGetData: если не удалось получить ответ.

    """
    rq = create_naumen_request(obj, request_type, mod_params,
                               mod_data, *args, **kwargs)
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
