from naumen_api.exceptions import CantGetData
from naumen_api.parser.flr import Flr, parse

import pytest


def test_parse_day_report():
    with open('naumen_api\\parser\\test\\parse-templates-page\\'
              'flr\\flr_day_report.html') as text:

        text = text.read()
        response = parse(text)
        assert response == (
            Flr(
                date='14.09.2022',
                flr_level='38',
                num_issues_closed_independently='15',
                total_primary_issues='39',
                ),
            )


def test_parse_empty_report():
    with open('naumen_api\\parser\\test\\parse-templates-page\\'
              'flr\\flr_empty_report.html') as text:

        text = text.read()
        response = parse(text)
        assert response == ()


def test_parse_error_report():
    with open('naumen_api\\parser\\test\\parse-templates-page\\'
              'flr\\flr_error_report.html') as text:
        text = text.read()

    with pytest.raises(CantGetData):
        parse(text)


error_text = [str(), list(), dict(), tuple(), int(), set(), 'error string']


@pytest.mark.parametrize('text', error_text)
def test_parse_error_params(text):
    with pytest.raises(CantGetData):
        parse(text)


if __name__ == '__main__':

    pytest.main()
