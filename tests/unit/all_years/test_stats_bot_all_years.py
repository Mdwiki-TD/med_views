"""
Tests for src.app.all_years.stats_bot_all_years
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from src.app.all_years.stats import MultiYearStatsService
from src.app.config import Config


class TestMultiYearStatsService:
    """Tests for the MultiYearStatsService class."""

    def test_dump_stats_with_single_year_data(self):
        """Test calculating statistics with single year data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config = MagicMock(spec=Config)
            mock_config.main_dump_path = Path(tmpdir)

            service = MultiYearStatsService(config=mock_config)

            articles = ["Art1", "Art2", "Art3"]
            new_data = {
                "Art1": {"2024": 100, "all": 100},
                "Art2": {"2024": 200, "all": 200},
                "Art3": {"2024": 0, "all": 0},
            }

            result = service.dump_stats(articles, new_data, "en")

            assert result["articles"] == 3
            assert result["views"] == 600  # 300 from 2024 + 300 from all
            assert result["empty"] == 1
            assert result["not_empty"] == 2

    def test_dump_stats_with_multi_year_data(self):
        """Test calculating statistics with multi-year data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config = MagicMock(spec=Config)
            mock_config.main_dump_path = Path(tmpdir)

            service = MultiYearStatsService(config=mock_config)

            articles = ["Art1", "Art2"]
            new_data = {
                "Art1": {"2020": 100, "2021": 200, "all": 300},
                "Art2": {"2020": 50, "2021": 75, "all": 125},
            }

            result = service.dump_stats(articles, new_data, "en")

            assert result["articles"] == 2
            # Views sum all int values: (100+200+300) + (50+75+125) = 850
            assert result["views"] == 850

    def test_dump_stats_with_empty_entries(self):
        """Test calculating statistics with empty entries"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config = MagicMock(spec=Config)
            mock_config.main_dump_path = Path(tmpdir)

            service = MultiYearStatsService(config=mock_config)

            articles = ["Art1", "Art2", "Art3"]
            new_data = {
                "Art1": {"2020": 0, "2021": 0, "all": 0},  # All zeros
                "Art2": {"2020": 100, "all": 100},
                "Art3": 0,  # Integer zero
            }

            result = service.dump_stats(articles, new_data, "en")

            assert result["empty"] == 2  # Art1 and Art3
            assert result["not_empty"] == 1  # Art2

    def test_dump_stats_with_missing_entries(self):
        """Test calculating statistics with missing entries"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config = MagicMock(spec=Config)
            mock_config.main_dump_path = Path(tmpdir)

            service = MultiYearStatsService(config=mock_config)

            articles = ["Art1", "Art2", "Art3"]
            new_data = {
                "Art1": {"2020": 100, "all": 100},
                # Art2 and Art3 missing
            }

            result = service.dump_stats(articles, new_data, "en")

            assert result["articles"] == 3
            assert result["empty"] == 2  # Art2 and Art3 are missing (treated as 0)
            # Note: not_empty can be negative when articles are missing from new_data
            # This is existing behavior: not_empty = len(data2) - len(empty)
            assert result["not_empty"] == -1  # len(data2)=1, len(empty)=2

    def test_dump_stats_with_mixed_data_types(self):
        """Test calculating statistics with mixed int and dict data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config = MagicMock(spec=Config)
            mock_config.main_dump_path = Path(tmpdir)

            service = MultiYearStatsService(config=mock_config)

            articles = ["Art1", "Art2", "Art3"]
            new_data = {
                "Art1": {"2020": 100, "all": 100},  # Dict
                "Art2": 50,  # Integer
                "Art3": {"2020": 0, "all": 0},  # Dict with zeros
            }

            result = service.dump_stats(articles, new_data, "en")

            assert result["articles"] == 3
            assert result["views"] == 250  # 200 from Art1 + 50 from Art2
            assert result["empty"] == 1  # Art3

    def test_dump_stats_filters_hash_in_articles_list(self):
        """Test that hash entries in articles list are counted separately"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config = MagicMock(spec=Config)
            mock_config.main_dump_path = Path(tmpdir)

            service = MultiYearStatsService(config=mock_config)

            articles = ["Art1", "Art2#section"]
            new_data = {
                "Art1": {"2020": 100, "all": 100},
                "Art2#section": {"2020": 50, "all": 50},
            }

            result = service.dump_stats(articles, new_data, "en")

            assert result["hash"] == 1
            assert result["views"] == 200  # Only Art1 counted in views

    def test_dump_stats_all(self):
        """Test writing all statistics to files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config = MagicMock(spec=Config)
            mock_config.main_dump_path = Path(tmpdir)

            service = MultiYearStatsService(config=mock_config)

            # Add some stats
            service.stats_all_data = {
                "en": {"articles": 100, "empty": 10, "not_empty": 90, "hash": 5, "views": 5000},
                "ar": {"articles": 50, "empty": 5, "not_empty": 45, "hash": 2, "views": 2500},
            }

            service.dump_stats_all(service.stats_all_data)

            # Check files were created
            summary_file = Path(tmpdir) / "all_years_summary.json"
            stats_file = Path(tmpdir) / "all_years_stats_all.json"

            assert summary_file.exists()
            assert stats_file.exists()

            with open(summary_file) as f:
                summary = json.load(f)
                assert summary["articles"] == 150
                assert summary["total_views"] == 7500
