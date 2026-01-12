from datetime import date, datetime

import pytest

from src.services.mw_views import (
    PageviewsClient,
    format_date,
    month_from_day,
    parse_date,
    timestamps_between,
)


def test_parse_date():
    # "YYYYMMDDHH" -> datetime
    input_str = "2023010100"
    expected = datetime(2023, 1, 1, 0, 0)
    assert parse_date(input_str) == expected

    # Test padding
    input_str_short = "20230101"
    expected_short = datetime(2023, 1, 1, 0, 0)
    assert parse_date(input_str_short) == expected_short


def test_format_date():
    dt = datetime(2023, 1, 1, 5, 0)
    expected = "2023010105"
    assert format_date(dt) == expected

    d = date(2023, 12, 31)
    # strftime on date object usually defaults time to 00:00:00
    expected_date = "2023123100"
    assert format_date(d) == expected_date


def test_timestamps_between():
    start = datetime(2023, 1, 1)
    end = datetime(2023, 1, 3)
    increment = datetime(2023, 1, 2) - datetime(2023, 1, 1)  # 1 day

    gen = timestamps_between(start, end, increment)
    results = list(gen)

    assert len(results) == 3
    assert results[0] == datetime(2023, 1, 1)
    assert results[1] == datetime(2023, 1, 2)
    assert results[2] == datetime(2023, 1, 3)


def test_month_from_day():
    dt = datetime(2023, 5, 15, 12, 30)
    expected = datetime(2023, 5, 1, 0, 0)
    assert month_from_day(dt) == expected

    dt2 = datetime(2023, 12, 31)
    expected2 = datetime(2023, 12, 1, 0, 0)
    assert month_from_day(dt2) == expected2


@pytest.mark.skip(reason="Requires network mocking")
def test_PageviewsClient():
    # TODO: Implement test with mocks
    pass
