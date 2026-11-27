"""
Tests for src.app.views_utils.views_helps
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from src.app.config import Config
from src.app.views_utils.views_helps import ViewsFetcher


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

    def test_article_views_all_years_be_x_old_mapping(self):
        """Test be-x-old is mapped to be-tarask for all years."""
        mock_client = MagicMock()
        mock_client.article_views_new.return_value = {}

        fetcher = ViewsFetcher(pageviews_client=mock_client)
        fetcher.article_views_all_years("be-x-old", ["Test"])

        # Check that the project was mapped correctly
        call_args = mock_client.article_views_new.call_args
        assert call_args[0][0] == "be-tarask.wikipedia"

    def test_get_view_file(self):
        """Test computing view file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config = MagicMock(spec=Config)
            mock_config.views_by_year_path = Path(tmpdir)

            fetcher = ViewsFetcher(config=mock_config)
            result = fetcher.get_view_file("en", 2024)

            expected_dir = Path(tmpdir) / "2024"
            expected_file = expected_dir / "en.json"

            assert result == expected_file
            assert expected_dir.exists()
