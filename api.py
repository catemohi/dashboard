from typing import Iterable, Mapping, NamedTuple

from .client import DOMAIN, TypeReport
from .client import get_report, get_session
from .response_creator import JSONResponseFormatter, make_response
from .response_creator import StatusType, ResponseTemplate


class Client:

    """_summary_
    """

    def __init__(self, username: str, password: str, domain: DOMAIN) -> None:
        """_summary_

        Args:
            username (str): _description_
            password (str): _description_
            domain (DOMAIN): _description_
        """

        self.username = username
        self.password = password
        self.domain = DOMAIN

    def connect(self, *, username: str = '',
                password: str = '', domain: DOMAIN = '') -> None:
        local_credentials = all([username, password, domain])
        self_credentials = all([self.username, self.password, self.domain])
        if not any([local_credentials, self_credentials]):

            error_response = ResponseTemplate(
                StatusType._UNAUTHORIZED,
                'Failed to create a connection.'
                'Please check the data and route to the system.', (),
                )

            return make_response(error_response, JSONResponseFormatter)

        self._sesson = get_session(username, password, domain)

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
