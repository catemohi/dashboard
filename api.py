import logging

from requests import exceptions

from .client import DOMAIN, TypeReport
from .client import get_report, get_session
from .exceptions import CantGetData, ConnectionsFailed
from .response_creator import JSONResponseFormatter, make_response
from .response_creator import ResponseFormatter, ResponseTemplate, StatusType


log = logging.getLogger(__name__)


class Client:

    """Класс для взаимодействия с системой Naumen.
        Возвращает ответы JSON строками.
    """

    def __init__(self, *, username: str = '', password: str = '',
                 domain: DOMAIN = '',
                 formatter: ResponseFormatter = JSONResponseFormatter) -> None:

        """Инициализация клиента api. Принимает именнованные аргументы.

        Kwargs:
            username (str): Логин в системе. По умолчанию ''.
            password (str): Пароль в системе. По умолчанию ''.
            domain (DOMAIN): Домен. По умолчанию ''.
        """
        log.debug('Инициализация клиента API.')
        log.debug(f'Переданы параметры: username: {username};'
                  f'password: {password};domain: {domain}.')
        self.username = username
        self.password = password
        self.domain = domain
        self.formatter = formatter
        self._session = None

    def connect(self, *, username: str = '',
                password: str = '', domain: DOMAIN = '') -> \
            ResponseFormatter.FORMATTED_RESPONSE:

        """Метод для соединение с системой NAUMEN.
           Принимает именнованные аргументы.

        Kwargs:
            username (str, optional): Логин в системе. По умолчанию ''.
            password (str, optional): Пароль в системе. По умолчанию ''.
            domain (DOMAIN, optional): Домен. По умолчанию ''.

        Returns:
            ResponseFormatter.FORMATTED_RESPONSE: отформатированный ответ

        """

        log.debug('Создание соединения с CRM NAUMEN.')
        log.debug(f'Переданы параметры: username: {username};'
                  f'password: {password};domain: {domain}.')
        local_credentials = all([username, password, domain])
        self_credentials = all([self.username, self.password, self.domain])
        error_response = ResponseTemplate(StatusType._UNAUTHORIZED, ())

        if not any([local_credentials, self_credentials]):
            log.error('Не передано данных для соединения с CRM NAUMEN.')
            return make_response(error_response, self.formatter)

        if local_credentials:
            self.username = username
            self.password = password
            self.domain = domain
        try:
            self._session = get_session(self.username,
                                        self.password,
                                        self.domain)
            log.info('Соединение с CRM NAUMEN успешно установлено.')
            success_response = ResponseTemplate(StatusType._SUCCESS, ())
            return make_response(success_response, self.formatter)

        except ConnectionsFailed:
            logging.exception('Ошибка соединения с CRM NAUMEN.')
            return make_response(error_response, self.formatter)

    def get_issues(self, is_vip: bool = False, *args, **kwargs) -> \
            ResponseFormatter.FORMATTED_RESPONSE:

        """Функция для получения отчёта о проблемах на линии ТП.

        Args:
            is_vip: флаг указывающий на то, тикеты какой линии получить.
            *args: другие позиционные аргументы.
            **kwargs: другие именнованные аргументы.

        Returns:
            ResponseFormatter.FORMATTED_RESPONSE: отформатированный ответ

        Raises:

        """

        report = TypeReport.ISSUES_VIP_LINE if is_vip \
            else TypeReport.ISSUES_FIRST_LINE

        log.debug('Запрос открытых проблем техподдержки.')
        log.debug(f'Параметр is_vip: {is_vip}')
        return self._get_response(report)

    def _get_response(self, report: TypeReport, *args, **kwargs) -> \
            ResponseFormatter.FORMATTED_RESPONSE:

        """Шаблонный метод для получения ответа от CRM NAUMEN.

            Args:
                report: необходимый отчёт.
                *args: прокинутые позиционные аргументы.
                **kwargs: прокинутые именнованные аргументы.

            Returns:
                ResponseFormatter.FORMATTED_RESPONSE: отформатированный ответ

            Raises:

        """

        try:
            content = get_report(self._session, report, args, kwargs)
            api_response = ResponseTemplate(StatusType._SUCCESS, content)
            log.info('Ответ на запрос проблем техподдержки получен.')
            return make_response(api_response, self.formatter)

        except exceptions.ConnectionError:
            logging.exception('Ошибка соединения с CRM NAUMEN.')
            error_response = ResponseTemplate(StatusType._GATEWAY_TIMEOUT, ())
            return make_response(error_response, self.formatter)

        except CantGetData:
            logging.exception('Ошибка получения данных из CRM NAUMEN.')
            error_response = ResponseTemplate(StatusType._BAD_REQUEST, ())
            return make_response(error_response, self.formatter)

        except ConnectionsFailed:
            logging.exception('Ошибка соединения с CRM NAUMEN.')
            error_response = ResponseTemplate(StatusType._UNAUTHORIZED, ())
            return make_response(error_response, self.formatter)
