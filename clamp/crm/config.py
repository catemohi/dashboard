from pathlib import Path
from json import load
from typing import Mapping
from dataclasses import dataclass

CONFIG_FILE_PATH = Path('.') / 'config.json'
with open(CONFIG_FILE_PATH) as file:
    CONFIG = load(file)
#TODO прокинуть переменную из окружения
NAUMEN_LOGIN = ''
#TODO прокинуть переменную из окружения
NAUMEN_PASSWORD = ''
#TODO прокинуть переменную из окружения
NAUMEN_DOMAIN = ''
CONFIG.update({'auth': {'login': NAUMEN_LOGIN,
                        'password': NAUMEN_PASSWORD,
                        'domain': NAUMEN_DOMAIN}})

@dataclass
class CreateParams:
    
    """Класс данных для хранения сформированного запроса к CRM Naumen.
    
        Attributes:
            uuid: идентификатор обьекта
            header: header для запроса
            parsms: параметры для запроса
            data: данные запроса
            verify: верификация
    """
    uuid: str
    headers: Mapping
    params: Mapping
    data: Mapping
    verify: bool
    delay_attems: int
    num_attems: int


def get_params_create_report(report_name: str) -> CreateParams:
    """Функция которая достает необходимые параметры из конфигурационного файла.
    
    Args:
        report_name: название отчета
    Returns:
        Коллекцию параметров.
    Raises:
    
    """
    data_create = CreateParams('',{},{},{},False,0,0)
    reports_name = [key for key, val in CONFIG.items() if "create request" in val]
    if not report_name in reports_name:
        return data_create
    data_create.uuid = CONFIG[report_name]['uuid']
    data_create.headers = CONFIG['headers']
    data_create.data = CONFIG[report_name]['create request']['data']
    data_create.params = CONFIG[report_name]['create request']['params']
    data_create.verify = CONFIG['verify']['value']
    data_create.delay_attems = CONFIG[report_name]['delay attems']['value']
    data_create.num_attems = CONFIG[report_name]['num attems']['value']
    return data_create


if __name__ == "__main__":
    data = get_params_create_report('')
    print(data)