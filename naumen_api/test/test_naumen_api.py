import logging
from json import loads
from os import environ
from datetime import datetime

from naumen_api.config.config import CONFIG
from naumen_api.naumen_api import Client

import pytest


log = logging.getLogger(__name__)


error_credentials = (
    ('login', 'password', 'domain'),
    (
        ('', '', ''),
        (environ.get('DOMAIN_LOGIN'),
         environ.get('DOMAIN_PASSWORD'),
         ''),
        (environ.get('DOMAIN_LOGIN'),
         '',
         ''),
        ('',
         environ.get('DOMAIN_PASSWORD'),
         ''),
        ),
    )


@pytest.mark.parametrize(*error_credentials)
def test_error_connect(login, password, domain):
    CONFIG.config_path = 'E:\\.dev\\projects\\naumen_api\\.env\\config.json'
    CONFIG.load_config()
    client = Client()
    responce = loads(client.connect(username=login,
                                    password=password, domain=domain))
    assert responce.get('status_code') == 401
    assert responce.get('status_message') == "Unauthorized"
    assert responce.get("content") == []


def test_success_connect():
    CONFIG.config_path = 'E:\\.dev\\projects\\naumen_api\\.env\\config.json'
    CONFIG.load_config()
    client = Client()
    responce = loads(client.connect(username=environ.get('DOMAIN_LOGIN'),
                                    password=environ.get('DOMAIN_PASSWORD'),
                                    domain='CORP.ERTELECOM.LOC'))
    assert responce.get('status_code') == 200
    assert responce.get('status_message') == "OK"
    assert responce.get("content") == []


def test_get_issues():
    CONFIG.config_path = 'E:\\.dev\\projects\\naumen_api\\.env\\config.json'
    CONFIG.load_config()
    client = Client()
    client.connect(username=environ.get('DOMAIN_LOGIN'),
                   password=environ.get('DOMAIN_PASSWORD'),
                   domain='CORP.ERTELECOM.LOC')
    responce = loads(client.get_issues())
    assert responce.get('status_code') == 200
    assert responce.get('status_message') == "OK"
    assert responce.get("content") != []
    for issue in responce.get("content"):
        assert not issue.get("vip_contragent")


def test_get_issues_parse_cards():
    CONFIG.config_path = 'E:\\.dev\\projects\\naumen_api\\.env\\config.json'
    CONFIG.load_config()
    client = Client()
    client.connect(username=environ.get('DOMAIN_LOGIN'),
                   password=environ.get('DOMAIN_PASSWORD'),
                   domain='CORP.ERTELECOM.LOC')
    responce = loads(client.get_issues(parse_issues_cards=True))
    assert responce.get('status_code') == 200
    assert responce.get('status_message') == "OK"
    assert responce.get("content") != []


def test_get_vip_issues():
    CONFIG.config_path = 'E:\\.dev\\projects\\naumen_api\\.env\\config.json'
    CONFIG.load_config()
    client = Client()
    client.connect(username=environ.get('DOMAIN_LOGIN'),
                   password=environ.get('DOMAIN_PASSWORD'),
                   domain='CORP.ERTELECOM.LOC')
    responce = loads(client.get_issues(is_vip=True))
    assert responce.get('status_code') == 200
    assert responce.get('status_message') == "OK"
    assert responce.get("content") != []
    for issue in responce.get("content"):
        assert issue.get("vip_contragent")


def test_get_vip_issues_parse_cards():
    CONFIG.config_path = 'E:\\.dev\\projects\\naumen_api\\.env\\config.json'
    CONFIG.load_config()
    client = Client()
    client.connect(username=environ.get('DOMAIN_LOGIN'),
                   password=environ.get('DOMAIN_PASSWORD'),
                   domain='CORP.ERTELECOM.LOC')
    responce = loads(client.get_issues(is_vip=True, parse_issues_cards=True))
    assert responce.get('status_code') == 200
    assert responce.get('status_message') == "OK"
    assert responce.get("content") != []


error_text = [str(), list(), dict(), tuple(), int(), set(),
              datetime.now().date(), datetime.now()]


@pytest.mark.parametrize('error_param', error_text)
def test_get_service_level_error_date(error_param):
    CONFIG.config_path = 'E:\\.dev\\projects\\naumen_api\\.env\\config.json'
    CONFIG.load_config()
    client = Client()
    client.connect(username=environ.get('DOMAIN_LOGIN'),
                   password=environ.get('DOMAIN_PASSWORD'),
                   domain='CORP.ERTELECOM.LOC')
    responce = loads(client.get_sl_report(error_param, error_param, 15))
    assert responce.get('status_code') == 400
    assert responce.get('status_message') == "Bad Request"
    assert responce.get("content") == []


@pytest.mark.parametrize('error_param', error_text)
def test_get_service_level_error_params(error_param):
    CONFIG.config_path = 'E:\\.dev\\projects\\naumen_api\\.env\\config.json'
    CONFIG.load_config()
    client = Client()
    client.connect(username=environ.get('DOMAIN_LOGIN'),
                   password=environ.get('DOMAIN_PASSWORD'),
                   domain='CORP.ERTELECOM.LOC')
    responce = loads(client.get_sl_report(error_param, error_param,
                                          error_param))
    assert responce.get('status_code') == 400
    assert responce.get('status_message') == "Bad Request"
    assert responce.get("content") == []


error_date_format = (
    ('start_date', 'end_date'),
    (
        ('2022.02.01', '2022.03.02'),
        ('02.2022.01', '03.2022.01'),
        ('02.01', '03.01'),
    ),
    )


@pytest.mark.parametrize(*error_date_format)
def test_get_service_level_error_date_format(start_date, end_date):
    CONFIG.config_path = 'E:\\.dev\\projects\\naumen_api\\.env\\config.json'
    CONFIG.load_config()
    client = Client()
    client.connect(username=environ.get('DOMAIN_LOGIN'),
                   password=environ.get('DOMAIN_PASSWORD'),
                   domain='CORP.ERTELECOM.LOC')
    responce = loads(client.get_sl_report(start_date, end_date, 15))
    assert responce.get('status_code') == 400
    assert responce.get('status_message') == "Bad Request"
    assert responce.get("content") == []


success_dates = (
    ('start_date', 'end_date', 'expectation'),
    (
        ('01.09.2022', '01.10.2022', True),
        ('01.09.2022', '01.09.2022', False),
        ('01.09.2022', '02.09.2022', True),
    ),
    )


@pytest.mark.parametrize(*success_dates)
def test_get_service_level(start_date, end_date, expectation):

    CONFIG.config_path = 'E:\\.dev\\projects\\naumen_api\\.env\\config.json'
    CONFIG.load_config()
    client = Client()
    client.connect(username=environ.get('DOMAIN_LOGIN'),
                   password=environ.get('DOMAIN_PASSWORD'),
                   domain='CORP.ERTELECOM.LOC')
    responce = loads(client.get_sl_report(start_date, end_date, 15))
    assert responce.get('status_code') == 200
    assert responce.get('status_message') == "OK"
    assert bool(len(responce.get("content"))) == expectation


@pytest.mark.parametrize(*success_dates)
def test_get_mttr_report(start_date, end_date, expectation):

    CONFIG.config_path = 'E:\\.dev\\projects\\naumen_api\\.env\\config.json'
    CONFIG.load_config()
    client = Client()
    client.connect(username=environ.get('DOMAIN_LOGIN'),
                   password=environ.get('DOMAIN_PASSWORD'),
                   domain='CORP.ERTELECOM.LOC')
    responce = loads(client.get_mttr_report(start_date, end_date))
    assert responce.get('status_code') == 200
    assert responce.get('status_message') == "OK"
    assert bool(len(responce.get("content"))) == expectation


@pytest.mark.parametrize(*success_dates)
def test_get_flr_report(start_date, end_date, expectation):

    CONFIG.config_path = 'E:\\.dev\\projects\\naumen_api\\.env\\config.json'
    CONFIG.load_config()
    client = Client()
    client.connect(username=environ.get('DOMAIN_LOGIN'),
                   password=environ.get('DOMAIN_PASSWORD'),
                   domain='CORP.ERTELECOM.LOC')
    responce = loads(client.get_flr_report(start_date, end_date))
    assert responce.get('status_code') == 200
    assert responce.get('status_message') == "OK"
    assert bool(len(responce.get("content"))) == expectation


if __name__ == '__main__':

    pytest.main()
