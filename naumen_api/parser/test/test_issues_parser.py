from naumen_api.exceptions import CantGetData
from naumen_api.parser.issues import Issue
from naumen_api.parser.issues import parse


import pytest


def test_parse_day_first_line_report():
    with open('naumen_api\\parser\\test\\parse-templates-page\\'
              'issue\\issues_first_line.html') as text:

        text = text.read()
        response = parse(text)
        for line in response:
            assert type(line) == Issue


def test_parse_day_vip_line_report():
    with open('naumen_api\\parser\\test\\parse-templates-page\\'
              'issue\\issues_vip_line.html') as text:

        text = text.read()
        response = parse(text)
        for line in response:
            assert type(line) == Issue


def test_parse_error_report():
    with open('naumen_api\\parser\\test\\parse-templates-page\\'
              'issue\\issues_error_line.html') as text:
        text = text.read()

    with pytest.raises(CantGetData):
        parse(text)


error_text = [str(), list(), dict(), tuple(), int(), set()]


@pytest.mark.parametrize('text', error_text)
def test_parse_error_params(text):
    with pytest.raises(CantGetData):
        parse(text)


if __name__ == '__main__':

    pytest.main()
