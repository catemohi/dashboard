from datetime import datetime
from json import load
from logging import getLogger
from pathlib import PurePath
from random import randint
from typing import Any, Literal, Mapping, Tuple, Union, Sequence

from .structures import NaumenRequest, SearchOptions, TypeReport
from .structures import NaumenRequestType, SearchType
from ..exceptions import CantGetData, InvalidDate


log = getLogger(__name__)


class AppConfig:
    """Класс для хранения настроек приложения и переопределения их.
    """

    def __init__(self, config: Mapping = {},
                 config_path: Union[PurePath, None] = None) -> None:
        """
        Создание обьекта для хранения настроек приложения

        Args:
            config (Mapping): параметры конфигурации.По умолчанию {}.
            config_path (Union[PurePath, None]): путь к файлу конфигрурации. По умолчанию None.
        """
        self.config = config
        self._config_path = config_path

    @property
    def config_path(self) -> Union[PurePath, None]:
        return self._config_path

    @config_path.setter
    def config_path(self, value: Union[PurePath, str]) -> None:
        if not isinstance(value, str) or not isinstance(value, PurePath):
            raise TypeError("Path must be in string format.")
        if isinstance(value, str):
            value = PurePath(value)
        self._config_path = PurePath(value)

    def load_config(self) -> None:
        """Метод для генирации конфигурационного атрибута.
        """

        if self.config_path is None:
            self._config_path = PurePath(__file__).with_name("config.json")

        path_to_config = str(self.config_path)
        with open(path_to_config, encoding='utf-8') as file:
            self.config = load(file)


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


def _params_erector(params: Mapping[str, Mapping[Literal['name', 'value'],
                                                 str]]) -> Mapping[str, str]:
    """Функция для уплотнения, даты или параметров запроса.

    Args:
        params: данные которые необходимо собрать

    Returns:
        Mapping: Готовый словарь для запроса.
    """

    return dict([[val for _, val in root_val.items()
                  ] for _, root_val in params.items()])


def get_report_name() -> str:
    """Функция получения уникального названия для отчета.

    Args:

    Returns:
        Строку названия.
    """

    return f"ID{randint(1000000,9999999)}"


def get_search_create_report_params(report: TypeReport, report_name: str,
                                    ) -> SearchOptions:
    """Функция для формирования параметров для поиска созданного отчета

    Args:
        report: тип запрашиваемого отчета.
        report_name: название созданного отчета

    Returns:
        SearchOptions: параметры для поиска созданного отчета
    """
    delay_attems = CONFIG.config[report.value]['delay_attems']['value']
    num_attems = CONFIG.config[report.value]['num_attems']['value']
    uuid = CONFIG.config[report.value]['uuid']
    search_options = SearchOptions(report_name, delay_attems, num_attems, uuid)
    return search_options


def configure_params(report: TypeReport, request_type: NaumenRequestType,
                     mod_data: Union[Tuple[Tuple[str, Any]], Tuple] = (),
                     mod_params: Union[Tuple[Tuple[str, Any]], Tuple] = (),
                     ) -> NaumenRequest:
    """Функция для создания, даты или параметров запроса.

    Args:
        report (TypeReport): тип запрашиваемого отчета.
        request_type (NaumenRequestType): тип запроса к NAUMEN
        mod_data (Union[Tuple[Tuple[str, Any]], Tuple]): данные запроса,
        которые необходимо модифицировать
        mod_params (Union[Tuple[Tuple[str, Any]], Tuple]): параметры запроса,
        которые необходимо модифицировать
    Returns:
        NaumenRequest: сформированный запрос для CRM Naumen
        SearchOptions: параметры для поиска созданного отчета
    """
    url_map = {
        NaumenRequestType.CREATE_REPORT: CONFIG.config['url']['create'],
        NaumenRequestType.SEARCH_REPORT: CONFIG.config['url']['open'],
        NaumenRequestType.DELETE_REPORT: CONFIG.config['url']['delete'],
        NaumenRequestType.CONTROL: CONFIG.config['url']['control'],
    }
    date_name_keys = ('start_date', 'end_date')

    try:
        headers = CONFIG.config["headers"]
        verify = CONFIG.config["verify"]["value"]
        data = CONFIG.config[report.value][request_type.value]['data'].copy()
        params = CONFIG.config[report.value][request_type.value]['params']\
            .copy()
        url = url_map[request_type]
    except KeyError:
        raise CantGetData

    for name, value in mod_data:
        if name in date_name_keys:
            value = _validate_date(value)
        data[name]['value'] = value

    for name, value in mod_params:
        params[name]['value'] = value

    data = _params_erector(data)
    params = _params_erector(params)

    request = NaumenRequest(url, headers, params, data, verify)
    return request


def create_naumen_request(obj: Union[TypeReport, SearchType],
                          request_type: NaumenRequestType,
                          mod_params: Union[Tuple[Tuple[str, Any]], Tuple] = (),
                          mod_data: Union[Tuple[Tuple[str, Any]], Tuple] = (),
                          *args: Sequence,
                          **kwargs: Mapping) -> NaumenRequest:

    """Метод для создания первичного запроса в NAUMEN .

    Args:
        obj (Union[TypeReport, SearchType]): обьект, который необходимо
        создать/получить из CRM.
        request_type (NaumenRequestType): типа запроса
        mod_params (Union[Tuple[Tuple[str, Any]], Tuple]): параметры, которые необходимо
        модифицировать в запроса
        mod_data (Union[Tuple[Tuple[str, Any]], Tuple]): данные, которые необходимо
        модифицировать в запросе
        *args: позиционные аргументы(не используются)
        **kwargs: именнованные аргументы для создания отчёта.

    Returns:
        Tuple[NaumenRequest, SearchOptions]: запрос и данные для нахождения
        Tuple[Response, SearchOptions]: коллекция обьектов необходимого отчёта.
    Raises:
        CantGetData: в случае невозможности вернуть коллекцию.
    """

    log.debug(f'Запуск создания отчета: {obj}')
    log.debug(f'Переданы модифицированные params: {mod_params}')
    log.debug(f'Переданы модифицированные data: {mod_data}')
    log.debug(f'Переданы параметры args: {args}')
    log.debug(f'Переданы параметры kwargs: {kwargs}')

    if not any([isinstance(obj, TypeReport), isinstance(obj, SearchType)]):
        raise CantGetData

    naumen_reuqest = configure_params(obj, request_type, mod_data, mod_params)
    log.debug(f'Запрос к CRM: {naumen_reuqest}')
    return naumen_reuqest


CONFIG = AppConfig()
CONFIG.load_config()

if __name__ == "__main__":
    ...
