naumen-api 
===================

[![Build Status](https://github.com/catemohi/naumen_api/actions/workflows/check_flake8.yml/badge.svg?branch=master)](https://github.com/catemohi/naumen_api/actions/workflows/check_flake8.yml) 
[![Coverege Percent](https://img.shields.io/badge/coverage-94%25-brightgreen?branch=master)](https://github.com/catemohi/naumen_api/)

Что за проект?
--------------

Проект интерфейса взаимодействия с CRM. Без доступа к БД и API. Написание собственной API основанной на парсинге DOM-дерева представлений.

Быстрый старт
-------------

Установить пакет из исходников:

    python setup.py install

Настроить файл config.json в корне пакета или создать коипию на его основе и передать в конфигуратор.

    from naumen_api.config.config import CONFIG


    CONFIG.config_path = '<path to config.json>'
    CONFIG.load_config()

Инициализировать объект клиента и соеденится с CRM системой.

    from naumen_api.config.config import CONFIG
    from naumen_api import naumen_api


    CONFIG.config_path = '<path to config.json>'
    CONFIG.load_config()
    client = naumen_api.Client()
    client.connect(username='test',password='test',domain='')

Методы API
-----------

- __get_issues(is_vip: bool = False, parse_issues_cards: bool = False)__:

    Метод для получения задач открытых на тех.поддержке в данный момент. Именнованный аргумент is_vip указывает на линию, задачи которой необходимо получить:

    * is_vip = False: первая линия.
    * is_vip = True: vip линия.

    parse_issues_cards, указывает нужно ли парсить данные с карточек этих задач. Иногда нам не нужна вся ифнормация о задаче, а только ее статус.
    Тогда имеет смысл передать parse_issues_cards = False, для ускорения.

- __get_sl_report(start_date: str, end_date: str, deadline: int)__:

    Метод для получения отчета о уровне service level. Ожидает на вход даты начала и конца периода и время обработки обращений, в формате целого числа, относительно которого и будет считать показатель.
    __Важно: Формат строки даты: %d.%m.%Y.__
    __Отчёт считается по дням в месяце. Если вы передадите период больше одного месяца, вы увидите средний процент за каждый день месяца, а не отчёт за каждый календарный день.__

- __get_mttr_report(start_date: str, end_date: str)__:

    Метод для получения отчета о уровне MTTR. Ожидает на вход даты начала и конца периода.
    __Важно: Формат строки даты: %d.%m.%Y.__
    __Отчёт считается по дням в месяце. Если вы передадите период больше одного месяца, вы увидите средний процент за каждый день месяца, а не отчёт за каждый календарный день.__

- __get_flr_report(start_date: str, end_date: str)__:

    Метод для получения отчета о уровне FLR. Ожидает на вход даты начала и конца периода.
    __Важно: Формат строки даты: %d.%m.%Y.__


