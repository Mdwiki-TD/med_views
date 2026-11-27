"""
Tests for src.app.one_year.views
"""

from unittest.mock import MagicMock

from src.app.one_year.views import SingleYearViewsService


class TestSingleYearViewsService:
    """Tests for the SingleYearViewsService class."""

    def test_calculate_total_views(self):
        """Test calculating total views."""
        data = {"Cancer": 1000, "Diabetes": 500}
        result = SingleYearViewsService.calculate_total_views("en", data)
        assert result == 1500

    def test_calculate_total_views_with_dict(self):
        """Test calculating total views with dict values."""
        data = {"Cancer": {"all": 1000, "2024": 1000}}
        result = SingleYearViewsService.calculate_total_views("en", data)
        assert result == 1000

    def test_calculate_total_views_empty(self):
        """Test calculating total views with empty data."""
        result = SingleYearViewsService.calculate_total_views("fr", {})
        assert result == 0

    def test_update_data(self):
        """Test merging data with underscore normalization."""
        all_data = {"Art1": 10, "Art2": 0}
        data = {"Art1": 20, "Art2": 5, "Art3": 15}

        result = SingleYearViewsService.update_data(all_data, data)

        assert result == {"Art1": 10, "Art2": 5, "Art3": 15}

    def test_update_data_with_underscores(self):
        """Test that update_data handles underscores in titles."""
        all_data = {"Art_1": 10}
        data = {"Art 1": 20, "Art_2": 5}

        result = SingleYearViewsService.update_data(all_data, data)

        assert "Art 1" in result
        assert "Art 2" in result
        assert result["Art 1"] == 10  # Should keep original

    def test_get_one_lang_views_by_titles(self):
        """Test fetching views for all titles."""
        mock_fetcher = MagicMock()
        mock_fetcher.article_views.return_value = {"Cancer": 1000}

        service = SingleYearViewsService(views_fetcher=mock_fetcher)
        result = service.get_one_lang_views_by_titles("en", ["Cancer"], 2024)

        assert result == {"Cancer": 1000}

    def test_get_one_lang_views_by_titles_batching(self):
        """Test that get_one_lang_views_by_titles batches requests in groups of 500."""
        mock_fetcher = MagicMock()
        mock_fetcher.article_views.return_value = {}

        service = SingleYearViewsService(views_fetcher=mock_fetcher)

        # Create 1200 titles to test batching (should be 3 batches of 500, 500, 200)
        titles = [f"Art{i}" for i in range(1200)]
        service.get_one_lang_views_by_titles("en", titles, 2024)

        assert mock_fetcher.article_views.call_count == 3  # Should have made 3 API calls
