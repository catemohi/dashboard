from naumen_api.exceptions import CantGetData
from naumen_api.parser.service_level import ServiceLevel, parse

import pytest


def test_parse_day_report():
    with open('naumen_api\\parser\\test\\parse-templates-page\\'
              'service_level_templates\\'
              'service_level_day_report.html') as text:

        text = text.read()
        response = parse(text)
        assert response == (
            [
                ServiceLevel(
                    day='1',
                    group='Группа поддержки VIP - клиентов (Напр ТП В2В)',
                    total_issues=18,
                    total_primary_issues=5,
                    num_issues_before_deadline=17,
                    num_issues_after_deadline=1,
                    service_level=94.0),
                ServiceLevel(
                    day='1',
                    group='Группа поддержки и управления сетью  (Напр ТП В2В)',
                    total_issues=85,
                    total_primary_issues=34,
                    num_issues_before_deadline=83,
                    num_issues_after_deadline=2,
                    service_level=97.0),
                ServiceLevel(
                    day='1',
                    group='Итог',
                    total_issues=103,
                    total_primary_issues=39,
                    num_issues_before_deadline=100,
                    num_issues_after_deadline=3,
                    service_level=95.5),
                ],
            )


def test_parse_empty_report():
    with open('naumen_api\\parser\\test\\parse-templates-page\\'
              'service_level_templates\\'
              'service_level_empty_report.html') as text:

        text = text.read()
        response = parse(text)
        assert response == ()


def test_parse_error_report():
    with open('naumen_api\\parser\\test\\parse-templates-page\\'
              'service_level_templates\\'
              'service_level_error_report.html') as text:
        text = text.read()

    with pytest.raises(CantGetData):
        parse(text)


if __name__ == '__main__':

    pytest.main()
