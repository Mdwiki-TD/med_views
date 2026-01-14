"""
Tests for src.views_all_years
"""
from unittest.mock import MagicMock
from _pytest.monkeypatch import MonkeyPatch

from src.views_all_years import (
    calculate_total_views,
    get_one_lang_views_by_titles,
    update_data,
)


def test_calculate_total_views():
    """Test calculate_total_views with multi-year data structure"""
    u_data = {
        "Art1": {"all": 100},  # Uses "all" key
        "Art2": {"all": 200},
        "Art3": {"all": 0},
    }
    assert calculate_total_views("en", u_data) == 300
    assert calculate_total_views("fr", {}) == 0


def test_calculate_total_views_with_mixed_data():
    """Test calculate_total_views with mixed integer and dict data"""
    u_data = {
        "Art1": {"all": 250},  # Uses "all" key
        "Art2": {"all": 50},
    }
    assert calculate_total_views("en", u_data) == 300


def test_update_data():
    """Test update_data replaces underscores and updates correctly"""
    all_data = {"Art1": {2020: 10}, "Art2": 0}
    data = {"Art1": {2020: 20}, "Art2": {2021: 5}, "Art3": {2022: 15}}
    result = update_data(all_data, data)
    
    # Art1 should keep original value (10), Art2 should update (was 0), Art3 should be added
    assert result["Art1"] == {2020: 10}
    assert result["Art2"] == {2021: 5}
    assert result["Art3"] == {2022: 15}


def test_update_data_with_underscores():
    """Test that update_data handles underscores in titles"""
    all_data = {"Art_1": {2020: 10}}
    data = {"Art 1": {2020: 20}, "Art_2": {2021: 5}}
    result = update_data(all_data, data)
    
    # Underscores should be replaced with spaces
    assert "Art 1" in result
    assert "Art 2" in result
    assert result["Art 1"] == {2020: 10}  # Should keep original


def test_get_one_lang_views_by_titles(monkeypatch: MonkeyPatch) -> None:
    """Test get_one_lang_views_by_titles calls article_views_all_years correctly"""
    mock_article_views_all_years = MagicMock(
        return_value={
            "Art1": {2020: 10, 2021: 20},
            "Art2": {2020: 30, 2021: 40},
        }
    )
    monkeypatch.setattr("src.views_all_years.article_views_all_years", mock_article_views_all_years)

    result = get_one_lang_views_by_titles("en", ["Art1", "Art2"])
    
    assert result == {
        "Art1": {2020: 10, 2021: 20},
        "Art2": {2020: 30, 2021: 40},
    }
    mock_article_views_all_years.assert_called_once_with("en", ["Art1", "Art2"])


def test_get_one_lang_views_by_titles_batching(monkeypatch: MonkeyPatch) -> None:
    """Test that get_one_lang_views_by_titles batches requests in groups of 500"""
    call_count = 0
    
    def mock_article_views_all_years(langcode, titles):
        nonlocal call_count
        call_count += 1
        # Return mock data for each batch
        return {title: {2020: call_count * 10} for title in titles}
    
    monkeypatch.setattr("src.views_all_years.article_views_all_years", mock_article_views_all_years)

    # Create 1200 titles to test batching (should be 3 batches of 500, 500, 200)
    titles = [f"Art{i}" for i in range(1200)]
    result = get_one_lang_views_by_titles("en", titles)
    
    assert call_count == 3  # Should have made 3 API calls
    assert len(result) == 1200  # Should have all titles in result
