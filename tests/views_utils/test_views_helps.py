"""
Tests for src.views_utils.views_helps
"""
from unittest.mock import MagicMock
from _pytest.monkeypatch import MonkeyPatch

from src.views_utils.views_helps import (
    article_views,
    article_views_all_years,
    get_view_file,
)


def test_article_views(monkeypatch: MonkeyPatch) -> None:
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


def test_article_views_all_years(monkeypatch: MonkeyPatch) -> None:
    """Test article_views_all_years returns multi-year data structure"""
    mock_bot = MagicMock()
    monkeypatch.setattr("src.views_utils.views_helps.view_bot", mock_bot)

    mock_bot.article_views_new.return_value = {
        "Title_1": {2020: 50, 2021: 100, 2022: 150},
        "Title_2": {2020: 25, 2021: 75},
        "Title_3": {},
    }

    articles = ["Title 1", "Title 2", "Title 3"]
    result = article_views_all_years("en", articles)

    # Check that underscores are replaced with spaces
    assert "Title 1" in result
    assert "Title 2" in result
    assert "Title 3" in result
    
    # Check multi-year data structure is preserved
    assert result["Title 1"] == {2020: 50, 2021: 100, 2022: 150}
    assert result["Title 2"] == {2020: 25, 2021: 75}
    assert result["Title 3"] == {}
    
    # Verify the bot was called with correct parameters
    mock_bot.article_views_new.assert_called_once_with(
        "en.wikipedia",
        articles,
        granularity="monthly",
        start="20150101",
        end="20251231",
    )


def test_article_views_all_years_be_x_old(monkeypatch: MonkeyPatch) -> None:
    """Test that be-x-old is correctly converted to be-tarask"""
    mock_bot = MagicMock()
    monkeypatch.setattr("src.views_utils.views_helps.view_bot", mock_bot)

    mock_bot.article_views_new.return_value = {"Title_1": {2020: 100}}

    articles = ["Title 1"]
    article_views_all_years("be-x-old", articles)

    # Check that be-x-old was converted to be-tarask
    mock_bot.article_views_new.assert_called_once()
    call_args = mock_bot.article_views_new.call_args
    assert call_args[0][0] == "be-tarask.wikipedia"


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
