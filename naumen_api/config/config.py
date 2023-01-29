from datetime import datetime
from json import load
from pathlib import PurePath
from typing import Any, Literal, Mapping, NamedTuple, Tuple

from ..exceptions import InvalidDate


class AppConfig:
    """Класс для хранения настроек приложения и переопределения их.
    """

    def __init__(self) -> None:
        self.config = {}
        self._config_path = ''

    @property
    def config_path(self) -> str:
        return self._config_path

    @config_path.setter
    def config_path(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Path must be in string format.")
        self._config_path = PurePath(value)

    def load_config(self) -> None:
        """Метод для генирации конфигурационного атрибута.
        """

        if not self.config_path:
            self._config_path = PurePath(__file__).with_name("config.json")

        with open(self.config_path, encoding='utf-8') as file:
            self.config = load(file)


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

    """Класс данных для хранения сформированного запроса поиска обьекта
    к CRM Naumen.

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


class DeleteParams(FindParams):
    """Класс данных для хранения сформированного запроса на удаление обьекта
    к CRM Naumen.

    Args:
        FindParams (NamedTuple): Класс данных для хранения
        сформированного запроса поиска обьекта к CRM Naumen.
    """


def get_params_create_report(report_name: str) -> CreateParams:

    """Функция которая достает необходимые параметры
    из конфигурационного файла.

    Args:
        report_name: название отчета

    Returns:
        Коллекцию параметров.

    Raises:

    """
    url = CONFIG.config['url']['create']
    data_create = CreateParams(url, '', {}, {}, {}, False, 0, 0)
    reports_name = [
        key for key, val in CONFIG.config.items() if "create_request" in val
        ]
    if report_name not in reports_name:
        return data_create
    uuid = CONFIG.config[report_name]['uuid']
    headers = CONFIG.config['headers']
    data = CONFIG.config[report_name]['create_request']['data']
    params = CONFIG.config[report_name]['create_request']['params']
    verify = CONFIG.config['verify']['value']
    delay_attems = CONFIG.config[report_name]['delay_attems']['value']
    num_attems = CONFIG.config[report_name]['num_attems']['value']
    params["param2"] = {'name': 'uuid', 'value': uuid}

    return CreateParams(url, uuid, headers, params, data,
                        verify, delay_attems, num_attems)


def get_params_search(report_name: str) -> CreateParams:

    """Функция которая достает необходимые параметры
    из конфигурационного файла.

    Args:
        report_name: название отчета

    Returns:
        Коллекцию параметров.

    Raises:

    """
    create_params = get_params_create_report(report_name)
    search_params = create_params._replace(
        url=CONFIG.config['url']['open'])
    return search_params


def get_params_control(report_name: str):
    """Функция которая достает необходимые параметры
    из конфигурационного файла.

    Args:
        report_name: название отчета

    Returns:
        Коллекцию параметров.

    Raises:

    """
    create_params = get_params_create_report(report_name)
    contol_params = create_params._replace(
        url=CONFIG.config['url']['control'], params={})
    return contol_params


def get_params_find_create_report() -> FindParams:

    """Функция которая достает необходимые параметры из
    конфигурационного файла.

    Args:
        report_name: название отчета

    Returns:
        Коллекцию параметров.

    Raises:

    """

    url = CONFIG.config['url']['open']
    headers = CONFIG.config['headers']
    data = {}
    params = {}
    verify = CONFIG.config['verify']['value']
    return FindParams(url, headers, params, data, verify)


def get_params_for_delete() -> DeleteParams:

    """Функция которая достает необходимые параметры
    из конфигурационного файла.

    Args:

    Returns:
        Коллекцию параметров.

    Raises:

    """

    url = CONFIG.config['url']['delete']
    headers = CONFIG.config['headers']
    data = {}
    params = CONFIG.config['delete_report']['params']
    verify = CONFIG.config['verify']['value']
    return DeleteParams(url, headers, params, data, verify)


def get_raw_params(report_name: str, request_type: str,
                   mod_params: Tuple[Tuple[str, Any]] = (),
                   mod_data: Tuple[Tuple[str, Any]] = (),
                   *args, **kwargs) -> Tuple[Tuple[str, Any],
                                             Tuple[str, Any]]:
    """Функция создания данных для запроса и поиска созданного отчета.

    Args:
        report_name: название типа отчета для которого требуется запрос.
        request_type: название типа запроса
        mod_params: модифицированные параметры. По умолчанию = ()
        mod_params: модифицированная дата. По умолчанию = ()
        *args: параметры необходимые для создания отчета.

    Kwargs:
        **kwargs: именнованные параметры необходимы для создания отчета.

    Returns:
        Сырые данные параметров и даты для создания запроса в CRM

    Raises:
        CantGetData: в случае неверной работы функции.

    """

    date_name_keys = ('start_date', 'end_date')
    data = CONFIG.config[report_name][request_type]['data'].copy()
    params = CONFIG.config[report_name][request_type]['params'].copy()

    for name, value in mod_params:
        params[name]['value'] = value

    for name, value in mod_data:
        if name in date_name_keys:
            value = _validate_date(value)
        data[name]['value'] = value

    return tuple(data.items()), tuple(params.items())


def _validate_date(check_date: str) -> str:
    """Функция проверки формата даты.

    Args:
        first_date: первая дата, format '%d.%m.%Y'

    Returns:
        date: строка даты необходимого формата.

    Raises:
        InvalidDate: при неудачной проверке или конвертиртации даты.

    """

    try:
        return datetime.strptime(check_date, '%d.%m.%Y').strftime("%d.%m.%Y")
    except ValueError:
        raise InvalidDate
    except TypeError:
        raise InvalidDate


def params_erector(params: Mapping[str, Mapping[Literal['name', 'value'],
                                                str]]) -> Mapping[str, str]:
    """Функция для уплотнения, даты или параметров запроса.

    Args:
        params: данные которые необходимо собрать

    Returns:
        Mapping: Готовый словарь для запроса.
    """

    return dict([[val for _, val in root_val.items()
                  ] for _, root_val in params.items()])


CONFIG = AppConfig()
CONFIG.load_config()

if __name__ == "__main__":
    data = get_params_create_report('')
    print(data)
