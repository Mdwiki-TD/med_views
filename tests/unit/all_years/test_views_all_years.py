"""
Tests for src.app.all_years.views
"""

from unittest.mock import MagicMock

from src.app.all_years.views import MultiYearViewsService


class TestMultiYearViewsService:
    """Tests for the MultiYearViewsService class."""

    def test_calculate_total_views(self):
        """Test calculate_total_views with multi-year data structure"""
        u_data = {
            "Art1": {"all": 100},  # Uses "all" key
            "Art2": {"all": 200},
            "Art3": {"all": 0},
        }
        assert MultiYearViewsService.calculate_total_views("en", u_data) == 300
        assert MultiYearViewsService.calculate_total_views("fr", {}) == 0

    def test_calculate_total_views_with_mixed_data(self):
        """Test calculate_total_views with mixed integer and dict data"""
        u_data = {
            "Art1": {"all": 250},  # Uses "all" key
            "Art2": {"all": 50},
        }
        assert MultiYearViewsService.calculate_total_views("en", u_data) == 300

    def test_update_data(self):
        """Test update_data replaces underscores and updates correctly"""
        all_data = {"Art1": {2020: 10}, "Art2": 0}
        data = {"Art1": {2020: 20}, "Art2": {2021: 5}, "Art3": {2022: 15}}
        result = MultiYearViewsService.update_data(all_data, data)

        # Art1 should keep original value (10), Art2 should update (was 0), Art3 should be added
        assert result["Art1"] == {2020: 10}
        assert result["Art2"] == {2021: 5}
        assert result["Art3"] == {2022: 15}

    def test_update_data_with_underscores(self):
        """Test that update_data handles underscores in titles"""
        all_data = {"Art_1": {2020: 10}}
        data = {"Art 1": {2020: 20}, "Art_2": {2021: 5}}
        result = MultiYearViewsService.update_data(all_data, data)

        # Underscores should be replaced with spaces
        assert "Art 1" in result
        assert "Art 2" in result
        assert result["Art 1"] == {2020: 10}  # Should keep original

    def test_get_one_lang_views_by_titles(self):
        """Test get_one_lang_views_by_titles calls article_views_all_years correctly"""
        mock_fetcher = MagicMock()
        mock_fetcher.article_views_all_years.return_value = {
            "Art1": {2020: 10, 2021: 20},
            "Art2": {2020: 30, 2021: 40},
        }

        service = MultiYearViewsService(views_fetcher=mock_fetcher)
        result = service.get_one_lang_views_by_titles("en", ["Art1", "Art2"])

        assert result == {
            "Art1": {2020: 10, 2021: 20},
            "Art2": {2020: 30, 2021: 40},
        }

    def test_get_one_lang_views_by_titles_batching(self):
        """Test that get_one_lang_views_by_titles batches requests in groups of 500"""
        call_count = 0

        def mock_article_views_all_years(langcode, titles, **kwargs):
            nonlocal call_count
            call_count += 1
            return {title: {2020: call_count * 10} for title in titles}

        mock_fetcher = MagicMock()
        mock_fetcher.article_views_all_years.side_effect = mock_article_views_all_years

        service = MultiYearViewsService(views_fetcher=mock_fetcher)

        # Create 1200 titles to test batching (should be 3 batches of 500, 500, 200)
        titles = [f"Art{i}" for i in range(1200)]
        result = service.get_one_lang_views_by_titles("en", titles)

        assert call_count == 3  # Should have made 3 API calls
        assert len(result) == 1200  # Should have all titles in result
