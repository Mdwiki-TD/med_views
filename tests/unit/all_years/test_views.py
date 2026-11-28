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

    def test_get_one_lang_views_by_titles_with_year(self):
        """Test get_one_lang_views_by_titles with specific year"""
        mock_fetcher = MagicMock()
        mock_fetcher.article_views.return_value = {"Art1": 100}

        service = MultiYearViewsService(views_fetcher=mock_fetcher)
        result = service.get_one_lang_views_by_titles("en", ["Art1"], year=2024)

        mock_fetcher.article_views.assert_called_once()
        assert result == {"Art1": 100}

    def test_load_one_lang_views_zero_true(self):
        """Test load_one_lang_views returns zeros when zero=True"""
        service = MultiYearViewsService(zero=True)
        result = service.load_one_lang_views("en", ["Art1", "Art2"])

        assert result == {"Art1": 0, "Art2": 0}

    def test_load_one_lang_views_zero_false(self):
        """Test load_one_lang_views fetches data when zero=False"""
        mock_fetcher = MagicMock()
        mock_fetcher.article_views_all_years.return_value = {"Art1": {2020: 100}}

        service = MultiYearViewsService(views_fetcher=mock_fetcher, zero=False)
        result = service.load_one_lang_views("en", ["Art1"])

        assert result == {"Art1": {2020: 100}}

    def test_load_one_lang_views_with_year(self):
        """Test load_one_lang_views passes year to fetcher"""
        mock_fetcher = MagicMock()
        mock_fetcher.article_views.return_value = {"Art1": 500}

        service = MultiYearViewsService(views_fetcher=mock_fetcher, zero=False)
        result = service.load_one_lang_views("en", ["Art1"], year=2024)

        mock_fetcher.article_views.assert_called_once()
        assert result == {"Art1": 500}

    def test_get_one_lang_views_from_cache(self, tmp_path):
        """Test get_one_lang_views loads from cache file"""
        json_file = tmp_path / "en.json"
        json_file.write_text('{"Art1": {"all": 100}, "Art2": {"all": 200}}')

        mock_fetcher = MagicMock()
        service = MultiYearViewsService(views_fetcher=mock_fetcher, local=True)

        result = service.get_one_lang_views("en", ["Art1", "Art2"], json_file)

        # Should not call fetcher because local=True
        mock_fetcher.article_views_all_years.assert_not_called()
        assert result == {"Art1": {"all": 100}, "Art2": {"all": 200}}

    def test_get_one_lang_views_missing_cache(self, tmp_path):
        """Test get_one_lang_views handles missing cache file"""
        json_file = tmp_path / "nonexistent.json"

        mock_fetcher = MagicMock()
        mock_fetcher.article_views_all_years.return_value = {"Art1": {2020: 100}}

        service = MultiYearViewsService(views_fetcher=mock_fetcher, local=True)
        result = service.get_one_lang_views("en", ["Art1"], json_file)

        # With local=True and missing file, returns empty dict
        assert result == {}

    def test_get_one_lang_views_fetches_missing_titles(self, tmp_path):
        """Test get_one_lang_views fetches titles not in cache"""
        json_file = tmp_path / "en.json"
        json_file.write_text('{"Art1": {"all": 100}}')

        mock_fetcher = MagicMock()
        mock_fetcher.article_views_all_years.return_value = {"Art2": {2020: 200}}

        service = MultiYearViewsService(views_fetcher=mock_fetcher, local=False)
        result = service.get_one_lang_views("en", ["Art1", "Art2"], json_file)

        assert "Art1" in result
        assert "Art2" in result

    def test_get_one_lang_views_maxv_skip(self, tmp_path):
        """Test get_one_lang_views skips when titles exceed maxv"""
        json_file = tmp_path / "en.json"
        # File doesn't exist, so all 100 titles are "not in file"

        mock_fetcher = MagicMock()
        service = MultiYearViewsService(views_fetcher=mock_fetcher, local=False)

        titles = [f"Art{i}" for i in range(100)]
        result = service.get_one_lang_views("en", titles, json_file, maxv=50)

        # Should not fetch because len(titles_not_in_file) > maxv
        mock_fetcher.article_views_all_years.assert_not_called()
        assert result == {}

    def test_get_one_lang_views_normalizes_underscores(self, tmp_path):
        """Test get_one_lang_views normalizes underscores in titles"""
        json_file = tmp_path / "en.json"
        json_file.write_text('{"hello_world": {"all": 100}}')

        mock_fetcher = MagicMock()
        service = MultiYearViewsService(views_fetcher=mock_fetcher, local=True)

        result = service.get_one_lang_views("en", ["hello_world"], json_file)

        assert "hello world" in result


class TestSingleYearViewsService:
    """Tests for the MultiYearViewsService class."""

    def test_calculate_total_views(self):
        """Test calculating total views."""
        data = {"Cancer": 1000, "Diabetes": 500}
        result = MultiYearViewsService.calculate_total_views("en", data)
        assert result == 1500

    def test_calculate_total_views_with_dict(self):
        """Test calculating total views with dict values."""
        data = {"Cancer": {"all": 1000, "2024": 1000}}
        result = MultiYearViewsService.calculate_total_views("en", data)
        assert result == 1000

    def test_calculate_total_views_empty(self):
        """Test calculating total views with empty data."""
        result = MultiYearViewsService.calculate_total_views("fr", {})
        assert result == 0

    def test_get_one_lang_views_by_titles(self):
        """Test fetching views for all titles."""
        mock_fetcher = MagicMock()
        mock_fetcher.article_views.return_value = {"Cancer": 1000}

        service = MultiYearViewsService(views_fetcher=mock_fetcher)
        result = service.get_one_lang_views_by_titles("en", ["Cancer"], 2024)

        assert result == {"Cancer": 1000}

    def test_get_one_lang_views_by_titles_batching(self):
        """Test that get_one_lang_views_by_titles batches requests in groups of 500."""
        mock_fetcher = MagicMock()
        mock_fetcher.article_views.return_value = {}

        service = MultiYearViewsService(views_fetcher=mock_fetcher)

        # Create 1200 titles to test batching (should be 3 batches of 500, 500, 200)
        titles = [f"Art{i}" for i in range(1200)]
        service.get_one_lang_views_by_titles("en", titles, 2024)

        assert mock_fetcher.article_views.call_count == 3  # Should have made 3 API calls
