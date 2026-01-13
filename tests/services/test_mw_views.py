from datetime import date, datetime
from _pytest.monkeypatch import MonkeyPatch
from unittest.mock import MagicMock

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


def test_PageviewsClient(monkeypatch: MonkeyPatch) -> None:
    # Setup mock response
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"items": [{"article": "Test_Article", "timestamp": "2023010100", "views": 50}]}
    mock_resp.status_code = 200

    mock_get = MagicMock(return_value=mock_resp)
    monkeypatch.setattr("src.services.mw_views.requests.get", mock_get)

    client = PageviewsClient(user_agent="test-agent", parallelism=1)

    # Test article_views
    # Use dates that match the mock data
    results = client.article_views("en.wikipedia", ["Test Article"], start="2023010100", end="2023010100")

    # Verify results
    expected_date = datetime(2023, 1, 1, 0)
    assert results[expected_date]["Test Article"] == 50

    # Test article_views_new
    client.parallelism = 1  # for easier mocking if needed, but we already mocked get
    new_results = client.article_views_new("en.wikipedia", ["Test Article"], start="2023010100", end="2023010100")

    assert "Test Article" in new_results
    assert new_results["Test Article"]["2023"] == 50
    assert new_results["Test Article"]["all"] == 50
