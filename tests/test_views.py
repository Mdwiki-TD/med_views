"""
Tests for src.views
"""
from pathlib import Path
from unittest.mock import MagicMock

from src.views import (
    calculate_total_views,
    get_one_lang_views,
    get_one_lang_views_by_titles,
    get_one_lang_views_by_titles_plus_1k,
    load_one_lang_views,
    retrieve_view_statistics,
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


def test_get_one_lang_views_by_titles(monkeypatch):
    mock_article_views = MagicMock(return_value={"Art1": 10})
    monkeypatch.setattr("src.views.article_views", mock_article_views)

    result = get_one_lang_views_by_titles("en", ["Art1"], "2020")
    assert result == {"Art1": 10}


def test_get_one_lang_views_by_titles_plus_1k(monkeypatch):
    mock_json_load = MagicMock(return_value={})
    monkeypatch.setattr("src.views.json_load", mock_json_load)

    mock_article_views = MagicMock(return_value={"New": 10})
    monkeypatch.setattr("src.views.article_views", mock_article_views)

    mock_dump = MagicMock()
    monkeypatch.setattr("src.views.dump_one", mock_dump)

    json_file = MagicMock(spec=Path)
    json_file.exists.return_value = False

    result = get_one_lang_views_by_titles_plus_1k("en", ["New"], "2020", json_file)
    assert result == {"New": 10}
    mock_dump.assert_called()


def test_retrieve_view_statistics():
    data = {"Art_1": 10}
    in_file = {"Old Art": 5}
    result = retrieve_view_statistics(data, "en", in_file)
    # Underscores in data keys should be replaced
    assert "Art 1" in result
    assert result["Art 1"] == 10
    assert result["Old Art"] == 5


def test_load_one_lang_views(monkeypatch):
    mock_get_file = MagicMock()
    monkeypatch.setattr("src.views.get_view_file", mock_get_file)

    mock_get_titles = MagicMock(return_value={"Art1": 10})
    monkeypatch.setattr("src.views.get_one_lang_views_by_titles", mock_get_titles)

    result = load_one_lang_views("en", ["Art1"], "2020")
    assert result == {"Art1": 10}


def test_get_one_lang_views(monkeypatch):
    mock_get_file = MagicMock()
    monkeypatch.setattr("src.views.get_view_file", mock_get_file)

    mock_json = MagicMock(return_value={})
    monkeypatch.setattr("src.views.json_load", mock_json)

    mock_load = MagicMock(return_value={"Art1": 10})
    monkeypatch.setattr("src.views.load_one_lang_views", mock_load)

    mock_dump = MagicMock()
    monkeypatch.setattr("src.views.dump_one", mock_dump)

    mock_calc = MagicMock(return_value=10)
    monkeypatch.setattr("src.views.calculate_total_views", mock_calc)

    json_file = MagicMock(spec=Path)
    json_file.exists.return_value = False
    mock_get_file.return_value = json_file

    result = get_one_lang_views("en", ["Art1"], "2020")
    assert result == 10
