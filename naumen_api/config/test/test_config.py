from naumen_api.config.config import CONFIG
from naumen_api.config.config import get_params_create_report
from naumen_api.config.config import get_params_find
from naumen_api.config.config import get_params_for_delete
from naumen_api.config.config import CreateParams, FindParams, DeleteParams
from naumen_api.transceiver.transceiver import TypeReport
from pathlib import PurePath


import pytest

error_type = [list(), dict(), tuple(), int(), set()]
type_report_name = [
    TypeReport.FLR_LEVEL.value,
    TypeReport.MTTR_LEVEL.value,
    TypeReport.ISSUES_FIRST_LINE.value,
    TypeReport.ISSUES_VIP_LINE.value,
    TypeReport.SERVICE_LEVEL.value,
    ]


@pytest.mark.parametrize('path', error_type)
def test_type_path(path):
    with pytest.raises(TypeError):
        CONFIG.config_path = error_type


def test_type_valid_path():
    CONFIG.config_path = ''
    assert isinstance(CONFIG.config_path, PurePath)


@pytest.mark.parametrize('name', type_report_name)
def test_get_create_report_params(name):
    params_empry = get_params_create_report('')
    params = get_params_create_report(name)
    assert params != params_empry


@pytest.mark.parametrize('name', error_type)
def test_get_create_report_params_error_input(name):
    params = get_params_create_report(name)
    assert isinstance(params, CreateParams)


def test_get_find_report_params():
    params = get_params_find()
    assert isinstance(params, FindParams)


def test_get_delete_report_params():
    params = get_params_for_delete()
    assert isinstance(params, DeleteParams)
