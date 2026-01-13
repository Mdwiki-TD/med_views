"""
Tests for src.views
"""
from unittest.mock import MagicMock
from _pytest.monkeypatch import MonkeyPatch

from src.views import (
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
    mock_article_views = MagicMock(return_value={"Art1": 10})
    monkeypatch.setattr("src.views.article_views", mock_article_views)

    result = get_one_lang_views_by_titles("en", ["Art1"], "2020")
    assert result == {"Art1": 10}
