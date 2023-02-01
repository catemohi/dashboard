import logging
from typing import Any, Literal, Tuple, Union, Sequence, Mapping

from requests import Response, Session
from requests.adapters import HTTPAdapter, Retry
from requests.packages.urllib3 import disable_warnings

from ..config.config import CONFIG, create_naumen_request
from ..config.structures import ActiveConnect, NaumenRequestType
from ..config.structures import SearchType, TypeReport
from ..exceptions import CantGetData, ConnectionsFailed


disable_warnings()
log = logging.getLogger(__name__)
DOMAIN = str


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
                     *args: Sequence,
                     mod_params: Union[Tuple[Tuple[str, Any]], Tuple] = (),
                     mod_data: Union[Tuple[Tuple[str, Any]], Tuple] = (),
                     method: Literal['GET', 'POST'] = 'POST',
                     **kwargs: Mapping) -> Response:
    """Функция для получения ответа из CRM системы.

    Args:
        crm: сессия с CRM Naumen.
        obj (Union[TypeReport, SearchType]): обьект которого строится запрос.
        mod_params (Union[Tuple[Tuple[str, Any]], Tuple]): модифицированные параметры запроса
        mod_params (Union[Tuple[Tuple[str, Any]], Tuple]): модифицированные данные запроса
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
