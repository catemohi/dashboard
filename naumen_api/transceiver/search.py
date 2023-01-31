import logging
from time import sleep
from typing import Sequence, Iterable, Tuple

from .crm import ActiveConnect, get_crm_response
from ..config.structures import SearchOptions, NaumenRequest, TypeReport
from ..config.structures import PageType, SearchType
from ..exceptions import CantGetData
from ..parser.parser import parse_naumen_page


log = logging.getLogger(__name__)


def search(crm: ActiveConnect, report: SearchType, *args,
               naumen_uuid: str = '', **kwargs) -> Iterable:
    """Функция для получения отчёта из CRM.

    Args:
        crm: активное соединение с CRM.
        report: отчёт, который необходимо получить.
        *args: позиционные аргументы(не используются)

    Kwargs:
        naumen_uuid: uuid уже созданного отчёта.
        **kwargs: именнованные аргументы для создания отчёта.

    Returns:
        Itrrable: коллекция обьектов необходимого отчёта.
    Raises:
        CantGetData: в случае невозможности вернуть коллекцию.
    """

    if report in [SearchType.ISSUES_SEARCH]:
        naumen_responce = _create_report(crm, report, *args, **kwargs)
        page_text = naumen_responce.text
        log.debug('Проверка количества страниц')
        page_count = parse_naumen_page(page_text, PageType.PAGINATION_PAGE)
        log.debug(f'Количество страниц: {page_count}')
        page_collection = [page_text]
        for i in range(1, page_count):
            naumen_responce = _create_report(
                crm, report, *args, **{'mod_params': {'pagination': str(i)},
                                       **kwargs})
            page_collection.append(naumen_responce.text)
        collect = []
        for page in page_collection:
            collect += parse_naumen_page(page, report.page)
        return collect





    # if report in [TypeReport.ISSUES_SEARCH]:
    #     get_crm_response(crm, TypeReport.CONTROL_ENABLE_SEARCH,
    #                      NaumenRequestType.CREATE_REPORT, *[], **{})
    #     sleep(1)
    #     get_crm_response(crm, TypeReport.CONTROL_SELECT_SEARCH,
    #                      NaumenRequestType.CREATE_REPORT, *[], **{})
    #     sleep(2)
    #     naumen_responce = get_crm_response(crm, report,
    #                                        NaumenRequestType.CREATE_REPORT,
    #                                        *args, mod_params=mod_params,
    #                                        mod_data=mod_data, **kwargs)
    #     page_text = naumen_responce.text
    #     log.debug('Проверка количества страниц')
    #     page_count = parse_naumen_page(page_text, PageType.PAGINATION_PAGE)
    #     log.debug(f'Количество страниц: {page_count}')
    #     page_collection = [page_text]
    #     for i in range(1, page_count):
    #         mod_params = dict(mod_params)
    #         mod_params.update({'pagination': str(i)})
    #         mod_params = tuple(mod_params.items())
    #         naumen_responce = get_crm_response(
    #             crm, report, NaumenRequestType.CREATE_REPORT, *args,
    #             mod_params=mod_params, mod_data=mod_data,
    #             **kwargs)
    #         page_collection.append(naumen_responce.text)
    #     collect = []
    #     for page in page_collection:
    #         collect += parse_naumen_page(page, report.page)
    #     return collect
