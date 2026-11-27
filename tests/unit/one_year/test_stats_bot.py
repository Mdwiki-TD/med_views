"""
Tests for src.app.one_year.stats
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from src.app.config import Config
from src.app.one_year.stats import SingleYearStatsService


class TestSingleYearStatsService:
    """Tests for the SingleYearStatsService class."""

    def test_dump_stats(self):
        """Test calculating statistics for one language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config = MagicMock(spec=Config)
            mock_config.main_dump_path = Path(tmpdir)

            service = SingleYearStatsService(config=mock_config)

            articles = ["Cancer", "Diabetes", "Empty"]
            new_data = {"Cancer": 1000, "Diabetes": 500, "Empty": 0}

            result = service.dump_stats(articles, new_data, "en")

            assert result["articles"] == 3
            assert result["views"] == 1500
            assert result["empty"] == 1
            assert result["not_empty"] == 2

    def test_dump_stats_filters_hash(self):
        """Test that hash entries are filtered out."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config = MagicMock(spec=Config)
            mock_config.main_dump_path = Path(tmpdir)

            service = SingleYearStatsService(config=mock_config)

            articles = ["Cancer", "Test#section"]
            new_data = {"Cancer": 1000, "Test#section": 500}

            result = service.dump_stats(articles, new_data, "en")

            assert result["hash"] == 1
            assert result["views"] == 1000  # Only Cancer counted

    def test_dump_stats_all(self):
        """Test writing all statistics to files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config = MagicMock(spec=Config)
            mock_config.main_dump_path = Path(tmpdir)

            service = SingleYearStatsService(config=mock_config)

            # Add some stats
            service.stats_all_data = {
                "en": {"articles": 100, "empty": 10, "not_empty": 90, "hash": 5, "views": 5000},
                "ar": {"articles": 50, "empty": 5, "not_empty": 45, "hash": 2, "views": 2500},
            }

            service.dump_stats_all(2024, service.stats_all_data)

            # Check files were created
            summary_file = Path(tmpdir) / "2024_summary.json"
            stats_file = Path(tmpdir) / "2024_stats_all.json"

            assert summary_file.exists()
            assert stats_file.exists()

            with open(summary_file) as f:
                summary = json.load(f)
                assert summary["articles"] == 150
                assert summary["total_views"] == 7500
