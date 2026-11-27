"""
Tests for src.app.helps
"""

import json
import tempfile
from pathlib import Path

from src.app.helps import JsonHelper


class TestJsonHelper:
    """Tests for the JsonHelper class."""

    def test_is_empty_data_none(self):
        """Test None data is empty."""
        assert JsonHelper.is_empty_data(None) is True

    def test_is_empty_data_empty_dict(self):
        """Test empty dict is empty."""
        assert JsonHelper.is_empty_data({}) is True

    def test_is_empty_data_zero_all(self):
        """Test dict with all=0 is empty."""
        assert JsonHelper.is_empty_data({"all": 0}) is True

    def test_is_empty_data_single_key(self):
        """Test dict with single key is empty."""
        assert JsonHelper.is_empty_data({"key": "value"}) is True

    def test_is_empty_data_not_empty(self):
        """Test non-empty dict."""
        assert JsonHelper.is_empty_data({"all": 100, "2024": 100}) is False

    def test_json_load_with_underscores(self):
        """Test loading JSON normalizes underscores."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"hello_world": 1, "test_case": 2}, f)
            temp_path = f.name

        result = JsonHelper.json_load(temp_path)
        assert result == {"hello world": 1, "test case": 2}

        Path(temp_path).unlink()

    def test_json_load_list(self):
        """Test loading JSON list normalizes underscores."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(["hello_world", "test_case"], f)
            temp_path = f.name

        result = JsonHelper.json_load(temp_path)
        assert result == ["hello world", "test case"]

        Path(temp_path).unlink()

    def test_json_load_missing_file(self):
        """Test loading missing file returns None."""
        result = JsonHelper.json_load("/nonexistent/file.json")
        assert result is None
