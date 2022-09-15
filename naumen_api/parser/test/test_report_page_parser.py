from naumen_api.exceptions import CantGetData
from naumen_api.parser.report_page import parse

import pytest


@pytest.mark.parametrize(
    ('input_name', 'expected'),
    (
        ('test', None), ('ID7981604', ('adhrpi18058200000o6eta10hi9s9nao',)),
        ),
    )
def test_parse_day_report(input_name, expected):
    with open('naumen_api\\parser\\test\\parse-templates-page\\'
              'report_page\\report_page.html') as text:

        text = text.read()
        response = parse(text, input_name)
        print(response)
        assert response == expected


error_text = [str(), list(), dict(), tuple(), int(), set()]


@pytest.mark.parametrize('text', error_text)
def test_parse_error_params(text):
    with pytest.raises(CantGetData):
        parse(text, 'test')


if __name__ == '__main__':

    pytest.main()
