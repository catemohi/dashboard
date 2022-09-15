from naumen_api.exceptions import CantGetData
from naumen_api.parser.mttr import Mttr, parse

import pytest


def test_parse_day_report():
    with open('naumen_api\\parser\\test\\parse-templates-page\\'
              'mttr\\mttr_day_report.html') as text:

        text = text.read()
        response = parse(text)
        print(response)
        assert response == (
            Mttr(
                day='14',
                total_issues='37',
                average_mttr='505.7837837837838',
                average_mttr_tech_support='67.08108108108108',
                ),
            )


def test_parse_empty_report():
    with open('naumen_api\\parser\\test\\parse-templates-page\\'
              'mttr\\mttr_empty_report.html') as text:

        text = text.read()
        response = parse(text)
        assert response == ()


def test_parse_error_report():
    with open('naumen_api\\parser\\test\\parse-templates-page\\'
              'mttr\\mttr_error_report.html') as text:
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
