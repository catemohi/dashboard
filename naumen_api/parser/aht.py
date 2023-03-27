import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Mapping, Sequence, Union

from bs4 import BeautifulSoup

from .parser_base import (
    PageType,
    _forming_days_collecion,
    _forming_days_dict,
    _get_columns_name,
    _get_date_range,
    _parse_date_report,
    _validate_text_for_parsing,
)

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Aht:

    """Класс данных для хранения данных отчета Aht.

    Attributes:
        date: дата отсчёта.
        segment: сегмент отчёта.
        aht_level: уровень aht level в минутах.
        issues_received: Обращения закрытые самостоятельно.

    """

    date: str
    segment: str
    aht_level: float
    issues_received: int


def parse(
    text: str,
    *args: Sequence,
    **kwargs: Mapping,
) -> Union[Sequence[Aht], Sequence]:

    """Функция парсинга карточки обращения.

    Args:
        text: сырой текст страницы.

    Returns:
        Sequence or Sequence[Literal['']]: Коллекцию с найденными элементами.

    Raises:
        CantGetData: Если не удалось найти данные.
    """

    log.debug("Запуск парсинг отчёта AHT")

    _validate_text_for_parsing(text)
    soup = BeautifulSoup(text, "html.parser")
    start_date, end_date = _parse_date_report(
        soup,
        "Дата перевода, с",
        "Дата перевода, по",
    )
    log.debug(f"Получены даты отчета с {start_date} по {end_date}")
    label = _get_columns_name(soup)
    log.debug(f"Получены названия столбцов {label}")
    data_table = soup.find("table", id="stdViewpart0.part0_TableList")
    data_table = data_table.find_all("tr")[1:]
    day_collection = _forming_days_collecion(
        data_table,
        label,
        PageType.AHT_LEVEL_REPORT_PAGE,
    )
    date_range = _get_date_range(start_date, end_date)
    days = _forming_days_dict(
        date_range,
        day_collection,
        PageType.AHT_LEVEL_REPORT_PAGE,
    )
    days = _aht_data_completion(days, label)
    collection = _formating_aht_data(days)
    return tuple(collection)


def _aht_data_completion(days: dict, lable: Sequence) -> Dict[int, Sequence]:
    # TODO
    """Функция для дополнения данных отчёта AHT.
        т.к Naumen отдает не все необходимые данные, необходимо их дополнить.
        Заполнить пропуски за не наступившие дни:ATH будет 0

    Args:
        days: словарь дней, где ключ номер дня
        lable: название категорий

    Returns:
        Dict: дополненый словарь.
    """
    segments = []
    for _, day_content in days.items():
        for item in day_content:
            segments.append(item[lable[2]])
    segments = list(set(segments))
    aht_level = "0"
    issues_received = "0"
    for day, content in days.items():
        if len(content) == 0:
            day_collection = []
            obj_day = datetime.strptime(day, "%d.%m.%Y")
            for segment in segments:
                day_collection.append(
                    dict(
                        zip(
                            lable,
                            [
                                str(obj_day.month),
                                str(obj_day.day),
                                segment,
                                issues_received,
                                aht_level,
                            ],
                        ),
                    ),
                )
            days[day] = day_collection
        else:
            issue_count = 0
            need_index = 0
            for num, item in enumerate(content):
                try:
                    issue_count += int(item.get("Поступило", 0))
                except ValueError:
                    need_index = num
            content[need_index]["Поступило"] = str(issue_count)
            days[day] = content
    return days


def _formating_aht_data(days: Mapping[int, Sequence]) -> Sequence[Sequence[Aht]]:

    """Формирование итоговой коллекции обьектов отчёта AHT.

    Args:
        days: словарь дней, где ключ номер дня.

    Returns:
        Sequence[Sequence[Aht]]: коллекция с отчётами AHT.
    """

    collection = []
    for day, day_content in days.items():
        day_collection = []
        for item in day_content:
            date = str(day)
            aht_level = float(item.get("Среднее время", "0.0").replace(",", "."))
            issues_received = int(item["Поступило"])
            segment = item["Сегмент"]
            aht = Aht(
                date,
                segment,
                aht_level,
                issues_received,
            )
            day_collection.append(aht)
        collection.append(day_collection)

    return collection
