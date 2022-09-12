import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from re import findall
from typing import Iterable, Literal, Sequence

from bs4 import BeautifulSoup, element

from .parser_base import _get_columns_name
from .parser_base import _get_url_param_value
from ..exceptions import CantGetData


log = logging.getLogger(__name__)


@dataclass
class Issue:

    """Класс данных для хранения данных по обращению.

        Attributes:
            uuid: уникалный идентификатор обьекта в CRM системе.
            number: номер обращения.
            name: название обращения.
            issue_type: тип обращения
            step: шаг на котром находится обращение.
            step_time: время последнего шага .
            responsible: ответственный за последний шаг.
            last_edit_time: время последнего изменения.
            vip_contragent: имеет ли клиент статус vip.
            creation_date: дата создания обращения.
            uuid_service: уникалный идентификатор обьекта в CRM системе.
            name_service: название услуги.
            uuid_contragent: уникалный идентификатор обьекта в CRM системе.
            name_contragent: название контр агента.
            return_to_work_time: время возврата обращения в работу.
            description: описание обращения.
    """

    uuid: str = ''
    number: int = 0
    name: str = ''
    issue_type: str = ''
    step: str = ''
    step_time: timedelta = timedelta(0, 0)
    responsible: str = ''
    last_edit_time: datetime = datetime.now()
    vip_contragent: bool = False
    creation_date: datetime = datetime.now()
    uuid_service: str = ''
    name_service: str = ''
    uuid_contragent: str = ''
    name_contragent: str = ''
    return_to_work_time: datetime = datetime.now()
    description: str = ''


def parse(text: str, *args, **kwargs) \
                        -> Sequence[Issue] | Sequence[Literal['']]:

    """Функция парсинга страницы с обращениями на группе.

    Args:
        text: сырой текст страницы.

    Returns:
        Sequence | Sequence[Literal['']]: Коллекцию с найденными элементами.

    Raises:
        CantGetData: Если не удалось найти данные.
    """

    soup = BeautifulSoup(text, "html.parser")
    category = _get_columns_name(soup)
    rows = soup.select(".supp tr")[7:-1]
    if len(rows) < 1:
        return ('',)
    def parse_table_row(row: element.Tag,

                        category: Iterable[str]) -> Issue:
        """Функция парсинга строки таблицы.

        Args:
            row: сырая строка.
            category: названия столбцов, строки.

        Returns:
            Sequence[Issue] | Sequence[Literal['']: Коллекцию обращений.

        """

        issue = Issue()
        issus_params = [
            col.text.replace('\n', '').strip() for col in row.select('td')]
        issues_dict = dict(zip(category, issus_params))
        _url = (row.find('a', href=True)['href'])
        issue.uuid = _get_url_param_value(_url, 'uuid')
        issue.number = _get_issue_num(issues_dict['Обращение'])
        issue.step_time = _get_step_duration(issues_dict['Время решения'])
        issue.last_edit_time = datetime.now() - issue.step_time
        issue.name = issues_dict['Обращение']
        issue.issue_type = issues_dict['Тип обращения']
        issue.step = issues_dict['Состояние']
        issue.responsible = issues_dict['Ответственный']
        return issue
    collection = [parse_table_row(row, category) for row in rows]
    return tuple(collection)


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


def _get_return_to_work_time(soup: BeautifulSoup) -> datetime:

    """Функция парсинга данных времени возврата в работу.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        datetime: время возврата в работу

    Raises:

    """

    return_times = (soup.find('td', id="obrd"), soup.find('td', id="obrd1"),
                    soup.find('td', id="obrd2"))
    return_times = [
        time.text.replace('\n', '').strip() for time in return_times if time]
    if return_times:
        times = [datetime.strptime(
            time, '%d.%m.%Y %H:%M') for time in return_times]
        if len(times) > 1:
            times.sort()
        return times[-1]
    return datetime.now() + timedelta(days=365)


def card_parse(text: str, issue: Issue) -> Issue:

    """Функция парсинга карточки обращения.

    Args:
        text: сырой текст страницы.
        issue: обращение, поля которого нужно дополнить.

    Returns:
        Issue: Модифицированный объект обращения.

    Raises:

    """

    soup = BeautifulSoup(text, "html.parser")
    issue.name_contragent, issue.uuid_contragent = _get_contragent_params(soup)
    issue.description = _get_description(soup)
    issue.creation_date = _get_creation_date(soup)
    issue.name_service, issue.uuid_service = _get_service_params(soup)
    issue.return_to_work_time = _get_return_to_work_time(soup)
    return issue


def _get_issue_num(issue_name: str) -> str:

    """Функция для парсинга номера обращения.

    Args:
        issue_name: имя обращения.

    Returns:
        Номер обращения.

    Raises:

    """

    number = findall(r'\d{7,10}', issue_name)[0]
    return number


def _get_step_duration(raw_duration: str) -> timedelta:

    """Функция для парсинга строки продолжительности в обьект timedelta.

    Args:
        raw_duration: строчная задержка.

    Returns:
        Объект задержки шага.

    Raises:

    """

    duration = dict(zip(('days', 'h', 'min'), findall(r'\d+', raw_duration)))
    duration = timedelta(days=int(duration['days']),
                         hours=int(duration['h']),
                         minutes=int(duration['min']))
    return duration
