import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from re import findall
from typing import Iterable, Literal, Sequence

from bs4 import BeautifulSoup, element

from .parser_base import _get_columns_name
from .parser_base import _get_url_param_value
from .parser_base import _validate_text_for_parsing


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

    _validate_text_for_parsing(text)
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
