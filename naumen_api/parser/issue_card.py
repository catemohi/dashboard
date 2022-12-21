import logging
from datetime import datetime, timedelta
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
    issue.name_contragent, issue.uuid_contragent = _get_contragent_params(soup)
    issue.description = _get_description(soup)
    issue.creation_date = _get_creation_date(soup)
    issue.name_service, issue.uuid_service = _get_service_params(soup)
    issue.return_to_work_time = _get_return_to_work_time(soup)
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
    if services:
        name = services.text.replace('\n', '').strip()
        _url = services.find('a')['href']
        try:
            uuid = _get_url_param_value(_url, 'uuid')
        except CantGetData:
            uuid = ''
        return (name, uuid)
    return ('', '')


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
        description = description\
                                .text\
                                .replace('\r', '')\
                                .replace('\t', '')\
                                .replace('\n', '')\
                                .strip()
        if len(description) > 140:
            description = description[:137] + '...'
        return description
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
