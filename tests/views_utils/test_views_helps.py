"""
Tests
# TODO: Implement test
"""
import pytest

from src.views_utils.views_helps import (
    article_views,
    article_all_views,
)


import unittest.mock

def test_article_views():
    with unittest.mock.patch("src.views_utils.views_helps.view_bot") as mock_bot:
        # Mock return data structure from article_views_new
        # Format: {title: {year: views}} or similar depending on how PageviewsClient works,
        # but the function expects `views.get(year)` etc.
        mock_bot.article_views_new.return_value = {
            "Title 1": {2024: 100},
            "Title 2": {"2024": 200}, # String key case
            "Title 3": {"all": 300},  # Fallback
            "Title 4": {},            # No data
        }
        
        articles = ["Title 1", "Title 2", "Title 3", "Title 4"]
        
        # Test 1: Normal site
        result = article_views("en", articles, year=2024)
        
        assert result["Title_1"] == 100
        assert result["Title_2"] == 200
        assert result["Title_3"] == 300
        assert result["Title_4"] == 0
        
        mock_bot.article_views_new.assert_called_with(
            "en.wikipedia", articles, granularity="monthly", start="20240101", end="20241231"
        )
        
        # Test 2: Special site 'be-x-old' -> 'be-tarask'
        article_views("be-x-old", articles, year=2024)
        args, kwargs = mock_bot.article_views_new.call_args
        assert args[0] == "be-tarask.wikipedia"



def test_article_all_views():
    with unittest.mock.patch("src.views_utils.views_helps.view_bot") as mock_bot:
        mock_data = {"Title 1": {"2020": 10, "2021": 20}}
        mock_bot.article_views_new.return_value = mock_data
        
        articles = ["Title 1"]
        result = article_all_views("en", articles, year=2024) # Year arg is used for what? Actually function signature has year but uses fixed dates?
        
        assert result == mock_data
        
        # Verify fixed start/end dates from implementation
        mock_bot.article_views_new.assert_called_with(
            "en.wikipedia", articles, granularity="monthly", start="20100101", end="20250627"
        )
        
        # Test site translation
        article_all_views("be-x-old", articles)
        args, kwargs = mock_bot.article_views_new.call_args
        assert args[0] == "be-tarask.wikipedia"

