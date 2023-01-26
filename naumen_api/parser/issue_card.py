import logging
from datetime import datetime
from typing import Iterable

from bs4 import BeautifulSoup

from .issues import Issue
from .parser_base import _get_url_param_value
from .parser_base import _validate_text_for_parsing
from ..exceptions import CantGetData


log = logging.getLogger(__name__)


def parse(text: str, *args, issue: Issue = None) -> Issue:

    """Функция парсинга карточки обращения.

    Args:
        text: сырой текст страницы.
        issue: обращение, поля которого нужно дополнить.

    Returns:
        Issue: Модифицированный объект обращения.

    Raises:

    """

    if not issue:
        issue = Issue()
    _validate_text_for_parsing(text)
    soup = BeautifulSoup(text, "html.parser")
    if not soup:
        raise CantGetData
    issue.number = _get_number(soup)
    issue.name = _get_title(soup)
    issue.step = _get_step(soup)
    issue.issue_type = _get_issue_type(soup)
    _, issue.responsible = _get_responsible(soup)
    issue.name_contragent, issue.uuid_contragent = _get_contragent_params(soup)
    issue.description = _get_description(soup)
    issue.creation_date = _get_creation_date(soup)
    issue.name_service, issue.uuid_service = _get_service_params(soup)
    issue.info_service = _get_service_info(soup)
    issue.return_to_work_time = _get_return_to_work_time(soup)
    issue.diagnostics = _get_diagnostics(soup)
    return (issue, )


def _get_return_to_work_time(soup: BeautifulSoup) -> datetime:

    """Функция парсинга данных времени возврата в работу.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        datetime: время возврата в работу

    Raises:

    """
    log.debug('Нахождение времени возврата в работу.')

    return_times = (soup.find('td', id="obrd"), soup.find('td', id="obrd1"),
                    soup.find('td', id="obrd2"))
    return_times = [
        time.text.replace('\n', '').strip() for time in return_times if time]
    log.debug(f'Из CRM собраны следующие данные: {return_times}.')

    def _return_defalut_time():
        return_to_work_time = datetime(datetime.now().year + 1,
                                       12, 31, 12, 0, 0)
        log.debug('Дата возврата в работу не обнаружена, '
                  'поставлено значение по умолчанию: '
                  f'{return_to_work_time}')
        return return_to_work_time

    if not return_times:
        return _return_defalut_time()

    def _string_to_time(string_time: str):
        try:
            return datetime.strptime(string_time, '%d.%m.%Y %H:%M')
        except ValueError:
            log.error(f'Значение {string_time} не удалось преобразовать '
                      'в обьект datetime, по шаблону %d.%m.%Y %H:%M')
    needed_time_string_count = 1
    times = [_string_to_time(time) for time in return_times if time]

    if not times:
        return _return_defalut_time()

    if len(times) > needed_time_string_count:
        log.debug(f'Получено больше {needed_time_string_count} '
                  'значений даты. Возвращаем последнюю.')
    # возвращаем самую последнюю дату.
    return_to_work_time = sorted(times)[-1]
    log.info(f'Найдена дата возврата в работу {return_to_work_time}')
    return return_to_work_time


def _get_service_params(soup: BeautifulSoup) -> Iterable[str]:

    """Функция парсинга данных услуги.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        Iterable[str]: коллекцию с параметрами.

    Raises:

    """

    services = soup.find('td', id="services")
    if not services:
        return ('', '')
    a_collection = services.find_all('a')
    names, uuids = [], []

    for a_tag in a_collection:
        uuids.append(_get_url_param_value(a_tag['href'], 'uuid'))
        names.append(' '.join(list(a_tag.stripped_strings)))
    return ';'.join(names), ';'.join(uuids)


def _get_description(soup: BeautifulSoup) -> str:

    """Функция парсинга данных описания обращения.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        str: Описание обращения.

    Raises:

    """

    description = soup.find('td', id="requestDescription")
    if description:
        return ' '.join(list(description.stripped_strings))
    return ''


def _get_creation_date(soup: BeautifulSoup) -> datetime:

    """Функция парсинга даты создания обращения.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        datetime: дата создания обращения.

    Raises:

    """

    creation_date = soup.find('td', id="creationDate")
    if creation_date:
        str_datetime = creation_date.text.replace('\n', '').strip()
        return datetime.strptime(str_datetime, '%d.%m.%Y %H:%M')
    return datetime.now()


def _get_contragent_params(soup: BeautifulSoup) -> Iterable[str]:

    """Функция парсинга данных контрагента.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        Iterable[str]: Коллекцию с параметрами контрагента.

    Raises:

    """

    contragent_tag = soup.find('td', id='contragent')
    if contragent_tag:
        name = contragent_tag.text.replace('\n', '').strip()
        _url = contragent_tag.find('a')['href']
        try:
            uuid = _get_url_param_value(_url, 'uuid')
        except CantGetData:
            uuid = ''
        return (name, uuid)
    return ('', '')


def _get_number(soup: BeautifulSoup) -> str:
    """Функция парсинга номера обращения.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        str

    Raises:

    """
    number_tag = soup.find(id='number')
    number = ' '.join(list(number_tag.stripped_strings))
    return number


def _get_responsible(soup: BeautifulSoup) -> tuple['str', 'str']:
    """Функция парсинга ответсвенного за состояние.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        str

    Raises:

    """
    responsible_tag = soup.find(id='stateResponsible')
    _url = responsible_tag.find('a', href=True)
    if _url is not None:
        _url = _url.get('href')
        uuid_responsible = _get_url_param_value(_url, 'uuid')
    else:
        uuid_responsible = ''

    name_responsible = responsible_tag.find('a')
    if name_responsible is not None:
        name_responsible = ' '.join(list(name_responsible.stripped_strings))
    else:
        name_responsible = ''

    return uuid_responsible, name_responsible


def _get_title(soup: BeautifulSoup) -> str:
    """Функция парсинга названия обращения.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        str

    Raises:

    """
    title_tag = soup.find(id='title')
    title = ' '.join(list(title_tag.stripped_strings))
    return title


def _get_step(soup: BeautifulSoup) -> str:
    """Функция парсинга названия обращения.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        str

    Raises:

    """
    step_tag = soup.find(id='stage')
    step = ' '.join(list(step_tag.stripped_strings))
    return step


def _get_issue_type(soup: BeautifulSoup) -> str:
    """Функция парсинга названия обращения.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        str

    Raises:

    """
    issue_type_tag = soup.find(id='BOCase')
    issue_type = ' '.join(list(issue_type_tag.stripped_strings))
    return issue_type


def _get_service_info(soup: BeautifulSoup) -> str:
    """Функция парсинга информации по услугам.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        str

    Raises:

    """
    service_info_tag = soup.find(id='srvInf')
    service_info = ' '.join(list(service_info_tag.stripped_strings))
    service_info = ['Услуга ' + item for item in service_info.split('Услуга')
                    if item]
    return ';'.join(service_info)


def _get_diagnostics(soup: BeautifulSoup) -> str:
    """Функция парсинга диагностики.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        str

    Raises:

    """
    diagnostics_tag = soup.find(id='diagnostica')
    diagnostics = ' '.join(list(diagnostics_tag.stripped_strings))
    return diagnostics
