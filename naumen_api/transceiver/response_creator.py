import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta
from typing import Any, Iterable, NamedTuple, Type

from ..config.structures import StatusType

FORMATTED_RESPONSE = str


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
        FORMATTED_RESPONSE: форматированный ответа.
    """

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

    @classmethod
    def make(cls, api_response: ResponseTemplate) -> FORMATTED_RESPONSE:

        """Метод для форматирования ответа.

        Args:
            api_response: сырой ответ от API,
            который требуется отфармотировать.

        Returns:
            FORMATTED_RESPONSE: отформатированный ответ.

        """

        dict_for_json = {
            "status_code": api_response.status.code,
            "status_message": api_response.status.message,
            "description": api_response.status.description,
            "content": api_response.content,
        }
        json_string = json.dumps(
            dict_for_json,
            sort_keys=False,
            ensure_ascii=False,
            separators=(",", ": "),
            cls=EnhancedJSONEncoder,
        )
        return json_string


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, encoding_object: Any) -> Any:
        if is_dataclass(encoding_object):
            return asdict(encoding_object)
        if isinstance(encoding_object, datetime):
            return datetime.strftime(encoding_object, "%d.%m.%Y %H:%M:%S")
        if isinstance(encoding_object, timedelta):
            return encoding_object.total_seconds()
        return super().default(encoding_object)


def make_response(
    api_response: ResponseTemplate,
    formatter: Type[ResponseFormatter],
) -> FORMATTED_RESPONSE:

    """Функция форматорования ответа.

    Args:
        api_response: шаблонный ответ от api
        formatter: класс для форматированния ответа.

    Returns:
        ResponseFormatter.FORMATTED_RESPONSE: форматированный ответ.

    Raises:

    """

    return formatter.make(api_response)
