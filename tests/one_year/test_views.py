"""
Tests for src.app.one_year.views
"""

from unittest.mock import MagicMock

from _pytest.monkeypatch import MonkeyPatch

from src.app.one_year.views import (
    SingleYearViewsService,
    calculate_total_views,
    get_one_lang_views_by_titles,
    update_data,
)


def test_calculate_total_views():
    u_data = {"Art1": 100, "Art2": {"all": 200}, "Art3": {"all": 0}}
    assert calculate_total_views("en", u_data) == 300
    assert calculate_total_views("fr", {}) == 0


def test_update_data():
    all_data = {"Art1": 10, "Art2": 0}
    data = {"Art1": 20, "Art2": 5, "Art3": 15}
    result = update_data(all_data, data)
    assert result == {"Art1": 10, "Art2": 5, "Art3": 15}


def test_get_one_lang_views_by_titles(monkeypatch: MonkeyPatch) -> None:
    mock_service = MagicMock(spec=SingleYearViewsService)
    mock_service.get_one_lang_views_by_titles.return_value = {"Art1": 10}

    monkeypatch.setattr(
        "src.app.one_year.views._get_default_service",
        lambda: mock_service,
    )

    result = get_one_lang_views_by_titles("en", ["Art1"], "2020")
    assert result == {"Art1": 10}
