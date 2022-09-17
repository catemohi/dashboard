from naumen_api.exceptions import CantGetData
from naumen_api.parser.issue_card import parse
from naumen_api.parser.issues import Issue

import pytest


def test_parse_day_report():
    with open('naumen_api\\parser\\test\\parse-templates-page\\'
              'issue_card\\issue_card.html') as text:

        text = text.read()
        response = parse(text)
        for line in response:
            assert type(line) == Issue


def test_parse_error_report():
    with open('naumen_api\\parser\\test\\parse-templates-page\\'
              'issue_card\\issue_card_error.html') as text:
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
