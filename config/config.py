from json import load
from pathlib import Path
from typing import Mapping, NamedTuple


CONFIG_FILE_PATH = Path(__file__).with_name("config.json")
with open(CONFIG_FILE_PATH) as file:
    CONFIG = load(file)

# TODO прокинуть переменную из окружения
NAUMEN_LOGIN = ''
# TODO прокинуть переменную из окружения
NAUMEN_PASSWORD = ''
# TODO прокинуть переменную из окружения
NAUMEN_DOMAIN = ''
CONFIG.update({'auth': {'login': NAUMEN_LOGIN,
                        'password': NAUMEN_PASSWORD,
                        'domain': NAUMEN_DOMAIN}})


class CreateParams(NamedTuple):

    """Класс данных для хранения данных для создания отчета в CRM Naumen.

        Attributes:
            url: ссылка для создания отчета
            uuid: идентификатор обьекта
            headers: header для запроса
            params: параметры для запроса
            data: данные запроса
            verify: верификация
    """
    url: str
    uuid: str
    headers: Mapping
    params: Mapping
    data: Mapping
    verify: bool
    delay_attems: int
    num_attems: int


class FindParams(NamedTuple):

    """Класс данных для хранения сформированного запроса к CRM Naumen.

        Attributes:
            url: ссылка
            headers: headers для запроса
            params: параметры для запроса
            data: данные запроса
            verify: верификация
    """
    url: str
    headers: Mapping
    params: Mapping
    data: Mapping
    verify: bool


def get_params_create_report(report_name: str) -> CreateParams:

    """Функция которая достает необходимые параметры из конфигурационного файла.

    Args:
        report_name: название отчета

    Returns:
        Коллекцию параметров.

    Raises:

    """

    data_create = CreateParams('', '', {}, {}, {}, False, 0, 0)
    reports_name = [
        key for key, val in CONFIG.items() if "create_request" in val
        ]
    if report_name not in reports_name:
        return data_create
    url = CONFIG['url']['create']
    uuid = CONFIG[report_name]['uuid']
    headers = CONFIG['headers']
    data = CONFIG[report_name]['create_request']['data']
    params = CONFIG[report_name]['create_request']['params']
    verify = CONFIG['verify']['value']
    delay_attems = CONFIG[report_name]['delay_attems']['value']
    num_attems = CONFIG[report_name]['num_attems']['value']
    params["param2"] = {'name': 'uuid', 'value': uuid}

    return CreateParams(url, uuid, headers, params, data,
                        verify, delay_attems, num_attems)


def get_params_find() -> FindParams:

    """Функция которая достает необходимые параметры из конфигурационного файла.

    Args:
        report_name: название отчета

    Returns:
        Коллекцию параметров.

    Raises:

    """

    url = CONFIG['url']['open']
    headers = CONFIG['headers']
    data = {}
    params = {}
    verify = CONFIG['verify']['value']
    return FindParams(url, headers, params, data, verify)


if __name__ == "__main__":
    data = get_params_create_report('')
    print(data)
