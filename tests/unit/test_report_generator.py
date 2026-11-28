"""
Tests for src.app.report_generator module.
"""

import json
from unittest.mock import MagicMock, patch

from src.app.report_generator import ReportGenerator


class TestReportGenerator:
    """Tests for the ReportGenerator class."""

    def test_init_defaults(self, tmp_path):
        """Test initialization with default values."""
        with patch("src.app.report_generator.Config") as mock_config:
            mock_config.get_instance.return_value.paths.dump_dir_path = tmp_path

            generator = ReportGenerator()

            assert generator.save is True
            assert generator.dump_dir_path == tmp_path

    def test_init_with_save_false(self, tmp_path):
        """Test initialization with save=False."""
        with patch("src.app.report_generator.Config") as mock_config:
            mock_config.get_instance.return_value.paths.dump_dir_path = tmp_path

            generator = ReportGenerator(save=False)

            assert generator.save is False

    def test_get_languages_articles_counts_from_file(self, tmp_path):
        """Test get_languages_articles_counts loads from file."""
        data = {"en": 1000, "fr": 500}
        (tmp_path / "languages_titles_counts.json").write_text(json.dumps(data))

        mock_dump_manager = MagicMock()
        mock_dump_manager.load_languages_counts.return_value = data

        with patch("src.app.report_generator.Config") as mock_config:
            mock_config.get_instance.return_value.paths.dump_dir_path = tmp_path

            generator = ReportGenerator(dump_manager=mock_dump_manager)
            result = generator.get_languages_articles_counts()

            assert result == data

    def test_get_languages_articles_counts_fallback(self, tmp_path):
        """Test get_languages_articles_counts falls back to counting files."""
        mock_dump_manager = MagicMock()
        mock_dump_manager.load_languages_counts.return_value = {}
        mock_dump_manager.count_languages_in_json.return_value = {"en": 100, "de": 50}

        with patch("src.app.report_generator.Config") as mock_config:
            mock_config.get_instance.return_value.paths.dump_dir_path = tmp_path

            generator = ReportGenerator(dump_manager=mock_dump_manager)
            result = generator.get_languages_articles_counts()

            assert result == {"en": 100, "de": 50}

    def test_calculate_total_views_with_int_values(self):
        """Test calculate_total_views with integer values."""
        generator = ReportGenerator.__new__(ReportGenerator)
        data = {"Cancer": 1000, "Diabetes": 500}

        result = generator.calculate_total_views("en", data)

        assert result == 1500

    def test_calculate_total_views_with_dict_values(self):
        """Test calculate_total_views with dict values containing 'all' key."""
        generator = ReportGenerator.__new__(ReportGenerator)
        data = {"Cancer": {"all": 1000, "2024": 800}, "Diabetes": {"all": 500}}

        result = generator.calculate_total_views("en", data)

        assert result == 1500

    def test_calculate_total_views_with_none(self):
        """Test calculate_total_views with None returns 0."""
        generator = ReportGenerator.__new__(ReportGenerator)

        result = generator.calculate_total_views("en", None)

        assert result == 0

    def test_calculate_total_views_empty(self):
        """Test calculate_total_views with empty data returns 0."""
        generator = ReportGenerator.__new__(ReportGenerator)

        result = generator.calculate_total_views("en", {})

        assert result == 0

    def test_fetch_language_statistics(self, tmp_path):
        """Test fetch_language_statistics loads and calculates views."""
        mock_dump_manager = MagicMock()
        mock_dump_manager.json_load.return_value = {"Art1": 100, "Art2": 200}

        mock_views_fetcher = MagicMock()
        mock_views_fetcher.get_view_file.return_value = tmp_path / "en.json"

        with patch("src.app.report_generator.Config") as mock_config:
            mock_config.get_instance.return_value.paths.dump_dir_path = tmp_path

            generator = ReportGenerator(
                dump_manager=mock_dump_manager,
                views_fetcher=mock_views_fetcher,
            )
            result = generator.fetch_language_statistics(2024, "en")

            assert result == 300

    def test_fetch_language_statistics_invalid_data(self, tmp_path):
        """Test fetch_language_statistics handles non-dict data."""
        mock_dump_manager = MagicMock()
        mock_dump_manager.json_load.return_value = ["not", "a", "dict"]

        mock_views_fetcher = MagicMock()
        mock_views_fetcher.get_view_file.return_value = tmp_path / "en.json"

        with patch("src.app.report_generator.Config") as mock_config:
            mock_config.get_instance.return_value.paths.dump_dir_path = tmp_path

            generator = ReportGenerator(
                dump_manager=mock_dump_manager,
                views_fetcher=mock_views_fetcher,
            )
            result = generator.fetch_language_statistics(2024, "en")

            assert result == 0

    def test_make_views_local(self, tmp_path):
        """Test make_views_local iterates through languages."""
        mock_views_fetcher = MagicMock()

        with patch("src.app.report_generator.Config") as mock_config:
            mock_config.get_instance.return_value.paths.dump_dir_path = tmp_path

            generator = ReportGenerator(views_fetcher=mock_views_fetcher)
            generator.fetch_language_statistics = MagicMock(side_effect=[100, 200, 0])

            languages = {"en": 1000, "fr": 500, "de": 200}
            result = generator.make_views_local(languages, 2024, limit=0)

            assert result == {"en": 100, "fr": 200, "de": 0}

    def test_make_views_local_with_limit(self, tmp_path):
        """Test make_views_local respects limit."""
        mock_views_fetcher = MagicMock()

        with patch("src.app.report_generator.Config") as mock_config:
            mock_config.get_instance.return_value.paths.dump_dir_path = tmp_path

            generator = ReportGenerator(views_fetcher=mock_views_fetcher)
            generator.fetch_language_statistics = MagicMock(return_value=100)

            languages = {"en": 1000, "fr": 500, "de": 200}
            result = generator.make_views_local(languages, 2024, limit=2)

            assert len(result) == 2

    def test_make_page_text_no_languages(self, tmp_path):
        """Test make_page_text returns None when no languages."""
        mock_dump_manager = MagicMock()
        mock_dump_manager.load_languages_counts.return_value = {}
        mock_dump_manager.count_languages_in_json.return_value = {}

        with patch("src.app.report_generator.Config") as mock_config:
            mock_config.get_instance.return_value.paths.dump_dir_path = tmp_path

            generator = ReportGenerator(dump_manager=mock_dump_manager)
            result = generator.make_page_text(2024, limit=0)

            assert result is None

    def test_make_page_text_no_views(self, tmp_path):
        """Test make_page_text returns None when all views are 0."""
        mock_dump_manager = MagicMock()
        mock_dump_manager.load_languages_counts.return_value = {"en": 100}

        mock_views_fetcher = MagicMock()

        with patch("src.app.report_generator.Config") as mock_config:
            mock_config.get_instance.return_value.paths.dump_dir_path = tmp_path

            generator = ReportGenerator(
                dump_manager=mock_dump_manager,
                views_fetcher=mock_views_fetcher,
            )
            generator.fetch_language_statistics = MagicMock(return_value=0)
            result = generator.make_page_text(2024, limit=0)

            assert result is None

    def test_make_page_text_success(self, tmp_path):
        """Test make_page_text generates text successfully."""
        mock_dump_manager = MagicMock()
        mock_dump_manager.load_languages_counts.return_value = {"en": 100}

        mock_views_fetcher = MagicMock()

        mock_wiki_builder = MagicMock()
        mock_wiki_builder.build_wiki_text.return_value = "Generated wiki text"

        with patch("src.app.report_generator.Config") as mock_config:
            mock_config.get_instance.return_value.paths.dump_dir_path = tmp_path

            generator = ReportGenerator(
                dump_manager=mock_dump_manager,
                views_fetcher=mock_views_fetcher,
                wiki_builder=mock_wiki_builder,
            )
            generator.fetch_language_statistics = MagicMock(return_value=500)
            result = generator.make_page_text(2024, limit=0)

            assert result == "Generated wiki text"
            # Should dump views and text files
            assert (tmp_path / "2024_views_by_lang.json").exists()
            assert (tmp_path / "2024_text.txt").exists()

    def test_start_dry_run(self, tmp_path):
        """Test start with save=False doesn't upload."""
        mock_dump_manager = MagicMock()
        mock_dump_manager.load_languages_counts.return_value = {}

        with patch("src.app.report_generator.Config") as mock_config:
            mock_config.get_instance.return_value.paths.dump_dir_path = tmp_path

            generator = ReportGenerator(
                dump_manager=mock_dump_manager,
                save=False,
            )
            # Should not raise, just return
            generator.start(2024, limit=0)
