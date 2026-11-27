"""Additional tests for refactored service classes."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.app.all_years.stats_bot_all_years import MultiYearStatsService
from src.app.all_years.views_all_years import MultiYearViewsService
from src.app.one_year.stats_bot import SingleYearStatsService
from src.app.one_year.views import SingleYearViewsService
from src.app.sql_utils import MedicalTitlesRepository
from src.app.titles_utils import TitlesLoader
from src.app.views_utils.views_helps import ViewsFetcher


class TestMedicalTitlesRepository:
    """Tests for the MedicalTitlesRepository class."""

    def test_get_en_articles(self):
        """Test getting English articles."""
        mock_sql_client = MagicMock()
        mock_sql_client.retrieve_sql_results.return_value = [
            {"page_title": "Cancer"},
            {"page_title": "Diabetes"},
        ]

        repo = MedicalTitlesRepository(sql_client=mock_sql_client)
        result = repo.get_en_articles()

        assert result == ["Cancer", "Diabetes"]
        mock_sql_client.retrieve_sql_results.assert_called_once()

    def test_one_lang_titles_english(self):
        """Test getting English titles uses get_en_articles."""
        mock_sql_client = MagicMock()
        mock_sql_client.retrieve_sql_results.return_value = [{"page_title": "Test"}]

        repo = MedicalTitlesRepository(sql_client=mock_sql_client)
        result = repo.one_lang_titles("en")

        assert result == ["Test"]

    def test_one_lang_titles_other_language(self):
        """Test getting titles for non-English language."""
        mock_sql_client = MagicMock()
        mock_sql_client.retrieve_sql_results.return_value = [{"ll_title": "Cáncer"}]

        repo = MedicalTitlesRepository(sql_client=mock_sql_client)
        result = repo.one_lang_titles("es")

        assert result == ["Cáncer"]

    def test_retrieve_medicine_titles(self):
        """Test retrieving all medicine titles."""
        mock_sql_client = MagicMock()
        mock_sql_client.retrieve_sql_results.side_effect = [
            # First call: retrieve_medicine_titles query
            [
                {"page_title": "Cancer", "ll_lang": "es", "ll_title": "Cáncer"},
                {"page_title": "Cancer", "ll_lang": "fr", "ll_title": "Cancer"},
            ],
            # Second call: get_en_articles query
            [{"page_title": "Cancer"}],
        ]

        repo = MedicalTitlesRepository(sql_client=mock_sql_client)
        result = repo.retrieve_medicine_titles()

        assert "en" in result
        assert "es" in result
        assert "fr" in result


class TestTitlesLoader:
    """Tests for the TitlesLoader class."""

    def test_load_lang_titles_from_dump(self):
        """Test loading titles from dump file."""
        mock_dump_manager = MagicMock()
        mock_dump_manager.load_lang_titles_from_dump.return_value = ["Cancer", "Diabetes"]

        loader = TitlesLoader(dump_manager=mock_dump_manager)
        result = loader.load_lang_titles("en")

        assert result == ["Cancer", "Diabetes"]
        mock_dump_manager.load_lang_titles_from_dump.assert_called_once_with("en")

    def test_load_lang_titles_fallback_to_sql(self):
        """Test fallback to SQL when dump is empty."""
        mock_dump_manager = MagicMock()
        mock_dump_manager.load_lang_titles_from_dump.return_value = []

        mock_titles_repo = MagicMock()
        mock_titles_repo.one_lang_titles.return_value = ["Cancer", "Diabetes"]

        loader = TitlesLoader(dump_manager=mock_dump_manager, titles_repo=mock_titles_repo)

        with patch("sys.argv", []):
            result = loader.load_lang_titles("en")

        assert result == ["Cancer", "Diabetes"]
        mock_titles_repo.one_lang_titles.assert_called_once_with("en")

    def test_load_lang_titles_local_mode(self):
        """Test local mode returns empty when dump is empty."""
        mock_dump_manager = MagicMock()
        mock_dump_manager.load_lang_titles_from_dump.return_value = []

        loader = TitlesLoader(dump_manager=mock_dump_manager)

        with patch("sys.argv", ["local"]):
            result = loader.load_lang_titles("en")

        assert result == []


class TestViewsFetcher:
    """Tests for the ViewsFetcher class."""

    def test_article_views(self):
        """Test fetching article views for a year."""
        mock_client = MagicMock()
        mock_client.article_views_new.return_value = {
            "Cancer": {"2024": 1000, "all": 1000},
            "Diabetes": {"2024": 500, "all": 500},
        }

        fetcher = ViewsFetcher(pageviews_client=mock_client)
        result = fetcher.article_views("en", ["Cancer", "Diabetes"], 2024)

        assert result == {"Cancer": 1000, "Diabetes": 500}

    def test_article_views_all_years(self):
        """Test fetching article views for all years."""
        mock_client = MagicMock()
        mock_client.article_views_new.return_value = {
            "Cancer": {"2020": 800, "2021": 900, "all": 1700},
        }

        fetcher = ViewsFetcher(pageviews_client=mock_client)
        result = fetcher.article_views_all_years("en", ["Cancer"])

        assert "Cancer" in result
        assert result["Cancer"]["all"] == 1700

    def test_article_views_be_x_old_mapping(self):
        """Test be-x-old is mapped to be-tarask."""
        mock_client = MagicMock()
        mock_client.article_views_new.return_value = {}

        fetcher = ViewsFetcher(pageviews_client=mock_client)
        fetcher.article_views("be-x-old", ["Test"], 2024)

        # Check that the project was mapped correctly
        call_args = mock_client.article_views_new.call_args
        assert call_args[0][0] == "be-tarask.wikipedia"


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

    def test_update_data(self):
        """Test merging data with underscore normalization."""
        all_data = {"hello_world": 100}
        data = {"test_case": 200, "hello_world": 0}

        result = SingleYearViewsService.update_data(all_data, data)

        assert result == {"hello world": 100, "test case": 200}

    def test_get_one_lang_views_by_titles(self):
        """Test fetching views for all titles."""
        mock_fetcher = MagicMock()
        mock_fetcher.article_views.return_value = {"Cancer": 1000}

        service = SingleYearViewsService(views_fetcher=mock_fetcher)
        result = service.get_one_lang_views_by_titles("en", ["Cancer"], 2024)

        assert result == {"Cancer": 1000}


class TestSingleYearStatsService:
    """Tests for the SingleYearStatsService class."""

    def test_dump_stats(self):
        """Test calculating statistics for one language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.app.config import Config

            config = Config()
            config.main_dump_path = Path(tmpdir)

            service = SingleYearStatsService(config=config)

            articles = ["Cancer", "Diabetes", "Empty"]
            new_data = {"Cancer": 1000, "Diabetes": 500, "Empty": 0}

            result = service.dump_stats(articles, new_data, "en")

            assert result["articles"] == 3
            assert result["views"] == 1500
            assert result["empty"] == 1
            assert result["not_empty"] == 2

    def test_dump_stats_all(self):
        """Test writing all statistics to files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.app.config import Config

            config = Config()
            config.main_dump_path = Path(tmpdir)

            service = SingleYearStatsService(config=config)

            # Add some stats
            service._stats_all_data = {
                "en": {"articles": 100, "empty": 10, "not_empty": 90, "hash": 5, "views": 5000},
                "ar": {"articles": 50, "empty": 5, "not_empty": 45, "hash": 2, "views": 2500},
            }

            service.dump_stats_all(2024)

            # Check files were created
            summary_file = Path(tmpdir) / "2024_summary.json"
            stats_file = Path(tmpdir) / "2024_stats_all.json"

            assert summary_file.exists()
            assert stats_file.exists()

            with open(summary_file) as f:
                summary = json.load(f)
                assert summary["articles"] == 150
                assert summary["total_views"] == 7500


class TestMultiYearViewsService:
    """Tests for the MultiYearViewsService class."""

    def test_calculate_total_views(self):
        """Test calculating total views across years."""
        data = {"Cancer": {"all": 1000, "2024": 500}}
        result = MultiYearViewsService.calculate_total_views("en", data)
        assert result == 1000

    def test_update_data(self):
        """Test merging multi-year data."""
        all_data = {"hello_world": {"all": 100}}
        data = {"test_case": {"all": 200}}

        result = MultiYearViewsService.update_data(all_data, data)

        assert "hello world" in result
        assert "test case" in result


class TestMultiYearStatsService:
    """Tests for the MultiYearStatsService class."""

    def test_dump_stats_with_dict_values(self):
        """Test calculating statistics with dict values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.app.config import Config

            config = Config()
            config.main_dump_path = Path(tmpdir)

            service = MultiYearStatsService(config=config)

            articles = ["Cancer", "Diabetes"]
            new_data = {
                "Cancer": {"2024": 500, "2023": 400, "all": 900},
                "Diabetes": {"2024": 200, "2023": 100, "all": 300},
            }

            result = service.dump_stats(articles, new_data, "en")

            assert result["articles"] == 2
            # Views sum all int values in each dict: (500+400+900) + (200+100+300) = 2400
            assert result["views"] == 2400

    def test_dump_stats_all(self):
        """Test writing all statistics to files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.app.config import Config

            config = Config()
            config.main_dump_path = Path(tmpdir)

            service = MultiYearStatsService(config=config)
            service._stats_all_data = {
                "en": {"articles": 100, "empty": 10, "not_empty": 90, "hash": 5, "views": 5000},
            }

            service.dump_stats_all()

            summary_file = Path(tmpdir) / "all_years_summary.json"
            assert summary_file.exists()


class TestServiceLegacyCompatibility:
    """Tests for legacy function compatibility of service classes."""

    def test_sql_utils_legacy_functions(self):
        """Test legacy sql_utils functions."""
        from src.app.sql_utils import get_en_articles

        mock_sql_client = MagicMock()
        mock_sql_client.retrieve_sql_results.return_value = [{"page_title": "Test"}]

        with patch("src.app.sql_utils.MedicalTitlesRepository") as MockRepo:
            MockRepo.return_value.get_en_articles.return_value = ["Test"]
            result = get_en_articles()
            assert result == ["Test"]

    def test_views_helps_legacy_functions(self):
        """Test legacy views_helps functions."""
        from src.app.views_utils.views_helps import article_views

        mock_fetcher = MagicMock()
        mock_fetcher.article_views.return_value = {"Cancer": 1000}

        with patch("src.app.views_utils.views_helps.ViewsFetcher", return_value=mock_fetcher):
            result = article_views("en", ["Cancer"], 2024)
            assert result == {"Cancer": 1000}

    def test_one_year_views_legacy_functions(self):
        """Test legacy one_year.views functions."""
        from src.app.one_year.views import calculate_total_views, update_data

        assert calculate_total_views("en", {"a": 100}) == 100
        assert update_data({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}

    def test_all_years_views_legacy_functions(self):
        """Test legacy all_years.views_all_years functions."""
        from src.app.all_years.views_all_years import calculate_total_views, update_data

        assert calculate_total_views("en", {"a": {"all": 100}}) == 100
        assert update_data({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}
