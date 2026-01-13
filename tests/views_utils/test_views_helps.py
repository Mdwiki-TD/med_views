"""
Tests for src.views_utils.views_helps
"""
from unittest.mock import MagicMock

from src.views_utils.views_helps import (
    article_views,
    get_view_file,
)


def test_article_views(monkeypatch):
    mock_bot = MagicMock()
    monkeypatch.setattr("src.views_utils.views_helps.view_bot", mock_bot)

    mock_bot.article_views_new.return_value = {
        "Title_1": {2024: 100},
        "Title_2": {"2024": 200},
        "Title_3": {"all": 300},
        "Title_4": {},
    }

    articles = ["Title 1", "Title 2", "Title 3", "Title 4"]
    result = article_views("en", articles, year=2024)

    assert result["Title 1"] == 100
    assert result["Title 2"] == 200
    assert result["Title 3"] == 300
    assert result["Title 4"] == 0


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
