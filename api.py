from typing import Iterable, Mapping, NamedTuple

from .client import DOMAIN, TypeReport
from .client import get_report, get_session
from .response_creator import JSONResponseFormatter, make_response
from .response_creator import StatusType, ResponseTemplate
from .exceptions import ConnectionsFailed


class Client:

    """Класс для взаимодействия с системой Naumen.
        Возвращает ответы JSON строками.
    """

    def __init__(self, *, username: str = '',
                 password: str = '', domain: DOMAIN = '') -> None:

        """Инициализация клиента api.

        Args:
            username (str): Логин в системе. По умолчанию ''.
            password (str): Пароль в системе. По умолчанию ''.
            domain (DOMAIN): Домен. По умолчанию ''.
        """

        self.username = username
        self.password = password
        self.domain = DOMAIN
        self._sesson = None
        if all([self.username, self.password, self.domain]):
            self.connect()

    def connect(self, *, username: str = '',
                password: str = '', domain: DOMAIN = '') -> None:

        """Метод для соединение с системой Naumen.

        Args:
            username (str, optional): Логин в системе. По умолчанию ''.
            password (str, optional): Пароль в системе. По умолчанию ''.
            domain (DOMAIN, optional): Домен. По умолчанию ''.

        Returns:
            None:
        """
        local_credentials = all([username, password, domain])
        self_credentials = all([self.username, self.password, self.domain])

        if not any([local_credentials, self_credentials]):
            error_response = ResponseTemplate(StatusType._UNAUTHORIZED, ())
            return make_response(error_response, JSONResponseFormatter)
        if local_credentials:
            self.username = username
            self.password = password
            self.domain = domain
        try:
            self._sesson = get_session(self.username,
                                       self.password,
                                       self.domain)
        except ConnectionsFailed:
            return make_response(error_response, JSONResponseFormatter)

    def get_issues(self, is_vip: bool = False, *args, **kwargs) -> Iterable:

        """Функция для получения отчёта о проблемах на линии ТП.

        Args:
            crm: активное соединение с CRM.
            is_vip: флаг указывающий на то, тикеты какой линии получить.
            *args: другие позиционные аргументы.
            **kwargs: другие именнованные аргументы.

        Returns:
            Itrrable: коллекция обьектов необходимого отчёта.

        Raises:
            CantGetData: в случае невозможности вернуть коллекцию.
        """

        #TODO requests.exceptions.ConnectionError:
        report = TypeReport.ISSUES_VIP_LINE if is_vip \
            else TypeReport.ISSUES_FIRST_LINE
        get_report(self._sesson, report)
