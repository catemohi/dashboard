import logging
import re
from datetime import datetime
from typing import Iterable

from bs4 import BeautifulSoup

from .issues import Issue
from .parser_base import _get_columns_name, _get_url_param_value
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
    issue.uuid_responsible, issue.responsible = _get_responsible(soup)
    issue.name_contragent, issue.uuid_contragent = _get_contragent_params(soup)
    issue.description = _get_description(soup)
    issue.creation_date = _get_creation_date(soup)
    issue.name_service, issue.uuid_service = _get_service_params(soup)
    issue.info_service = _get_service_info(soup)
    issue.return_to_work_time = _get_return_to_work_time(soup)
    issue.diagnostics = _get_diagnostics(soup)
    issue.required_date = _get_required_date(soup)
    issue.close_date = _get_close_date(soup)
    issue.client_requisite = _get_client_requisite(soup)
    issue.contragent_category = _get_contragent_category(soup)
    issue.contact = _get_contact(soup)
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
    return names, uuids


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

    creation_date = soup.find('td', id="requestDate")
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
    if title_tag:
        title = ' '.join(list(title_tag.stripped_strings))
        return title
    return ''


def _get_step(soup: BeautifulSoup) -> str:
    """Функция парсинга названия обращения.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        str

    Raises:

    """
    step_tag = soup.find(id='stage')
    if step_tag:
        step = ' '.join(list(step_tag.stripped_strings))
        return step
    return ''


def _get_issue_type(soup: BeautifulSoup) -> str:
    """Функция парсинга названия обращения.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        str

    Raises:

    """
    issue_type_tag = soup.find(id='BOCase')
    if issue_type_tag:
        issue_type = ' '.join(list(issue_type_tag.stripped_strings))
        return issue_type
    issue_type_tag = soup.find(id='problemCategory')
    if issue_type_tag:
        issue_type = ' '.join(list(issue_type_tag.stripped_strings))
        return issue_type
    return ''


def _get_service_info(soup: BeautifulSoup) -> str:
    """Функция парсинга информации по услугам.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        str

    Raises:

    """
    service_info_tag = soup.find(id='srvInf')
    if service_info_tag:
        collection_service = []
        service_info = ' '.join(list(service_info_tag.stripped_strings))
        service_info = ['Услуга ' + item for item
                        in service_info.split('Услуга') if item]
        for item in service_info:
            item = [_.replace(':', '').strip() for _ in re.split(
                r"(Услуга\s?:) | (Адрес установки\s?:) | (Состояние\s?:)",
                item) if _]
            if len(item) >= 6:
                service_name = {item[:2][0]: item[:2][1]}
                service_addres = {item[2:4][0]: item[2:4][1]}
                service_status = {item[4:][0]: item[4:][1]}
                item = {**service_name, **service_addres, **service_status}
                collection_service.append(tuple(item.items()))
            else:
                collection_service.append(())
        return collection_service
    return ()


def _get_diagnostics(soup: BeautifulSoup) -> str:
    """Функция парсинга диагностики.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        str

    Raises:

    """
    diagnostics_tag = soup.find(id='diagnostica')
    if diagnostics_tag:
        try:
            diagnostics_base = [item.split(': ') for item in list(
                diagnostics_tag.stripped_strings) if ':' in item]
            for item in diagnostics_base:
                if len(item) < 2:
                    item.append('')
                else:
                    item = item[:2]
                print(item)
            diagnostics_base = dict(diagnostics_base)
            for item in list(diagnostics_tag.stripped_strings):
                if ':' not in item:
                    diagnostics_base['Диагностика'] += ' ' + item
        except KeyError:
            diagnostics_base = {
                'Диагностика':
                ' '.join([text.strip() for text
                          in diagnostics_tag.stripped_strings])}
        return tuple(diagnostics_base.items())
    return ()


def _get_required_date(soup: BeautifulSoup) -> str:
    """Функция парсинга даты отработки по умолчанию.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        str

    Raises:

    """
    required_date_tag = soup.find(id='reqDeadLineDate')
    if required_date_tag:
        required_date = ' '.join(list(required_date_tag.stripped_strings))
        if required_date:
            required_date = datetime.strptime(required_date, '%d.%m.%Y %H:%M')
            return required_date
    return None


def _get_close_date(soup: BeautifulSoup) -> str:
    """Функция парсинга даты закрытия заявки.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        str

    Raises:

    """
    close_date_tag = soup.find(id='closeDate')
    if close_date_tag:
        close_date = ' '.join(list(close_date_tag.stripped_strings))
        if close_date:
            close_date = datetime.strptime(close_date, '%d.%m.%Y %H:%M')
            return close_date
    return None


def _get_client_requisite(soup: BeautifulSoup) -> str:
    """Функция парсинга реквизиты клиентов.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        str

    Raises:

    """
    client_requisite_tag = soup.find(id='clientRequisite')
    reg_template = (r"(Полное наименование\s?:\s?) | (ИНН\s?:\s?) | "
                    r"(КПП\s?:\s?) | (Юр. адрес\s?:\s?) | "
                    r"(Почт. адрес\s?:\s?)")
    if client_requisite_tag:
        client_requisite = ' '.join(
            list(client_requisite_tag.stripped_strings))
        client_requisite = [item.replace(':', '').strip() for item in
                            re.split(reg_template, client_requisite) if item]
        client_fullname = {client_requisite[0]: client_requisite[1]}
        client_inn = {client_requisite[2]: client_requisite[3]}
        client_kpp = {client_requisite[4]: client_requisite[5]}
        client_address = {client_requisite[6]: client_requisite[7]}
        client_mail_address = {client_requisite[8]: client_requisite[9]}
        return tuple({**client_fullname, **client_inn, **client_kpp,
                      **client_address, **client_mail_address}.items())
    return ()


def _get_contragent_category(soup: BeautifulSoup) -> str:
    """Функция парсинга категории контрагента.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        str

    Raises:

    """
    contragent_category_tag = soup.find(id='custCategory')
    if contragent_category_tag:
        contragent_category = ' '.join(list(
            contragent_category_tag.stripped_strings))
        return contragent_category
    return ''


def _get_contact(soup: BeautifulSoup) -> str:
    """Функция парсинга контактов.

    Args:
        soup: подготовленная для парсинга HTML страница.

    Returns:
        str

    Raises:

    """
    collection = []
    category = _get_columns_name(soup)
    result_table = soup.find(name='table', attrs={
        'id': 'Request.ListsParent.ListsParent2.ContactPersonsList'})

    if not result_table:
        return tuple(collection)

    tr_tag_collection = result_table.find_all(name='tr')[1:]
    for tr in tr_tag_collection:
        text = [' '.join(list(td.stripped_strings))
                for td in tr.find_all(name='td')]
        tr_dict = dict(zip(category, text))
        collection.append(tuple(tr_dict.items()))

    return tuple(collection)
