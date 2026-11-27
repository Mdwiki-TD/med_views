"""
Tests for src.app.titles_utils
"""

from unittest.mock import MagicMock

from src.app.titles_utils import TitlesLoader


class TestTitlesLoader:
    """Tests for the TitlesLoader class."""

    def test_load_lang_titles_from_dump(self):
        """Test loading titles from dump file."""
        mock_dump_manager = MagicMock()
        mock_dump_manager.load_lang_titles_from_dump.return_value = ["Title 1", "Title 2"]

        loader = TitlesLoader(dump_manager=mock_dump_manager)
        result = loader.load_lang_titles("en")

        assert result == ["Title 1", "Title 2"]
        mock_dump_manager.load_lang_titles_from_dump.assert_called_once_with("en")

    def test_load_lang_titles_fallback_to_sql(self):
        """Test fallback to SQL when dump is empty."""
        mock_dump_manager = MagicMock()
        mock_dump_manager.load_lang_titles_from_dump.return_value = []

        mock_titles_repo = MagicMock()
        mock_titles_repo.one_lang_titles.return_value = ["Title_1", "Title_2"]

        loader = TitlesLoader(dump_manager=mock_dump_manager, titles_repo=mock_titles_repo)

        import sys

        original_argv = sys.argv
        try:
            sys.argv = ["script.py"]
            result = loader.load_lang_titles("en")
        finally:
            sys.argv = original_argv

        assert result == ["Title 1", "Title 2"]
        mock_titles_repo.one_lang_titles.assert_called_once_with("en")

    def test_load_lang_titles_local_mode(self):
        """Test local mode returns empty when dump is empty."""
        mock_dump_manager = MagicMock()
        mock_dump_manager.load_lang_titles_from_dump.return_value = []

        loader = TitlesLoader(dump_manager=mock_dump_manager)

        import sys

        original_argv = sys.argv
        try:
            sys.argv = ["script.py", "local"]
            result = loader.load_lang_titles("en")
        finally:
            sys.argv = original_argv

        assert result == []
