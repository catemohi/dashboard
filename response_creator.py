import json
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
    _SUCCESS = {'code': 200, 'message': 'OK'}
    _BAD_REQUEST = {'code': 400, 'message': 'Bad Request'}
    _UNAUTHORIZED = {'code': 401, 'message': 'Unauthorized'}
    _GATEWAY_TIMEOUT = {'code': 504, 'message': 'Naumen Does Not Answer'}

    def __init__(self, status_content: Mapping):
        self.code = status_content['code']
        self.message = status_content['message']


class ResponseTemplate(NamedTuple):

    """Класс данных для хранения сформированного запроса к CRM Naumen.

        Attributes:
            status: состояние ответа
            description: описание ответа.
            content: содержание ответа
    """
    status: StatusType
    description: str
    content: Iterable


class ResponseFormatter:

    """Интерфейс для любых классов создания ответа.

        Attributes:
            FORMATTED_RESPONSE: формат ответа.
    """

    FORMATTED_RESPONSE = str

    def make(self, api_response: ResponseTemplate) -> \
            FORMATTED_RESPONSE:
        raise NotImplementedError


class JSONResponseFormatter(ResponseFormatter):

    """Класс для создание ответов API в формате JSON"""

    FORMATTED_RESPONSE = 'str'

    @staticmethod
    def make(api_response: ResponseTemplate) -> \
            FORMATTED_RESPONSE:
        dict_for_json = dict()
        dict_for_json.update({'status_code': api_response.status.code})
        dict_for_json.update({'status_message': api_response.status.message})
        dict_for_json.update({'description': api_response.description})
        dict_for_json.update({'content': tuple()})
        if api_response.content:
            dict_for_json.update({'content': ''})
        return json.dumps(dict_for_json)


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
