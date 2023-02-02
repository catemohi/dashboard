import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from re import findall
from typing import Any, Iterable, Sequence, Mapping, Union, Tuple

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
            uuid_responsible: уникалный идентификатор обьекта в CRM системе.
            responsible: ответственный за последний шаг.
            last_edit_time: время последнего изменения.
            vip_contragent: имеет ли клиент статус vip.
            creation_date: дата создания обращения.
            uuid_service: уникалный идентификатор обьекта в CRM системе.
            name_service: название услуги.
            info_service: данные услуги
            uuid_contragent: уникалный идентификатор обьекта в CRM системе.
            name_contragent: название контр агента.
            return_to_work_time: время возврата обращения в работу.
            description: описание обращения.
            diagnostics: диагностика
            required_date: стандартная дата отработки обращения
            close_date: дата закрытия обращения
            client_requisite: реквизиты клиента
            contact: контакты клиента
    """

    uuid: str = ''
    number: str = ''
    name: str = ''
    issue_type: str = ''
    step: str = ''
    step_time: timedelta = timedelta(0, 0)
    uuid_responsible: str = ''
    responsible: str = ''
    last_edit_time: Union[datetime, None] = None
    vip_contragent: bool = False
    creation_date: datetime = datetime.now()
    uuid_service: Union[Tuple, str] = ''
    name_service: Union[Tuple, str] = ''
    info_service: Sequence = ()
    uuid_contragent: str = ''
    name_contragent: str = ''
    contragent_category: str = ''
    return_to_work_time: Union[datetime, None] = None
    description: str = ''
    diagnostics: Union[Sequence[Sequence[Any]], Sequence] = ''
    required_date: Union[datetime, None] = None
    close_date: Union[datetime, None] = None
    client_requisite: Sequence = ()
    contact: Sequence = ()


def parse(text: str, *args: Sequence, **kwargs: Mapping
          ) -> Union[Sequence[Issue], Sequence]:

    """Функция парсинга страницы с обращениями на группе.

    Args:
        text: сырой текст страницы.

    Returns:
        Union[Sequence[Issue], Sequence]: Коллекцию с найденными элементами.

    Raises:
        CantGetData: Если не удалось найти данные.
    """

    _validate_text_for_parsing(text)
    soup = BeautifulSoup(text, "html.parser")
    category = _get_columns_name(soup)
    rows = soup.select(".supp tr")[7:-1]
    if len(rows) < 1:
        return ()
    def parse_table_row(row: element.Tag,

                        category: Iterable[str]) -> Issue:
        """Функция парсинга строки таблицы.

        Args:
            row: сырая строка.
            category: названия столбцов, строки.

        Returns:
            Sequence[Issue] or Sequence[Literal['']: Коллекцию обращений.

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
    return str(number)


def _get_step_duration(raw_duration: str) -> timedelta:

    """Функция для парсинга строки продолжительности в обьект timedelta.

    Args:
        raw_duration: строчная задержка.

    Returns:
        Объект задержки шага.

    Raises:

    """

    raw_duration_dict = dict(zip(('days', 'h', 'min'),
                                 findall(r'\d+', raw_duration)))
    duration = timedelta(days=int(raw_duration_dict['days']),
                         hours=int(raw_duration_dict['h']),
                         minutes=int(raw_duration_dict['min']))
    return duration
