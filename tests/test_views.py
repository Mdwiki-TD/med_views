"""
Tests for src.views
"""
from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path

from src.views import (
    get_one_lang_views,
    get_one_lang_views_by_titles,
    get_one_lang_views_by_titles_plus_1k,
    load_one_lang_views,
    update_data,
)


def test_update_data():
    all_data = {"Art1": 10, "Art2": 0}
    data = {"Art1": 20, "Art2": 5, "Art3": 15}
    # update_data updates only if key not in all_data or value is 0
    result = update_data(all_data, data)
    assert result == {"Art1": 10, "Art2": 5, "Art3": 15}


@patch("src.views.article_views")
def test_get_one_lang_views_by_titles(mock_article_views):
    mock_article_views.return_value = {"Art1": 10, "Art2": 20}
    titles = ["Art1", "Art2"]
    result = get_one_lang_views_by_titles("en", titles, "2020")
    assert result == {"Art1": 10, "Art2": 20}
    mock_article_views.assert_called_once()


@patch("src.views.article_views")
@patch("src.views.json_load")
@patch("src.views.dump_one")
def test_get_one_lang_views_by_titles_plus_1k(mock_dump, mock_json_load, mock_article_views):
    mock_json_load.return_value = {"Old": 5}
    mock_article_views.return_value = {"New": 10}

    json_file = MagicMock(spec=Path)
    json_file.exists.return_value = True

    result = get_one_lang_views_by_titles_plus_1k("en", ["New"], "2020", json_file)

    assert result == {"New": 10}
    mock_dump.assert_called()


@patch("src.views.get_view_file")
@patch("src.views.get_one_lang_views_by_titles")
def test_load_one_lang_views(mock_get_titles, mock_get_file):
    mock_get_titles.return_value = {"Art1": 10}

    result = load_one_lang_views("en", ["Art1"], "2020")
    assert result == {"Art1": 10}


@patch("src.views.get_view_file")
@patch("src.views.json_load")
@patch("src.views.load_one_lang_views")
@patch("src.views.dump_one")
@patch("src.views.calculate_total_views")
def test_get_one_lang_views(mock_calc, mock_dump, mock_load, mock_json, mock_get_file):
    mock_json.return_value = {"Art1": 10}
    mock_load.return_value = {"Art2": 20}
    mock_calc.return_value = 30

    json_file = MagicMock(spec=Path)
    json_file.exists.return_value = True
    mock_get_file.return_value = json_file

    result = get_one_lang_views("en", ["Art1", "Art2"], "2020")
    assert result == 30
    mock_dump.assert_called_once()
