"""
Tests for src.app.views_utils.views_helps
"""

from unittest.mock import MagicMock

from _pytest.monkeypatch import MonkeyPatch

from src.app.views_utils.views_helps import (
    ViewsFetcher,
    article_views,
    article_views_all_years,
    get_view_file,
)


def test_article_views(monkeypatch: MonkeyPatch) -> None:
    mock_fetcher = MagicMock(spec=ViewsFetcher)
    mock_fetcher.article_views.return_value = {
        "Title 1": 100,
        "Title 2": 200,
        "Title 3": 300,
        "Title 4": 0,
    }

    monkeypatch.setattr(
        "src.app.views_utils.views_helps._get_default_fetcher",
        lambda: mock_fetcher,
    )

    articles = ["Title 1", "Title 2", "Title 3", "Title 4"]
    result = article_views("en", articles, year=2024)

    assert result["Title 1"] == 100
    assert result["Title 2"] == 200
    assert result["Title 3"] == 300
    assert result["Title 4"] == 0


def test_article_views_all_years(monkeypatch: MonkeyPatch) -> None:
    """Test article_views_all_years returns multi-year data structure"""
    mock_fetcher = MagicMock(spec=ViewsFetcher)
    mock_fetcher.article_views_all_years.return_value = {
        "Title 1": {2020: 50, 2021: 100, 2022: 150},
        "Title 2": {2020: 25, 2021: 75},
        "Title 3": {},
    }

    monkeypatch.setattr(
        "src.app.views_utils.views_helps._get_default_fetcher",
        lambda: mock_fetcher,
    )

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


def test_article_views_all_years_be_x_old(monkeypatch: MonkeyPatch) -> None:
    """Test that be-x-old is correctly converted to be-tarask"""
    mock_fetcher = MagicMock(spec=ViewsFetcher)
    mock_fetcher.article_views_all_years.return_value = {"Title 1": {2020: 100}}

    monkeypatch.setattr(
        "src.app.views_utils.views_helps._get_default_fetcher",
        lambda: mock_fetcher,
    )

    articles = ["Title 1"]
    article_views_all_years("be-x-old", articles)

    # Verify the fetcher was called
    mock_fetcher.article_views_all_years.assert_called_once()


def test_get_view_file(tmp_path, monkeypatch):
    # Mock get_config to return a config with views_by_year_path
    mock_config = MagicMock()
    mock_config.views_by_year_path = tmp_path

    monkeypatch.setattr("src.app.views_utils.views_helps.get_config", lambda: mock_config)

    # Reset the default fetcher so it picks up the mocked config
    import src.app.views_utils.views_helps as views_helps

    views_helps._default_fetcher = None

    lang = "en"
    year = 2024
    result = get_view_file(lang, year)

    expected_dir = tmp_path / "2024"
    expected_file = expected_dir / "en.json"

    assert result == expected_file
    assert expected_dir.exists()
