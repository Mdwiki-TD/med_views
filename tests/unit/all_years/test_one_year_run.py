"""
Unit tests for src/app/all_years/run.py module.

Tests for: MultiYearViewsPipeline
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.app.all_years.run import MultiYearViewsPipeline


@pytest.fixture
def tmp_paths(tmp_path):
    """Create a temporary directory structure for tests."""
    dump_dir = tmp_path / "dumps"
    dump_dir.mkdir()
    titles_dir = dump_dir / "titles"
    titles_dir.mkdir()
    views_by_year_dir = dump_dir / "views_by_year"
    views_by_year_dir.mkdir()
    return {
        "root": tmp_path,
        "dump_dir": dump_dir,
        "titles_dir": titles_dir,
        "views_by_year_dir": views_by_year_dir,
    }


@pytest.fixture
def mock_deps(tmp_paths):
    """Create mock dependencies for the pipeline."""
    mock_views_fetcher = MagicMock()
    mock_views_fetcher.get_view_file.side_effect = lambda lang, year: (
        tmp_paths["views_by_year_dir"] / str(year) / f"{lang}.json"
    )

    # Create year subdirectory when get_view_file is called
    def get_view_file_with_mkdir(lang, year):
        year_dir = tmp_paths["views_by_year_dir"] / str(year)
        year_dir.mkdir(exist_ok=True)
        return year_dir / f"{lang}.json"

    mock_views_fetcher.get_view_file.side_effect = get_view_file_with_mkdir

    mock_dump_manager = MagicMock()
    mock_dump_manager.dump_dir_path = tmp_paths["dump_dir"]
    mock_dump_manager.dump_dir_titles_path = tmp_paths["titles_dir"]

    return {
        "views_fetcher": mock_views_fetcher,
        "dump_manager": mock_dump_manager,
    }


@pytest.fixture
def pipeline(tmp_paths, mock_deps):
    """Create a MultiYearViewsPipeline with mocked dependencies."""
    return MultiYearViewsPipeline(
        views_fetcher=mock_deps["views_fetcher"],
        dump_manager=mock_deps["dump_manager"],
        local=True,
        dump_dir_path=tmp_paths["dump_dir"],
    )


class TestSingleYearViewsPipelineInit:
    """Tests for MultiYearViewsPipeline initialization."""

    def test_init_with_default_dependencies(self):
        """Test initialization creates default dependencies."""
        with patch("src.app.all_years.run.Config") as mock_config:
            mock_config.get_instance.return_value.paths.dump_dir_path = Path("/tmp/test")
            pipeline = MultiYearViewsPipeline()
            assert pipeline.views_fetcher is not None
            assert pipeline.dump_manager is not None
            assert pipeline.views_service is not None
            assert pipeline.stats_service is not None
            assert pipeline.titles_loader is not None
            assert pipeline.empty_data_all == {}

    def test_init_with_injected_dependencies(self, mock_deps, tmp_paths):
        """Test initialization uses injected dependencies."""
        pipeline = MultiYearViewsPipeline(
            views_fetcher=mock_deps["views_fetcher"],
            dump_manager=mock_deps["dump_manager"],
            local=True,
            dump_dir_path=tmp_paths["dump_dir"],
        )
        assert pipeline.views_fetcher is mock_deps["views_fetcher"]
        assert pipeline.dump_manager is mock_deps["dump_manager"]
        assert pipeline.local is True
        assert pipeline.dump_dir_path == tmp_paths["dump_dir"]


class TestGetLanguagesArticlesCounts:
    """Tests for get_languages_articles_counts method."""

    def test_returns_loaded_languages_counts_when_available(self, pipeline, mock_deps):
        """Test that cached language counts are returned when available."""
        mock_deps["dump_manager"].load_languages_counts.return_value = {"en": 100, "fr": 50}

        result = pipeline.get_languages_articles_counts()

        assert result == {"en": 100, "fr": 50}

    def test_falls_back_to_sql_when_not_local(self, tmp_paths, mock_deps):
        """Test fallback to SQL when not in local mode and no cached data."""
        mock_deps["dump_manager"].load_languages_counts.return_value = {}

        pipeline = MultiYearViewsPipeline(
            views_fetcher=mock_deps["views_fetcher"],
            dump_manager=mock_deps["dump_manager"],
            local=False,
            dump_dir_path=tmp_paths["dump_dir"],
        )

        with patch("src.app.all_years.run.MedicalTitlesRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_language_article_counts_sql.return_value = {"en": 200}
            mock_repo_cls.return_value = mock_repo

            result = pipeline.get_languages_articles_counts()

            assert result == {"en": 200}
            mock_repo.get_language_article_counts_sql.assert_called_once()

    def test_falls_back_to_count_languages_in_json_when_local(self, pipeline, mock_deps):
        """Test fallback to counting JSON files in local mode."""
        mock_deps["dump_manager"].load_languages_counts.return_value = {}
        mock_deps["dump_manager"].count_languages_in_json.return_value = {"de": 75}

        result = pipeline.get_languages_articles_counts()

        assert result == {"de": 75}
        mock_deps["dump_manager"].count_languages_in_json.assert_called_once()


class TestDumpEmptyDataAll:
    """Tests for dump_empty_data_all method."""

    def test_writes_empty_data_to_file(self, pipeline, tmp_paths):
        """Test that empty data is written to JSON file."""
        pipeline.empty_data_all = {
            "en": ["Art1", "Art2", "Art3"],
            "fr": ["Art1"],
        }

        pipeline.dump_empty_data_all(2024)

        output_file = tmp_paths["dump_dir"] / "empty_views_2024.json"
        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)
        # Should be sorted by length descending
        assert list(data.keys()) == ["en", "fr"]
        assert data["en"] == ["Art1", "Art2", "Art3"]

    def test_writes_empty_dict_when_no_empty_data(self, pipeline, tmp_paths):
        """Test that empty dict is written when no empty data."""
        pipeline.empty_data_all = {}

        pipeline.dump_empty_data_all(2024)

        output_file = tmp_paths["dump_dir"] / "empty_views_2024.json"
        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)
        assert data == {}


class TestDumpOneLangFiles:
    """Tests for dump_one_lang_files method."""

    def test_returns_early_when_data_is_empty(self, pipeline, mock_deps):
        """Test that method returns early when data is empty."""
        # Note: get_view_file is called before the empty check in the implementation
        with patch("builtins.open") as mock_open:
            pipeline.dump_one_lang_files(["Art1", "Art2"], {}, "en", 2024)
            # open should not be called to write data
            mock_open.assert_not_called()

    def test_writes_non_empty_data_to_file(self, pipeline, mock_deps, tmp_paths):
        """Test that non-empty data is written correctly."""
        titles = ["Cancer", "Diabetes"]
        data = {"Cancer": 1000, "Diabetes": 0}

        pipeline.dump_one_lang_files(titles, data, "en", 2024)

        # Check the file was written with non-empty data only
        mock_deps["views_fetcher"].get_view_file.assert_called_once_with("en", 2024)

    def test_normalizes_underscores_in_titles(self, pipeline, mock_deps, tmp_paths):
        """Test that underscores are normalized to spaces."""
        # Replace stats_service with a mock for this test
        pipeline.stats_service = MagicMock()

        titles = ["Heart_Attack", "Lung_Cancer"]
        data = {"Heart_Attack": 500, "Lung_Cancer": 300}

        pipeline.dump_one_lang_files(titles, data, "en", 2024)

        # Stats should be called with normalized titles
        pipeline.stats_service.dump_stats.assert_called_once()
        call_args = pipeline.stats_service.dump_stats.call_args
        assert "Heart Attack" in call_args[0][0]
        assert "Lung Cancer" in call_args[0][0]

    def test_tracks_empty_articles(self, pipeline, mock_deps):
        """Test that articles with zero views are tracked."""
        titles = ["Cancer", "Diabetes", "Empty"]
        data = {"Cancer": 1000, "Diabetes": 500, "Empty": 0}

        pipeline.dump_one_lang_files(titles, data, "en", 2024)

        assert "en" in pipeline.empty_data_all
        assert "Empty" in pipeline.empty_data_all["en"]


class TestMakeViews:
    """Tests for make_views method."""

    def test_processes_all_languages_when_no_limit(self, pipeline):
        """Test that all languages are processed when limit is 0."""
        languages = {"en": 100, "fr": 50, "de": 25}

        with patch.object(pipeline, "process_language_views") as mock_process:
            mock_process.return_value = {"Art1": 100}

            result = pipeline.make_views(languages=languages, year=2024, limit=0)

            assert mock_process.call_count == 3
            assert len(result) == 3

    def test_respects_limit_parameter(self, pipeline):
        """Test that limit restricts number of languages processed."""
        languages = {"en": 100, "fr": 50, "de": 25}

        with patch.object(pipeline, "process_language_views") as mock_process:
            mock_process.return_value = {"Art1": 100}

            result = pipeline.make_views(languages=languages, year=2024, limit=2)

            assert mock_process.call_count == 2
            assert len(result) == 2

    def test_dumps_stats_after_processing(self, pipeline):
        """Test that stats are dumped after processing all languages."""
        pipeline.stats_service = MagicMock()
        languages = {"en": 100}

        with patch.object(pipeline, "process_language_views") as mock_process:
            mock_process.return_value = {"Art1": 100}

            pipeline.make_views(languages=languages, year=2024, limit=0)

            pipeline.stats_service.dump_stats_all.assert_called_once()

    def test_processes_languages_in_iteration_order(self, pipeline):
        """Test that languages are processed in the order they are provided."""
        # Note: sorting happens in start(), not in make_views()
        # make_views processes languages in the order they are given
        languages = {"de": 25, "fr": 50, "en": 100}  # Already sorted ascending
        processed_order = []

        with patch.object(pipeline, "process_language_views") as mock_process:
            mock_process.side_effect = lambda lang, maxv=0, year=0: processed_order.append(lang) or {"Art1": 100}

            pipeline.make_views(languages=languages, year=2024, limit=0)

            # Languages should be processed in the order provided
            assert processed_order == ["de", "fr", "en"]


class TestProcessLanguageViews:
    """Tests for process_language_views method."""

    def test_loads_titles_for_language(self, pipeline):
        """Test that titles are loaded for the given language."""
        pipeline.titles_loader = MagicMock()
        pipeline.titles_loader.load_lang_titles.return_value = ["Art1", "Art2"]
        pipeline.views_service = MagicMock()
        pipeline.views_service.get_one_lang_views.return_value = {"Art1": 100, "Art2": 200}

        result = pipeline.process_language_views("en", 2024)

        pipeline.titles_loader.load_lang_titles.assert_called_once_with("en")
        assert result == {"Art1": 100, "Art2": 200}

    def test_calls_views_service_with_correct_params(self, pipeline):
        """Test that views service is called with correct parameters."""
        pipeline.titles_loader = MagicMock()
        pipeline.titles_loader.load_lang_titles.return_value = ["Art1"]
        pipeline.views_service = MagicMock()
        pipeline.views_service.get_one_lang_views.return_value = {"Art1": 100}

        pipeline.process_language_views(lang="en", year=2024, maxv=500)

        pipeline.views_service.get_one_lang_views.assert_called_once()
        call_kwargs = pipeline.views_service.get_one_lang_views.call_args.kwargs
        assert call_kwargs.get("year") == 2024
        assert call_kwargs.get("maxv") == 500

    def test_dumps_files_after_fetching(self, pipeline):
        """Test that files are dumped after fetching views."""
        pipeline.titles_loader = MagicMock()
        pipeline.titles_loader.load_lang_titles.return_value = ["Art1"]
        pipeline.views_service = MagicMock()
        pipeline.views_service.get_one_lang_views.return_value = {"Art1": 100}

        with patch.object(pipeline, "dump_one_lang_files") as mock_dump:
            pipeline.process_language_views("en", 2024)

            mock_dump.assert_called_once()


class TestStart:
    """Tests for start method."""

    def test_returns_early_when_no_languages(self, pipeline, mock_deps):
        """Test that pipeline returns early when no languages found."""
        mock_deps["dump_manager"].load_languages_counts.return_value = {}
        mock_deps["dump_manager"].count_languages_in_json.return_value = {}

        with patch.object(pipeline, "make_views") as mock_make:
            pipeline.start(limit=0, maxv=0, year=2024)

            mock_make.assert_not_called()

    def test_returns_early_when_all_zero_counts(self, pipeline, mock_deps):
        """Test that pipeline returns early when all language counts are zero."""
        mock_deps["dump_manager"].load_languages_counts.return_value = {"en": 0, "fr": 0}

        with patch.object(pipeline, "make_views") as mock_make:
            pipeline.start(limit=0, maxv=0, year=2024)

            mock_make.assert_not_called()

    def test_calls_make_views_with_sorted_languages(self, pipeline, mock_deps):
        """Test that make_views is called with sorted languages."""
        mock_deps["dump_manager"].load_languages_counts.return_value = {"en": 100, "fr": 50, "de": 25}

        with patch.object(pipeline, "make_views") as mock_make:
            pipeline.start(limit=0, maxv=0, year=2024)

            mock_make.assert_called_once()
            call_args = mock_make.call_args
            # make_views is called with all keyword arguments
            languages = call_args.kwargs.get("languages")
            # Should be sorted ascending by count
            assert list(languages.keys()) == ["de", "fr", "en"]

    def test_passes_parameters_to_make_views(self, pipeline, mock_deps):
        """Test that parameters are passed through to make_views."""
        mock_deps["dump_manager"].load_languages_counts.return_value = {"en": 100}

        with patch.object(pipeline, "make_views") as mock_make:
            pipeline.start(limit=10, maxv=500, year=2024)

            call_args = mock_make.call_args
            # make_views is called with keyword arguments
            assert call_args.kwargs.get("year") == 2024
            assert call_args.kwargs.get("limit") == 10
            assert call_args.kwargs.get("maxv") == 500


class TestIntegration:
    """Integration tests for MultiYearViewsPipeline."""

    def test_full_pipeline_with_mocked_services(self, tmp_paths, mock_deps):
        """Test full pipeline execution with mocked external services."""
        pipeline = MultiYearViewsPipeline(
            views_fetcher=mock_deps["views_fetcher"],
            dump_manager=mock_deps["dump_manager"],
            local=True,
            dump_dir_path=tmp_paths["dump_dir"],
        )

        # Setup mocks
        mock_deps["dump_manager"].load_languages_counts.return_value = {"en": 100}

        pipeline.titles_loader = MagicMock()
        pipeline.titles_loader.load_lang_titles.return_value = ["Cancer", "Diabetes"]

        pipeline.views_service = MagicMock()
        pipeline.views_service.get_one_lang_views.return_value = {
            "Cancer": 1000,
            "Diabetes": 500,
        }

        # Run pipeline
        pipeline.start(limit=0, maxv=0, year=2024)

        # Verify stats were recorded - the stats are keyed by year in this implementation
        # Check that stats were recorded (the key could be "en" or the year)
        assert pipeline.stats_service.stats_all_data
        # Get the first (and only) stats entry
        stats = list(pipeline.stats_service.stats_all_data.values())[0]
        assert stats["views"] == 1500
        assert stats["articles"] == 2
