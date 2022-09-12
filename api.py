import logging

from requests import exceptions

from .client import DOMAIN, TypeReport
from .client import get_report, get_session
from .exceptions import CantGetData, ConnectionsFailed, InvalidDate
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

        """Метод для получения отчёта о проблемах на линии ТП.

        Args:
            is_vip: флаг указывающий на то, тикеты какой линии получить.
            *args: не используются и не пробрасываются.
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

    def get_sl_report(self, start_date: str, end_date: str,
                      deadline: int = 15,
                      *args, **kwargs) -> ResponseFormatter.FORMATTED_RESPONSE:

        """Метод для получения отчёта о Service Level за период.
           Метод возвращает дни, без привязки к месяцу.
           Если передать период с 01.05.2022 по 01.07.2022
           вернется отчет за 31 день, процент дня будет средним
           за два месяца.

        Args:
            start_date: дата начала периода.
            end_date: дата конца периода.
            deadline: количество минут относительно которых
            считать service level.
            *args: не используются и не пробрасываются.
            **kwargs: другие именнованные аргументы.

        Returns:
            ResponseFormatter.FORMATTED_RESPONSE: отформатированный ответ

        Raises:

        """

        log.debug('Запрос service level техподдержки.')
        try:
            deadline = int(deadline)
        except (ValueError, TypeError):
            logging.exception(f'Аргумент deadline не int и'
                              f'не валидный литерал: '
                              f'{deadline}')
            error_response = ResponseTemplate(StatusType._BAD_REQUEST, ())
            error_response.status.description = (f'Invalid deadline value: '
                                                 f'{deadline}')
            return make_response(error_response, self.formatter)

        log.debug(f'Параметр start_date: {start_date}; '
                  f'Параметр end_date: {end_date}; '
                  f'Параметр deadline: {deadline}; ')

        report_kwargs = {
            'start_date': start_date,
            'end_date': end_date,
            'deadline': deadline,
            **kwargs,
        }
        return self._get_response(TypeReport.SERVICE_LEVEL, **report_kwargs)

    def get_mttr_report(self, start_date: str, end_date: str, *args,
                        **kwargs) -> ResponseFormatter.FORMATTED_RESPONSE:

        """Метод для получения отчёта о Mttr за период.
           Метод возвращает дни, без привязки к месяцу.
           Если передать период с 01.05.2022 по 01.07.2022
           вернется отчет за 31 день, процент дня будет средним
           за два месяца.

        Args:
            start_date: дата начала периода.
            end_date: дата конца периода.
            *args: не используются и не пробрасываются.
            **kwargs: другие именнованные аргументы.

        Returns:
            ResponseFormatter.FORMATTED_RESPONSE: отформатированный ответ

        Raises:

        """

        log.debug(f'Параметр start_date: {start_date}; '
                  f'Параметр end_date: {end_date}; ')

        report_kwargs = {
            'start_date': start_date,
            'end_date': end_date,
            **kwargs,
        }
        return self._get_response(TypeReport.MTTR_LEVEL, **report_kwargs)

    def get_flr_report(self, start_date: str, end_date: str, *args,
                       **kwargs) -> ResponseFormatter.FORMATTED_RESPONSE:

        """Метод для получения отчёта о Flr за период.
           Метод возвращает дни, c привязкой к месяцу.

        Args:
            start_date: дата начала периода.
            end_date: дата конца периода.
            *args: не используются и не пробрасываются.
            **kwargs: другие именнованные аргументы.

        Returns:
            ResponseFormatter.FORMATTED_RESPONSE: отформатированный ответ

        Raises:

        """

        log.debug(f'Параметр start_date: {start_date}; '
                  f'Параметр end_date: {end_date}; ')

        report_kwargs = {
            'start_date': start_date,
            'end_date': end_date,
            **kwargs,
        }
        return self._get_response(TypeReport.FLR_LEVEL, **report_kwargs)

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
            content = get_report(self._session, report, *args, **kwargs)
            log.debug(content)
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

        except InvalidDate:
            logging.exception('Передан не верный формат дыты из CRM NAUMEN.')
            error_response = ResponseTemplate(StatusType._BAD_REQUEST, ())
            error_response.status.description = ('Invalid date format. '
                                                 'Allowed date format: '
                                                 '%d.%m.%Y')
            return make_response(error_response, self.formatter)

        except ConnectionsFailed:
            logging.exception('Ошибка соединения с CRM NAUMEN.')
            error_response = ResponseTemplate(StatusType._UNAUTHORIZED, ())
            return make_response(error_response, self.formatter)
