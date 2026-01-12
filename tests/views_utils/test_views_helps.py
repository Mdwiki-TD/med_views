"""
Tests for src.views_utils.views_helps
"""
from pathlib import Path
from unittest.mock import patch

from src.views_utils.views_helps import (
    article_all_views,
    article_views,
    get_view_file,
)


def test_article_views():
    with patch("src.views_utils.views_helps.view_bot") as mock_bot:
        mock_bot.article_views_new.return_value = {
            "Title 1": {2024: 100},
            "Title 2": {"2024": 200},
            "Title 3": {"all": 300},
            "Title 4": {},
        }

        articles = ["Title 1", "Title 2", "Title 3", "Title 4"]
        result = article_views("en", articles, year=2024)

        assert result["Title_1"] == 100
        assert result["Title_2"] == 200
        assert result["Title_3"] == 300
        assert result["Title_4"] == 0


def test_article_all_views():
    with patch("src.views_utils.views_helps.view_bot") as mock_bot:
        mock_data = {"Title 1": {"2020": 10}}
        mock_bot.article_views_new.return_value = mock_data

        result = article_all_views("en", ["Title 1"])
        assert result == mock_data


def test_get_view_file(tmp_path, monkeypatch):
    # Mock views_by_year_path
    monkeypatch.setattr("src.views_utils.views_helps.views_by_year_path", tmp_path)

    lang = "en"
    year = 2024
    result = get_view_file(lang, year)

    expected_dir = tmp_path / "2024"
    expected_file = expected_dir / "en.json"

    assert result == expected_file
    assert expected_dir.exists()
