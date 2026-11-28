"""
Tests for src.app.dump_utils
"""

import json
import tempfile
from pathlib import Path

from src.app.io.dump_utils import DumpManager


class TestDumpManagerJSONLoad:
    """Tests for the DumpManager.json_load ."""

    def test_json_load_with_underscores(self):
        """Test loading JSON normalizes underscores."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"hello_world": 1, "test_case": 2}, f)
            temp_path = f.name

        result = DumpManager.json_load(temp_path)
        assert result == {"hello world": 1, "test case": 2}

        Path(temp_path).unlink()

    def test_json_load_list(self):
        """Test loading JSON list normalizes underscores."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(["hello_world", "test_case"], f)
            temp_path = f.name

        result = DumpManager.json_load(temp_path)
        assert result == ["hello world", "test case"]

        Path(temp_path).unlink()

    def test_json_load_missing_file(self):
        """Test loading missing file returns None."""
        result = DumpManager.json_load("/nonexistent/file.json")
        assert result is None


class TestDumpManager:
    """Tests for the DumpManager class."""

    def test_count_languages_in_json(self, tmp_path):
        """Test counting languages in JSON files."""
        # Create test JSON files
        titles_path = tmp_path / "titles"
        titles_path.mkdir()

        (titles_path / "en.json").write_text(json.dumps(["Title1", "Title2"]))
        (titles_path / "fr.json").write_text(json.dumps(["Title1"]))

        manager = DumpManager(dump_dir_path=tmp_path, dump_dir_titles_path=titles_path)
        result = manager.count_languages_in_json()

        assert result == {"en": 2, "fr": 1}

    def test_load_lang_titles_from_dump(self, tmp_path):
        """Test loading titles from dump file."""
        titles_path = tmp_path / "titles"
        titles_path.mkdir()

        (titles_path / "en.json").write_text(json.dumps(["Title_1", "Title_2"]))

        manager = DumpManager(dump_dir_path=tmp_path, dump_dir_titles_path=titles_path)
        result = manager.load_lang_titles_from_dump("en")

        assert result == ["Title 1", "Title 2"]

    def test_load_lang_titles_from_dump_missing_file(self, tmp_path):
        """Test loading from non-existent file returns empty list."""
        titles_path = tmp_path / "titles"
        titles_path.mkdir()

        manager = DumpManager(dump_dir_path=tmp_path, dump_dir_titles_path=titles_path)
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
        manager = DumpManager(dump_dir_path=tmp_path)

        file = tmp_path / "test.json"
        data = {"hello_world": 1}
        manager.dump_one(file, data)

        with open(file) as f:
            result = json.load(f)
        assert result == {"hello world": 1}

    def test_dump_one_empty_data(self, tmp_path):
        """Test dumping empty data does nothing."""
        manager = DumpManager(dump_dir_path=tmp_path)

        file = tmp_path / "test.json"
        manager.dump_one(file, [])
        assert not file.exists()

    def test_dump_languages_counts(self, tmp_path):
        """Test dumping language counts."""

        manager = DumpManager(dump_dir_path=tmp_path)
        data = {"en": 1000, "fr": 500}

        # Need more than 200 entries for file to be written
        data = {f"lang{i}": i for i in range(250)}
        manager.dump_languages_counts(data)

        file = tmp_path / "languages_counts.json"
        assert file.exists()

    def test_load_languages_counts(self, tmp_path):
        """Test loading language counts."""

        # Create test file
        data = {"en": 1000, "fr": 500}
        (tmp_path / "languages_counts.json").write_text(json.dumps(data))

        manager = DumpManager(dump_dir_path=tmp_path)
        result = manager.load_languages_counts()

        assert result == data

    def test_load_languages_counts_missing_file(self, tmp_path):
        """Test loading missing file returns empty dict."""

        manager = DumpManager(dump_dir_path=tmp_path)
        result = manager.load_languages_counts()

        assert result == {}
