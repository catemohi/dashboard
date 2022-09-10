import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Iterable, Mapping, NamedTuple


class StatusType(Enum):

    """Enum перечисление видов статуса API .

        Attributes:
            _SUCCESS: успешный ответ
            _BAD_REQUEST: ответ при ошибке запроса
            _UNAUTHORIZED: ответ при проблемах с авторизацией
            _GATEWAY_TIMEOUT: при проблемах с Naumen

    """

    _SUCCESS = {'code': 200,
                'message': 'OK',
                'description': '',
                }
    _BAD_REQUEST = {'code': 400,
                    'message': 'Bad Request',
                    'description': 'Wrong, incorrect request.',
                    }
    _UNAUTHORIZED = {'code': 401,
                     'message': 'Unauthorized',
                     'description': 'Failed to create a connection. '
                     'Please check the data and route to the system '
                     'or config.json settings.',
                     }
    _GATEWAY_TIMEOUT = {'code': 504,
                        'message': 'Naumen Does Not Answer',
                        'description': 'Remote end closed '
                        'connection without response',
                        }

    def __init__(self, status_content: Mapping):
        self.code = status_content['code']
        self.message = status_content['message']
        self.description = status_content['description']


class ResponseTemplate(NamedTuple):

    """Класс данных для хранения сформированного запроса к CRM Naumen.

        Attributes:
            status: состояние ответа
            content: содержание ответа
    """
    status: StatusType
    content: Iterable


class ResponseFormatter:

    """Интерфейс для любых классов создания ответа.

        Attributes:
            FORMATTED_RESPONSE: формат ответа.
    """

    FORMATTED_RESPONSE = str

    @classmethod
    def make(cls, api_response: ResponseTemplate) -> FORMATTED_RESPONSE:

        """Метод, который вызывается для формирования отчета.

        Args:
            api_response (ResponseTemplate): сырой ответ от API.

        Raises:
            NotImplementedError: не реализован.

        Returns:
            FORMATTED_RESPONSE: форматированный ответ.
        """
        raise NotImplementedError


class JSONResponseFormatter(ResponseFormatter):

    """Класс для создание ответов API в формате JSON"""

    FORMATTED_RESPONSE = 'str'

    @classmethod
    def make(cls, api_response: ResponseTemplate) -> \
            FORMATTED_RESPONSE:

        """Метод для форматирования ответа.

        Args:
            api_response: сырой ответ от API,
            который требуется отфармотировать.

        Returns:
            FORMATTED_RESPONSE: отформатированный ответ.

        """

        dict_for_json = dict()
        dict_for_json.update({'status_code': api_response.status.code})
        dict_for_json.update({'status_message': api_response.status.message})
        dict_for_json.update({'description': api_response.status.description})
        dict_for_json.update({'content': tuple()})
        if not api_response.content:
            json_string = json.dumps(dict_for_json, sort_keys=False,
                                     ensure_ascii=False,
                                     separators=(',', ': '))
            return json_string

        dataclass_items = [cls.date_obj_to_string(asdict(line))
                           for line in api_response.content
                           if is_dataclass(line)]

        dict_for_json.update({'content': dataclass_items})
        json_string = json.dumps(dict_for_json, sort_keys=False,
                                 ensure_ascii=False, separators=(',', ': '))
        return json_string

    @classmethod
    def date_obj_to_string(cls, content: Mapping,
                           datetime_string_format: str = '%d.%m.%Y %H:%M:%S')\
            -> Mapping:

        """Метод для конвертации datetime полей словаря в строки.

        Args:
            content (Mapping): словарь с параметрами
            datetime_string_format: формат времени.

        Returns:
            Mapping: словарь с модифицированными параметрами.
        """

        for name, value in content.items():
            if isinstance(value, datetime):
                content[name] = datetime.strftime(value,
                                                  datetime_string_format)
            elif isinstance(value, timedelta):
                content[name] = value.total_seconds()
        return content


def make_response(api_response: ResponseTemplate,
                  formatter: ResponseFormatter) -> \
                                        ResponseFormatter.FORMATTED_RESPONSE:

    """Функция форматорования ответа.

    Args:
        api_response: шаблонный ответ от api
        formatter: класс для форматированния ответа.

    Returns:
        ResponseFormatter.FORMATTED_RESPONSE: форматированный ответ.

    Raises:

    """

    return formatter.make(api_response)
