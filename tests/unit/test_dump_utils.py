"""
Tests for src.app.dump_utils
"""

import json
from unittest.mock import MagicMock

from src.app.config import Config
from src.app.dump_utils import DumpManager


class TestDumpManager:
    """Tests for the DumpManager class."""

    def test_count_languages_in_json(self, tmp_path):
        """Test counting languages in JSON files."""
        # Create test JSON files
        (tmp_path / "en.json").write_text(json.dumps(["Title1", "Title2"]))
        (tmp_path / "fr.json").write_text(json.dumps(["Title1"]))

        mock_config = MagicMock(spec=Config)
        mock_config.json_titles_path = tmp_path

        manager = DumpManager(config=mock_config)
        result = manager.count_languages_in_json()

        assert result == {"en": 2, "fr": 1}

    def test_load_lang_titles_from_dump(self, tmp_path):
        """Test loading titles from dump file."""
        (tmp_path / "en.json").write_text(json.dumps(["Title_1", "Title_2"]))

        mock_config = MagicMock(spec=Config)
        mock_config.json_titles_path = tmp_path

        manager = DumpManager(config=mock_config)
        result = manager.load_lang_titles_from_dump("en")

        assert result == ["Title 1", "Title 2"]

    def test_load_lang_titles_from_dump_missing_file(self, tmp_path):
        """Test loading from non-existent file returns empty list."""
        mock_config = MagicMock(spec=Config)
        mock_config.json_titles_path = tmp_path

        manager = DumpManager(config=mock_config)
        result = manager.load_lang_titles_from_dump("nonexistent")

        assert result == []

    def test_replace_underscores_dict(self):
        """Test replacing underscores in dict keys."""
        data = {"hello_world": 1, "test_case": 2}
        result = DumpManager.replace_underscores(data)
        assert result == {"hello world": 1, "test case": 2}

    def test_replace_underscores_list(self):
        """Test replacing underscores in list."""
        data = ["hello_world", "test_case"]
        result = DumpManager.replace_underscores(data)
        assert result == ["hello world", "test case"]

    def test_dump_one(self, tmp_path):
        """Test dumping data to file."""
        mock_config = MagicMock(spec=Config)
        manager = DumpManager(config=mock_config)

        file = tmp_path / "test.json"
        data = {"hello_world": 1}
        manager.dump_one(file, data)

        with open(file) as f:
            result = json.load(f)
        assert result == {"hello world": 1}

    def test_dump_one_empty_data(self, tmp_path):
        """Test dumping empty data does nothing."""
        mock_config = MagicMock(spec=Config)
        manager = DumpManager(config=mock_config)

        file = tmp_path / "test.json"
        manager.dump_one(file, [])
        assert not file.exists()

    def test_dump_languages_counts(self, tmp_path):
        """Test dumping language counts."""
        mock_config = MagicMock(spec=Config)
        mock_config.main_dump_path = tmp_path

        manager = DumpManager(config=mock_config)
        data = {"en": 1000, "fr": 500}

        # Need more than 200 entries for file to be written
        data = {f"lang{i}": i for i in range(250)}
        manager.dump_languages_counts(data)

        file = tmp_path / "languages_counts.json"
        assert file.exists()

    def test_load_languages_counts(self, tmp_path):
        """Test loading language counts."""
        mock_config = MagicMock(spec=Config)
        mock_config.main_dump_path = tmp_path

        # Create test file
        data = {"en": 1000, "fr": 500}
        (tmp_path / "languages_counts.json").write_text(json.dumps(data))

        manager = DumpManager(config=mock_config)
        result = manager.load_languages_counts()

        assert result == data

    def test_load_languages_counts_missing_file(self, tmp_path):
        """Test loading missing file returns empty dict."""
        mock_config = MagicMock(spec=Config)
        mock_config.main_dump_path = tmp_path

        manager = DumpManager(config=mock_config)
        result = manager.load_languages_counts()

        assert result == {}
