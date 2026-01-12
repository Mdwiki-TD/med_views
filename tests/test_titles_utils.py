"""
Tests
# TODO: Implement test
"""
import pytest

from src.titles_utils import (
    load_lang_titles,
)


import unittest.mock

def test_load_lang_titles(monkeypatch):
    # Scenario 1: load_lang_titles_from_dump returns data
    with unittest.mock.patch("src.titles_utils.load_lang_titles_from_dump") as mock_dump:
        mock_dump.return_value = ["Title 1", "Title 2"]
        result = load_lang_titles("en")
        assert result == ["Title 1", "Title 2"]
        mock_dump.assert_called_once_with("en")

    # Scenario 2: load_lang_titles_from_dump returns empty, 'local' in sys.argv
    with unittest.mock.patch("src.titles_utils.load_lang_titles_from_dump") as mock_dump:
        mock_dump.return_value = []
        monkeypatch.setattr("sys.argv", ["script.py", "local"])
        result = load_lang_titles("en")
        assert result == []
        mock_dump.assert_called_once_with("en")

    # Scenario 3: load_lang_titles_from_dump returns empty, 'local' NOT in sys.argv
    with unittest.mock.patch("src.titles_utils.load_lang_titles_from_dump") as mock_dump, \
         unittest.mock.patch("src.titles_utils.one_lang_titles") as mock_sql:
        
        mock_dump.return_value = []
        mock_sql.return_value = ["Title_1", "Title_2"]
        monkeypatch.setattr("sys.argv", ["script.py"])
        
        result = load_lang_titles("en")
        
        # Verify underscores are replaced
        assert result == ["Title 1", "Title 2"]
        mock_dump.assert_called_once_with("en")
        mock_sql.assert_called_once_with("en")

